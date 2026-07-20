from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.ocr_result import OcrResultCrud
from app.db.crud.user import UserCrud
from app.db.crud.user_profile import UserProfileCrud
from app.db.scheme.ocr_result import OcrResultCreate, OcrMatchCreate
from app.db.scheme.user_profile import UserProfileRead
from app.db.models.ocr_result import OcrResult, OcrResultMatch
from app.services.ai_client import AiClient


class OcrResultService:

    @staticmethod
    async def create_ocr_svc(db: AsyncSession, data: OcrResultCreate) -> OcrResult:
        if not await UserCrud.get_user(db, data.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        try:
            ocr = await OcrResultCrud.create_ocr(db, data)
            await db.commit()
            await db.refresh(ocr)
            return ocr
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OCR 결과 저장에 실패했습니다.")

    @staticmethod
    async def get_ocr_svc(db: AsyncSession, ocr_id: int) -> OcrResult:
        ocr = await OcrResultCrud.get_ocr(db, ocr_id)
        if not ocr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR 결과를 찾을 수 없습니다.")
        return ocr

    @staticmethod
    async def get_by_user_svc(db: AsyncSession, user_id: int) -> list[OcrResult]:
        if not await UserCrud.get_user(db, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        return await OcrResultCrud.get_by_user(db, user_id)

    @staticmethod
    async def add_match_svc(db: AsyncSession, data: OcrMatchCreate) -> OcrResultMatch:
        try:
            match = await OcrResultCrud.add_match(db, data)
            await db.commit()
            await db.refresh(match)
            return match
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OCR 매칭 추가에 실패했습니다.")

    @staticmethod
    async def delete_ocr_svc(db: AsyncSession, ocr_id: int) -> dict:
        ocr = await OcrResultCrud.get_ocr(db, ocr_id)
        if not ocr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OCR 결과를 찾을 수 없습니다.")
        try:
            await OcrResultCrud.delete_ocr(db, ocr)
            await db.commit()
            return {"message": f"ocr_id '{ocr_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OCR 결과 삭제에 실패했습니다.")

    # 이미지 업로드 -> bene_ai 분석 -> OCR 결과 + 매칭 저장
    @staticmethod
    async def analyze_image_svc(
        db: AsyncSession, user_id: int, image_bytes: bytes, filename: str, content_type: str
    ) -> dict:
        if not await UserCrud.get_user(db, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")

        if not content_type or not content_type.startswith("image/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미지 파일만 업로드 가능합니다.")

        ai_result = await AiClient.analyze_image(image_bytes, filename, content_type)

        extracted_text = ai_result.get("extracted_text", "")
        ai_matches = ai_result.get("matches", [])  # [{policy_id, plcyNo, plcyNm, score}, ...]
        summary_text = ai_result.get("summary_text")

        # 매칭된 정책마다 "지원가능"/"지원불가" 판정을 붙인다. 프로필 미등록/AI 호출 실패 시엔
        # eligible을 None으로 두고 조용히 넘어간다(화면에서는 그 경우 칩을 안 보여주면 됨).
        if ai_matches:
            profile = await UserProfileCrud.get_profile(db, user_id)
            if profile:
                try:
                    user_profile_payload = UserProfileRead.model_validate(profile).model_dump(mode="json")
                    plcy_nos = [m["plcyNo"] for m in ai_matches if m.get("plcyNo")]
                    eligibility_results = await AiClient.check_eligibility_batch(user_profile_payload, plcy_nos)
                    eligibility_by_plcyno = {r["plcyNo"]: r for r in eligibility_results}
                    for m in ai_matches:
                        result = eligibility_by_plcyno.get(m.get("plcyNo"))
                        m["eligible"] = result["result"] if result else None
                        m["ineligible_reasons"] = result["reasons"] if result else []
                except HTTPException:
                    for m in ai_matches:
                        m["eligible"] = None
                        m["ineligible_reasons"] = []
            else:
                for m in ai_matches:
                    m["eligible"] = None
                    m["ineligible_reasons"] = []

        if not extracted_text:
            return {
                "extracted_text": "",
                "matches": [],
                "summary_text": None,
                "message": ai_result.get("message", "텍스트를 추출하지 못했습니다."),
            }

        try:
            ocr = await OcrResultCrud.create_ocr(db, OcrResultCreate(user_id=user_id, extracted_text=extracted_text))
            await db.flush()

            for m in ai_matches:
                await OcrResultCrud.add_match(
                    db, OcrMatchCreate(ocr_id=ocr.ocr_id, policy_id=m["policy_id"], match_score=m["score"], match_type="ocr")
                )

            # LLM 요약이 있으면 pdf_summary에도 같이 저장 (기존 PdfSummaryService 재사용)
            pdf_id = None
            if summary_text:
                from app.services.pdf_summary import PdfSummaryService
                from app.db.scheme.pdf_summary import PdfSummaryCreate, PdfMatchCreate
                from app.db.crud.pdf_summary import PdfSummaryCrud

                pdf = await PdfSummaryCrud.create_pdf(db, PdfSummaryCreate(user_id=user_id, summary_text=summary_text))
                await db.flush()
                pdf_id = pdf.pdf_id
                for m in ai_matches:
                    await PdfSummaryCrud.add_match(
                        db, PdfMatchCreate(pdf_id=pdf.pdf_id, policy_id=m["policy_id"], match_score=m["score"], match_type="llm")
                    )

            await db.commit()
            await db.refresh(ocr)
        except HTTPException:
            raise
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="분석 결과 저장에 실패했습니다.")

        return {
            "ocr_id": ocr.ocr_id,
            "pdf_id": pdf_id,
            "extracted_text": extracted_text,
            "matches": ai_matches,
            "summary_text": summary_text,
            "message": ai_result.get("message"),
        }