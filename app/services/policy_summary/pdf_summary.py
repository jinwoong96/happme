import os
import re
import json

import numpy as np
import fitz

from app.core.settings import settings


class PdfSummaryService:
    """
    청년정책 PDF 매칭/요약 서비스.
    임베딩 모델, watsonx LLM, 정책 DB를 들고 있으므로 lifespan에서 한 번만 생성해서 재사용하세요.
    WebSummaryService가 이 인스턴스를 주입받아 모델/DB/요약 함수를 재사용합니다.
    """

    def __init__(self):
        from sentence_transformers import SentenceTransformer

        print("[PdfSummaryService] 임베딩 모델 로드 중...")
        self.embed_model = SentenceTransformer(settings.policy_summary_embed_model)

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

        print("[PdfSummaryService] 정책 DB 로드 중...")
        self.policy_names, self.policy_texts, self.policy_institutions, self.policy_by_name = self._load_policies()
        self.db_embeddings = self._load_or_encode_db()
        print(f"[PdfSummaryService] 준비 완료 (정책 {len(self.policy_names)}개)")

    # ---------- DB 로드/캐시 ----------

    def _load_policies(self):
        with open(settings.policy_summary_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        target = None
        if isinstance(data, list):
            target = data
        elif isinstance(data, dict):
            if "result" in data and "youthPolicyList" in data.get("result", {}):
                target = data["result"]["youthPolicyList"]
            elif "youthPolicyList" in data:
                target = data["youthPolicyList"]

        names, texts, institutions, by_name = [], [], [], {}
        seen = set()
        for item in target or []:
            if not isinstance(item, dict):
                continue
            name = item.get("plcyNm", "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            by_name[name] = item

            institution = " ".join(filter(None, [
                item.get("operInstCdNm", ""), item.get("sprvsnInstCdNm", ""), item.get("rgtrInstCdNm", ""),
            ]))
            combined = " ".join(filter(None, [
                name, institution, item.get("plcyKywdNm", ""), item.get("plcyExplnCn", ""),
                item.get("plcySprtCn", ""), item.get("ptcpPrpTrgtCn", ""), item.get("plcyAplyMthdCn", ""),
            ]))
            names.append(name)
            texts.append(combined)
            institutions.append(institution)

        return names, texts, institutions, by_name

    def _load_or_encode_db(self):
        json_mtime = os.path.getmtime(settings.policy_summary_json_path)
        cache_path = settings.policy_summary_embed_cache

        if os.path.exists(cache_path):
            cache = np.load(cache_path)
            if cache["json_mtime"] == json_mtime and int(cache["count"]) == len(self.policy_texts):
                print("[PdfSummaryService] 캐시된 임베딩 재사용")
                return cache["embeddings"]

        print(f"[PdfSummaryService] 정책 {len(self.policy_texts)}개 벡터화 중...")
        prefixed = [f"passage: {t}" for t in self.policy_texts]
        embeddings = self.embed_model.encode(prefixed, batch_size=64, show_progress_bar=True)
        np.savez(cache_path, embeddings=embeddings, json_mtime=json_mtime, count=len(self.policy_texts))
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

    def summarize_policy_svc(self, policy_detail: dict) -> str | None:
        name = policy_detail.get("plcyNm", "").strip()
        explain = policy_detail.get("plcyExplnCn", "").strip()
        support = policy_detail.get("plcySprtCn", "").strip()
        apply_method = policy_detail.get("plcyAplyMthdCn", "").strip()
        apply_period = policy_detail.get("aplyYmd", "").strip()
        biz_start = policy_detail.get("bizPrdBgngYmd", "").strip()
        biz_end = policy_detail.get("bizPrdEndYmd", "").strip()
        target = policy_detail.get("ptcpPrpTrgtCn", "").strip() or policy_detail.get("earnEtcCn", "").strip()
        age_min = policy_detail.get("sprtTrgtMinAge", "").strip()
        age_max = policy_detail.get("sprtTrgtMaxAge", "").strip()
        institution = policy_detail.get("sprvsnInstCdNm", "").strip() or policy_detail.get("rgtrInstCdNm", "").strip()
        apply_url = policy_detail.get("aplyUrlAddr", "").strip()
        scale = policy_detail.get("sprtSclCnt", "").strip()

        biz_period = self._format_period(biz_start, biz_end) if (biz_start and biz_end) else ""
        age_str = f"{age_min}~{age_max}세" if age_min and age_max else ""
        scale_str = f"{scale}명" if scale and scale != "0" else ""

        fields = {
            "정책명": name, "정책설명": explain, "지원내용": support,
            "지원대상": target, "연령조건": age_str, "신청방법": apply_method,
            "신청URL": apply_url, "신청기간": apply_period,
            "사업기간": biz_period, "담당기관": institution, "지원규모": scale_str,
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
        if institution:
            instructions.append(f"- 담당기관: {institution} 그대로 표기")

        instructions_text = "\n".join(instructions)

        prompt = f"""아래 청년 정책 정보를 보기 쉽게 요약해줘.

[정책 원본 정보]
{info_text}

아래 라벨들을 각각 정확히 한 번씩만 사용해서, "**라벨**: 내용" 형식으로 한 줄씩 정리해줘.
각 항목은 완전한 문장(~합니다, ~됩니다, ~하는 자 등)으로 쓰지 말고, 핵심 키워드/조건 위주로 짧게 정리해줘.
라벨 이름이나 지시문을 그대로 출력하지 말고, 실제 요약 내용만 채워써. 원본에 없는 내용은 추측해서 만들지 말고, 아래 목록에 없는 항목은 출력하지 마.

{instructions_text}

답변:"""

        try:
            raw = self.llm_model.generate(prompt=prompt)
            print(f"[DEBUG] LLM 원본 전체 응답: {raw}")
            response = raw["results"][0]["generated_text"]
            response = raw["results"][0]["generated_text"]
            print("=" * 80)
            print(response)
            print("=" * 80)

            return response.strip()
            return response.strip()
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
        if not combined_text:
            return {"matched_policy": None, "method": "텍스트추출실패"}

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
            f"[정책 {i+1}] {s['policy_name']}\n{s['summary']}"
            for i, s in enumerate(summaries) if s.get("summary")
        )
        names_str = " | ".join(s["policy_name"] for s in summaries)
        divider_str = "|".join("------" for _ in summaries)

        prompt = f"""아래 {len(summaries)}개의 청년 정책을 비교 분석해줘.

{policy_list}

다음 형식으로 비교해줘:

**📊 정책 비교**

| 항목 | {names_str} |
|------|{divider_str}|
| 지원대상 | (각 정책 지원대상) |
| 지원내용 | (각 정책 지원내용) |
| 신청기간 | (각 정책 신청기간) |
| 담당기관 | (각 정책 담당기관) |

**💡 추천**: (어떤 상황에 어떤 정책이 더 적합한지)"""
            
        try:
            raw = self.llm_model.generate(prompt=prompt)
            print(f"[DEBUG] LLM 원본 전체 응답: {raw}")
            response = raw["results"][0]["generated_text"]
            return response.strip()
        except Exception as e:
            print(f"[PdfSummaryService] 요약 생성 오류: {e}")
            return None