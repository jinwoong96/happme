"""
로컬에서 띄운 bene_ai 서버(POST /recommendations/chat)에 다양한 상황을 실제로 던져서,
recommendation_service.py의 EVAL_CAPTURE 캡처(evaluation/collected/raw_capture.jsonl)를
채우는 스크립트. bene_backend를 거치지 않고 bene_ai를 직접 호출하므로 user_id는 실제 DB
사용자가 아니어도 된다(가짜 값으로 충분).

정답셋 100개 목표로 카테고리별(일자리/주거/교육/건강돌봄/복지금융/창업/문화예술/참여권리/기타)로
상황을 골고루 채워뒀다. 일부러 "정책이 없어야 정상인" 엣지 케이스(나이 안 맞음, 아예 무관한
질문 등)도 섞어서 LLM이 "없음(0)"을 잘 판단하는지도 같이 볼 수 있게 했다.

사전 준비
    1) bene_ai/.env에 EVAL_CAPTURE=true 추가
    2) (재시작 필수 - .env는 프로세스 시작 시 한 번만 읽음) python -m uvicorn main:app --port 8090
    3) 이 스크립트 실행: python collect_cases.py
    4) 끝나면: python build_cases_from_capture.py
"""

import httpx

BASE_URL = "http://localhost:8090"

SAMPLE_CASES = [
    # ---------- 기존 8건 (재실행해도 build_cases_from_capture.py가 중복은 알아서 걸러줌) ----------
    {"profile": {"user_id": 900001, "region": "서울", "district": "관악구", "employment_status": "미취업", "education": "대졸"},
     "chat": "저는 취업준비 중인 25세 대학생이고, 생활비 지원을 받을 수 있는 정책을 찾고 있어요."},
    {"profile": {"user_id": 900002, "region": "경기", "district": "수원시", "employment_status": "재직", "marital_status": "미혼"},
     "chat": "이번에 취업하면서 독립하려는데, 월세 부담이 커서 지원받을 수 있는 정책이 있을까요?"},
    {"profile": {"user_id": 900003, "region": "부산", "district": "해운대구", "employment_status": "재직"},
     "chat": "학자금 대출 이자가 부담돼요."},
    {"profile": {"user_id": 900004, "region": "서울", "district": "강남구", "employment_status": "재직"},
     "chat": "마음이 많이 힘든데 상담받을 수 있는 곳이 있을까요?"},
    {"profile": {"user_id": 900005, "region": "대전", "district": "유성구", "employment_status": "미취업"},
     "chat": "창업 초기 자금이 부족한데 도움받을 방법이 있을까요?"},
    {"profile": {"user_id": 900006, "region": "인천", "district": "연수구", "employment_status": "은퇴", "age": 61},
     "chat": "60대 은퇴 후 창업을 준비하고 있는데 지원받을 수 있는 정책이 있을까요?"},
    {"profile": {"user_id": 900007, "region": "광주", "district": "서구", "employment_status": "재직", "marital_status": "기혼"},
     "chat": "육아휴직 후 복직을 준비하고 있는 30대 직장인인데, 아이 돌봄 관련 지원이 있을까요?"},
    {"profile": {"user_id": 900008, "region": "울산", "district": "남구", "employment_status": "미취업", "sme_employment": True},
     "chat": "중소기업 다니는데 목돈 마련할 수 있는 저축 지원 정책이 있을까요?"},

    # ---------- 일자리 (13) ----------
    {"profile": {"user_id": 900101, "region": "서울", "district": "마포구", "employment_status": "미취업", "education": "대졸"},
     "chat": "취업 준비 중인데 이력서나 면접 컨설팅을 받을 수 있는 곳이 있을까요?"},
    {"profile": {"user_id": 900102, "region": "경기", "district": "성남시", "employment_status": "미취업"},
     "chat": "구직활동 중인데 활동비를 지원받을 수 있나요?"},
    {"profile": {"user_id": 900103, "region": "부산", "district": "동래구", "employment_status": "재직", "sme_employment": True},
     "chat": "중소기업에 막 취업했는데 정착지원금 같은 게 있을까요?"},
    {"profile": {"user_id": 900104, "region": "대구", "district": "수성구", "employment_status": "미취업"},
     "chat": "장기 실업 상태인데 재취업 지원 프로그램이 있을까요?"},
    {"profile": {"user_id": 900105, "region": "인천", "district": "부평구", "employment_status": "미취업", "education": "대졸"},
     "chat": "인턴십을 하고 싶은데 지원 프로그램이 있을까요?"},
    {"profile": {"user_id": 900106, "region": "광주", "district": "북구", "employment_status": "재직"},
     "chat": "이직을 준비 중인데 도움받을 수 있는 정책이 있나요?"},
    {"profile": {"user_id": 900107, "region": "대전", "district": "서구", "employment_status": "미취업", "education": "대졸"},
     "chat": "졸업 후 첫 직장을 구하고 있는데 취업 지원금이 있을까요?"},
    {"profile": {"user_id": 900108, "region": "울산", "district": "중구", "employment_status": "자영업"},
     "chat": "프리랜서로 일하는데 소득 안정 지원이 있을까요?"},
    {"profile": {"user_id": 900109, "region": "세종", "district": "세종시", "employment_status": "미취업"},
     "chat": "국가기술자격증 취득 비용을 지원받을 수 있나요?"},
    {"profile": {"user_id": 900110, "region": "강원", "district": "춘천시", "employment_status": "재직"},
     "chat": "취업한 지 6개월 됐는데 근속장려금 같은 게 있나요?"},
    {"profile": {"user_id": 900111, "region": "충북", "district": "청주시", "employment_status": "미취업"},
     "chat": "면접 정장을 대여할 수 있는 지원 서비스가 있을까요?"},
    {"profile": {"user_id": 900112, "region": "전북", "district": "전주시", "employment_status": "미취업"},
     "chat": "직업훈련을 받고 싶은데 무료로 들을 수 있는 과정이 있을까요?"},
    {"profile": {"user_id": 900113, "region": "경남", "district": "창원시", "employment_status": "미취업", "disability": True},
     "chat": "장애가 있는데 취업을 지원받을 수 있는 정책이 있을까요?"},

    # ---------- 주거 (12) ----------
    {"profile": {"user_id": 900201, "region": "서울", "district": "동작구", "employment_status": "재직", "marital_status": "미혼"},
     "chat": "전세 계약을 앞두고 있는데 보증금 대출 지원이 있을까요?"},
    {"profile": {"user_id": 900202, "region": "경기", "district": "부천시", "employment_status": "재직"},
     "chat": "1인 가구인데 월세 지원받을 수 있는 정책이 있나요?"},
    {"profile": {"user_id": 900203, "region": "부산", "district": "남구", "employment_status": "미취업"},
     "chat": "청년 임대주택에 입주하고 싶은데 어떻게 신청하나요?"},
    {"profile": {"user_id": 900204, "region": "대구", "district": "달서구", "employment_status": "재직"},
     "chat": "이사할 때 이사비를 지원해주는 정책이 있을까요?"},
    {"profile": {"user_id": 900205, "region": "서울", "district": "성북구", "employment_status": "미취업", "education": "대졸"},
     "chat": "기숙사비가 부담되는데 지원받을 방법이 있을까요?"},
    {"profile": {"user_id": 900206, "region": "서울", "district": "구로구", "employment_status": "미취업", "region_moved": True},
     "chat": "지방에서 서울로 상경했는데 주거 지원이 있을까요?"},
    {"profile": {"user_id": 900207, "region": "인천", "district": "미추홀구", "employment_status": "재직"},
     "chat": "전세사기 피해를 입었는데 지원받을 수 있는 정책이 있나요?"},
    {"profile": {"user_id": 900208, "region": "광주", "district": "광산구", "employment_status": "재직", "marital_status": "기혼"},
     "chat": "신혼부부인데 주택 마련 지원이 있을까요?"},
    {"profile": {"user_id": 900209, "region": "대전", "district": "유성구", "employment_status": "미취업"},
     "chat": "공공임대주택 입주 조건이 궁금해요."},
    {"profile": {"user_id": 900210, "region": "울산", "district": "동구", "employment_status": "미취업", "basic_livelihood": True},
     "chat": "주거급여를 받을 수 있는지 궁금해요."},
    {"profile": {"user_id": 900211, "region": "전남", "district": "순천시", "employment_status": "미취업"},
     "chat": "귀농을 준비 중인데 주거 지원이 있을까요?"},
    {"profile": {"user_id": 900212, "region": "서울", "district": "관악구", "employment_status": "미취업"},
     "chat": "고시원에서 나와 독립하고 싶은데 지원받을 수 있는 정책이 있을까요?"},

    # ---------- 교육 (12) ----------
    {"profile": {"user_id": 900301, "region": "서울", "district": "종로구", "employment_status": "미취업", "education": "대졸"},
     "chat": "대학원 진학을 준비 중인데 장학금 지원이 있을까요?"},
    {"profile": {"user_id": 900302, "region": "경기", "district": "안양시", "employment_status": "미취업", "education": "대학재학"},
     "chat": "국가장학금 신청 자격이 궁금해요."},
    {"profile": {"user_id": 900303, "region": "부산", "district": "부산진구", "employment_status": "미취업"},
     "chat": "직무 관련 자격증 시험 응시료를 지원받을 수 있나요?"},
    {"profile": {"user_id": 900304, "region": "대구", "district": "북구", "employment_status": "미취업"},
     "chat": "온라인 강의를 무료로 들을 수 있는 청년 지원 프로그램이 있을까요?"},
    {"profile": {"user_id": 900305, "region": "인천", "district": "연수구", "employment_status": "미취업", "education": "대졸"},
     "chat": "어학연수를 가고 싶은데 지원받을 수 있는 정책이 있나요?"},
    {"profile": {"user_id": 900306, "region": "광주", "district": "동구", "employment_status": "미취업", "education": "고졸"},
     "chat": "검정고시를 준비 중인데 학습비 지원이 있을까요?"},
    {"profile": {"user_id": 900307, "region": "대전", "district": "중구", "employment_status": "미취업", "education": "대학재학"},
     "chat": "대학교 등록금이 부담되는데 지원받을 방법이 있을까요?"},
    {"profile": {"user_id": 900308, "region": "울산", "district": "북구", "employment_status": "미취업"},
     "chat": "코딩 부트캠프를 듣고 싶은데 국비지원 과정이 있을까요?"},
    {"profile": {"user_id": 900309, "region": "세종", "district": "세종시", "employment_status": "미취업", "education": "고퇴"},
     "chat": "고등학교를 중퇴했는데 학업 복귀를 지원하는 정책이 있을까요?"},
    {"profile": {"user_id": 900310, "region": "강원", "district": "원주시", "employment_status": "미취업", "education": "대학재학"},
     "chat": "대학생인데 교재비를 지원받을 수 있나요?"},
    {"profile": {"user_id": 900311, "region": "충남", "district": "천안시", "employment_status": "미취업"},
     "chat": "다문화가정 자녀인데 교육 지원이 있을까요?"},
    {"profile": {"user_id": 900312, "region": "경북", "district": "포항시", "employment_status": "미취업", "education": "대학재학"},
     "chat": "군 제대 후 복학을 준비 중인데 지원받을 수 있는 정책이 있을까요?"},

    # ---------- 건강·돌봄 (12) ----------
    {"profile": {"user_id": 900401, "region": "서울", "district": "송파구", "employment_status": "재직", "marital_status": "기혼"},
     "chat": "임신 중인데 산전 검사비를 지원받을 수 있나요?"},
    {"profile": {"user_id": 900402, "region": "경기", "district": "고양시", "employment_status": "재직", "marital_status": "기혼"},
     "chat": "산후조리 비용을 지원받고 싶어요."},
    {"profile": {"user_id": 900403, "region": "부산", "district": "사하구", "employment_status": "미취업"},
     "chat": "치과 치료비가 부담되는데 지원받을 수 있는 정책이 있을까요?"},
    {"profile": {"user_id": 900404, "region": "대구", "district": "동구", "employment_status": "재직"},
     "chat": "정신적으로 지친 상태인데 상담을 지원받을 수 있을까요?"},
    {"profile": {"user_id": 900405, "region": "인천", "district": "남동구", "employment_status": "미취업"},
     "chat": "장애인 가족을 돌보고 있는데 돌봄 지원이 있을까요?"},
    {"profile": {"user_id": 900406, "region": "광주", "district": "서구", "employment_status": "재직", "marital_status": "기혼"},
     "chat": "난임 시술비를 지원받을 수 있는 정책이 있나요?"},
    {"profile": {"user_id": 900407, "region": "대전", "district": "유성구", "employment_status": "미취업", "gender": "여성", "age": 17},
     "chat": "여성청소년 생리용품 지원이 있다고 들었는데 맞나요?"},
    {"profile": {"user_id": 900408, "region": "울산", "district": "남구", "employment_status": "미취업"},
     "chat": "혼자 부모님을 간병하고 있는데 돌봄 청년 지원이 있을까요?"},
    {"profile": {"user_id": 900409, "region": "세종", "district": "세종시", "employment_status": "재직"},
     "chat": "건강검진을 무료로 받을 수 있는 정책이 있을까요?"},
    {"profile": {"user_id": 900410, "region": "강원", "district": "강릉시", "employment_status": "미취업"},
     "chat": "예방접종 비용을 지원받고 싶어요."},
    {"profile": {"user_id": 900411, "region": "충북", "district": "충주시", "employment_status": "미취업"},
     "chat": "자립준비청년인데 의료비 지원이 있을까요?"},
    {"profile": {"user_id": 900412, "region": "전북", "district": "익산시", "employment_status": "재직"},
     "chat": "만성질환이 있는데 치료비를 지원받을 수 있는 정책이 있나요?"},

    # ---------- 복지·금융 (12) ----------
    {"profile": {"user_id": 900501, "region": "서울", "district": "노원구", "employment_status": "재직"},
     "chat": "목돈 마련을 위한 청년 적금 상품이 있을까요?"},
    {"profile": {"user_id": 900502, "region": "경기", "district": "용인시", "employment_status": "미취업"},
     "chat": "신용회복이 필요한데 지원받을 수 있는 정책이 있나요?"},
    {"profile": {"user_id": 900503, "region": "부산", "district": "금정구", "employment_status": "재직"},
     "chat": "저축은행 대출 이자가 부담되는데 지원받을 방법이 있을까요?"},
    {"profile": {"user_id": 900504, "region": "대구", "district": "남구", "employment_status": "미취업", "basic_livelihood": True},
     "chat": "기초생활수급자인데 받을 수 있는 청년 지원이 있을까요?"},
    {"profile": {"user_id": 900505, "region": "인천", "district": "서구", "employment_status": "재직"},
     "chat": "자산형성을 위한 매칭펀드 같은 게 있을까요?"},
    {"profile": {"user_id": 900506, "region": "광주", "district": "남구", "employment_status": "재직"},
     "chat": "보이스피싱 피해를 입었는데 구제받을 방법이 있을까요?"},
    {"profile": {"user_id": 900507, "region": "대전", "district": "동구", "employment_status": "재직"},
     "chat": "신용카드 연체가 걱정되는데 상담받을 수 있는 곳이 있을까요?"},
    {"profile": {"user_id": 900508, "region": "울산", "district": "울주군", "employment_status": "미취업", "basic_livelihood": True},
     "chat": "생계가 어려운데 긴급복지 지원을 받을 수 있을까요?"},
    {"profile": {"user_id": 900509, "region": "세종", "district": "세종시", "employment_status": "미취업"},
     "chat": "청년 특례보증을 받고 싶은데 조건이 궁금해요."},
    {"profile": {"user_id": 900510, "region": "강원", "district": "원주시", "employment_status": "미취업", "basic_livelihood": True},
     "chat": "차상위계층인데 금융 지원 정책이 있을까요?"},
    {"profile": {"user_id": 900511, "region": "충남", "district": "아산시", "employment_status": "미취업"},
     "chat": "파산 위기인데 채무조정 지원을 받을 수 있나요?"},
    {"profile": {"user_id": 900512, "region": "경북", "district": "구미시", "employment_status": "미취업"},
     "chat": "가족돌봄청년인데 생계비 지원이 있을까요?"},

    # ---------- 창업 (10) ----------
    {"profile": {"user_id": 900601, "region": "서울", "district": "서초구", "employment_status": "미취업"},
     "chat": "청년 창업 아이템 경진대회 같은 게 있을까요?"},
    {"profile": {"user_id": 900602, "region": "경기", "district": "화성시", "employment_status": "자영업"},
     "chat": "1인 창업을 준비 중인데 사무공간 지원이 있을까요?"},
    {"profile": {"user_id": 900603, "region": "전남", "district": "여수시", "employment_status": "미취업"},
     "chat": "농업 창업을 준비 중인데 지원받을 수 있는 정책이 있을까요?"},
    {"profile": {"user_id": 900604, "region": "부산", "district": "연제구", "employment_status": "미취업"},
     "chat": "온라인 쇼핑몰 창업을 준비하는데 도움받을 방법이 있을까요?"},
    {"profile": {"user_id": 900605, "region": "대구", "district": "중구", "employment_status": "미취업"},
     "chat": "특허를 활용한 창업을 준비 중인데 지원받을 수 있나요?"},
    {"profile": {"user_id": 900606, "region": "인천", "district": "계양구", "employment_status": "자영업"},
     "chat": "소상공인 창업자금 대출을 받고 싶은데 조건이 궁금해요."},
    {"profile": {"user_id": 900607, "region": "광주", "district": "북구", "employment_status": "미취업"},
     "chat": "사회적기업 창업을 준비 중인데 지원 정책이 있을까요?"},
    {"profile": {"user_id": 900608, "region": "대전", "district": "서구", "employment_status": "미취업"},
     "chat": "예비창업패키지에 지원하고 싶은데 자격이 궁금해요."},
    {"profile": {"user_id": 900609, "region": "울산", "district": "중구", "employment_status": "자영업"},
     "chat": "폐업 후 재창업을 준비 중인데 지원받을 수 있는 정책이 있을까요?"},
    {"profile": {"user_id": 900610, "region": "경남", "district": "김해시", "employment_status": "자영업"},
     "chat": "해외 진출을 준비하는 스타트업인데 지원 프로그램이 있을까요?"},

    # ---------- 문화·예술 (8) ----------
    {"profile": {"user_id": 900701, "region": "서울", "district": "마포구", "employment_status": "재직"},
     "chat": "공연 관람비를 지원받을 수 있는 청년 문화패스가 있을까요?"},
    {"profile": {"user_id": 900702, "region": "경기", "district": "안산시", "employment_status": "미취업"},
     "chat": "예술 활동을 하는 청년인데 창작지원금이 있을까요?"},
    {"profile": {"user_id": 900703, "region": "부산", "district": "수영구", "employment_status": "미취업"},
     "chat": "전시회를 열고 싶은 신진 작가인데 지원받을 방법이 있을까요?"},
    {"profile": {"user_id": 900704, "region": "대구", "district": "수성구", "employment_status": "재직"},
     "chat": "독서 모임 운영비를 지원받고 싶어요."},
    {"profile": {"user_id": 900705, "region": "인천", "district": "동구", "employment_status": "미취업"},
     "chat": "지역 축제에 참여하는 청년 기획단 모집이 있을까요?"},
    {"profile": {"user_id": 900706, "region": "광주", "district": "남구", "employment_status": "미취업"},
     "chat": "영화 제작을 준비 중인 독립영화 감독인데 지원이 있을까요?"},
    {"profile": {"user_id": 900707, "region": "전북", "district": "군산시", "employment_status": "미취업", "basic_livelihood": True},
     "chat": "문화누리카드를 받을 수 있는 조건이 궁금해요."},
    {"profile": {"user_id": 900708, "region": "경남", "district": "진주시", "employment_status": "재직"},
     "chat": "청년 문화예술 동아리 활동비 지원이 있을까요?"},

    # ---------- 참여권리 (8) ----------
    {"profile": {"user_id": 900801, "region": "서울", "district": "은평구", "employment_status": "재직"},
     "chat": "청년정책 제안을 하고 싶은데 참여할 수 있는 위원회가 있을까요?"},
    {"profile": {"user_id": 900802, "region": "경기", "district": "의정부시", "employment_status": "미취업"},
     "chat": "법률 상담이 필요한데 무료로 받을 수 있는 곳이 있을까요?"},
    {"profile": {"user_id": 900803, "region": "부산", "district": "동구", "employment_status": "재직"},
     "chat": "임금체불을 당했는데 도움받을 수 있는 곳이 있을까요?"},
    {"profile": {"user_id": 900804, "region": "대구", "district": "달성군", "employment_status": "재직"},
     "chat": "부당해고를 당한 것 같은데 상담받을 수 있는 정책이 있을까요?"},
    {"profile": {"user_id": 900805, "region": "인천", "district": "중구", "employment_status": "미취업"},
     "chat": "청년 자원봉사단에 참여하고 싶은데 지원 정책이 있을까요?"},
    {"profile": {"user_id": 900806, "region": "광주", "district": "동구", "employment_status": "미취업"},
     "chat": "지역 청년의회에 참여하고 싶은데 방법이 있을까요?"},
    {"profile": {"user_id": 900807, "region": "대전", "district": "대덕구", "employment_status": "재직"},
     "chat": "직장 내 괴롭힘 상담을 받고 싶은데 지원 정책이 있을까요?"},
    {"profile": {"user_id": 900808, "region": "서울", "district": "중랑구", "employment_status": "재직"},
     "chat": "1인가구 안전 관련 지원 정책이 있을까요?"},

    # ---------- 기타 / 엣지 케이스 (정책이 없어야 정상인 경우 포함, 10) ----------
    {"profile": {"user_id": 900901, "region": "전남", "district": "목포시", "employment_status": "미취업"},
     "chat": "다른 지역으로 귀촌하려는데 정착 지원금이 있을까요?"},
    {"profile": {"user_id": 900902, "region": "서울", "district": "용산구", "employment_status": "미취업"},
     "chat": "군인인데 전역 후 받을 수 있는 지원 정책이 있을까요?"},
    {"profile": {"user_id": 900903, "region": "경기", "district": "평택시", "employment_status": "미취업"},
     "chat": "다문화가정인데 정착 지원 정책이 있을까요?"},
    {"profile": {"user_id": 900904, "region": "서울", "district": "강북구", "employment_status": "미취업"},
     "chat": "새터민(북한이탈주민)인데 정착 지원이 있을까요?"},
    {"profile": {"user_id": 900905, "region": "서울", "district": "동대문구", "employment_status": "미취업", "education": "대학재학"},
     "chat": "외국인 유학생인데 받을 수 있는 지원이 있을까요?"},
    {"profile": {"user_id": 900906, "region": "부산", "district": "기장군", "employment_status": "은퇴", "age": 72},
     "chat": "70대 어르신인데 노인 일자리 지원이 있을까요?"},
    {"profile": {"user_id": 900907, "region": "대구", "district": "서구", "employment_status": "재직", "marital_status": "기혼"},
     "chat": "초등학생 자녀를 둔 학부모인데 사교육비 지원이 있을까요?"},
    {"profile": {"user_id": 900908, "region": "인천", "district": "옹진군", "employment_status": "재직"},
     "chat": "반려동물 의료비를 지원받을 수 있나요?"},
    {"profile": {"user_id": 900909, "region": "광주", "district": "광산구", "employment_status": "재직"},
     "chat": "자동차 구입 지원금이 있을까요?"},
    {"profile": {"user_id": 900910, "region": "대전", "district": "중구", "employment_status": "재직", "marital_status": "기혼"},
     "chat": "결혼식 비용을 지원받을 수 있는 정책이 있을까요?"},
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
