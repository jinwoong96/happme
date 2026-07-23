import json
import re
from collections import OrderedDict

import pymysql

from app.core.settings import settings

# 매칭된 정책 조합(policy_id 집합)이 같으면 사진이 달라도 LLM을 다시 호출하지
# 않고 이전 요약을 재사용한다. 지원대상/지원내용/신청기간/신청방법 등 요약 내용은
# 정책 자체의 정보라 사진이 바뀐다고 달라지지 않기 때문.
_SUMMARY_CACHE_MAX_SIZE = 500

# 정책설명 한 줄 요약은 "이 사진에 어떤 정책들이 같이 매칭됐는지"와 무관하게
# 정책 자체(plcyExplnCn)에서만 나오는 값이므로, 조합이 아니라 policy_id 단위로
# 캐시한다. 전체 정책 수(약 2,869건, common_policies.json 기준)가 유한하므로
# 서비스가 운영되면서 점점 캐시가 채워지고, 이후엔 거의 LLM 재호출 없이 재사용된다.
_ONE_LINER_CACHE_MAX_SIZE = 3000
_ONE_LINER_MAX_CHARS = 40


class LlmService:
    """
    watsonx.ai 기반 정책 설명 생성 서비스.
    API 클라이언트를 들고 있으므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    """

    def __init__(self):
        self._summary_cache: "OrderedDict[tuple, str]" = OrderedDict()
        self._one_liner_cache: "OrderedDict[int, str]" = OrderedDict()

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
        """OCR로 뽑은 공고문 텍스트와 매칭된 정책 후보들로 요약 요청 프롬프트를 만든다."""
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

    # ---------- 정책 조합 요약 DB 백업 (image_analyze_summary_cache 테이블) ----------
    # 메모리 캐시(_summary_cache) 미스일 때만 조회한다. 서버 재시작으로 메모리가
    # 비어도, 같은 policy_id 조합이 예전에 요약된 적 있으면 LLM을 다시 안 부른다.

    @staticmethod
    def _db_get_combo_summary(combo_key: str) -> str | None:
        """정책 조합(combo_key)에 대한 이전 요약을 DB 캐시에서 찾는다. 없으면 None."""
        conn = pymysql.connect(
            host=settings.db_host, port=settings.db_port, user=settings.db_user,
            password=settings.db_password, db=settings.db_name, charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT summary_text FROM image_analyze_summary_cache WHERE combo_key = %s",
                    (combo_key,),
                )
                row = cursor.fetchone()
                return row["summary_text"] if row else None
        except Exception as e:
            print(f"[LlmService] 조합 요약 DB 캐시 조회 오류: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def _db_set_combo_summary(combo_key: str, summary_text: str) -> None:
        """정책 조합(combo_key)에 대한 요약을 DB 캐시에 저장(이미 있으면 갱신)한다."""
        conn = pymysql.connect(
            host=settings.db_host, port=settings.db_port, user=settings.db_user,
            password=settings.db_password, db=settings.db_name, charset="utf8mb4",
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO image_analyze_summary_cache (combo_key, summary_text)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                        summary_text = VALUES(summary_text),
                        last_used_at = CURRENT_TIMESTAMP
                    """,
                    (combo_key, summary_text),
                )
            conn.commit()
        except Exception as e:
            print(f"[LlmService] 조합 요약 DB 캐시 저장 오류: {e}")
        finally:
            conn.close()

    def summarize_svc(self, query_text: str, matches: list[dict]) -> str | None:
        """매칭된 정책들을 하나의 설명글로 요약한다. 같은 정책 조합이면 메모리 -> DB
        캐시 순으로 먼저 확인해 재사용하고, 캐시에 없을 때만 실제로 LLM을 호출한다."""
        if not self.enabled or not matches:
            return None

        cache_key = self._cache_key(matches)
        combo_key = ",".join(str(pid) for pid in cache_key) if cache_key else None

        if cache_key and cache_key in self._summary_cache:
            self._summary_cache.move_to_end(cache_key)
            print(f"[llm-cache] 메모리 hit {cache_key} - LLM 재호출 없이 이전 요약 재사용")
            return self._summary_cache[cache_key]

        if combo_key:
            db_summary = self._db_get_combo_summary(combo_key)
            if db_summary:
                print(f"[llm-cache] DB hit {cache_key} - LLM 재호출 없이 이전 요약 재사용, 메모리에 적재")
                self._summary_cache[cache_key] = db_summary
                self._summary_cache.move_to_end(cache_key)
                if len(self._summary_cache) > _SUMMARY_CACHE_MAX_SIZE:
                    self._summary_cache.popitem(last=False)
                return db_summary

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
            if combo_key:
                self._db_set_combo_summary(combo_key, summary)

        return summary

    @staticmethod
    def _fallback_one_liner(text: str) -> str:
        """LLM 호출/파싱에 실패했을 때 plcyExplnCn 원문 앞부분으로 대체."""
        cleaned = re.sub(r"\s+", " ", (text or "").strip())
        if not cleaned:
            return ""
        if len(cleaned) <= _ONE_LINER_MAX_CHARS:
            return cleaned
        return cleaned[:_ONE_LINER_MAX_CHARS].rstrip() + "..."

    @staticmethod
    def _build_one_liner_prompt(policies: list[dict]) -> str:
        """정책 여러 개를 한 번에 한 줄 요약하도록 요청하는 프롬프트를 만든다 (JSON 배열 응답 형식 지정)."""
        policies_text = ""
        for p in policies:
            policies_text += f'\n{{"policy_id": {p["policy_id"]}, "plcyNm": "{p["plcyNm"]}", "plcyExplnCn": "{p["plcyExplnCn"]}"}}'
        return f"""아래는 청년 정책 {len(policies)}개의 policy_id와 정책설명(plcyExplnCn) 원문입니다.
각 정책마다 정책설명을 {_ONE_LINER_MAX_CHARS}자 이내의 한 문장으로 핵심만 요약해주세요.
반드시 아래 JSON 배열 형식으로만 응답하고, 그 외 설명이나 마크다운은 절대 포함하지 마세요.

[{{"policy_id": 123, "summary": "한 줄 요약"}}, ...]

정책 목록:
{policies_text}
"""

    # ---------- 정책 한줄요약 DB 백업 (ai_policy_one_liner_cache 테이블) ----------
    # policy_id 단위라 매칭 조합/이미지와 무관하게 재사용된다.

    @staticmethod
    def _db_get_one_liner(policy_id: int) -> str | None:
        """정책 한 개의 한 줄 요약을 DB 캐시에서 찾는다. 없으면 None."""
        conn = pymysql.connect(
            host=settings.db_host, port=settings.db_port, user=settings.db_user,
            password=settings.db_password, db=settings.db_name, charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT one_liner FROM ai_policy_one_liner_cache WHERE policy_id = %s",
                    (policy_id,),
                )
                row = cursor.fetchone()
                return row["one_liner"] if row else None
        except Exception as e:
            print(f"[LlmService] 한줄요약 DB 캐시 조회 오류: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def _db_set_one_liner(policy_id: int, one_liner: str) -> None:
        """정책 한 개의 한 줄 요약을 DB 캐시에 저장(이미 있으면 갱신)한다."""
        conn = pymysql.connect(
            host=settings.db_host, port=settings.db_port, user=settings.db_user,
            password=settings.db_password, db=settings.db_name, charset="utf8mb4",
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ai_policy_one_liner_cache (policy_id, one_liner)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE one_liner = VALUES(one_liner)
                    """,
                    (policy_id, one_liner),
                )
            conn.commit()
        except Exception as e:
            print(f"[LlmService] 한줄요약 DB 캐시 저장 오류: {e}")
        finally:
            conn.close()

    def summarize_one_liners_svc(self, matches: list[dict]) -> dict[int, str]:
        """
        각 match(match['policy_raw']에 policy_id/plcyNm/plcyExplnCn 포함)에 대해
        정책설명 한 줄 요약을 policy_id -> summary 형태로 반환한다.
        policy_id 단위로 캐시하므로, 이미 요약된 정책은 다른 사진/다른 매칭 조합에서도
        재사용되고 LLM은 캐시에 없는 정책만 모아 한 번에 호출한다.
        """
        result: dict[int, str] = {}
        uncached: list[dict] = []

        for m in matches:
            policy_id = m.get("policy_id")
            raw = m.get("policy_raw", {})
            explain_text = raw.get("plcyExplnCn") or ""

            if policy_id is None:
                continue
            if policy_id in self._one_liner_cache:
                self._one_liner_cache.move_to_end(policy_id)
                result[policy_id] = self._one_liner_cache[policy_id]
                continue

            db_one_liner = self._db_get_one_liner(policy_id)
            if db_one_liner:
                self._one_liner_cache[policy_id] = db_one_liner
                self._one_liner_cache.move_to_end(policy_id)
                if len(self._one_liner_cache) > _ONE_LINER_CACHE_MAX_SIZE:
                    self._one_liner_cache.popitem(last=False)
                result[policy_id] = db_one_liner
                continue

            if not explain_text.strip():
                result[policy_id] = ""
                continue

            uncached.append({
                "policy_id": policy_id,
                "plcyNm": raw.get("plcyNm", ""),
                "plcyExplnCn": explain_text,
            })

        if not uncached:
            return result

        fallback_map = {p["policy_id"]: self._fallback_one_liner(p["plcyExplnCn"]) for p in uncached}

        if not self.enabled:
            result.update(fallback_map)
            return result

        prompt = self._build_one_liner_prompt(uncached)
        messages = [
            {"role": "system", "content": "당신은 청년 정책 설명을 짧고 이해하기 쉬운 한 문장으로 요약해주는 도우미입니다. JSON으로만 응답하세요."},
            {"role": "user", "content": prompt},
        ]
        params = {"temperature": 0, "max_tokens": 800}

        try:
            response = self.model.chat(messages=messages, params=params)
            content = response["choices"][0]["message"]["content"]
            # 모델이 ```json ... ``` 코드블록으로 감싸는 경우 제거
            content = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
            parsed = json.loads(content)
            new_summaries = {
                int(item["policy_id"]): str(item.get("summary", "")).strip()
                for item in parsed
                if "policy_id" in item
            }
        except Exception as e:
            print(f"[LlmService] 한 줄 요약 생성/파싱 실패, fallback 사용: {e}")
            new_summaries = {}

        for p in uncached:
            pid = p["policy_id"]
            summary = new_summaries.get(pid) or fallback_map[pid]
            self._one_liner_cache[pid] = summary
            self._one_liner_cache.move_to_end(pid)
            result[pid] = summary
            self._db_set_one_liner(pid, summary)

        while len(self._one_liner_cache) > _ONE_LINER_CACHE_MAX_SIZE:
            self._one_liner_cache.popitem(last=False)

        return result