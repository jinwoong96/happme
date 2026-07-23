import httpx
from fastapi import HTTPException, status
from app.core.settings import settings
from app.core.request_context import get_request_id, REQUEST_ID_HEADER

class AiClient:
    """bene_ai(AI 마이크로서비스)에 HTTP로 요청을 보내는 클라이언트. 추천/일정추출/이미지분석/
    공고문 매칭/캐시 재구축 등 AI 관련 기능은 전부 이 클래스를 통해 bene_ai를 호출한다."""

    @staticmethod
    async def recommend(user_profile: dict) -> dict:
        return await AiClient._post("/recommendations/", {"user_profile": user_profile})

    @staticmethod
    async def recommend_chat(user_profile: dict, chat: str) -> list[dict]:
        return await AiClient._post("/recommendations/chat", {"user_profile": user_profile, "chat": chat})

    @staticmethod
    async def resolve_scenario(
        region_choice: str, region_text: str | None, employment_choice: str, employment_other: str | None
    ) -> dict:
        """bene_ai의 구조화 질문(Q1 지역이동/Q2 취업 변화) diff 계산 호출. DB/Watson 미사용."""
        return await AiClient._post(
            "/recommendations/resolve-scenario",
            {
                "region_choice": region_choice,
                "region_text": region_text,
                "employment_choice": employment_choice,
                "employment_other": employment_other,
            },
        )

    @staticmethod
    async def judge_income_eligibility(plcy_no: str, answers: dict) -> dict:
        """bene_ai의 소득 조건 판정(rule engine + watsonx LLM) 호출. Returns: {eligible, method, reason}"""
        return await AiClient._post("/recommendations/income-eligibility", {"plcyNo": plcy_no, "answers": answers})

    @staticmethod
    async def check_eligibility_batch(user_profile: dict, plcy_nos: list[str]) -> list[dict]:
        """bene_ai의 POST /recommendations/eligibility-batch 호출.
        Returns: [{plcyNo, result: "YES"|"NO"|None}]"""
        return await AiClient._post(
            "/recommendations/eligibility-batch", {"user_profile": user_profile, "plcyNos": plcy_nos}
        )

    @staticmethod
    async def search_similar_policies(query_text: str, top_k: int = 5) -> list[dict]:
        """bene_ai의 POST /policy-dedup/search 호출 (BAAI/bge-m3 임베딩 유사도 검색).
        Returns: [{plcyNo, policy_name, policy_summary, score}]"""
        return await AiClient._post("/policy-dedup/search", {"query_text": query_text, "top_k": top_k})

    @staticmethod
    async def summarize_policies(policies: list[dict]) -> dict:
        """bene_ai의 POST /policy-summary/summarize-policies 호출.
        이미 알고 있는 정책들(예: 즐겨찾기)의 원본 필드를 그대로 넘겨서 매칭 없이 바로 요약만 한다(1개 이상 가능).
        Returns: {results: [{policy_name, summary, fields}]}"""
        return await AiClient._post("/policy-summary/summarize-policies", {"policies": policies})

    @staticmethod
    async def recommend_policies(summaries: list[dict]) -> dict:
        """bene_ai의 POST /policy-summary/recommend 호출.
        이미 만들어진 {policy_name, summary} 목록(2개 이상)으로 비교 추천 문장만 생성한다.
        Returns: {recommendation: str|None}"""
        return await AiClient._post("/policy-summary/recommend", {"summaries": summaries})

    @staticmethod
    async def trigger_search_docs_rebuild() -> dict:
        """bene_ai의 POST /search-docs/rebuild 호출. 새로 추가된 정책만 골라 검색문서/임베딩을
        생성해 운영 파일에 이어붙이는 백그라운드 작업을 시작시킨다.
        Returns: {status: "started"|"up_to_date"|"already_running", new_count?}"""
        return await AiClient._post("/search-docs/rebuild", {})

    @staticmethod
    async def get_search_docs_rebuild_status() -> dict:
        """bene_ai의 GET /search-docs/rebuild/status 호출. Returns: {running, last_run}"""
        return await AiClient._get("/search-docs/rebuild/status")

    @staticmethod
    async def trigger_policy_summary_rebuild() -> dict:
        """bene_ai의 POST /policy-summary/rebuild 호출. DB에 summary가 비어있는 정책만 골라
        policy.summary를 채우는 백그라운드 작업을 시작시킨다.
        Returns: {status: "started"|"up_to_date"|"already_running", new_count?}"""
        return await AiClient._post("/policy-summary/rebuild", {})

    @staticmethod
    async def get_policy_summary_rebuild_status() -> dict:
        """bene_ai의 GET /policy-summary/rebuild/status 호출. Returns: {running, last_run}"""
        return await AiClient._get("/policy-summary/rebuild/status")

    @staticmethod
    async def trigger_pdf_cache_rebuild() -> dict:
        """bene_ai의 POST /policy-summary/pdf-cache/rebuild 호출. 공고문 PDF/텍스트/URL 매칭용
        정책/임베딩 캐시(PdfSummaryService)를 DB 최신 상태로 갱신하는 백그라운드 작업을 시작시킨다.
        Returns: {status: "started"|"already_running"}"""
        return await AiClient._post("/policy-summary/pdf-cache/rebuild", {})

    @staticmethod
    async def get_pdf_cache_rebuild_status() -> dict:
        """bene_ai의 GET /policy-summary/pdf-cache/rebuild/status 호출. Returns: {running, last_run}"""
        return await AiClient._get("/policy-summary/pdf-cache/rebuild/status")

    @staticmethod
    async def sync_policy_cache_upsert(policy: dict) -> dict:
        """bene_ai의 POST /policy-cache/upsert 호출. bene_ai의 PolicyLoaderService는 서버
        시작 시 DB를 한 번만 읽어 메모리에 캐싱하고 그 뒤로는 다시 안 읽으므로, 정책을
        생성/수정하거나 외부 동기화(최신화) 배치가 끝난 뒤 재시작 없이 반영하려면 이걸 호출해야
        추천/알림 매칭(recommend_chat 등)이 해당 정책을 바로 알아본다."""
        return await AiClient._post("/policy-cache/upsert", policy)

    @staticmethod
    async def sync_policy_cache_remove(policy_id: int) -> dict:
        """bene_ai의 DELETE /policy-cache/{policy_id} 호출. 정책 삭제 시 메모리 캐시에서도 제거한다."""
        return await AiClient._delete(f"/policy-cache/{policy_id}")

    @staticmethod
    async def _post(path: str, payload: dict):
        try:
            async with httpx.AsyncClient(base_url=settings.ai_server_url, timeout=30) as client:
                response = await client.post(
                    path, json=payload, headers={REQUEST_ID_HEADER: get_request_id()}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI 서버 추천 요청에 실패했습니다.")
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI 서버에 연결할 수 없습니다.")

    @staticmethod
    async def _get(path: str):
        try:
            async with httpx.AsyncClient(base_url=settings.ai_server_url, timeout=30) as client:
                response = await client.get(path, headers={REQUEST_ID_HEADER: get_request_id()})
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI 서버 요청에 실패했습니다.")
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI 서버에 연결할 수 없습니다.")

    @staticmethod
    async def _delete(path: str):
        try:
            async with httpx.AsyncClient(base_url=settings.ai_server_url, timeout=30) as client:
                response = await client.delete(path)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI 서버 요청에 실패했습니다.")
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI 서버에 연결할 수 없습니다.")

    @staticmethod
    async def analyze_image(image_bytes: bytes, filename: str, content_type: str) -> dict:
        """
        bene_ai의 POST /image-analyze/ 호출.
        Returns: {extracted_text, detected_objects, matches:[{policy_id, plcyNo, plcyNm, score}], summary_text, message}
        """
        url = f"{settings.ai_service_url}/image-analyze/"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {"file": (filename, image_bytes, content_type or "image/jpeg")}
                resp = await client.post(url, files=files, headers={REQUEST_ID_HEADER: get_request_id()})
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI 분석 서비스 호출에 실패했습니다: {e}",
            )
