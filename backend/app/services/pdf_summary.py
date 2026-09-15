import httpx
from sqlalchemy import select
from app.db.models.policy import Policy
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.core.settings import settings
from app.db.crud.pdf_summary import PdfSummaryCrud
from app.db.crud.user import UserCrud
from app.db.scheme.pdf_summary import PdfSummaryCreate, PdfMatchCreate
from app.db.models.pdf_summary import PdfSummary, PdfSummaryMatch
from app.db.crud.policy_summary_cache import PolicySummaryCacheCrud

AI_SERVICE_URL = settings.ai_service_url

class PdfSummaryService:
    """공고문 PDF/텍스트/URL 매칭·요약 결과 생성/조회/삭제 및 bene_ai 연동."""

    @staticmethod
    async def create_pdf_svc(db: AsyncSession, data: PdfSummaryCreate) -> PdfSummary:
        if not await UserCrud.get_user(db, data.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        try:
            pdf = await PdfSummaryCrud.create_pdf(db, data)
            await db.commit()
            await db.refresh(pdf)
            return pdf
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF 요약 저장에 실패했습니다.")

    @staticmethod
    async def get_pdf_svc(db: AsyncSession, pdf_id: int) -> PdfSummary:
        pdf = await PdfSummaryCrud.get_pdf(db, pdf_id)
        if not pdf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF 요약을 찾을 수 없습니다.")
        return pdf

    @staticmethod
    async def get_by_user_svc(db: AsyncSession, user_id: int) -> list[PdfSummary]:
        if not await UserCrud.get_user(db, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        return await PdfSummaryCrud.get_by_user(db, user_id)

    @staticmethod
    async def add_match_svc(db: AsyncSession, data: PdfMatchCreate) -> PdfSummaryMatch:
        try:
            match = await PdfSummaryCrud.add_match(db, data)
            await db.commit()
            await db.refresh(match)
            return match
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF 매칭 추가에 실패했습니다.")

    @staticmethod
    async def delete_pdf_svc(db: AsyncSession, pdf_id: int) -> dict:
        pdf = await PdfSummaryCrud.get_pdf(db, pdf_id)
        if not pdf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF 요약을 찾을 수 없습니다.")
        try:
            await PdfSummaryCrud.delete_pdf(db, pdf)
            await db.commit()
            return {"message": f"pdf_id '{pdf_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF 요약 삭제에 실패했습니다.")

    @staticmethod
    async def _find_policy_id(db: AsyncSession, policy_name: str) -> int | None:
        """정책명으로 backend DB의 policy_id를 찾는다(bene_ai는 정책명만 알고 PK는 모르므로)."""
        result = await db.execute(
            select(Policy.policy_id).where(Policy.plcyNm == policy_name).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _save_ai_result_svc(db: AsyncSession, user_id: int, ai_result: dict) -> dict:
        """bene_ai가 반환한 매칭/요약 결과를 DB에 저장한다: 매칭된 정책들의 요약을 pdf_summary
        1건으로 묶어 저장하고, 정책별 매칭 기록과 요약 캐시도 함께 남긴다. 매칭된 게 없으면
        저장 없이 원본 결과만 그대로 반환한다."""
        results = ai_result.get("results", [])

        # 매칭 안 된 후보 정책들에도 즐겨찾기용 policy_id를 붙여줌
        for r in results:
            if not r.get("matched"):
                for cand in r.get("candidates", []) or []:
                    cand["policy_id"] = await PdfSummaryService._find_policy_id(db, cand["policy_name"])

        matched = [r for r in results if r.get("matched") and r.get("summary")]

        if not matched:
            return {"ai_result": ai_result, "saved": None}

        summary_text = ai_result.get("comparison") or matched[0]["summary"]
        pdf = await PdfSummaryService.create_pdf_svc(
            db, PdfSummaryCreate(user_id=user_id, summary_text=summary_text)
        )

        saved_count = 0
        for r in matched:
            policy_id = await PdfSummaryService._find_policy_id(db, r["policy_name"])
            if policy_id is None:
                continue

            r["policy_id"] = policy_id  # policy_id 추가 (즐겨찾기용)

            await PdfSummaryService.add_match_svc(
                db, PdfMatchCreate(pdf_id=pdf.pdf_id, policy_id=policy_id, match_type=r.get("method"))
            )

            # 캐시 저장
            existing = await PolicySummaryCacheCrud.get_cache(db, r["policy_name"])
            if not existing:
                await PolicySummaryCacheCrud.set_cache(db, r["policy_name"], r["summary"])

            saved_count += 1

        return {"ai_result": ai_result, "saved": {"pdf_id": pdf.pdf_id, "matches": saved_count}}

    @staticmethod
    async def analyze_pdf_svc(db: AsyncSession, user_id: int, files: list[tuple[str, bytes]]) -> dict:
        """PDF 파일들을 bene_ai에 보내 매칭/요약시키고, 캐시된 요약이 있으면 먼저 채운 뒤 결과를 저장한다."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                multipart = [("files", (filename, content, "application/pdf")) for filename, content in files]
                resp = await client.post(f"{AI_SERVICE_URL}/policy-summary/pdf", files=multipart)
                resp.raise_for_status()
                ai_result = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise HTTPException(status_code=400, detail=e.response.json().get("detail", "잘못된 요청입니다"))
            raise HTTPException(status_code=502, detail="AI 서비스 호출에 실패했습니다")
        except Exception:
            raise HTTPException(status_code=502, detail="AI 서비스 호출에 실패했습니다")

        for r in ai_result.get("results", []):
            if r.get("matched") and r.get("policy_name"):
                cached = await PolicySummaryCacheCrud.get_cache(db, r["policy_name"])
                if cached:
                    r["summary"] = cached.summary_text
                    r["from_cache"] = True

        return await PdfSummaryService._save_ai_result_svc(db, user_id, ai_result)

    @staticmethod
    async def analyze_text_svc(db: AsyncSession, user_id: int, text: str) -> dict:
        """공고문 텍스트를 bene_ai에 보내 매칭/요약시키고 결과를 저장한다."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{AI_SERVICE_URL}/policy-summary/text", json={"text": text})
                resp.raise_for_status()
                ai_result = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise HTTPException(status_code=400, detail=e.response.json().get("detail", "잘못된 요청입니다"))
            raise HTTPException(status_code=502, detail="AI 서비스 호출에 실패했습니다")
        except Exception:
            raise HTTPException(status_code=502, detail="AI 서비스 호출에 실패했습니다")

        for r in ai_result.get("results", []):
            if r.get("matched") and r.get("policy_name"):
                cached = await PolicySummaryCacheCrud.get_cache(db, r["policy_name"])
                if cached:
                    r["summary"] = cached.summary_text
                    r["from_cache"] = True

        return await PdfSummaryService._save_ai_result_svc(db, user_id, ai_result)

    @staticmethod
    async def analyze_url_svc(db: AsyncSession, user_id: int, url: str) -> dict:
        """공고문 URL을 bene_ai에 보내 크롤링 후 매칭/요약시키고 결과를 저장한다."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{AI_SERVICE_URL}/policy-summary/url", json={"url": url})
                resp.raise_for_status()
                ai_result = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise HTTPException(status_code=400, detail=e.response.json().get("detail", "잘못된 요청입니다"))
            raise HTTPException(status_code=502, detail="AI 서비스 호출에 실패했습니다")
        except Exception:
            raise HTTPException(status_code=502, detail="AI 서비스 호출에 실패했습니다")

        for r in ai_result.get("results", []):
            if r.get("matched") and r.get("policy_name"):
                cached = await PolicySummaryCacheCrud.get_cache(db, r["policy_name"])
                if cached:
                    r["summary"] = cached.summary_text
                    r["from_cache"] = True

        return await PdfSummaryService._save_ai_result_svc(db, user_id, ai_result)

    @staticmethod
    async def ask_svc(policy_name: str, question: str) -> dict:
        """매칭된 정책에 대한 추가 질문을 bene_ai에 그대로 위임한다(DB 저장 없음)."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{AI_SERVICE_URL}/policy-summary/ask",
                    json={"policy_name": policy_name, "question": question},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception:
            raise HTTPException(status_code=502, detail="AI 서비스 호출에 실패했습니다")