import hashlib
import json
from collections import OrderedDict

# persona 캐시 최대 개수. 넘치면 가장 오래 안 쓰인(가장 오래전에 get/set된) persona를 통째로
# 지운다(_evict_if_needed).
MAX_PERSONAS = 500

# 변경 로그(_change_log) 최대 보관 개수. 이보다 오래된 변경분은 트림되고, 트림된 범위까지
# 거슬러 올라가야 하는 persona는 안전하게 전체 재계산으로 폴백한다(get_changes_since).
MAX_CHANGE_LOG = 2000

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
    persona_signature 기준으로, 그 persona가 조건(apply_period 제외 7개 체크)을 만족하는
    정책만 {plcyNo: region_scope} 형태로 압축해서 인메모리에 캐싱한다(persona당 캐시 항목 1개).
    불만족 정책(보통 카탈로그 대부분)은 저장하지 않는다 - 저장해봐야 메모리만 먹고, 실제로
    쓰는 건 "만족하는 정책 목록"뿐이기 때문이다.

    apply_period는 "오늘 날짜"에 의존해 정책 내용이 그대로여도 매일 결과가 바뀔 수 있어
    캐싱 대상에서 제외하고 매 요청 새로 계산한다(recommendation_service.py 참고).

    무효화: 정책 하나가 생성/수정/삭제될 때마다(policy_cache.py 라우터) mark_policy_changed()로
    전역 변경 로그(_change_log)에 버전 번호와 함께 남긴다. persona 캐시를 재사용할 때는 그
    persona가 마지막으로 동기화된 버전(synced_version) 이후 바뀐 plcyNo만 get_changes_since로
    골라내서 그 정책들만 다시 평가한다(recommendation_service.py의 _get_persona_matches) -
    캐시 전체를 비우거나 persona 전체를 통째로 재계산하지 않는다. change_log 자체는
    MAX_CHANGE_LOG개까지만 보관하고, 그보다 오래돼서 트림된 변경분까지 거슬러 올라가야 하는
    persona는 안전하게 전체 재계산으로 폴백한다.

    용량은 MAX_PERSONAS로 상한을 두고, 넘치면 가장 오래 안 쓰인 persona부터 LRU로 지운다.
    """

    def __init__(self, max_personas: int = MAX_PERSONAS, max_change_log: int = MAX_CHANGE_LOG):
        # persona_signature -> {"matched": {plcyNo: region_scope}, "synced_version": int}
        self._store: "OrderedDict[str, dict]" = OrderedDict()
        self._max_personas = max_personas

        # 버전번호 -> plcyNo. 정책이 바뀔 때마다 하나씩 추가되고(mark_policy_changed), 오래된
        # 건 트림된다.
        self._change_log: "OrderedDict[int, str]" = OrderedDict()
        self._version = 0
        self._max_change_log = max_change_log

    def mark_policy_changed(self, plcy_no: str) -> None:
        """정책 하나가 생성/수정/삭제됐을 때 호출한다(policy_cache.py의 upsert/delete 엔드포인트)."""
        self._version += 1
        self._change_log[self._version] = str(plcy_no)
        while len(self._change_log) > self._max_change_log:
            self._change_log.popitem(last=False)

    def current_version(self) -> int:
        return self._version

    def get_persona(self, persona_signature: str) -> dict | None:
        """캐시된 persona 항목({"matched", "synced_version"})을 반환한다. 없으면 None."""
        entry = self._store.get(persona_signature)
        if entry is not None:
            self._store.move_to_end(persona_signature)  # 방금 사용했으니 가장 최근으로 표시
        return entry

    def set_persona(self, persona_signature: str, matched: dict, synced_version: int) -> None:
        self._store[persona_signature] = {"matched": matched, "synced_version": synced_version}
        self._store.move_to_end(persona_signature)
        self._evict_if_needed()

    def get_changes_since(self, since_version: int) -> list[str] | None:
        """since_version 이후 바뀐 plcyNo 목록을 반환한다. change_log가 트림돼서 since_version
        까지 안전하게 거슬러 올라갈 수 없으면(중간에 빠진 구간이 있으면) None을 반환해 호출부가
        전체 재계산으로 폴백하게 한다."""
        if not self._change_log:
            return []
        earliest_version = next(iter(self._change_log))
        if since_version < earliest_version - 1:
            return None
        return [plcy_no for version, plcy_no in self._change_log.items() if version > since_version]

    def _evict_if_needed(self) -> None:
        while len(self._store) > self._max_personas:
            self._store.popitem(last=False)  # 가장 오래 안 쓰인(맨 앞) persona부터 제거

    def clear(self) -> None:
        """persona 캐시만 비운다(변경 로그/버전은 그대로 둔다 - 로그까지 지우면 남아있는 persona가
        없으니 상관없고, 앞으로 새로 캐싱될 persona들은 현재 버전 기준으로 동기화되므로 문제
        없다). eligibility_rules.py의 판정 로직 자체가 바뀌었을 때처럼, 정책 데이터는 그대로인데
        옛 로직 기준으로 캐싱된 결과를 전부 무효화해야 하는 경우를 위한 수동 초기화용이다
        (policy_cache 라우터의 /rule-engine-cache/clear에서만 호출)."""
        self._store.clear()

    def stats(self) -> dict:
        return {
            "persona_count": len(self._store),
            "entry_count": sum(len(v["matched"]) for v in self._store.values()),
            "max_personas": self._max_personas,
            "change_log_size": len(self._change_log),
            "version": self._version,
        }
