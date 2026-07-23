import hashlib
import json
import logging
import os
import time
import uuid
from collections import OrderedDict

import pymysql
from fastapi import APIRouter, UploadFile, File, HTTPException, Request

from app.core.settings import settings
from app.core.exceptions import InvalidImageError
from app.services.image_analyze.analyze import ImageAnalyzeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image-analyze", tags=["ImageAnalyze"])

MAX_UPLOAD_BYTES = settings.max_upload_size_mb * 1024 * 1024

# 완전히 동일한 이미지가 다시 들어오면 탐지/OCR/검색/LLM을 다시 안 돌리고
# 이전 결과를 그대로 반환하기 위한 캐시. 이미지 바이트의 해시를 키로 쓴다.
# (서버 프로세스가 살아있는 동안만 유지되는 메모리 캐시. 재배포/재시작하면 비워짐.)
_ANALYZE_CACHE_MAX_SIZE = 200
_analyze_cache: "OrderedDict[str, dict]" = OrderedDict()


def _cache_get(key: str):
    """메모리 캐시에서 이미지 해시로 이전 분석 결과를 찾는다. 없으면 None."""
    if key in _analyze_cache:
        _analyze_cache.move_to_end(key)  # 최근 사용으로 갱신
        return _analyze_cache[key]
    return None


def _cache_set(key: str, value: dict):
    """분석 결과를 메모리 캐시에 저장한다. 최대 개수를 넘으면 가장 오래된 항목부터 지운다."""
    _analyze_cache[key] = value
    _analyze_cache.move_to_end(key)
    if len(_analyze_cache) > _ANALYZE_CACHE_MAX_SIZE:
        _analyze_cache.popitem(last=False)  # 가장 오래된 항목 제거


# 메모리 캐시 미스일 때만 확인하는 DB 백업 계층 (image_analyze_cache 테이블).
# 서버 재시작으로 메모리 캐시가 비어도, DB에 이미 있던 이미지는 파이프라인을
# 다시 돌리지 않고 여기서 채워서 반환한다.

def _db_cache_get(image_hash: str) -> dict | None:
    """DB 캐시 테이블에서 이미지 해시로 이전 분석 결과를 찾는다. 없거나 오류가 나면 None."""
    conn = pymysql.connect(
        host=settings.db_host, port=settings.db_port, user=settings.db_user,
        password=settings.db_password, db=settings.db_name, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT result_json FROM image_analyze_cache WHERE image_hash = %s",
                (image_hash,),
            )
            row = cursor.fetchone()
            return json.loads(row["result_json"]) if row else None
    except Exception as e:
        print(f"[image_analyze] DB 캐시 조회 오류: {e}")
        return None
    finally:
        conn.close()


def _db_cache_set(image_hash: str, result: dict) -> None:
    """분석 결과를 DB 캐시 테이블에 저장(이미 있으면 갱신)한다."""
    conn = pymysql.connect(
        host=settings.db_host, port=settings.db_port, user=settings.db_user,
        password=settings.db_password, db=settings.db_name, charset="utf8mb4",
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO image_analyze_cache (image_hash, result_json)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    result_json = VALUES(result_json),
                    last_used_at = CURRENT_TIMESTAMP
                """,
                (image_hash, json.dumps(result, ensure_ascii=False)),
            )
        conn.commit()
    except Exception as e:
        print(f"[image_analyze] DB 캐시 저장 오류: {e}")
    finally:
        conn.close()


def get_image_analyze_service(request: Request) -> ImageAnalyzeService:
    """앱 시작 시 만들어 둔 ImageAnalyzeService 인스턴스를 꺼내온다."""
    return request.app.state.image_analyze_service


# C 이미지 분석 (탐지 -> OCR -> 정책 검색 -> LLM 요약)
# 업로드된 이미지를 임시 저장 후 파이프라인을 돌리고, 끝나면 임시 파일은 지운다.
# 같은 이미지가 다시 오면 메모리 캐시 -> DB 캐시 순으로 확인해 파이프라인 재실행을 건너뛴다.
@router.post("/")
async def analyze_image(request: Request, file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    image_analyze_service = get_image_analyze_service(request)

    tmp_path = os.path.join(settings.temp_upload_dir, f"{uuid.uuid4().hex}_{file.filename}")
    try:
        content = await file.read()

        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"이미지 파일이 너무 커요. {settings.max_upload_size_mb}MB 이하로 업로드해주세요.",
            )

        image_hash = hashlib.sha256(content).hexdigest()
        cached = _cache_get(image_hash)
        if cached is not None:
            print(f"[cache] 메모리 hit ({image_hash[:8]}...) - 파이프라인 재실행 없이 즉시 반환")
            return cached

        db_cached = _db_cache_get(image_hash)
        if db_cached is not None:
            print(f"[cache] DB hit ({image_hash[:8]}...) - 파이프라인 재실행 없이 즉시 반환, 메모리에 적재")
            _cache_set(image_hash, db_cached)
            return db_cached

        with open(tmp_path, "wb") as f:
            f.write(content)

        t0 = time.perf_counter()
        result = image_analyze_service.analyze_svc(tmp_path)
        print(f"[cache] miss ({image_hash[:8]}...) - 새로 분석함 ({time.perf_counter() - t0:.2f}s), 캐시에 저장")

        _cache_set(image_hash, result)
        _db_cache_set(image_hash, result)
        return result

    except InvalidImageError:
        raise HTTPException(status_code=400, detail="올바른 이미지 파일이 아니에요. 다른 사진으로 다시 시도해주세요.")
    except HTTPException:
        raise
    except Exception:
        logger.exception("이미지 분석 중 예기치 못한 오류")
        raise HTTPException(status_code=500, detail="이미지 분석 중 문제가 발생했어요. 잠시 후 다시 시도해주세요.")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# R 헬스체크
@router.get("/health")
async def health_check(request: Request):
    loaded = hasattr(request.app.state, "image_analyze_service")
    return {"status": "ok", "image_analyze_service_loaded": loaded}