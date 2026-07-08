from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.code_master import CodeMaster
from app.db.models.user import User
from app.db.crud.user import UserCrud
from app.core.jwt_handle import get_password_hash

CODE_DATA = [
    # 성별
    ("GENDER", "M", "남성", 1),
    ("GENDER", "F", "여성", 2),
    # 고용 상태
    ("EMPLOY", "EMPLOYED", "재직중", 1),
    ("EMPLOY", "SEEKING", "구직중", 2),
    ("EMPLOY", "STUDENT", "학생", 3),
    ("EMPLOY", "FREELANCE", "프리랜서", 4),
    ("EMPLOY", "NONE", "미취업", 5),
    # 혼인 상태
    ("MARITAL", "SINGLE", "미혼", 1),
    ("MARITAL", "MARRIED", "기혼", 2),
    ("MARITAL", "DIVORCED", "이혼", 3),
    # 학력
    ("EDUCATION", "HIGH_SCHOOL", "고졸", 1),
    ("EDUCATION", "COLLEGE", "대학재학", 2),
    ("EDUCATION", "BACHELOR", "대졸", 3),
    ("EDUCATION", "MASTER", "석사", 4),
    ("EDUCATION", "DOCTOR", "박사", 5),
    # 재학 상태
    ("STUDENT_STATUS", "ENROLLED", "재학", 1),
    ("STUDENT_STATUS", "LEAVE", "휴학", 2),
    ("STUDENT_STATUS", "GRADUATED", "졸업", 3),
    ("STUDENT_STATUS", "EXPECTED", "졸업예정", 4),
    # 군 복무 상태
    ("MILITARY", "NONE", "해당없음", 1),
    ("MILITARY", "SERVING", "복무중", 2),
    ("MILITARY", "COMPLETED", "전역", 3),
    ("MILITARY", "EXEMPTED", "면제", 4),
    # 창업 상태
    ("STARTUP_STATUS", "INTERESTED", "관심있음", 1),
    ("STARTUP_STATUS", "PREPARING", "준비중", 2),
    ("STARTUP_STATUS", "OPERATING", "운영중", 3),
    # 주거 상태
    ("HOUSING", "OWN", "자가", 1),
    ("HOUSING", "RENT", "전세", 2),
    ("HOUSING", "MONTHLY", "월세", 3),
    ("HOUSING", "DORMITORY", "기숙사", 4),
    ("HOUSING", "ETC", "기타", 5),
    # 알림 타입
    ("NOTIFY_TYPE", "BOOKMARK", "즐겨찾기 정책 알림", 1),
    ("NOTIFY_TYPE", "NEW_POLICY", "새 정책 등록", 2),
    ("NOTIFY_TYPE", "NOTICE", "공지사항", 3),
    ("NOTIFY_TYPE", "SYSTEM", "시스템 알림", 4),
    ("NOTIFY_TYPE", "INQUIRY_ANSWER", "문의 답변 알림", 5),
]

ADMIN_EMAIL = "admin@admin"
ADMIN_PASSWORD = "admin1234!"


async def seed_code_master(session: AsyncSession):
    for code_group, code_value, code_label, sort_order in CODE_DATA:
        result = await session.execute(
            select(CodeMaster).where(
                CodeMaster.code_group == code_group,
                CodeMaster.code_value == code_value,
            )
        )
        if result.scalar_one_or_none() is None:
            session.add(CodeMaster(
                code_group=code_group,
                code_value=code_value,
                code_label=code_label,
                sort_order=sort_order,
            ))


async def seed_admin_user(session: AsyncSession):
    if await UserCrud.get_by_email_and_provider(session, ADMIN_EMAIL, "local") is None:
        session.add(User(
            name="관리자",
            email=ADMIN_EMAIL,
            provider="local",
            password=get_password_hash(ADMIN_PASSWORD),
            role="ADMIN",
            profile_completed=True,
        ))


async def run_all_seeds(session: AsyncSession):
    await seed_code_master(session)
    await seed_admin_user(session)
