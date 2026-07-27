"""
로컬에서 띄운 bene_ai 서버(POST /recommendations/chat)에 다양한 상황을 실제로 던져서,
recommendation_service.py의 EVAL_CAPTURE 캡처(evaluation/collected/raw_capture.jsonl)를
채우는 스크립트. bene_backend를 거치지 않고 bene_ai를 직접 호출하므로 user_id는 실제 DB
사용자가 아니어도 된다(가짜 값으로 충분).

사전 준비
    1) bene_ai/.env에 EVAL_CAPTURE=true 추가
    2) (재시작) python main.py   # 또는 uvicorn main:app --port 8090 --reload
    3) 이 스크립트 실행: python collect_cases.py
    4) 끝나면: python build_cases_from_capture.py
"""

import httpx

BASE_URL = "http://localhost:8090"

# 카테고리를 다양하게 섞은 샘플. 필요하면 여기 리스트에 원하는 만큼 더 추가해서 돌리면 된다.
SAMPLE_CASES = [
    {
        "profile": {"user_id": 900001, "region": "서울", "district": "관악구", "employment_status": "미취업", "education": "대졸"},
        "chat": "저는 취업준비 중인 25세 대학생이고, 생활비 지원을 받을 수 있는 정책을 찾고 있어요.",
    },
    {
        "profile": {"user_id": 900002, "region": "경기", "district": "수원시", "employment_status": "재직", "marital_status": "미혼"},
        "chat": "이번에 취업하면서 독립하려는데, 월세 부담이 커서 지원받을 수 있는 정책이 있을까요?",
    },
    {
        "profile": {"user_id": 900003, "region": "부산", "district": "해운대구", "employment_status": "재직"},
        "chat": "학자금 대출 이자가 부담돼요.",
    },
    {
        "profile": {"user_id": 900004, "region": "서울", "district": "강남구", "employment_status": "재직"},
        "chat": "마음이 많이 힘든데 상담받을 수 있는 곳이 있을까요?",
    },
    {
        "profile": {"user_id": 900005, "region": "대전", "district": "유성구", "employment_status": "미취업"},
        "chat": "창업 초기 자금이 부족한데 도움받을 방법이 있을까요?",
    },
    {
        "profile": {"user_id": 900006, "region": "인천", "district": "연수구", "employment_status": "은퇴", "age": 61},
        "chat": "60대 은퇴 후 창업을 준비하고 있는데 지원받을 수 있는 정책이 있을까요?",
    },
    {
        "profile": {"user_id": 900007, "region": "광주", "district": "서구", "employment_status": "재직", "marital_status": "기혼"},
        "chat": "육아휴직 후 복직을 준비하고 있는 30대 직장인인데, 아이 돌봄 관련 지원이 있을까요?",
    },
    {
        "profile": {"user_id": 900008, "region": "울산", "district": "남구", "employment_status": "미취업", "sme_employment": True},
        "chat": "중소기업 다니는데 목돈 마련할 수 있는 저축 지원 정책이 있을까요?",
    },
]


def main():
    with httpx.Client(timeout=60) as client:
        for i, case in enumerate(SAMPLE_CASES, start=1):
            print(f"\n[{i}/{len(SAMPLE_CASES)}] {case['chat'][:40]}...")
            payload = {"user_profile": case["profile"], "chat": case["chat"]}
            try:
                resp = client.post(f"{BASE_URL}/recommendations/chat", json=payload)
                resp.raise_for_status()
                llm_answer = resp.json().get("llm_answer")
                print(f"  -> llm_answer: {llm_answer}")
            except Exception as e:
                print(f"  [실패] {e}")

    print("\n완료. evaluation/collected/raw_capture.jsonl 확인 후 build_cases_from_capture.py를 실행하세요.")


if __name__ == "__main__":
    main()
