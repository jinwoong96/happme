import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.settings import settings


class PolicySimilarityService:
    """
    정책 검색문서(policy_search_docs.json)와 사전 계산된 임베딩을 이용한 유사도 계산 서비스.
    무거운 임베딩 모델/임베딩 배열은 __init__에서 한 번만 로드해 재사용합니다.
    """

    def __init__(self):
        self.model = SentenceTransformer(settings.similarity_model_name)

        self.embeddings = np.load(settings.similarity_embeddings_path)
        self.policy_docs = self._load_json(settings.similarity_docs_path)

        self._policy_index_by_id = {
            str(doc.get("policy_id")): idx for idx, doc in enumerate(self.policy_docs)
        }

    @staticmethod
    def _load_json(path: str):
        with open(Path(path), encoding="utf-8") as f:
            return json.load(f)

    def _encode_query(self, query_text: str) -> np.ndarray:
        return self.model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)[0]

    def search(self, query_text: str, candidate_policies: list[dict], top_k: int = 5) -> list[dict]:
        """
        query_text: 사용자 채팅
        candidate_policies: rule engine을 통과한 정책 dict 목록 (policy_id == plcyNo)
        반환: 유사도 상위 top_k개의 {policy_id, policy_name, policy_summary}
              (policy_name/policy_summary는 policy_search_docs.json 기준)
        """
        candidate_ids = {str(p.get("policy_id")) for p in candidate_policies}

        candidate_indices = [
            self._policy_index_by_id[policy_id]
            for policy_id in candidate_ids
            if policy_id in self._policy_index_by_id
        ]
        if not candidate_indices:
            return []

        query_embedding = self._encode_query(query_text)
        scores = query_embedding @ self.embeddings[candidate_indices].T

        ranked_indices = [idx for idx, _ in sorted(zip(candidate_indices, scores), key=lambda x: x[1], reverse=True)]

        return [
            {
                "policy_id": self.policy_docs[idx].get("policy_id"),
                "policy_name": self.policy_docs[idx].get("policy_name"),
                "policy_summary": self.policy_docs[idx].get("summary"),
            }
            for idx in ranked_indices[:top_k]
        ]
