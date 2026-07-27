# 상황매칭 LLM 성능평가 (Ragas)

## 1. 뭘 평가하는가

`recommendation_service.py`의 상황매칭 흐름에서 LLM이 쓰이는 두 지점을 각각 평가한다.

1. **`_llm_select_candidate`** — 룰엔진으로 자격조건을 거른 정책 중, 임베딩 유사도 top10 후보의 "제목"만 보고 사용자 상황(chat)에 맞는 1개를 번호로 선택 (없으면 0)
2. **`_llm_explain_policy`** — 1번에서 선택된 정책의 상세정보(정책설명/지원내용/대상연령/신청기간/소득조건 등)를 근거로, 왜 이 정책이 사용자 상황에 도움이 되는지 설명을 생성

두 단계는 성격이 완전히 다르다. 1번은 **정답이 하나로 정해진 선택형 분류**(10개 중 몇 번, 혹은 없음)이고, 2번은 **정답이 따로 없는 자유 생성**(주어진 정책 정보만 근거로 답하라는 제약이 있음)이다. 그래서 평가 방법도 다르게 적용한다.

## 2. 왜 Ragas인가

**Ragas**(Retrieval-Augmented Generation Assessment)는 LLM/RAG 애플리케이션 평가용 오픈소스 파이썬 라이브러리다. 지표가 두 종류로 나뉜다.

- **결정론적 지표** (LLM 심사 필요 없음): 정답 문자열과 그대로 비교. 예: Exact Match
- **LLM 기반 지표** (다른 LLM을 심사자로 사용): 정답이 없는 자유 생성문을 채점. 예: Faithfulness, Response Relevancy

우리 프로젝트는 위 두 단계가 정확히 이 두 종류로 나뉘기 때문에, 하나의 프레임워크(Ragas) 안에서 둘 다 처리할 수 있다.

## 3. 평가 지표

### 3.1 `_llm_select_candidate` → Exact Match

LLM이 답한 번호(`llm_response`)와 사람이 미리 판단해서 정해둔 정답 번호(`reference`)를 그대로 비교한다. 같으면 1, 다르면 0. 이 평균이 **선택 정확도(Accuracy)** 다. 심사용 LLM이 필요 없다.

### 3.2 `_llm_explain_policy` → Faithfulness + Response Relevancy

- **Faithfulness**: 생성된 답변의 각 주장이 실제로 제공된 정책 정보(context)에 근거하는지 측정. 프롬프트에 "아래 정책 정보에 있는 내용만 사용하세요, 추측하지 마세요"라는 규칙이 있으므로, 이 규칙을 실제로 지키는지(할루시네이션 여부)를 정량화하는 지표다.
- **Response Relevancy**: 생성된 답변이 사용자 상황(chat)과 실제로 관련 있는지 측정. 정책 설명만 나열하고 사용자 상황과 연결을 안 짓는 답변을 걸러낸다.

이 둘은 정답 라벨이 필요 없는 대신, **판단을 맡을 심사용(judge) LLM**이 필요하다.

## 4. Judge 모델 (4개 비교)

같은 답변을 심사용 LLM 4개로 각각 채점해서 결과를 비교한다. 판단 이유는 다음과 같다.

| judge | 모델 | 선정 이유 |
|---|---|---|
| `watsonx_mistral_small_24b` | `mistralai/mistral-small-3-1-24b-instruct-2503` | 지금 실제 답변 생성에 쓰는 모델과 동일. 자기가 만든 답변을 자기가 채점하는(self-eval) 기준선 |
| `watsonx_llama_3_3_70b` | `meta-llama/llama-3-3-70b-instruct` | 같은 watsonx 인프라, 훨씬 큰 모델(24B→70B)로 비교 |
| `ollama_qwen3_8b` | `qwen3:8b` (로컬, 무료) | 로컬 GPU로 돌리는 오픈소스 계열. 원래 32B로 계획했으나 로컬 하드웨어 부담으로 8B로 조정 |
| `groq_llama_3_3_70b` | `llama-3.3-70b-versatile` (Groq 무료 API) | 카드 등록 없이 완전 무료인 클라우드 옵션. watsonx/Ollama와 다른 제공사로 교차 검증 |

judge를 4개나 쓰는 이유: 같은 모델로 생성하고 같은 모델로 채점하면 자기 답을 관대하게 평가할 위험(self-eval bias)이 있다. 서로 다른 4개 judge의 점수를 비교해서, 특정 judge에 의존한 착시가 아닌지 확인한다.

## 5. `evaluation/` 폴더 구성

```
evaluation/
├── check_judges.py               judge 4개 연결 테스트 (본 평가 전 사전 점검용)
├── collect_cases.py              로컬 서버에 실제 상황 8개를 보내 원본 데이터 수집
├── build_cases_from_capture.py   수집된 원본을 정답셋 형식으로 변환
├── ragas_eval.py                 실제 Ragas 평가 실행 (메인 스크립트)
├── requirements-eval.txt         평가 전용 의존성 (ragas, langchain 계열 등)
├── collected/
│   └── raw_capture.jsonl         서버가 실시간으로 남긴 원본 캡처 (자동 생성)
├── test_cases/
│   ├── situation_selection_cases.json   1번(선택형) 정답셋 — reference는 사람이 채움
│   ├── situation_explain_cases.json     2번(생성형) 테스트셋 — 정답 불필요
│   └── *_example.json                   스키마 참고용 예시 (실제 평가에는 안 쓰임)
└── results/                      ragas_eval.py 실행 후 채점 결과 csv (자동 생성)
```

### 각 파일 역할

- **`check_judges.py`**: judge 4개(watsonx 2개, Ollama, Groq)에 "1만 답하라"는 간단한 프롬프트를 보내 연결이 되는지만 확인. 본 평가 전에 API 키/로컬 모델 설정이 제대로 됐는지 빠르게 점검하는 용도.
- **`collect_cases.py`**: 로컬에서 띄운 bene_ai 서버(`/recommendations/chat`)에 미리 짜둔 8가지 상황(주거/교육/건강/창업/육아/저축 등 카테고리를 다양하게 섞음)을 실제로 요청해서, 실제 운영 파이프라인(룰엔진→임베딩 유사도→LLM 2단계)이 그대로 동작하게 만든다.
- **`recommendation_service.py`에 추가된 캡처 로직**: `.env`의 `EVAL_CAPTURE=true`일 때만 켜지는 기록 스위치(평소 운영에는 영향 없음). `recommend_chat_svc` 호출마다 chat, 후보 10개, LLM이 고른 번호, 정책 context, 생성된 답변을 `raw_capture.jsonl`에 한 줄씩 남긴다. (기존 로그(`steps.jsonl`)에는 후보 개수/정책번호만 남고 실제 텍스트 내용이 없어서, 과거 로그로는 정답셋을 만들 수 없었다 — 그래서 이 캡처를 새로 추가했다.)
- **`build_cases_from_capture.py`**: `raw_capture.jsonl`을 읽어 `situation_selection_cases.json`(선택형, `reference`는 항상 빈 값)과 `situation_explain_cases.json`(생성형, 그대로 사용 가능)으로 변환해 이어붙인다.
- **`ragas_eval.py`**: 완성된 두 케이스 파일을 읽어 실제 채점을 수행. 1번은 Exact Match로 정확도 하나만 계산하고, 2번은 judge 4개 각각으로 Faithfulness/Response Relevancy를 계산해 `results/` 폴더에 csv로 저장한다.

## 6. 진행 순서 (재현 방법)

1. `bene_ai/.env`에 `EVAL_CAPTURE=true` 추가
2. 서버 재시작 (`.env` 변경은 프로세스 재시작 전에는 반영되지 않음): `python -m uvicorn main:app --port 8090`
3. `python evaluation/collect_cases.py` — 서버에 실제 요청을 보내 `collected/raw_capture.jsonl` 생성
4. `python evaluation/build_cases_from_capture.py` — 정답셋 초안 생성
5. **`situation_selection_cases.json`을 열어 `reference`(정답 번호)를 사람이 직접 채움** — 이 부분은 자동화 불가능(상황에 실제로 맞는 정책이 뭔지는 사람 판단이 필요)
6. `pip install -r requirements-eval.txt`, judge 계정/모델 준비(watsonx 키, Groq 키, `ollama pull`)
7. `python evaluation/check_judges.py`로 judge 4개 연결 확인
8. `python evaluation/ragas_eval.py` 실행 → `results/1_selection_result.csv`, `results/2_explanation_result.csv` 생성

## 7. 현재 진행 상황 (작성일 기준)

- judge 4개 연결 확인 완료 (watsonx 2개, Ollama qwen3:8b, Groq)
- `collect_cases.py`로 상황 8건 수집 완료
- `situation_explain_cases.json`: 6건 완성 (선택된 정책이 있었던 케이스만 해당)
- `situation_selection_cases.json`: 8건 수집, `reference` 채우는 중. 1차 검토에서 아래 케이스는 특히 주의가 필요했음
  - LLM이 명백히 오답을 고른 사례 발견 (예: "복직 후 아이돌봄 지원" 질문에 "임산부 용품 지원"을 선택 — 생성된 설명문 자체도 "직접적인 지원이 없다"고 자기모순적으로 답함). 이런 실패 사례는 삭제하지 않고 정답셋에 그대로 남겨서 정확도에 반영한다.
  - 후보 10개 중 정확히 맞는 정책이 없어 LLM이 차선책을 고른 애매한 사례 존재 (예: "학자금 대출 이자" 질문에 학자금 전용 상품이 후보에 없어 일반 채무조정 상품을 선택)
- `ragas_eval.py` 본 실행 및 결과 분석은 아직 진행 전
