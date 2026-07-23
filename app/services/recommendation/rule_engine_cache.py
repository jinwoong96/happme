import hashlib
import json

# rule engine 8개 체크 중 apply_period를 제외한 7개(age/region/marriage/school_status/major/
# sbiz/job)가 실제로 읽는 사용자 프로필 필드. 이 필드들이 전부 같으면 두 요청은 rule engine
# 관점에서 동일한 "페르소나"라 결과를 재사용할 수 있다. situation(자유텍스트)은 rule engine이
# 아니라 similarity_search에서만 쓰이므로 시그니처에서 제외한다.
# user_testprofile.id처럼 요청마다 새로 생기는 값을 키로 쓰면(분석 1회당 새 row가 쌓이는 구조라
# 재사용이 거의 안 됨) 캐시가 무용지물이 되므로, row id가 아니라 필드값 자체를 키로 쓴다.
PERSONA_SIGNATURE_FIELDS = (
    "age", "region", "district", "marital_status", "education", "major_category",
    "gender", "disability", "basic_livelihood", "single_parent",
    "employment_status", "sme_employment",
)


def make_persona_signature(user: dict) -> str:
    payload = {field: user.get(field) for field in PERSONA_SIGNATURE_FIELDS}
    normalized = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class RuleEngineCache:
    """
    persona_signature + plcyNo 기준으로, apply_period를 제외한 7개 체크의 "요약"을 인메모리에
    캐싱한다. apply_period는 "오늘 날짜"에 의존해 정책 내용이 그대로여도 매일 결과가 바뀔 수
    있어 캐싱 대상에서 제외하고 매 요청 새로 계산한다(recommendation_service.py 참고).

    저장 값은 evaluate_content()가 반환하는 7개 체크의 원본 결과(각 체크의 reason/user_value/
    policy_value 포함)가 아니라, 다운스트림에서 실제로 쓰는 두 값만 압축한
    {"content_matched": bool, "region_scope": str | None} 이다. rule engine 자체(eligibility_
    rules.py의 evaluate()/evaluate_content())는 OCR 자격판정(check_eligibility_svc)이 그대로
    쓰기 때문에 원본 상세정보를 그대로 반환하지만, 이 캐시는 결과만 필요해서 압축한다 - 압축
    안 하면 엔트리당 ~5KB라 persona 하나(카탈로그 전체 스캔 기준)당 ~19MB까지 나간다.

    무효화는 시간 비교가 아니라, 정책이 실제로 바뀌는 시점(policy_loader.upsert_policy/
    remove_policy를 트리거하는 policy_cache.py 라우터)에 그 자리에서 해당 plcyNo만 모든
    persona 캐시에서 지우는 방식으로 처리한다(invalidate_policy).

    TTL/용량 제한은 아직 없다 - persona 조합 수는 이론상 프로필 필드 카디널리티로 유한하게
    bound되지만, 실사용 트래픽에서 메모리 사용량이 문제가 되면 LRU 등 eviction을 추가로 고려한다.
    """

    def __init__(self):
        self._store: dict[str, dict[str, dict]] = {}

    def get(self, persona_signature: str, plcy_no: str) -> dict | None:
        return self._store.get(persona_signature, {}).get(str(plcy_no))

    def set(self, persona_signature: str, plcy_no: str, summary: dict) -> None:
        self._store.setdefault(persona_signature, {})[str(plcy_no)] = summary

    def invalidate_policy(self, plcy_no: str) -> None:
        """정책 하나가 생성/수정/삭제됐을 때, 모든 persona의 캐시에서 그 정책 항목만 지운다."""
        plcy_no = str(plcy_no)
        for policies in self._store.values():
            policies.pop(plcy_no, None)

    def stats(self) -> dict:
        return {
            "persona_count": len(self._store),
            "entry_count": sum(len(v) for v in self._store.values()),
        }
