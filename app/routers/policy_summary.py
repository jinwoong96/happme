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
        return {"filename": filename, "matched": True, "policy_name": matched_name, "method": method, "summary": summary}

    results = await asyncio.gather(*[
        asyncio.to_thread(process_one, filename, pdf_bytes) for filename, pdf_bytes in payloads
    ])

    if len(results) == 1:
        return {"mode": "summary", "results": results}

    matched_results = [r for r in results if r["matched"] and r["summary"]]
    comparison = pdf_service.compare_policies_svc(matched_results) if len(matched_results) >= 2 else None

    return {"mode": "compare", "results": results, "comparison": comparison}


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
        return {"filename": None, "matched": True, "policy_name": matched_name, "method": method, "summary": summary}

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