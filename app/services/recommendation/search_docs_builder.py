"""
새로 추가된 정책만 골라 검색문서(policy_search_docs.json)/임베딩(search_docs_full_text_embeddings.npy)을
생성해 운영 파일에 이어붙이는 백그라운드 파이프라인.

code_create_policy_search_docs/의 수동 스크립트(생성 -> 정제 -> 임베딩)와 같은 로직을 재사용하되,
전체 정책이 아니라 DB에 있고 아직 검색문서가 없는 정책만 대상으로 하고, 결과를 API로 바로
운영 파일에 반영한다. LLM 호출이 정책 수만큼 걸리므로 반드시 백그라운드로 실행해야 한다
(app/routers/search_docs.py에서 BackgroundTasks로 호출).
"""

import json
import threading
from pathlib import Path

import numpy as np
import pymysql

from app.core.settings import settings
from app.core.s3_utils import get_s3_client, upload_file
from code_create_policy_search_docs.search_doc_generator_watsonx import WatsonxSearchDocGenerator
from code_create_policy_search_docs.clean_search_docs import (
    dedupe_preserve_order, remove_suspicious_targets, MAX_ITEM_COUNTS,
)
from code_create_policy_search_docs.build_search_doc_embeddings import build_policy_text

DB_FIELDS = [
    "plcyNo", "plcyNm", "plcyKywdNm", "lclsfNm", "mclsfNm",
    "plcyExplnCn", "plcySprtCn", "earnEtcCn", "addAplyQlfcCndCn", "ptcpPrpTrgtCn",
]

# run_create_search_docs.py와 동일한 배치 크기/간격. 배치마다 운영 파일에 바로 저장해서,
# 중간에 서버가 재시작되거나 실패해도 그때까지 만든 결과는 남아있게 한다.
BATCH_SIZE = 5
SLEEP_SEC = 0.2

# 수동 파이프라인(code_create_policy_search_docs/)과 done_ids 등 상태를 공유하기 위한 스테이징 파일.
STAGING_RAW_FILE = "result/search_docs_watsonx.json"
STAGING_CLEANED_FILE = "result/search_docs_watsonx_cleaned.json"
STAGING_EXCEPTIONS_LOG_FILE = "result/search_docs_target_exceptions_log.json"

_lock = threading.Lock()
_status: dict = {"running": False, "last_run": None}


def get_status() -> dict:
    """검색문서 생성 작업이 지금 실행 중인지, 마지막 실행 결과가 뭐였는지 반환한다."""
    return {"running": _status["running"], "last_run": _status["last_run"]}


def _load_json(path, default):
    """JSON 파일을 읽는다. 파일이 없으면 default를 반환한다."""
    p = Path(path)
    if not p.exists():
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _save_json(path, data):
    """데이터를 JSON 파일로 저장한다(폴더가 없으면 만든다)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_policies_from_db() -> list[dict]:
    """검색문서 생성에 필요한 필드들을 DB에서 전부 읽어온다."""
    conn = pymysql.connect(
        host=settings.db_host, port=settings.db_port, user=settings.db_user,
        password=settings.db_password, db=settings.db_name, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join(DB_FIELDS)} FROM policy")
            return cursor.fetchall()
    finally:
        conn.close()


def get_new_policies(known_plcynos: set[str]) -> list[dict]:
    """DB의 전체 정책 중, 이미 검색문서가 만들어진(known_plcynos) 것을 제외한 정책만 반환한다."""
    policies = _load_policies_from_db()
    return [p for p in policies if p.get("plcyNo") and str(p["plcyNo"]) not in known_plcynos]


def _clean_doc(doc: dict, exceptions_log: list[dict]) -> dict:
    """LLM이 생성한 검색문서 하나를 정제한다: 중복 제거, 의심스러운 대상 표현 제거,
    항목별 최대 개수 제한."""
    for field in ("target", "support", "keywords", "situations", "example_queries"):
        value = doc.get(field)
        if isinstance(value, list):
            doc[field] = dedupe_preserve_order(value)
    remove_suspicious_targets(doc, exceptions_log)
    for field, max_count in MAX_ITEM_COUNTS.items():
        value = doc.get(field)
        if isinstance(value, list) and len(value) > max_count:
            doc[field] = value[:max_count]
    return doc


def _upload_if_configured(local_path: str, s3_key: str) -> None:
    """S3 설정이 돼 있으면 파일을 업로드하고, 아니면 아무것도 하지 않는다."""
    if settings.data_s3_bucket and s3_key:
        client = get_s3_client(settings.data_s3_public)
        upload_file(local_path, settings.data_s3_bucket, s3_key, client, label="search_docs_builder")


def _append_batch_to_production(cleaned_docs: list[dict], model) -> None:
    """새로 만든 검색문서를 임베딩하고, 기존 운영 파일(문서 JSON + 임베딩 npy)에 이어붙여 저장한다."""
    texts = [build_policy_text(doc, "full_text") for doc in cleaned_docs]
    new_embeddings = model.encode(texts, batch_size=64, convert_to_numpy=True, normalize_embeddings=True)

    existing_docs = _load_json(settings.similarity_docs_path, [])
    embeddings_path = Path(settings.similarity_embeddings_path)
    existing_embeddings = np.load(embeddings_path) if embeddings_path.exists() else None

    combined_docs = existing_docs + cleaned_docs
    combined_embeddings = (
        np.vstack([existing_embeddings, new_embeddings]) if existing_embeddings is not None else new_embeddings
    )

    _save_json(settings.similarity_docs_path, combined_docs)
    np.save(settings.similarity_embeddings_path, combined_embeddings)
    return combined_docs, combined_embeddings


def run_rebuild(policy_similarity_service, new_policies: list[dict]) -> None:
    """new_policies에 대해 검색문서 생성 -> 정제 -> 임베딩 -> 운영 파일 이어붙이기까지 수행한다.
    BATCH_SIZE만큼씩 나눠서 배치마다 운영 파일에 바로 저장하므로, 중간에 실패/재시작해도
    그때까지 처리한 배치는 남아있다. BackgroundTasks에서 호출되는 동기 함수."""
    with _lock:
        if _status["running"]:
            return
        _status["running"] = True

    result = {"requested": len(new_policies), "processed": 0, "failed": 0, "target_exceptions": 0, "error": None}
    _status["last_run"] = dict(result)
    try:
        if not new_policies:
            return

        generator = WatsonxSearchDocGenerator()
        # PolicySimilarityService가 이미 로드해둔 bge-m3 모델을 재사용한다(별도 로드 없이).
        model = policy_similarity_service.model

        total_batches = (len(new_policies) - 1) // BATCH_SIZE + 1
        for batch_idx, start in enumerate(range(0, len(new_policies), BATCH_SIZE), start=1):
            batch = new_policies[start:start + BATCH_SIZE]
            print(f"[search_docs_builder] 배치 {batch_idx}/{total_batches} 생성 중...")

            raw_docs, gen_errors = generator.create_search_docs(batch, sleep_sec=SLEEP_SEC, verbose=True)
            result["failed"] += len(gen_errors)
            if not raw_docs:
                _status["last_run"] = dict(result)
                continue

            exceptions_log = _load_json(STAGING_EXCEPTIONS_LOG_FILE, [])
            new_exceptions: list[dict] = []
            cleaned_docs = [_clean_doc(doc, new_exceptions) for doc in raw_docs]
            exceptions_log.extend(new_exceptions)
            result["target_exceptions"] += len(new_exceptions)

            combined_docs, combined_embeddings = _append_batch_to_production(cleaned_docs, model)

            # 수동 파이프라인과 done_ids 등 상태를 공유하도록 스테이징 파일에도 반영
            staging_raw = _load_json(STAGING_RAW_FILE, [])
            staging_raw.extend(raw_docs)
            _save_json(STAGING_RAW_FILE, staging_raw)

            staging_cleaned = _load_json(STAGING_CLEANED_FILE, [])
            staging_cleaned.extend(cleaned_docs)
            _save_json(STAGING_CLEANED_FILE, staging_cleaned)

            _save_json(STAGING_EXCEPTIONS_LOG_FILE, exceptions_log)

            # 서버 재시작 없이 바로 검색에 반영
            policy_similarity_service.refresh(combined_docs, combined_embeddings)

            result["processed"] += len(cleaned_docs)
            _status["last_run"] = dict(result)

        # S3 재업로드는 배치마다 하기엔 무거워서(수 MB~수십 MB 파일) 전체 배치가 끝난 뒤 한 번만 한다.
        _upload_if_configured(settings.similarity_docs_path, settings.similarity_docs_s3_key)
        _upload_if_configured(settings.similarity_embeddings_path, settings.similarity_embeddings_s3_key)
    except Exception as e:
        result["error"] = str(e)
    finally:
        _status["running"] = False
        _status["last_run"] = result
