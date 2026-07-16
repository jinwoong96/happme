import asyncio
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel

from app.services.policy_summary.pdf_summary import PdfSummaryService
from app.services.policy_summary.web_summary import WebSummaryService

router = APIRouter(prefix="/policy-summary", tags=["PolicySummary"])


class TextRequest(BaseModel):
    text: str


class UrlRequest(BaseModel):
    url: str


class QuestionRequest(BaseModel):
    policy_name: str
    question: str


class PolicyDetailInput(BaseModel):
    plcyNm: str
    plcyExplnCn: str = ""
    plcySprtCn: str = ""
    plcyAplyMthdCn: str = ""
    aplyYmd: str = ""
    bizPrdBgngYmd: str = ""
    bizPrdEndYmd: str = ""
    ptcpPrpTrgtCn: str = ""
    earnEtcCn: str = ""
    sprtTrgtMinAge: str = ""
    sprtTrgtMaxAge: str = ""
    aplyUrlAddr: str = ""
    sprtSclCnt: str = ""


class SummarizeRequest(BaseModel):
    policies: list[PolicyDetailInput]


class SummaryInput(BaseModel):
    policy_name: str
    summary: str


class RecommendRequest(BaseModel):
    summaries: list[SummaryInput]


def _extract_recommendation(comparison: str) -> str | None:
    """compare_policies_svc가 만드는 추천 텍스트에서 마크다운 문법(**)을 제거하고
    '- ' 항목마다 줄바꿈해 순수 텍스트로 정리한다. '💡 추천' 표시가 있으면 그 뒤만 쓰고,
    없으면(모델이 표시 없이 바로 답했을 때) 전체 텍스트를 그대로 쓴다."""
    import re

    match = re.search(r"\*{0,2}💡\s*추천\*{0,2}\s*:?\s*(.*)", comparison, re.S)
    text = (match.group(1) if match else comparison).strip().replace("**", "")
    text = re.sub(r"(다\.|요\.)\s+", r"\1\n", text)       # 문장이 끝날 때마다 줄바꿈
    text = re.sub(r"(- [^:\n]+:)\s*", r"\1\n", text)     # 제목 뒤 콜론 다음 바로 줄바꿈
    text = re.sub(r"\s+-\s+", "\n\n- ", text)            # 항목("- 제목")마다 빈 줄로 구분
    text = re.sub(r"\n{3,}", "\n\n", text)               # 과도한 빈 줄 정리
    text = text.strip()

    # 모델이 안내 문구를 앞에 붙이거나 항목을 3개 이상 만드는 경우가 있어서,
    # 첫 "-" 항목 앞은 잘라내고 최대 2개까지만 남긴다.
    first_dash = text.find("- ")
    if first_dash > 0:
        text = text[first_dash:]
    items = text.split("\n\n- ")
    items = [item if i == 0 else f"- {item}" for i, item in enumerate(items)]
    return "\n\n".join(items[:2]).strip()


def _parse_summary_fields(summary: str) -> dict:
    import re

    labels = ["한줄요약", "지원대상", "지원내용", "신청방법", "신청기간", "사업기간", "신청URL", "지원규모"]
    pattern = re.compile(
        rf"\*{{0,2}}({'|'.join(labels)})\*{{0,2}}\s*:\s*(.*?)(?=\*{{0,2}}(?:{'|'.join(labels)})\*{{0,2}}\s*:|$)",
        re.S,
    )
    return {label: value.strip() for label, value in pattern.findall(summary)}


def get_pdf_service(request: Request) -> PdfSummaryService:
    return request.app.state.pdf_summary_service


def get_web_service(request: Request) -> WebSummaryService:
    return request.app.state.web_summary_service


# PDF 1~4개 업로드 → 매칭 + 요약 (2개 이상이면 비교까지), 파일별 병렬 처리
@router.post("/pdf")
async def analyze_pdf(request: Request, files: List[UploadFile] = File(...)):
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="PDF 파일을 업로드해주세요")
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="최대 4개까지 업로드 가능합니다")
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{file.filename}은 PDF 파일이 아닙니다")

    pdf_service = get_pdf_service(request)
    payloads = [(file.filename, await file.read()) for file in files]

    def process_one(filename: str, pdf_bytes: bytes):
        match_result = pdf_service.match_pdf_svc(pdf_bytes, filename)
        matched_name = match_result["matched_policy"]
        method = match_result["method"]

        if match_result.get("method") == "텍스트추출실패":
            return {
                "filename": filename,
                "matched": False,
                "policy_name": None,
                "method": "텍스트추출실패",
                "summary": None,
                "candidates": [],
                "error_message": "이미지 기반 PDF라 텍스트를 추출할 수 없어요. 텍스트가 포함된 PDF를 업로드해주세요."
            }
        
        if matched_name in (None, "해당 없음"):
            candidate_infos = []

            for name in match_result.get("candidates", []):
                detail = pdf_service.get_policy_detail_svc(name)
                summary = pdf_service.summarize_policy_svc(detail) if detail else None

                fields = {}

                if summary:
                    import re

                    labels = [
                        "한줄요약",
                        "지원대상",
                        "지원내용",
                        "신청방법",
                        "신청기간",
                        "사업기간",
                        "신청URL",
                        "지원규모",
                    ]

                    pattern = re.compile(
                        rf"\*{{0,2}}({'|'.join(labels)})\*{{0,2}}\s*:\s*(.*?)(?=\*{{0,2}}(?:{'|'.join(labels)})\*{{0,2}}\s*:|$)",
                        re.S,
                    )

                    for label, value in pattern.findall(summary):
                        fields[label] = value.strip()
                    print(f"[DEBUG] name: {name}")
                    print(f"[DEBUG] summary: {summary}")
                    print(f"[DEBUG] fields: {fields}")
                    print(f"[DEBUG] apply_url: {detail.get('aplyUrlAddr', '') if detail else ''}")


                candidate_infos.append({
                    "policy_name": name,
                    "summary": summary,
                    "fields": fields,
                    "apply_url": detail.get("aplyUrlAddr", "") if detail else "",
                })

            return {
                "filename": filename,
                "matched": False,
                "policy_name": None,
                "method": method,
                "summary": None,
                "candidates": candidate_infos
            }

        policy_detail = pdf_service.get_policy_detail_svc(matched_name)
        summary = pdf_service.summarize_policy_svc(policy_detail) if policy_detail else None
        return {
            "filename": filename, "matched": True, "policy_name": matched_name, "method": method, "summary": summary,
            "apply_url": policy_detail.get("aplyUrlAddr", "") if policy_detail else "",
        }

    results = await asyncio.gather(*[
        asyncio.to_thread(process_one, filename, pdf_bytes) for filename, pdf_bytes in payloads
    ])

    if len(results) == 1:
        return {"mode": "summary", "results": results}

    matched_results = [r for r in results if r["matched"] and r["summary"]]
    comparison = pdf_service.compare_policies_svc(matched_results) if len(matched_results) >= 2 else None

    return {"mode": "compare", "results": results, "comparison": comparison}


# 이미 정책이 확정된 상태(예: 즐겨찾기 비교)에서 여러 정책을 짧게 요약 + 비교, 매칭 불필요
# 정책 dict 리스트(1개 이상)를 받아 각각 짧게 요약만 한다. 매칭/비교 없음 - 캐시 미스분만 여기로 보내면 됨.
@router.post("/summarize-policies")
async def summarize_policies(request: Request, payload: SummarizeRequest):
    if len(payload.policies) == 0:
        raise HTTPException(status_code=400, detail="요약할 정책이 1개 이상 필요합니다")

    pdf_service = get_pdf_service(request)

    def process_one(detail: dict):
        summary = pdf_service.summarize_policy_svc(detail)
        return {
            "policy_name": detail.get("plcyNm"),
            "summary": summary,
            "fields": _parse_summary_fields(summary) if summary else {},
        }

    results = await asyncio.gather(*[
        asyncio.to_thread(process_one, p.model_dump()) for p in payload.policies
    ])

    return {"results": results}


# 이미 요약이 있는 정책들(캐시 hit + 방금 요약한 것 합친 전체)을 받아 비교 추천 문장만 만든다.
@router.post("/recommend")
async def recommend(request: Request, payload: RecommendRequest):
    if len(payload.summaries) < 2:
        raise HTTPException(status_code=400, detail="비교할 정책이 2개 이상 필요합니다")

    pdf_service = get_pdf_service(request)
    summaries = [s.model_dump() for s in payload.summaries]

    comparison = await asyncio.to_thread(pdf_service.compare_policies_svc, summaries)
    recommendation = _extract_recommendation(comparison) if comparison else None

    return {"recommendation": recommendation}


# 공고문 텍스트 직접 입력 → 매칭 + 요약
@router.post("/text")
async def analyze_text(request: Request, payload: TextRequest):
    if not payload.text or len(payload.text.strip()) < 2:
        raise HTTPException(status_code=400, detail="텍스트를 더 입력해주세요")

    pdf_service = get_pdf_service(request)
    web_service = get_web_service(request)

    def process():
        match_result = web_service.match_text_svc(payload.text)
        matched_name = match_result["matched_policy"]
        method = match_result["method"]

        # ✅ 텍스트는 항상 후보군 3개 보여주기
        candidate_names = match_result.get("candidates", [])

        # 직접매칭/임베딩매칭도 matched_name을 첫 번째 후보로 포함
        if matched_name and matched_name not in ("해당 없음",):
            all_candidates = [matched_name] + [c for c in candidate_names if c != matched_name]
        else:
            all_candidates = candidate_names

        all_candidates = all_candidates[:3]

        candidate_infos = []
        for name in all_candidates:
            detail = pdf_service.get_policy_detail_svc(name)
            summary = pdf_service.summarize_policy_svc(detail) if detail else None

            fields = {}
            if summary:
                import re
                labels = ["한줄요약", "지원대상", "지원내용", "신청방법",
                        "신청기간", "사업기간", "신청URL", "지원규모"]
                pattern = re.compile(
                    rf"\*{{0,2}}({'|'.join(labels)})\*{{0,2}}\s*:\s*(.*?)(?=\*{{0,2}}(?:{'|'.join(labels)})\*{{0,2}}\s*:|$)",
                    re.S,
                )
                for label, value in pattern.findall(summary):
                    fields[label] = value.strip()

            candidate_infos.append({
                "policy_name": name,
                "summary": summary,
                "fields": fields,
                "apply_url": detail.get("aplyUrlAddr", "") if detail else "",
            })

        return {
            "filename": None,
            "matched": False,
            "policy_name": None,
            "method": method,
            "summary": None,
            "candidates": candidate_infos
        }

    result = await asyncio.to_thread(process)
    return {"mode": "summary", "results": [result]}


# URL 입력 → 크롤링(Playwright) + 매칭 + 요약
@router.post("/url")
async def analyze_url(request: Request, payload: UrlRequest):
    if not payload.url:
        raise HTTPException(status_code=400, detail="URL을 입력해주세요")

    pdf_service = get_pdf_service(request)
    web_service = get_web_service(request)

    def process():
        match_result = web_service.match_url_svc(payload.url)

        if match_result.get("blocked"):
            return {"filename": None, "matched": False, "policy_name": None, "method": "크롤링차단", "summary": None}

        matched_name = match_result["matched_policy"]
        method = match_result["method"]

        if matched_name in (None, "해당 없음"):

            candidate_infos = []

            for name in match_result.get("candidates", []):
                detail = pdf_service.get_policy_detail_svc(name)
                summary = pdf_service.summarize_policy_svc(detail) if detail else None

                fields = {}
                if summary:
                    import re
                    labels = ["한줄요약", "지원대상", "지원내용", "신청방법",
                            "신청기간", "사업기간", "신청URL", "지원규모"]
                    pattern = re.compile(
                        rf"\*{{0,2}}({'|'.join(labels)})\*{{0,2}}\s*:\s*(.*?)(?=\*{{0,2}}(?:{'|'.join(labels)})\*{{0,2}}\s*:|$)",
                        re.S,
                    )
                    for label, value in pattern.findall(summary):
                        fields[label] = value.strip()

                candidate_infos.append({
                    "policy_name": name,
                    "summary": summary,
                    "fields": fields,
                    "apply_url": detail.get("aplyUrlAddr", "") if detail else "",
                })

            return {
                "filename": None,
                "matched": False,
                "policy_name": None,
                "method": method,
                "summary": None,
                "candidates": candidate_infos
            }

        policy_detail = match_result.get("policy_detail") or pdf_service.get_policy_detail_svc(matched_name)
        summary = pdf_service.summarize_policy_svc(policy_detail) if policy_detail else None
        return {
            "filename": None, "matched": True, "policy_name": matched_name, "method": method, "summary": summary,
            "apply_url": policy_detail.get("aplyUrlAddr", "") if policy_detail else "",
        }

    result = await asyncio.to_thread(process)
    return {"mode": "summary", "results": [result]}


# 매칭된 정책에 대해 추가 질문
@router.post("/ask")
async def ask(request: Request, payload: QuestionRequest):
    pdf_service = get_pdf_service(request)
    web_service = get_web_service(request)

    policy_detail = pdf_service.get_policy_detail_svc(payload.policy_name)
    if not policy_detail:
        raise HTTPException(status_code=404, detail="정책 정보를 찾을 수 없습니다")

    def process():
        return web_service.answer_question_svc(payload.question, policy_detail)

    answer = await asyncio.to_thread(process)
    if answer is None:
        raise HTTPException(status_code=500, detail="답변 생성에 실패했습니다")
    return {"answer": answer}


# 헬스체크
@router.get("/health")
async def health_check(request: Request):
    loaded = hasattr(request.app.state, "pdf_summary_service")
    return {"status": "ok", "policy_summary_service_loaded": loaded}