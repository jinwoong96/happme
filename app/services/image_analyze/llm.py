from collections import OrderedDict

from app.core.settings import settings

# 매칭된 정책 조합(policy_id 집합)이 같으면 사진이 달라도 LLM을 다시 호출하지
# 않고 이전 요약을 재사용한다. 지원대상/지원내용/신청기간/신청방법 등 요약 내용은
# 정책 자체의 정보라 사진이 바뀐다고 달라지지 않기 때문.
_SUMMARY_CACHE_MAX_SIZE = 500


class LlmService:
    """
    watsonx.ai 기반 정책 설명 생성 서비스.
    API 클라이언트를 들고 있으므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    """

    def __init__(self):
        self._summary_cache: "OrderedDict[tuple, str]" = OrderedDict()

        self.enabled = bool(settings.enable_llm_summary) and bool(settings.watsonx_api_key) and bool(settings.watsonx_project_id)
        if not self.enabled:
            print("[LlmService] watsonx 설정이 없어 LLM 요약은 비활성화됩니다 (extracted_text/matches만 반환)")
            return

        from ibm_watsonx_ai import Credentials, APIClient
        from ibm_watsonx_ai.foundation_models import ModelInference

        print("[LlmService] watsonx.ai 연결 중...")
        credentials = Credentials(url=settings.watsonx_url, api_key=settings.watsonx_api_key)
        api_client = APIClient(credentials, project_id=settings.watsonx_project_id)
        self.model = ModelInference(api_client=api_client, model_id=settings.watsonx_model_id)
        print("[LlmService] 준비 완료")

    @staticmethod
    def _cache_key(matches: list[dict]) -> tuple:
        """매칭된 정책 id 조합을 정렬해서 캐시 키로 사용 (순서 차이는 무시)."""
        return tuple(sorted(m["policy_id"] for m in matches if m.get("policy_id") is not None))

    @staticmethod
    def _build_prompt(query_text: str, matches: list[dict]) -> str:
        policies_text = ""
        for i, m in enumerate(matches, 1):
            p = m["policy_raw"]
            policies_text += f"""
[정책 {i}] {p.get('plcyNm', '')}
- 지원 대상 연령: {p.get('sprtTrgtMinAge', '')}세 ~ {p.get('sprtTrgtMaxAge', '')}세
- 지원 내용: {p.get('plcySprtCn', '')}
- 신청 기간: {p.get('aplyYmd', '') or p.get('bizPrdEtcCn', '')}
- 신청 방법: {p.get('plcyAplyMthdCn', '')}
"""
        return f"""다음은 사용자가 업로드한 정책 공고문 이미지에서 추출된 텍스트입니다:
"{query_text}"

아래는 이와 유사한 정책 후보 {len(matches)}개입니다. 사용자에게 친절하게 정리해서 설명해주세요.
각 정책마다 지원대상, 지원내용, 신청기간, 신청방법을 명확히 정리하고,
가장 적합해 보이는 정책을 하나 추천해주세요.
{policies_text}
"""

    def summarize_svc(self, query_text: str, matches: list[dict]) -> str | None:
        if not self.enabled or not matches:
            return None

        cache_key = self._cache_key(matches)
        if cache_key and cache_key in self._summary_cache:
            self._summary_cache.move_to_end(cache_key)
            print(f"[llm-cache] hit {cache_key} - LLM 재호출 없이 이전 요약 재사용")
            return self._summary_cache[cache_key]

        prompt = self._build_prompt(query_text, matches)
        messages = [
            {"role": "system", "content": "당신은 청년 정책을 이해하기 쉽게 설명해주는 도우미입니다."},
            {"role": "user", "content": prompt},
        ]
        # temperature=0 -> 결정적(빠른) 디코딩, max_tokens로 불필요하게 길게
        # 생성되는 것을 막아 응답 시간을 줄인다. (공고문 요약 기능의 설정과 같은 취지)
        params = {"temperature": 0, "max_tokens": 500}
        try:
            response = self.model.chat(messages=messages, params=params)
            summary = response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LlmService] 요약 생성 실패: {e}")
            return None

        if cache_key:
            self._summary_cache[cache_key] = summary
            self._summary_cache.move_to_end(cache_key)
            if len(self._summary_cache) > _SUMMARY_CACHE_MAX_SIZE:
                self._summary_cache.popitem(last=False)

        return summary