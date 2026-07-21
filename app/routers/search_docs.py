from fastapi import APIRouter, BackgroundTasks, Request

from app.services.recommendation import search_docs_builder

router = APIRouter(prefix="/search-docs", tags=["SearchDocs"])


# DB에 새로 추가된 정책만 골라 검색문서/임베딩을 만들어 운영 파일에 이어붙인다. LLM 호출이 정책
# 수만큼 걸릴 수 있어 백그라운드로 실행하고, 바로 상태만 응답한다.
@router.post("/rebuild")
async def rebuild_search_docs(request: Request, background_tasks: BackgroundTasks):
    if search_docs_builder.get_status()["running"]:
        return {"status": "already_running"}

    similarity_service = request.app.state.policy_similarity_service
    new_policies = search_docs_builder.get_new_policies(similarity_service.known_plcynos())

    if not new_policies:
        return {"status": "up_to_date", "new_count": 0}

    background_tasks.add_task(search_docs_builder.run_rebuild, similarity_service, new_policies)
    return {"status": "started", "new_count": len(new_policies)}


@router.get("/rebuild/status")
async def rebuild_status():
    return search_docs_builder.get_status()
