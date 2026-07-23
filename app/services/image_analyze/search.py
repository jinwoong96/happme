import os

import numpy as np
import pymysql
from sentence_transformers import SentenceTransformer

from app.core.settings import settings
from app.core.s3_utils import get_s3_client, upload_file


class SearchService:
    """
    Sentence-BERT 기반 정책 임베딩 검색 서비스.
    정책 데이터는 bene_backend와 동일한 RDS MySQL의 policy 테이블에서 읽어옵니다.
    (온통청년 원본 json을 따로 들고 있지 않고, DB를 단일 소스로 사용)
    무거운 모델/임베딩을 들고 있으므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    """

    def __init__(self):
        print("[SearchService] RDS에서 정책 데이터 로드 중...")
        self.policies = self._load_policies_from_db()
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
    def _load_policies_from_db() -> list[dict]:
        """검색에 필요한 정책 필드들을 DB(policy 테이블)에서 전부 읽어온다."""
        conn = pymysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            db=settings.db_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        policy_id, plcyNo, plcyNm, plcyExplnCn, plcySprtCn,
                        sprtTrgtMinAge, sprtTrgtMaxAge, aplyYmd, bizPrdEtcCn,
                        plcyAplyMthdCn, aplyUrlAddr, refUrlAddr1, refUrlAddr2, sbmsnDcmntCn
                    FROM policy
                """)
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def _make_search_text(policy: dict) -> str:
        """정책 이름/설명/지원내용을 하나로 합쳐 임베딩용 텍스트를 만든다."""
        parts = [policy.get("plcyNm", ""), policy.get("plcyExplnCn", ""), policy.get("plcySprtCn", "")]
        return " ".join(x for x in parts if x)

    def _build_policy_embeddings(self):
        """모든 정책을 임베딩으로 변환해 로컬 캐시 파일에 저장하고, 필요하면 S3에도 올린다."""
        texts = [self._make_search_text(p) for p in self.policies]
        self.policy_embeddings = self.embedding_model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        np.save(settings.policy_embedding_cache, self.policy_embeddings)

        # DB(원본)가 더 최신이라 방금 로컬에서 다시 계산했으므로, S3에 있는 캐시도 최신으로 갱신한다.
        if settings.data_s3_bucket and settings.policy_embedding_cache_s3_key:
            client = get_s3_client(settings.data_s3_public)
            upload_file(
                settings.policy_embedding_cache, settings.data_s3_bucket,
                settings.policy_embedding_cache_s3_key, client, label="SearchService",
            )

    def search_policy_svc(self, query_text: str, top_k: int = None) -> list[dict]:
        """검색어(OCR 텍스트 등)를 임베딩해서 코사인 유사도가 가장 높은 정책 top_k개를 반환한다."""
        if not query_text.strip() or not self.policies:
            return []
        top_k = settings.top_k if top_k is None else top_k

        query_emb = self.embedding_model.encode([query_text], convert_to_numpy=True)
        sims = np.dot(self.policy_embeddings, query_emb.T).flatten() / (
            np.linalg.norm(self.policy_embeddings, axis=1) * np.linalg.norm(query_emb) + 1e-8
        )
        top_idx = sims.argsort()[::-1][:top_k]

        return [
            {
                "policy_id": self.policies[i]["policy_id"],
                "plcyNo": self.policies[i].get("plcyNo"),
                "plcyNm": self.policies[i].get("plcyNm"),
                "score": float(sims[i]),
                "policy_raw": self.policies[i],
            }
            for i in top_idx
        ]
