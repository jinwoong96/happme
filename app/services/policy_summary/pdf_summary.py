import os
import re
import hashlib
import threading

import numpy as np
import pymysql
import torch
import fitz

from app.core.settings import settings
from app.core.s3_utils import get_s3_client, upload_file

# _load_policies_from_db가 조회하는 컬럼. summarize_policy_svc/web_summary.py/라우터가
# policy_detail dict에서 참조하는 필드를 전부 포함한다.
POLICY_FIELDS = [
    "plcyNo", "plcyNm", "operInstCdNm", "sprvsnInstCdNm", "rgtrInstCdNm",
    "plcyKywdNm", "plcyExplnCn", "plcySprtCn", "ptcpPrpTrgtCn", "plcyAplyMthdCn",
    "aplyYmd", "bizPrdBgngYmd", "bizPrdEndYmd", "earnEtcCn",
    "sprtTrgtMinAge", "sprtTrgtMaxAge", "aplyUrlAddr", "sprtSclCnt",
    "sbmsnDcmntCn", "etcMttrCn",
]


class PdfSummaryService:
    """
    청년정책 PDF 매칭/요약 서비스.
    임베딩 모델, watsonx LLM, 정책 DB를 들고 있으므로 lifespan에서 한 번만 생성해서 재사용하세요.
    WebSummaryService가 이 인스턴스를 주입받아 모델/DB/요약 함수를 재사용합니다.
    """

    def __init__(self):
        from sentence_transformers import SentenceTransformer

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[PdfSummaryService] 임베딩 모델 로드 중... (device={device})")
        self.embed_model = SentenceTransformer(settings.policy_summary_embed_model, device=device)

        print("[PdfSummaryService] watsonx LLM 연결 중...")
        from ibm_watsonx_ai import Credentials, APIClient
        from ibm_watsonx_ai.foundation_models import ModelInference

        credentials = Credentials(url=settings.watsonx_url, api_key=settings.watsonx_api_key)
        api_client = APIClient(credentials, project_id=settings.watsonx_project_id)
        self.llm_model = ModelInference(
            api_client=api_client,
            model_id=settings.policy_summary_llm_model_id,
            params={"max_new_tokens": 500, "temperature": 0.0, "decoding_method": "greedy"},
        )

        print("[PdfSummaryService] RDS에서 정책 데이터 로드 중...")
        self.policy_plcynos, self.policy_names, self.policy_texts, self.policy_institutions, self.policy_by_name = \
            self._load_policies_from_db()
        print(f"[PdfSummaryService] 총 {len(self.policy_names)}개 정책 로드")
        self.db_embeddings = self._load_or_encode_db()
        print(f"[PdfSummaryService] 준비 완료 (정책 {len(self.policy_names)}개)")

    def reload_policies_svc(self) -> dict:
        """DB에서 정책을 다시 읽고 임베딩 캐시를 갱신한다. __init__과 동일한 두 호출을
        재사용하며, _load_or_encode_db()가 텍스트 해시로 신규/변경분만 판별해 재임베딩하므로
        서버 재시작 없이도 "최신화"로 새로 들어온 정책을 이 캐시에 반영할 수 있다."""
        self.policy_plcynos, self.policy_names, self.policy_texts, self.policy_institutions, self.policy_by_name = \
            self._load_policies_from_db()
        self.db_embeddings = self._load_or_encode_db()
        return {"policy_count": len(self.policy_names)}

    # ---------- DB 로드/캐시 ----------

    @staticmethod
    def _load_policies_from_db():
        """
        SearchService/PolicyLoaderService와 동일하게 RDS를 직접 조회한다.
        정책명이 같은 정책이 여러 건이면(같은 정책이 다른 연도/기관으로 재등록된 경우 등)
        policy_id가 더 큰(가장 최근에 등록된) 쪽을 채택한다 - ORDER BY DESC로 조회해서
        먼저 순회되는 쪽이 항상 최신 건이 되도록 한다.
        """
        conn = pymysql.connect(
            host=settings.db_host, port=settings.db_port, user=settings.db_user,
            password=settings.db_password, db=settings.db_name, charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT {', '.join(POLICY_FIELDS)} FROM policy ORDER BY policy_id DESC"
                )
                rows = cursor.fetchall()
        finally:
            conn.close()

        plcynos, names, texts, institutions, by_name = [], [], [], [], {}
        seen = set()
        for item in rows:
            name = (item.get("plcyNm") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            by_name[name] = item

            institution = " ".join(filter(None, [
                item.get("operInstCdNm") or "", item.get("sprvsnInstCdNm") or "", item.get("rgtrInstCdNm") or "",
            ]))
            combined = " ".join(filter(None, [
                name, institution, item.get("plcyKywdNm") or "", item.get("plcyExplnCn") or "",
                item.get("plcySprtCn") or "", item.get("ptcpPrpTrgtCn") or "", item.get("plcyAplyMthdCn") or "",
            ]))
            plcynos.append(item.get("plcyNo"))
            names.append(name)
            texts.append(combined)
            institutions.append(institution)

        return plcynos, names, texts, institutions, by_name

    @staticmethod
    def _text_hash(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _load_or_encode_db(self):
        """
        정책별로 텍스트 해시를 따로 저장해뒀다가, 이번에 로드한 정책들 중 캐시에 없거나(신규)
        해시가 달라진(내용 변경) 것만 새로 임베딩하고 나머지는 캐시에서 그대로 재사용한다.
        DB에서 사라진 정책은 최종 배열을 plcyNo 기준으로 다시 조립하는 과정에서 자연히 빠진다.
        """
        cache_path = settings.policy_summary_embed_cache
        current_hashes = [self._text_hash(t) for t in self.policy_texts]

        cached_by_plcyno = {}
        if os.path.exists(cache_path):
            cache = np.load(cache_path, allow_pickle=True)
            if "plcy_nos" in cache.files and "text_hashes" in cache.files:
                plcy_nos_arr = cache["plcy_nos"]
                text_hashes_arr = cache["text_hashes"]
                embeddings_arr = cache["embeddings"]
                for idx, plcy_no in enumerate(plcy_nos_arr):
                    cached_by_plcyno[str(plcy_no)] = (text_hashes_arr[idx], embeddings_arr[idx])

        to_encode_idx = []
        for i, plcy_no in enumerate(self.policy_plcynos):
            cached = cached_by_plcyno.get(str(plcy_no))
            if cached is None or cached[0] != current_hashes[i]:
                to_encode_idx.append(i)

        reused = len(self.policy_plcynos) - len(to_encode_idx)
        print(
            f"[PdfSummaryService] 신규/변경 {len(to_encode_idx)}건 벡터화, "
            f"캐시 재사용 {reused}건 (전체 {len(self.policy_plcynos)}건)"
        )

        new_embeddings_by_idx = {}
        if to_encode_idx:
            prefixed = [f"passage: {self.policy_texts[i]}" for i in to_encode_idx]
            encoded = self.embed_model.encode(prefixed, batch_size=64, show_progress_bar=True)
            for i, emb in zip(to_encode_idx, encoded):
                new_embeddings_by_idx[i] = emb

        embeddings = np.stack([
            new_embeddings_by_idx[i] if i in new_embeddings_by_idx
            else cached_by_plcyno[str(self.policy_plcynos[i])][1]
            for i in range(len(self.policy_plcynos))
        ])

        if to_encode_idx or reused != len(cached_by_plcyno):
            np.savez(
                cache_path, embeddings=embeddings,
                plcy_nos=np.array(self.policy_plcynos, dtype=object),
                text_hashes=np.array(current_hashes, dtype=object),
            )
            if settings.data_s3_bucket and settings.policy_summary_embed_cache_s3_key:
                client = get_s3_client(settings.data_s3_public)
                upload_file(
                    cache_path, settings.data_s3_bucket,
                    settings.policy_summary_embed_cache_s3_key, client, label="PdfSummaryService",
                )

        return embeddings

    # ---------- 공용 함수 (WebSummaryService도 재사용) ----------

    def get_policy_detail_svc(self, policy_name: str):
        return self.policy_by_name.get(policy_name)

    def verify_with_llm_svc(self, text: str, candidates: list[str], pdf_name: str | None = None) -> str:
        candidate_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(candidates)])

        if pdf_name is not None:
            is_english = bool(re.search(r'[a-zA-Z]{3,}', pdf_name))
            text_length = 1000 if is_english else 600
        else:
            text_length = 1000

        prompt = f"""당신은 공고문과 정책을 매칭하는 전문가입니다.

[공고문 내용]:
{text[:text_length]}

[정책 후보 목록]:
{candidate_str}

규칙:
1. 공고문과 정책이 완전히 같은 사업일 때만 매칭하세요
2. 사업 내용, 지원 대상, 운영 방식이 일치해야 합니다
3. 후보 목록에 정확히 일치하는 사업이 없으면 반드시 '없음'을 출력하세요
4. 비슷하지만 다른 기관이거나 내용이 다르면 '없음'을 출력하세요
5. 정책 이름 또는 '없음' 하나만 출력하세요. 설명 없이.

답변:"""
        try:
            return self.llm_model.generate_text(prompt=prompt).strip()
        except Exception as e:
            print(f"[PdfSummaryService] Watson API 오류: {e}")
            return "없음"

    @staticmethod
    def _format_period(start_ymd, end_ymd):
        def fmt(ymd):
            if not ymd or len(ymd) != 8:
                return ""
            return f"{ymd[:4]}.{ymd[4:6]}.{ymd[6:]}"
        s, e = fmt(start_ymd), fmt(end_ymd)
        return "상시" if not s and not e else f"{s} ~ {e}"

    # ---------- 요약 캐시 (policy_summary_cache 테이블, bene_backend와 공유) ----------
    # 캐시 조회를 LLM 호출보다 먼저 해서, 캐시가 있으면 LLM을 아예 부르지 않는다.
    # (기존에는 bene_backend가 매번 LLM 요약을 새로 받은 뒤에야 캐시로 덮어써서,
    # 캐시가 있어도 LLM 호출 자체는 매번 발생하는 낭비가 있었다. 이 캐시를 요약이
    # 실제로 만들어지는 지점으로 옮겨서, summarize_policy_svc를 부르는 모든
    # 경로(pdf/text/url 매칭, 후보 요약, 즐겨찾기 비교용 summarize-policies)가
    # 자동으로 캐시 혜택을 받게 한다.)

    @staticmethod
    def _get_cached_summary(policy_name: str) -> str | None:
        conn = pymysql.connect(
            host=settings.db_host, port=settings.db_port, user=settings.db_user,
            password=settings.db_password, db=settings.db_name, charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT summary_text FROM policy_summary_cache WHERE policy_name = %s",
                    (policy_name,),
                )
                row = cursor.fetchone()
                return row["summary_text"] if row and row["summary_text"] else None
        except Exception as e:
            print(f"[PdfSummaryService] 캐시 조회 오류: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def _set_cached_summary(policy_name: str, summary_text: str) -> None:
        conn = pymysql.connect(
            host=settings.db_host, port=settings.db_port, user=settings.db_user,
            password=settings.db_password, db=settings.db_name, charset="utf8mb4",
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO policy_summary_cache (policy_name, summary_text)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE summary_text = VALUES(summary_text)
                    """,
                    (policy_name, summary_text),
                )
            conn.commit()
        except Exception as e:
            print(f"[PdfSummaryService] 캐시 저장 오류: {e}")
        finally:
            conn.close()

    def summarize_policy_svc(self, policy_detail: dict) -> str | None:
        name = (policy_detail.get("plcyNm") or "").strip()

        if name:
            cached = self._get_cached_summary(name)
            if cached:
                print(f"[PdfSummaryService] 캐시된 요약 재사용: {name}")
                return cached

        explain = (policy_detail.get("plcyExplnCn") or "").strip()
        support = (policy_detail.get("plcySprtCn") or "").strip()
        apply_method = (policy_detail.get("plcyAplyMthdCn") or "").strip()
        apply_period = (policy_detail.get("aplyYmd") or "").strip()
        biz_start = (policy_detail.get("bizPrdBgngYmd") or "").strip()
        biz_end = (policy_detail.get("bizPrdEndYmd") or "").strip()
        target = (policy_detail.get("ptcpPrpTrgtCn") or "").strip() or (policy_detail.get("earnEtcCn") or "").strip()
        age_min_val = policy_detail.get("sprtTrgtMinAge")
        age_max_val = policy_detail.get("sprtTrgtMaxAge")
        scale_val = policy_detail.get("sprtSclCnt")
        age_min = str(age_min_val).strip() if age_min_val is not None else ""
        age_max = str(age_max_val).strip() if age_max_val is not None else ""
        apply_url = (policy_detail.get("aplyUrlAddr") or "").strip()
        scale = str(scale_val).strip() if scale_val is not None else ""

        biz_period = self._format_period(biz_start, biz_end) if (biz_start and biz_end) else ""
        age_str = f"{age_min}~{age_max}세" if age_min and age_max else ""
        scale_str = f"{scale}명" if scale and scale != "0" else ""

        fields = {
            "정책명": name, "정책설명": explain, "지원내용": support,
            "지원대상": target, "연령조건": age_str, "신청방법": apply_method,
            "신청URL": apply_url, "신청기간": apply_period,
            "사업기간": biz_period,  "지원규모": scale_str,
        }
        info_text = "\n".join(f"{k}: {v}" for k, v in fields.items() if v)

        instructions = []
        if explain:
            instructions.append("- 한줄요약: 정책의 핵심 목적만 간결한 구(句) 형태로 (완전한 문장 X)")
        if target or age_str:
            instructions.append("- 지원대상: 연령·자격 조건만 나열식으로 간결하게 (완전한 문장 X)")
        if support:
            instructions.append("- 지원내용: 지원 금액/내용 핵심만 간결하게 (완전한 문장 X)")
        if apply_method or apply_url:
            instructions.append("- 신청방법: 신청 방법만 간결하게 작성하고 URL은 출력하지 말 것 (완전한 문장 X)")
        if apply_period:
            instructions.append(f"- 신청기간: {apply_period} 그대로 표기")

        instructions_text = "\n".join(instructions)

        prompt = f"""아래 청년 정책 정보를 보기 쉽게 요약해줘.

[정책 원본 정보]
{info_text}

반드시 아래 형식을 정확히 지켜서 출력해줘. 다른 형식은 절대 사용하지 마.
각 항목은 반드시 "**라벨**: 내용" 형식으로 한 줄씩 작성해줘.
예시: **한줄요약**: 청년 자산형성 지원 정책

아래 라벨들을 각각 정확히 한 번씩만 사용해서 출력해줘.

{instructions_text}

답변:"""

        try:
            raw = self.llm_model.generate(prompt=prompt)
            print(f"[DEBUG] LLM 원본 전체 응답: {raw}")
            response = raw["results"][0]["generated_text"]
            print("=" * 80)
            print(response)
            print("=" * 80)

            result = response.strip()
            if name and result:
                self._set_cached_summary(name, result)
            return result
        except Exception as e:
            print(f"[PdfSummaryService] 요약 생성 오류: {e}")
            return None
    # ---------- PDF 전용 ----------

    @staticmethod
    def extract_pdf_features_svc(pdf_bytes: bytes):
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for idx, page in enumerate(doc):
                if idx >= 5:
                    break
                text += page.get_text()
            doc.close()
            text = " ".join(text.split())
            print(f"[DEBUG] 추출된 텍스트 길이: {len(text)}자")  # ← 추가
            print(f"[DEBUG] 추출된 텍스트: {text[:200]}")        # ← 추가
            keyword_text = ""
            for kw in ["사업명", "사업개요", "지원내용", "지원대상", "모집내용", "인턴", "공고명"]:
                idx = text.find(kw)
                if idx != -1:
                    keyword_text += text[idx:idx + 100] + " "
            combined_text = text[:300] + " " + keyword_text

            institution = ""
            for pattern in [
                r'([가-힣]+(?:시|군|구|청|원|공단|재단|센터|연금|공사|위원회|부|처|청))\s*(?:공고|장|에서)',
                r'([가-힣]{2,10}(?:공단|공사|연금|위원회))',
            ]:
                m = re.search(pattern, text[:300])
                if m:
                    institution = m.group(1)
                    break

            return combined_text, text, institution
        except Exception as e:
            print(f"[PdfSummaryService] PDF 추출 오류: {e}")
            return "", "", ""

    def _cosine_sim(self, query_emb):
        db = self.db_embeddings
        return np.dot(db, query_emb.T).flatten() / (
            np.linalg.norm(db, axis=1) * np.linalg.norm(query_emb) + 1e-8
        )

    def match_pdf_svc(self, pdf_bytes: bytes, filename: str,
                       raw_threshold_high=0.88, raw_threshold_low=0.875, top_k=10) -> dict:
        combined_text, full_text, pdf_institution = self.extract_pdf_features_svc(pdf_bytes)
        if not combined_text or len(combined_text.strip()) < 10:
            return {"matched_policy": None, "method": "텍스트추출실패", "candidates": []}

        pdf_name_clean = filename.replace(" ", "").replace(".pdf", "").replace(".hwp", "").replace(".hwpx", "")
        pdf_text_clean = full_text.replace(" ", "")

        for name in self.policy_names:
            nc = name.replace(" ", "")
            if nc == pdf_name_clean or (nc in pdf_name_clean and len(nc) > 10) or (nc in pdf_text_clean and len(nc) > 10):
                return {"matched_policy": name, "method": "직접매칭"}

        embedding = self.embed_model.encode([f"query: {combined_text}"], show_progress_bar=False)
        similarities = self._cosine_sim(embedding)
        raw_best_score = float(similarities.max())

        s_min, s_max = similarities.min(), similarities.max()
        normalized = (similarities - s_min) / (s_max - s_min + 1e-8)

        if pdf_institution:
            for i, inst in enumerate(self.policy_institutions):
                if inst and pdf_institution not in inst and pdf_institution not in self.policy_texts[i]:
                    normalized[i] *= 0.85

        top_indices = normalized.argsort()[::-1][:top_k]
        top_names = [self.policy_names[i] for i in top_indices]
        best_match = top_names[0]
        print("raw_best_score =", raw_best_score)
        print("top_names =", top_names)

        if raw_best_score < raw_threshold_low:
            return {
                "matched_policy": "해당 없음",
                "method": "매칭불가",
                "candidates": top_names[:3],      # ← 문자열 리스트
                "raw_score": raw_best_score
            }
        if raw_best_score >= raw_threshold_high:
            return {
                "matched_policy": best_match,
                "method": "임베딩매칭",
                "candidates": top_names[:2],      # ← 문자열 리스트
                "raw_score": raw_best_score
            }

        llm_result = self.verify_with_llm_svc(full_text, top_names, filename)
        is_none = llm_result == "없음" or llm_result not in self.policy_names
        matched = "해당 없음" if is_none else llm_result
        return {
            "matched_policy": matched,
            "method": "매칭불가" if is_none else "하이브리드매칭",
            "candidates": top_names[:2],          # ← 문자열 리스트
            "raw_score": raw_best_score
        }

    def compare_policies_svc(self, summaries: list[dict]) -> str | None:
        policy_list = "\n\n".join(
            f"{s['policy_name']}\n{s['summary']}"
            for s in summaries if s.get("summary")
        )

        prompt = f"""아래 {len(summaries)}개의 청년 정책 정보를 보고, 두 가지 서로 다른 상황을 정해서 각 상황에 어떤 정책이 더 적합한지 한눈에 보기 쉽게 정리해줘.

{policy_list}

작성 방법:
1. 정책명은 위에 나온 이름을 그대로 사용한다.
2. 하이픈(-)으로 시작하는 항목을 정확히 2개 작성한다.
3. 각 항목은 "<상황 키워드>: <정책명> — <핵심 이유 키워드>" 형태로, 완전한 문장이 아니라 짧은 단어와 구로만 작성한다.
4. 안내 문장 없이 첫 번째 항목부터 바로 시작한다.

답변:"""

        try:
            raw = self.llm_model.generate(prompt=prompt)
            print(f"[DEBUG] LLM 원본 전체 응답: {raw}")
            response = raw["results"][0]["generated_text"]
            return response.strip()
        except Exception as e:
            print(f"[PdfSummaryService] 요약 생성 오류: {e}")
            return None


# ---------------------------------------------------------------------------
# 캐시 재구축 (관리자 "최신화" 흐름 후처리 - search_docs_builder.py와 동일한 상태 관리 패턴).
# PdfSummaryService.reload_policies_svc()가 신규/변경분만 재임베딩하도록 이미 되어있으므로
# 여기서는 그걸 백그라운드로 실행하고 상태만 추적한다.
# ---------------------------------------------------------------------------

_rebuild_lock = threading.Lock()
_rebuild_status: dict = {"running": False, "last_run": None}


def get_rebuild_status() -> dict:
    return {"running": _rebuild_status["running"], "last_run": _rebuild_status["last_run"]}


def run_rebuild(service: PdfSummaryService) -> None:
    """BackgroundTasks에서 호출되는 동기 함수. service는 app.state.pdf_summary_service(싱글턴)."""
    with _rebuild_lock:
        if _rebuild_status["running"]:
            return
        _rebuild_status["running"] = True

    result: dict = {"policy_count": None, "error": None}
    _rebuild_status["last_run"] = dict(result)
    try:
        result.update(service.reload_policies_svc())
    except Exception as e:
        result["error"] = str(e)
    finally:
        _rebuild_status["running"] = False
        _rebuild_status["last_run"] = result