import json
import re
import time

from app.core.settings import settings


SYSTEM_PROMPT = """한국 청년정책 공고문([정책설명]/[신청방법]/[심사방법])에서 실제 날짜가 명시된
사건만 JSON 배열로 추출하는 도구입니다.

규칙:
- 같은 사건이 여러 섹션에 중복 언급되면 한 번만, 더 구체적인 표현으로 출력
- 같은 날짜에 type 여러 개 부여 금지
- "신청/모집" 관련 type은 aplyYmd가 별도 관리하므로 금지
- raw_text에 실제 날짜 표현이 없으면 추출 금지 (절차 번호, 횟수, "익월"은 날짜 아님)
- "~일 이내", "~후", "상시", "연중", "예산 소진 시까지"처럼 기준일 없는 상대 기간/무기한 표현은 추출 금지
- "OO 기준"처럼 자격요건 판단을 위한 기준 시점은 사용자가 할 일이 아니므로 추출 금지
  (예: "2025.12.22 기준 자격 충족 시 자동 승인"은 자격 판단용 기준일이지 일정이 아님 → 추출 금지)
- "OO일 이전/이후는 OO서류 제출"처럼 서류 종류를 가르는 조건부 안내는 일정이 아니므로 추출 금지
- 일(day) 정보 없으면 지어내지 말고 date는 "YYYY-MM"으로
- 연도 없는 날짜(월/일만 있음)는 [공고 등록연도] 기준 추정. 날짜 자체가 없으면 추정 금지
- 시작일과 종료일이 둘 다 원문에 있을 때만 범위(~)로 출력. 끝 날짜를 지어내지 말 것

type은 다음 중 가장 가까운 것: 서류심사, 결과발표, 면접, 서류등록, 배치통보, 사업개시, 기수별기간

출력 형식: {"type": "...", "date": "YYYY-MM-DD 또는 YYYY-MM 또는 YYYY-MM-DD ~ YYYY-MM-DD", "raw_text": "원문 인용"}
해당 일정 없으면 []. JSON 배열만 출력하고 다른 설명은 절대 포함하지 마세요."""

TIP_SYSTEM_PROMPT = """한국 청년정책 신청자에게 다음 준비물/일정을 언제까지 준비하면 좋을지
짧은 한 문장으로 안내하는 도우미입니다.

규칙:
- 신청마감일과 추출된 일정(서류심사/결과발표/면접 등) 중 가장 가까운 것을 기준으로 조언
- "OO까지 준비하세요" 또는 "OO부터 시작 권장" 같은 실용적인 한 문장만 출력
- 다른 설명, 인사말, 따옴표 없이 문장 하나만 출력
- 참고할 일정이 전혀 없으면 빈 문자열만 출력"""

FORBIDDEN_TYPE_SUBSTRINGS = ["신청", "모집"]

# "7. 20." 또는 "7월 20일" 같은 월/일 패턴을 찾아서 (월, 일) 튜플로 반환.
MD_PATTERN = re.compile(r"(?<!\d)(\d{1,2})\s*(?:[.\-/]|월)\s*(\d{1,2})(?!\d)")
MONTH_ONLY_PATTERN = re.compile(r"(?<!\d)(\d{1,2})\s*월")
CONDITIONAL_RULE_PATTERN = re.compile(r"(이전|이후)(은|는|에는)")


def _normalize_for_match(text: str) -> str:
    """공백을 지워서 비교하기 쉽게 만든다."""
    return re.sub(r"\s+", "", text or "")


def _raw_text_is_grounded(raw_text: str, source_text: str) -> bool:
    """LLM이 추출한 raw_text가 실제로 원문(source_text)에 있는 문장인지 확인한다.
    LLM이 없는 내용을 지어내는 것(할루시네이션)을 걸러내기 위한 검증이다."""
    needle = _normalize_for_match(raw_text)
    haystack = _normalize_for_match(source_text)
    if not needle:
        return False
    return needle in haystack


def _extract_md_pairs(text: str) -> list:
    """텍스트에서 "7.20" "7월 20일" 같은 월/일 표현을 전부 찾아 (월, 일) 튜플 리스트로 반환한다."""
    return [(int(m), int(d)) for m, d in MD_PATTERN.findall(text or "")]


def _is_conditional_rule_text(text: str) -> bool:
    """"~이전은/~이후는"처럼 일정이 아니라 서류 종류를 가르는 조건부 안내 문장인지 확인한다."""
    return bool(CONDITIONAL_RULE_PATTERN.search(text or ""))


def _build_date_from_raw(raw_text: str, reg_year: str) -> str:
    """raw_text에서 월/일을 뽑아 공고 등록연도(reg_year)를 붙여 실제 날짜 문자열로 만든다.
    월/일이 2개면 기간(~)으로, 1개면 단일 날짜로, 월만 있으면 "YYYY-MM"으로 만든다."""
    if not reg_year or not reg_year.isdigit():
        return ""

    pairs = _extract_md_pairs(raw_text)

    if len(pairs) >= 2:
        m1, d1 = pairs[0]
        m2, d2 = pairs[-1]
        return f"{reg_year}-{m1:02d}-{d1:02d} ~ {reg_year}-{m2:02d}-{d2:02d}"
    if len(pairs) == 1:
        m, d = pairs[0]
        return f"{reg_year}-{m:02d}-{d:02d}"

    month_only = MONTH_ONLY_PATTERN.search(raw_text or "")
    if month_only:
        return f"{reg_year}-{int(month_only.group(1)):02d}"

    return ""


def _extract_json_array(text: str) -> list:
    """LLM 응답 텍스트에서 JSON 배열 부분만 뽑아 파싱한다. 실패하면 빈 리스트."""
    text = text.strip()
    text = re.sub(r"^```json|^```|```$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return []


def _clean_events(events: list, raw_full_text: str, reg_year: str) -> list:
    """LLM이 추출한 일정 후보들을 검증/정제한다: 원문에 실제로 있는지, 금지된
    타입(신청/모집)은 아닌지, 조건부 안내 문장은 아닌지 걸러내고 날짜를 채운다."""
    cleaned = []
    for e in events:
        etype = e.get("type") or ""
        raw_text = e.get("raw_text") or ""

        if not _raw_text_is_grounded(raw_text, raw_full_text):
            continue
        if any(bad in etype for bad in FORBIDDEN_TYPE_SUBSTRINGS):
            continue
        if _is_conditional_rule_text(raw_text):
            continue

        date_str = _build_date_from_raw(raw_text, reg_year)
        if not date_str:
            continue

        cleaned.append({"type": etype, "date": date_str, "raw_text": raw_text})

    return cleaned


def _build_user_prompt(policy: dict) -> str:
    """정책의 설명/신청방법/심사방법 원문과 공고 등록연도를 LLM에게 줄 프롬프트로 합친다."""
    reg_year = (policy.get("frstRegDt") or "")[:4] or "알 수 없음"
    parts = [
        f"[공고 등록연도] {reg_year}",
        f"[정책설명]\n{policy.get('plcyExplnCn', '') or '(없음)'}",
        f"[신청방법]\n{policy.get('plcyAplyMthdCn', '') or '(없음)'}",
        f"[심사방법]\n{policy.get('srngMthdCn', '') or '(없음)'}",
    ]
    return "\n\n".join(parts)


class ScheduleService:
    """
    청년정책 공고문에서 실제 일정(서류심사/결과발표/면접 등)을 추출하고,
    준비 팁 문장을 생성하는 rule-engine + watsonx.ai 기반 서비스.
    API 클라이언트를 들고 있으므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    """

    def __init__(self):
        self.enabled = bool(settings.watsonx_api_key) and bool(settings.watsonx_project_id)
        if not self.enabled:
            print("[ScheduleService] watsonx 설정이 없어 일정 추출은 비활성화됩니다")
            return

        from ibm_watsonx_ai import Credentials, APIClient
        from ibm_watsonx_ai.foundation_models import ModelInference

        print("[ScheduleService] watsonx.ai 연결 중...")
        credentials = Credentials(url=settings.watsonx_url, api_key=settings.watsonx_api_key)
        api_client = APIClient(credentials, project_id=settings.watsonx_project_id)
        self.model = ModelInference(api_client=api_client, model_id=settings.schedule_model_id)
        print("[ScheduleService] 준비 완료")

    def extract_events_svc(self, policy: dict, retries: int = 1) -> list[dict]:
        """공고문에서 실제 날짜가 있는 일정(서류심사/결과발표/면접 등)을 LLM으로 추출하고
        검증한다. 실패하면 retries만큼 재시도하고, 그래도 실패하면 빈 리스트를 반환한다."""
        if not self.enabled:
            return []

        raw_full_text = _build_user_prompt(policy)
        reg_year = (policy.get("frstRegDt") or "")[:4]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_full_text},
        ]

        last_error = None
        for _ in range(retries + 1):
            try:
                response = self.model.chat(messages=messages, params={"temperature": 0, "max_completion_tokens": 512})
                content = response["choices"][0]["message"]["content"]
                events = _extract_json_array(content)
                return _clean_events(events, raw_full_text, reg_year)
            except Exception as e:
                last_error = e
                time.sleep(1)
        print(f"[ScheduleService] 일정 추출 실패: {last_error}")
        return []

    def generate_prep_tip_svc(self, policy: dict, events: list[dict]) -> str | None:
        """추출된 일정과 신청마감일을 보고 "언제까지 뭘 준비하면 좋을지" 짧은 안내 문장을 만든다."""
        if not self.enabled:
            return None

        events_text = "\n".join(f"- {e['type']}: {e['date']} ({e['raw_text']})" for e in events) or "(추출된 일정 없음)"
        user_prompt = f"[정책명] {policy.get('plcyNm', '')}\n[신청마감] {policy.get('aplyYmd', '') or '(없음)'}\n[추출된 일정]\n{events_text}"
        messages = [
            {"role": "system", "content": TIP_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.model.chat(messages=messages, params={"temperature": 0.3, "max_completion_tokens": 128})
            tip = response["choices"][0]["message"]["content"].strip().strip('"')
            return tip or None
        except Exception as e:
            print(f"[ScheduleService] 준비 팁 생성 실패: {e}")
            return None
