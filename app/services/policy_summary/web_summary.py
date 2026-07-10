import re
import asyncio

from app.services.policy_summary.pdf_summary import PdfSummaryService


class WebSummaryService:
    """
    텍스트 직접입력 / URL 크롤링 매칭 + 질문답변.
    PdfSummaryService가 들고 있는 임베딩 모델, LLM, 정책 DB를 그대로 재사용합니다.
    """

    def __init__(self, pdf_summary_service: PdfSummaryService):
        self.pdf = pdf_summary_service

    # ---------- 텍스트 매칭 ----------

    def match_text_svc(self, text: str, top_k_keyword=5, top_k_embed=5,
                        raw_threshold_high=0.88, raw_threshold_low=0.80) -> dict:
        if not text or len(text.strip()) < 2:
            return {"matched_policy": None, "method": "텍스트부족"}

        text_clean = text.replace(" ", "")

        # 1) 직접매칭
        direct_matches = [
            name for name in self.pdf.policy_names
            if name.replace(" ", "") in text_clean and len(name.replace(" ", "")) > 10
        ]
        if len(direct_matches) == 1:
            return {"matched_policy": direct_matches[0], "method": "직접매칭"}
        if len(direct_matches) > 1:
            return {"matched_policy": None, "method": "후보다수", "candidates": direct_matches[:5]}

        # 2) 키워드 점수 매칭
        keyword_list = text.split()
        scored = []
        for name, policy_text in zip(self.pdf.policy_names, self.pdf.policy_texts):
            name_score = sum(2 for kw in keyword_list if kw in name)
            text_score = sum(1 for kw in keyword_list if kw in policy_text)
            score = name_score + text_score
            if score > 0:
                scored.append((score, name))
        scored.sort(reverse=True)

        # 3) 임베딩 매칭
        keyword_text = ""
        for kw in ["사업명", "사업개요", "지원내용", "지원대상", "모집내용", "공고명"]:
            idx = text.find(kw)
            if idx != -1:
                keyword_text += text[idx:idx + 100] + " "
        combined_text = text[:300] + " " + keyword_text

        embedding = self.pdf.embed_model.encode([f"query: {combined_text}"], show_progress_bar=False)
        similarities = self.pdf._cosine_sim(embedding)
        raw_best_score = float(similarities.max())

        top_indices = similarities.argsort()[::-1][:top_k_embed]
        top_names = [self.pdf.policy_names[i] for i in top_indices]

        if raw_best_score < raw_threshold_low and not scored:
            return {"matched_policy": "해당 없음", "method": "매칭불가"}

        keyword_names = [name for _, name in scored[:top_k_keyword]]
        if raw_best_score < raw_threshold_low:
            combined_results = keyword_names[:5]
        else:
            combined_results = list(dict.fromkeys(keyword_names + top_names))[:5]

        if raw_best_score >= raw_threshold_high:
            return {"matched_policy": top_names[0], "method": "임베딩매칭"}

        if len(combined_results) == 1:
            return {"matched_policy": combined_results[0], "method": "키워드+임베딩"}

        if combined_results:
            llm_result = self.pdf.verify_with_llm_svc(text, combined_results)
            is_none = llm_result == "없음" or llm_result not in self.pdf.policy_names
            if not is_none:
                return {"matched_policy": llm_result, "method": "키워드+LLM"}
            return {"matched_policy": None, "method": "후보다수", "candidates": combined_results}

        return {"matched_policy": "해당 없음", "method": "매칭불가"}  

    # ---------- URL 매칭 (Playwright) ----------

    @staticmethod
    def extract_policy_no_from_url(url: str):
        m = re.search(r"ythPlcyDetail/(\d+)", url)
        return m.group(1) if m else None

    def get_policy_by_no_svc(self, plcy_no: str):
        for item in self.pdf.policy_by_name.values():
            if item.get("plcyNo", "").strip() == plcy_no:
                return item
        return None

    async def _extract_url_features_async(self, url: str):
        from playwright.async_api import async_playwright

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ),
                    extra_http_headers={
                        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    },
                )
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                except Exception:
                    await browser.close()
                    return "", "", "", "", False

                await page.wait_for_timeout(1000)
                title = await page.title()
                text = " ".join((await page.inner_text("body")).split())

                if len(text) < 500:
                    try:
                        await asyncio.wait_for(
                            page.evaluate("""
                                async () => {
                                    const distance = 800, delay = 300;
                                    while (document.scrollingElement.scrollTop + window.innerHeight
                                           < document.scrollingElement.scrollHeight) {
                                        document.scrollingElement.scrollBy(0, distance);
                                        await new Promise(r => setTimeout(r, delay));
                                    }
                                }
                            """),
                            timeout=3,
                        )
                    except asyncio.TimeoutError:
                        pass
                    await page.wait_for_timeout(500)
                    text = " ".join((await page.inner_text("body")).split())

                await browser.close()
                if len(text) < 200:
                    return "", "", "", "", False

            if "400" in title or "403" in title or "Bad Request" in title:
                return "", "", "", "", True

            institution = ""
            for pattern in [
                r'([가-힣]+(?:시|군|구|청|원|공단|재단|센터|연금|공사|위원회|부|처|청))\s*(?:공고|장|에서)',
                r'([가-힣]{2,10}(?:공단|공사|연금|위원회))',
            ]:
                m = re.search(pattern, text[:500])
                if m:
                    institution = m.group(1)
                    break

            keyword_text = ""
            for kw in ["사업명", "사업개요", "지원내용", "지원대상", "모집내용", "공고명"]:
                idx = text.find(kw)
                if idx != -1:
                    keyword_text += text[idx:idx + 100] + " "

            combined_text = (title + " " + text[:300] + " " + keyword_text).strip()
            return combined_text, text, institution, title, False
        except Exception as e:
            print(f"[WebSummaryService] URL 추출 오류: {e}")
            return "", "", "", "", False

    def match_url_svc(self, url: str, raw_threshold_high=0.88, raw_threshold_low=0.875, top_k=10) -> dict:
        plcy_no = self.extract_policy_no_from_url(url)
        if plcy_no:
            detail = self.get_policy_by_no_svc(plcy_no)
            if detail:
                return {"matched_policy": detail.get("plcyNm", ""), "method": "정책번호매칭",
                         "policy_detail": detail, "blocked": False}

        combined_text, full_text, institution, title, blocked = asyncio.run(
            self._extract_url_features_async(url)
        )
        if blocked:
            return {"matched_policy": None, "method": "크롤링차단", "policy_detail": None, "blocked": True}
        if not combined_text:
            return {"matched_policy": None, "method": "텍스트추출실패", "policy_detail": None, "blocked": False}

        text_clean, title_clean = full_text.replace(" ", ""), title.replace(" ", "")
        for name in self.pdf.policy_names:
            nc = name.replace(" ", "")
            if nc == title_clean or (nc in title_clean and len(nc) > 10) or (nc in text_clean and len(nc) > 10):
                return {"matched_policy": name, "method": "직접매칭", "policy_detail": None, "blocked": False}

        embedding = self.pdf.embed_model.encode([f"query: {combined_text}"], show_progress_bar=False)
        similarities = self.pdf._cosine_sim(embedding)
        raw_best_score = float(similarities.max())

        s_min, s_max = similarities.min(), similarities.max()
        normalized = (similarities - s_min) / (s_max - s_min + 1e-8)
        if institution:
            for i, inst in enumerate(self.pdf.policy_institutions):
                if inst and institution not in inst and institution not in self.pdf.policy_texts[i]:
                    normalized[i] *= 0.85

        top_indices = normalized.argsort()[::-1][:top_k]
        top_names = [self.pdf.policy_names[i] for i in top_indices]
        best_match = top_names[0]

        if raw_best_score < raw_threshold_low:
            return {
                "matched_policy": "해당 없음",
                "method": "매칭불가",
                "candidates": top_names[:3],  # ← 추가
                "policy_detail": None,
                "blocked": False
            }
        return {
            "matched_policy": best_match,
            "method": "임베딩매칭",
            "candidates": top_names[:2],  # ← 추가
            "policy_detail": None,
            "blocked": False
        }

    # ---------- 질문답변 ----------

    @staticmethod
    def _preprocess_question(question: str) -> str:
        if any(kw in question for kw in ["금액", "얼마", "돈", "비용", "지원금"]):
            return f"{question} (지원내용, 지원방식, 지원품목 중심으로 답변)"
        if any(kw in question for kw in ["어디", "장소", "곳", "센터"]):
            return f"{question} (신청방법, 신청URL 중심으로 답변)"
        if any(kw in question for kw in ["자격", "조건", "대상", "누가", "몇 살"]):
            return f"{question} (지원대상, 연령조건 중심으로 답변)"
        if any(kw in question for kw in ["언제", "기간", "마감", "기한"]):
            return f"{question} (신청기간, 사업기간 중심으로 답변)"
        return question

    def answer_question_svc(self, question: str, policy_detail: dict) -> str | None:
        if not policy_detail:
            return None

        institution = policy_detail.get("sprvsnInstCdNm", "").strip() or policy_detail.get("rgtrInstCdNm", "").strip()
        fields = {
            "정책명": policy_detail.get("plcyNm", "").strip(),
            "정책설명": policy_detail.get("plcyExplnCn", "").strip(),
            "지원내용": policy_detail.get("plcySprtCn", "").strip(),
            "지원대상": policy_detail.get("ptcpPrpTrgtCn", "").strip() or policy_detail.get("earnEtcCn", "").strip(),
            "신청방법": policy_detail.get("plcyAplyMthdCn", "").strip(),
            "제출서류": policy_detail.get("sbmsnDcmntCn", "").strip(),
            "신청URL": policy_detail.get("aplyUrlAddr", "").strip(),
            "신청기간": policy_detail.get("aplyYmd", "").strip(),
            "담당기관": institution,
            "기타사항": policy_detail.get("etcMttrCn", "").strip(),
        }
        info_text = "\n".join(f"{k}: {v}" for k, v in fields.items() if v)
        processed_question = self._preprocess_question(question)

        prompt = f"""당신은 청년 정책 전문 상담사입니다.

[정책 정보]
{info_text}

[사용자 질문]
{processed_question}

위 정책 정보를 읽고 질문에 답변해주세요.
정책 정보에 있는 내용으로만 답변하고, 없는 내용은 만들지 마세요.
정말 관련 정보가 없을 때만 "담당기관({institution})에 문의해주세요"라고 하세요.
1~3문장으로 간결하게 답변하고, 지시문이나 예시 문구는 출력하지 마세요.

답변:"""
        try:
            return self.pdf.llm_model.generate_text(prompt=prompt).strip()
        except Exception as e:
            print(f"[WebSummaryService] 답변 생성 오류: {e}")
            return None