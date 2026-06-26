from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.ocr_result import OcrResultCrud
from app.db.crud.user import UserCrud
from app.db.scheme.ocr_result import OcrResultCreate, OcrMatchCreate
from app.db.models.ocr_result import OcrResult, OcrResultMatch


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
