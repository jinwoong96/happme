import json
import os

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.settings import settings


class SearchService:
    """
    Sentence-BERT 기반 정책 임베딩 검색 서비스.
    무거운 모델/임베딩을 들고 있으므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    """

    def __init__(self):
        print("[SearchService] 정책 데이터 로드 중...")
        with open(settings.policy_json_path, encoding="utf-8") as f:
            self.policies = json.load(f)
        print(f"[SearchService] 총 {len(self.policies)}개 정책 로드")

        print(f"[SearchService] 임베딩 모델 로드 중... ({settings.embedding_model_name})")
        self.embedding_model = SentenceTransformer(settings.embedding_model_name)

        if os.path.exists(settings.policy_embedding_cache):
            print("[SearchService] 캐시된 임베딩 로드")
            self.policy_embeddings = np.load(settings.policy_embedding_cache)
            if len(self.policy_embeddings) != len(self.policies):
                print("[SearchService] 캐시 크기 불일치 -> 재계산")
                self._build_policy_embeddings()
        else:
            self._build_policy_embeddings()

        print("[SearchService] 준비 완료")

    @staticmethod
    def _make_search_text(policy: dict) -> str:
        parts = [policy.get("plcyNm", ""), policy.get("plcyExplnCn", ""), policy.get("plcySprtCn", "")]
        return " ".join(x for x in parts if x)

    def _build_policy_embeddings(self):
        texts = [self._make_search_text(p) for p in self.policies]
        self.policy_embeddings = self.embedding_model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        np.save(settings.policy_embedding_cache, self.policy_embeddings)

    def search_policy_svc(self, query_text: str, top_k: int = None) -> list[dict]:
        if not query_text.strip():
            return []
        top_k = settings.top_k if top_k is None else top_k

        query_emb = self.embedding_model.encode([query_text], convert_to_numpy=True)
        sims = np.dot(self.policy_embeddings, query_emb.T).flatten() / (
            np.linalg.norm(self.policy_embeddings, axis=1) * np.linalg.norm(query_emb) + 1e-8
        )
        top_idx = sims.argsort()[::-1][:top_k]

        return [
            {
                "plcyNo": self.policies[i].get("plcyNo"),
                "plcyNm": self.policies[i].get("plcyNm"),
                "score": float(sims[i]),
                "policy_raw": self.policies[i],
            }
            for i in top_idx
        ]