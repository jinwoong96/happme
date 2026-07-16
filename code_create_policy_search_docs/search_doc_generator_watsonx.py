### watsonx.ai로 정책 문서 생성 (하위 코드)

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import ModelInference


DEFAULT_LLM_INPUT_FIELDS = [
    "plcyNo",
    "plcyNm",
    "plcyKywdNm",
    "lclsfNm",
    "mclsfNm",
    "plcyExplnCn",
    "plcySprtCn",
    "earnEtcCn",
    "addAplyQlfcCndCn",
    "ptcpPrpTrgtCn",
]


class WatsonxSearchDocGenerator:
    def __init__(
        self,
        model_id: Optional[str] = None,
        input_fields: Optional[List[str]] = None,
        max_tokens: int = 1200,
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
너는 청년정책 추천 시스템의 검색용 문서를 생성하는 도우미다.

목표:
- 사용자의 짧은 채팅 문장과 정책을 잘 매칭하기 위한 검색용 JSON 문서를 만든다.
- 사용자는 보통 "취업 준비 중인데 지원금 있어?", "창업하면 받을 수 있는 거 있어?", "돈 모으고 싶어"처럼 짧게 입력한다.

중요 규칙:
- 반드시 입력된 정책 정보에 근거해서만 작성한다.
- 입력 정보에 없는 조건, 대상, 혜택을 추측해서 만들지 마라.
- 불확실하면 일반화하지 말고 제외한다.
- 출력은 반드시 JSON 객체 하나만 작성한다.
- 설명, 마크다운, 코드블록은 절대 출력하지 마라.

출력 JSON 형식:
{{
  "policy_id": "",
  "policy_name": "",
  "summary": "",
  "target": [],
  "support": [],
  "keywords": [],
  "situations": [],
  "example_queries": [],
  "search_text": ""
}}

작성 기준:
- policy_id: 입력 정책의 plcyNo 사용
- policy_name: 입력 정책의 plcyNm 사용
- summary: 정책을 1~2문장으로 요약
- target: 정책의 공식 지원 대상과 지원 자격만 명사구 배열로 작성한다.
- 정책 목적, 지원이 필요한 상황, 지원 이유는 target에 포함하지 않는다.
- 정책에서 공식 지원 대상이나 지원 자격이 명확하지 않은 경우 target은 빈 배열([])로 작성한다.
- target의 각 항목은 혼자 읽어도 의미가 완전한 독립적인 의미 단위로 작성한다.
- 하나의 조건은 여러 항목으로 나누지 않는다.

target 작성 예시:

좋은 예:
[
  "전북 내 중소기업",
  "중위소득 150% 이하",
  "거래금액 2억원 이하인 무주택 임차가구"
]

나쁜 예:
[
  "근무환경 개선 필요 기업",
  "청년 고용을 원하는 기업",
  "주거비 부담이 큰 청년"
]

- support: 정책을 통해 실제 제공되는 내용을 명사구 배열로 작성한다.
- 정책 유형에 맞게 지원금, 교육, 특강, 상담, 멘토링, 컨설팅, 바우처 등 실제 제공되는 서비스를 작성한다.
- 프로그램명, 교육명, 특강명 등은 가능한 한 원문 표현을 유지한다.
- support의 각 항목도 혼자 읽어도 의미가 완전한 독립적인 의미 단위로 작성한다.
- 지원 금액, 지원 기간, 지원 한도 등 숫자가 포함된 경우 가능한 한 포함한다.
- 교육/특강 정책은 support 항목에 "교육", "특강", "강의" 같은 제공 형태를 자연스럽게 포함한다.
- keywords: 사용자가 검색하거나 채팅에 입력할 만한 관련 키워드
- keywords는 반드시 10개 이하로 작성한다.
- keywords는 서로 의미가 다른 표현만 작성하고, 비슷한 표현을 반복하지 않는다.
- keywords에는 "신청", "문의", "절차", "안내", "정보 제공"처럼 일반적인 행정 표현을 반복해서 넣지 않는다.
- example_queries는 반드시 3개 이상 5개 이하로 작성한다.
- situations는 반드시 3개 이상 5개 이하로 작성한다.
- situations: 사용자가 처한 상태나 상황을 질문형이 아닌 짧은 서술형 문장으로 작성한다.
- situations는 정책이 필요한 상황을 작성하고, 지원 대상을 그대로 설명하지 않는다.
  예) "서울에서 이사를 준비 중이다", "중개보수가 부담된다", "이사비 지원이 필요하다"
- example_queries: 사용자가 검색창이나 채팅에 입력할 법한 질문형 또는 검색어형 문장으로 작성한다.
  예) "서울 청년 이사비 지원 있어?", "중개보수 지원받을 수 있나요?"
- search_text: policy_name, summary, target, support의 핵심 내용을 포함하여 하나의 자연스러운 문단으로 작성한다.
- 지원 대상과 지원 내용을 가능한 한 모두 포함한다.
- keywords의 핵심 표현을 자연스럽게 문장 속에 반영한다.
- keywords를 나열하거나 반복하지 않는다.

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
                        "너는 청년정책 추천 시스템의 검색용 문서를 생성하는 도우미다. "
                        "반드시 JSON 객체 하나만 출력한다. "
                        "배열 항목 수 제한을 반드시 지킨다. "
                        "반복 문구를 생성하지 않는다."
                    )
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

        return response["choices"][0]["message"]["content"]

    def create_search_doc(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        policy_input = self.pick_policy_fields(policy)
        prompt = self.build_prompt(policy_input)
        response_text = self.call_watsonx(prompt)
        search_doc = self.extract_json_object(response_text)

        # 원본 식별값 보정
        search_doc["policy_id"] = search_doc.get("policy_id") or policy.get("plcyNo", "")
        search_doc["policy_name"] = search_doc.get("policy_name") or policy.get("plcyNm", "")

        return search_doc

    def create_search_docs(
        self,
        policies: List[Dict[str, Any]],
        sleep_sec: float = 0.0,
        verbose: bool = True,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        results = []
        errors = []

        for idx, policy in enumerate(policies, start=1):
            policy_id = policy.get("plcyNo", "")
            policy_name = policy.get("plcyNm", "")

            try:
                if verbose:
                    print(f"[{idx}/{len(policies)}] 생성 중: {policy_name}")

                search_doc = self.create_search_doc(policy)
                results.append(search_doc)

            except Exception as e:
                errors.append(
                    {
                        "index": idx,
                        "policy_id": policy_id,
                        "policy_name": policy_name,
                        "error": str(e),
                    }
                )

                if verbose:
                    print(f"  실패: {policy_name} / {e}")

            if sleep_sec > 0:
                time.sleep(sleep_sec)

        return results, errors

    def create_search_docs_in_batches(
        self,
        policies: List[Dict[str, Any]],
        batch_size: int = 10,
        sleep_sec: float = 0.0,
        verbose: bool = True,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        all_results = []
        all_errors = []

        for start in range(0, len(policies), batch_size):
            batch = policies[start : start + batch_size]

            if verbose:
                print(f"\n===== Batch {start // batch_size + 1} / {((len(policies) - 1) // batch_size) + 1} =====")

            results, errors = self.create_search_docs(
                batch,
                sleep_sec=sleep_sec,
                verbose=verbose,
            )

            all_results.extend(results)
            all_errors.extend(errors)

        return all_results, all_errors


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