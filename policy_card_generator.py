### watsonx.ai로 정책 카드(제목/신청기간/지원대상/지원내용요약/링크) 생성 (하위 코드)
# policy_card_generator.py

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import ModelInference


# ---------------------------------------------------------------------------
# 코드값 매핑
# ---------------------------------------------------------------------------

# 신청기간구분코드(aplyPrdSeCd) 매핑
# 데이터 실측으로 확인한 값:
#   0057001 -> 특정기간 (aplyYmd에 "YYYYMMDD ~ YYYYMMDD" 값이 채워짐)
#   0057002 -> 상시     (aplyYmd 비어 있음, bizPrdEtcCn 등에 "상시/연중" 표기)
#   0057003 -> 마감     (aplyYmd 비어 있음, 정책명에 "[n월 마감]" 등 표기)
APLY_PRD_SE_CD_MAP = {
    "0057001": "특정기간",
    "0057002": "상시",
    "0057003": "마감",
}


# ---------------------------------------------------------------------------
# 규칙 기반 필드 (제목 / 신청기간 / 지원대상 / 링크)
# ---------------------------------------------------------------------------

def parse_apply_period(policy: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    신청기간 관련 필드를 만든다.

    Returns:
        (apply_period_type, apply_period)
        - apply_period_type: "상시" | "마감" | "특정기간" | "확인필요"
        - apply_period: 특정기간일 때만 "YYYY-MM-DD ~ YYYY-MM-DD", 그 외 None
    """
    code = policy.get("aplyPrdSeCd", "")
    period_type = APLY_PRD_SE_CD_MAP.get(code, "확인필요")

    if period_type != "특정기간":
        return period_type, None

    aply_ymd = (policy.get("aplyYmd") or "").strip()
    match = re.match(r"(\d{8})\s*~\s*(\d{8})", aply_ymd)

    if not match:
        # 특정기간 코드인데 날짜 파싱이 안 되면 원문을 그대로 보존
        return period_type, aply_ymd or None

    start_raw, end_raw = match.groups()

    def fmt(ymd: str) -> str:
        return f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"

    return period_type, f"{fmt(start_raw)} ~ {fmt(end_raw)}"


def build_target(policy: Dict[str, Any]) -> str:
    """
    지원대상 텍스트를 만든다. (나이 + 소득조건 + 추가 자격조건 조합)
    """
    parts: List[str] = []

    age_limit_yn = (policy.get("sprtTrgtAgeLmtYn") or "").strip()
    min_age = (policy.get("sprtTrgtMinAge") or "").strip()
    max_age = (policy.get("sprtTrgtMaxAge") or "").strip()

    # "0~0"은 나이 정보가 없다는 뜻의 더미값이라 실제 연령 조건이 아님 (데이터 확인 결과)
    is_dummy_age = min_age == "0" and max_age == "0"

    if age_limit_yn == "Y" and (min_age or max_age) and not is_dummy_age:
        if min_age and max_age:
            parts.append(f"만 {min_age}~{max_age}세")
        elif min_age:
            parts.append(f"만 {min_age}세 이상")
        elif max_age:
            parts.append(f"만 {max_age}세 이하")

    earn_etc = (policy.get("earnEtcCn") or "").strip()
    if earn_etc:
        parts.append(earn_etc)

    add_qlfc = (policy.get("addAplyQlfcCndCn") or "").strip()
    if add_qlfc:
        parts.append(add_qlfc)

    if not parts:
        return "제한없음"

    return " | ".join(parts)


def pick_link(policy: Dict[str, Any]) -> str:
    """
    신청 또는 공식 페이지 링크를 고른다.
    우선순위: aplyUrlAddr(신청 URL) > refUrlAddr1 > refUrlAddr2
    """
    for field in ("aplyUrlAddr", "refUrlAddr1", "refUrlAddr2"):
        value = (policy.get(field) or "").strip()
        if value:
            return value

    return ""


def build_base_card(policy: Dict[str, Any]) -> Dict[str, Any]:
    """
    watsonx 요약을 제외한, 규칙 기반으로 채울 수 있는 필드만 먼저 만든다.
    """
    apply_period_type, apply_period = parse_apply_period(policy)

    return {
        "plcyNo": policy.get("plcyNo", ""),
        "title": policy.get("plcyNm", ""),
        "apply_period_type": apply_period_type,
        "apply_period": apply_period,
        "target": build_target(policy),
        "support_summary": None,  # watsonx가 채움
        "link": pick_link(policy),
    }


# ---------------------------------------------------------------------------
# watsonx 지원내용 요약 (금액 위주)
# ---------------------------------------------------------------------------

DEFAULT_LLM_INPUT_FIELDS = [
    "plcyNo",
    "plcyNm",
    "plcySprtCn",
    "plcyExplnCn",
    "sprtSclCnt",
    "earnMinAmt",
    "earnMaxAmt",
]


class WatsonxPolicySummaryGenerator:
    def __init__(
        self,
        model_id: Optional[str] = None,
        input_fields: Optional[List[str]] = None,
        max_tokens: int = 300,
        temperature: float = 0.0,
    ):
        load_dotenv()

        self.api_key = os.getenv("WATSONX_API_KEY")
        self.url = os.getenv("WATSONX_URL")
        self.project_id = os.getenv("WATSONX_PROJECT_ID")
        self.model_id = model_id or os.getenv("WATSONX_MODEL_ID")

        if not self.api_key or not self.url or not self.project_id or not self.model_id:
            raise ValueError(
                ".env에 WATSONX_API_KEY, WATSONX_URL, "
                "WATSONX_PROJECT_ID, WATSONX_MODEL_ID를 설정하세요."
            )

        self.input_fields = input_fields or DEFAULT_LLM_INPUT_FIELDS

        self.model = ModelInference(
            model_id=self.model_id,
            credentials={
                "apikey": self.api_key,
                "url": self.url,
            },
            project_id=self.project_id,
            params={
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )

    def pick_policy_fields(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: policy.get(key)
            for key in self.input_fields
            if policy.get(key) not in [None, ""]
        }

    def build_prompt(self, policy_input: Dict[str, Any]) -> str:
        return f"""
너는 청년정책 정보를 요약하는 도우미다.

목표:
- 정책의 "지원내용"을 사용자가 한눈에 볼 수 있도록 1~2문장으로 요약한다.
- 금액, 한도, 지원 횟수처럼 숫자로 표현되는 정보를 최우선으로 포함한다.

중요 규칙:
- 반드시 입력된 정책 정보에 근거해서만 작성한다.
- 입력 정보에 없는 금액, 조건, 혜택을 추측해서 만들지 마라.
- 지원 금액/한도/횟수 정보가 있으면 반드시 요약 맨 앞쪽에 배치한다.
- 금액 정보가 여러 개 언급된 경우(예: 월별 지원금, 회당 지원금, 기간별 지원금 등), 그중 신청자가 최종적으로 받을 수 있는 총 금액 또는 최대 지원 한도금액을 가장 먼저, 가장 강조되게 언급한다.
- 총 금액/최대 한도가 명시되어 있다면 "최대 OOO원" 형태로 요약의 맨 앞 구절에 배치하고, 월별/회당 금액 등 세부 내역은 그 뒤에 이어서 설명한다.
- 총 금액이나 최대 한도가 따로 명시되어 있지 않고 회당/월별 금액만 있다면, 있는 금액 정보를 그대로 맨 앞에 배치한다.
- 지원 금액 정보가 전혀 없는 정책(예: 상담, 교육, 멘토링형 정책)은 실제 제공되는 서비스 내용을 금액 대신 구체적으로 요약한다.
- 불확실한 내용은 일반화하지 말고 제외한다.
- 출력은 반드시 JSON 객체 하나만 작성한다. 설명, 마크다운, 코드블록은 절대 출력하지 마라.

출력 JSON 형식:
{{
  "plcyNo": "",
  "support_summary": ""
}}

작성 기준:
- plcyNo: 입력 정책의 plcyNo 사용
- support_summary: 최대 2문장. 금액/한도/횟수 등 숫자 정보 위주로 간결하게 작성. 총 금액/최대 한도가 있으면 반드시 맨 앞에 배치.

작성 예시:
입력 지원내용: "최대 40만원 실비 지원(중개보수, 이사비) ※ 생애 1회"
출력 support_summary 예: "중개보수·이사비 실비 최대 40만원 지원(생애 1회)."

입력 지원내용: "월 20만원씩 최대 12개월 지원(총 240만원 한도)"
출력 support_summary 예: "최대 240만원 한도로 월 20만원씩 최대 12개월 지원."

입력 지원내용: "○ 맞춤형 1:1 상담 제공 · 진로 설계 · 경력 전환 ..."
출력 support_summary 예: "진로 설계, 경력 전환 등 맞춤형 1:1 상담을 1회당 90분씩 제공."

정책 정보:
{json.dumps(policy_input, ensure_ascii=False, indent=2)}
""".strip()

    @staticmethod
    def extract_json_object(text: str) -> Dict[str, Any]:
        text = text.strip()
        text = re.sub(r"```json|```", "", text).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError(f"JSON 객체를 찾지 못했습니다.\nRAW:\n{text}")

        return json.loads(match.group(0))

    def call_watsonx(self, prompt: str) -> str:
        response = self.model.chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "너는 청년정책 지원내용을 금액 위주로 요약하는 도우미다. "
                        "반드시 JSON 객체 하나만 출력한다."
                    )
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

        return response["choices"][0]["message"]["content"]

    def summarize_one(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        policy_input = self.pick_policy_fields(policy)
        prompt = self.build_prompt(policy_input)
        response_text = self.call_watsonx(prompt)
        result = self.extract_json_object(response_text)

        result["plcyNo"] = result.get("plcyNo") or policy.get("plcyNo", "")

        return result

    def create_policy_cards(
        self,
        policies: List[Dict[str, Any]],
        sleep_sec: float = 0.0,
        verbose: bool = True,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        규칙 기반 필드(build_base_card) + watsonx 요약(support_summary)을 합쳐서
        정책 카드 리스트를 만든다.
        """
        results = []
        errors = []

        for idx, policy in enumerate(policies, start=1):
            plcy_no = policy.get("plcyNo", "")
            policy_name = policy.get("plcyNm", "")

            try:
                if verbose:
                    print(f"[{idx}/{len(policies)}] 생성 중: {policy_name}")

                card = build_base_card(policy)
                summary_result = self.summarize_one(policy)
                card["support_summary"] = summary_result.get("support_summary", "")

                results.append(card)

            except Exception as e:
                errors.append(
                    {
                        "index": idx,
                        "plcyNo": plcy_no,
                        "policy_name": policy_name,
                        "error": str(e),
                    }
                )

                if verbose:
                    print(f"  실패: {policy_name} / {e}")

            if sleep_sec > 0:
                time.sleep(sleep_sec)

        return results, errors


# ---------------------------------------------------------------------------
# 공용 유틸
# ---------------------------------------------------------------------------

def load_policies(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if "result" in data and "youthPolicyList" in data["result"]:
            return data["result"]["youthPolicyList"]
        if "youthPolicyList" in data:
            return data["youthPolicyList"]

    raise ValueError("지원하지 않는 JSON 구조입니다.")


def save_json(path: str, data: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
