from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.user_profile import UserProfileCrud
from app.db.crud.bookmark import BookmarkCrud
from app.db.crud.policy import PolicyCrud
from app.db.crud.policy_income_required import PolicyIncomeRequiredCrud
from app.db.crud.user_testprofile import UserTestProfileCrud
from app.db.scheme.recommendation import ScenarioRecommendationRequest
from app.db.scheme.user_profile import UserProfileRead
from app.db.scheme.user_testprofile import UserTestProfileCreate
from app.services.ai_client import AiClient
from app.services.policy import PolicyService

# user_testprofile은 user_profile과 컬럼이 동일하다. UserProfileRead에는 있지만
# user_testprofile에는 없는 계정성/계산 필드(user_id 제외, updated_at, age)는 제외하고 골라낸다.
TEST_PROFILE_FIELDS = (
    "birth_date", "gender", "region", "district", "education", "major_category",
    "employment_status", "sme_employment",
    "marital_status", "disability", "basic_livelihood", "single_parent", "situation",
)


class RecommendationService:
    """맞춤형 정책 추천(bene_ai 호출) 결과에 카드 표시 필드/DB policy_id/소득확인 필요
    필드/즐겨찾기 여부를 붙여서 반환한다."""

    @staticmethod
    async def get_recommendations_svc(db: AsyncSession, user_id: int) -> dict:
        """사용자 프로필 기반 맞춤형 정책 추천을 받는다."""
        user_profile_payload = await RecommendationService._get_user_profile_payload(db, user_id)

        # TODO(1차 테스트 이후): 추천 결과 DB 저장, updated_at 비교를 통한 캐시 재사용 로직 추가
        result = await AiClient.recommend(user_profile_payload)
        result = await RecommendationService._attach_policy_cards(db, result)
        result = await RecommendationService._attach_db_policy_ids(db, result)
        result = await RecommendationService._attach_income_required_fields(db, result)
        return await RecommendationService._attach_bookmark_flags(db, user_id, result)

    @staticmethod
    async def get_chat_recommendations_svc(db: AsyncSession, user_id: int, chat: str) -> dict:
        """사용자 프로필 + 채팅 상황 설명을 함께 사용한 맞춤형 정책 추천을 받는다."""
        user_profile_payload = await RecommendationService._get_user_profile_payload(db, user_id)
        result = await AiClient.recommend_chat(user_profile_payload, chat)
        result = await RecommendationService._attach_policy_cards(db, result)
        result = await RecommendationService._attach_db_policy_ids(db, result)
        result = await RecommendationService._attach_income_required_fields(db, result)
        return await RecommendationService._attach_bookmark_flags(db, user_id, result)

    @staticmethod
    async def get_scenario_recommendations_svc(db: AsyncSession, user_id: int, data: ScenarioRecommendationRequest) -> dict:
        """
        Q1(지역이동)/Q2(취업 변화) 구조화 답변으로 what-if 프로필을 만들어 추천을 받는다.
        실제 user_profile은 건드리지 않고, diff를 얹은 스냅샷을 user_testprofile에 먼저 저장한 뒤
        그 값으로 AI 분석(recommend_chat)을 수행한다.
        """
        user_profile_payload = await RecommendationService._get_user_profile_payload(db, user_id)

        resolved = await AiClient.resolve_scenario(
            data.region_choice, data.region_text, data.employment_choice, data.employment_other
        )
        test_profile = {**user_profile_payload, **resolved["diff"], "situation": data.situation}

        test_profile_fields = {k: test_profile.get(k) for k in TEST_PROFILE_FIELDS}
        await UserTestProfileCrud.create_test_profile(
            db, UserTestProfileCreate(user_id=user_id, **test_profile_fields)
        )
        await db.commit()

        result = await AiClient.recommend_chat(test_profile, data.situation)
        result = await RecommendationService._attach_policy_cards(db, result)
        result = await RecommendationService._attach_db_policy_ids(db, result)
        result = await RecommendationService._attach_income_required_fields(db, result)
        result = await RecommendationService._attach_bookmark_flags(db, user_id, result)

        # simulation_result 기록은 일단 보류 (표시 개수 제한을 없애면서 분석 1회당 수천 건이 쌓여서 중단)

        return result

    @staticmethod
    async def judge_income_eligibility_svc(plcy_no: str, answers: dict) -> dict:
        """카드의 '소득계산' 버튼에서 호출. 답변은 판정에만 쓰이고 DB에 저장하지 않는다."""
        return await AiClient.judge_income_eligibility(plcy_no, answers)

    @staticmethod
    async def _get_user_profile_payload(db: AsyncSession, user_id: int) -> dict:
        """추천 요청에 넘길 사용자 프로필 dict를 만든다. 프로필이 없으면 404 에러."""
        profile = await UserProfileCrud.get_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="프로필을 먼저 등록해주세요.")
        return UserProfileRead.model_validate(profile).model_dump(mode="json")

    @staticmethod
    async def _attach_policy_cards(db: AsyncSession, result: dict) -> dict:
        """plcyNo 기준으로 PolicyService.get_policy_cards_svc의 카드 표시용 필드를 덧붙입니다. 버킷 키 구성과 무관하게 동작합니다."""
        plcy_nos = {
            str(policy.get("plcyNo"))
            for policies in result.values() if isinstance(policies, list)
            for policy in policies if policy.get("plcyNo") is not None
        }

        cards = await PolicyService.get_policy_cards_svc(db, list(plcy_nos))
        summaries = await PolicyCrud.get_summaries_by_plcyno(db, list(plcy_nos))

        for policies in result.values():
            if not isinstance(policies, list):
                continue
            for policy in policies:
                plcy_no = str(policy.get("plcyNo"))
                summary = summaries.get(plcy_no)
                if summary:
                    policy["policy_summary"] = summary

                card = cards.get(plcy_no)
                if not card:
                    continue

                if card.get("policy_name"):
                    policy["policy_name"] = card["policy_name"]
                policy["apply_period_type"] = card.get("apply_period_type")
                policy["apply_period"] = card.get("apply_period")
                policy["target"] = card.get("target")
                policy["link"] = card.get("link")

        return result

    @staticmethod
    async def _attach_db_policy_ids(db: AsyncSession, result: dict) -> dict:
        """AI 응답의 plcyNo로 backend DB에서 실제 policy_id를 조회해 각 정책 dict에 붙입니다. 버킷 키 구성과 무관하게 동작합니다."""
        plcy_nos = {
            str(policy.get("plcyNo"))
            for policies in result.values() if isinstance(policies, list)
            for policy in policies if policy.get("plcyNo") is not None
        }

        plcyno_to_policy_id = await PolicyCrud.get_policy_ids_by_plcyno(db, list(plcy_nos))

        for policies in result.values():
            if not isinstance(policies, list):
                continue
            for policy in policies:
                policy["policy_id"] = plcyno_to_policy_id.get(str(policy.get("plcyNo")))

        return result

    @staticmethod
    async def _attach_income_required_fields(db: AsyncSession, result: dict) -> dict:
        """
        policy_incomeRequired 기준으로 각 정책에 required_fields(list[str])를 붙입니다.
        행이 없으면(=애초에 소득 확인이 필요없는 정책) 빈 리스트를 붙입니다.
        프론트는 이 리스트가 비어있지 않을 때만 "소득계산" 버튼을 보여주면 됩니다.
        """
        plcy_nos = {
            str(policy.get("plcyNo"))
            for policies in result.values() if isinstance(policies, list)
            for policy in policies if policy.get("plcyNo") is not None
        }

        required_fields_by_plcyno = await PolicyIncomeRequiredCrud.get_required_fields_by_plcyno(db, list(plcy_nos))

        for policies in result.values():
            if not isinstance(policies, list):
                continue
            for policy in policies:
                policy["required_fields"] = required_fields_by_plcyno.get(str(policy.get("plcyNo")), [])

        return result

    @staticmethod
    async def _attach_bookmark_flags(db: AsyncSession, user_id: int, result: dict) -> dict:
        """policy_id(backend DB PK) 기준으로 즐겨찾기 여부를 붙입니다. plcyNo는 사용하지 않습니다."""
        bookmarks = await BookmarkCrud.get_by_user(db, user_id)
        bookmarked_ids = {str(b.policy_id) for b in bookmarks}

        for policies in result.values():
            if not isinstance(policies, list):
                continue
            for policy in policies:
                policy["is_bookmarked"] = str(policy.get("policy_id")) in bookmarked_ids

        return result
