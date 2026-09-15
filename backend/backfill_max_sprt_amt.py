"""
policy.plcySprtCn(지원 내용)에서 정규식으로 "최대 지원 금액"을 추출해
policy.maxSprtAmt 컬럼(원 단위)에 채워 넣는 백필 스크립트.

"최대 X[억원|백만원|만원|원]" 또는 "X[단위] 한도"처럼 마커가 금액에 직접 붙어있을
때만 추출한다(오추출 방지를 위해 보수적으로 동작 - 마커 없이 나열된 금액이나
"최대 12개월"처럼 금액이 아닌 값을 수식하는 경우는 무시). "대출한도: 최대 1억원",
"대출잔액(최대 1억원)", "최대 5억원 대출 지원"처럼 대출/융자의 원금·한도·잔액
자체를 가리키는 금액도 제외한다(실제 지원금이 아니라 빌리는 돈의 상한선이므로).
"본인부담금 ... 최대 24,000원"처럼 지원 없이 본인이 내는 금액도 제외한다(단,
"본인부담금 최대 100만원 지원"처럼 그 부담금을 대신 지원해주는 경우는 제외하지
않음). 같은 문장 안에서 "기업은"/"기업이"처럼 기업/업체/사업체가 문장의 주어로
쓰인 경우(예: "기업은 ... 프로그램별 최대 50억원까지 지원")도 청년 개인이 아니라
그 기업이 받는 돈이므로 제외한다. 같은 문장/줄 안에 "소득공제"가 있으면(예: "연
300만원 한도로 40%까지 소득공제 제공") 실제 지원금이 아니라 세제 혜택 한도이므로
제외한다. 한 텍스트에 후보가 여러 개면 그중 최댓값을 쓴다.
(app/services/policy.py의 PolicyService와 동일 로직)

매번 재실행해도 결과가 일관되도록, UPDATE 전에 maxSprtAmt를 전부 NULL로 초기화한
뒤 새로 추출한 값만 다시 채운다(이전 실행에서 지금은 제외 대상이 된 값이 남아있지
않도록).

사전 준비:
    pip install pymysql python-dotenv
    (.env는 기존 policy 적재 때 쓰던 것 그대로 사용)

사용법:
    python backfill_max_sprt_amt.py            # 실제로 DB에 반영
    python backfill_max_sprt_amt.py --dry-run   # DB에 반영하지 않고 결과만 미리보기
"""

import os
import re
import argparse

import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
}

UNIT_MULTIPLIER = [
    ("억원", 100_000_000),
    ("백만원", 1_000_000),
    ("만원", 10_000),
    ("원", 1),
]
AMOUNT_UNIT_RE = "|".join(unit for unit, _ in UNIT_MULTIPLIER)
NUMBER_RE = r"[0-9][0-9,\.]*"
MAX_PREFIX_RE = re.compile(rf"최대\s*({NUMBER_RE})\s*({AMOUNT_UNIT_RE})")
LIMIT_SUFFIX_RE = re.compile(rf"({NUMBER_RE})\s*({AMOUNT_UNIT_RE})\s*한도")

# "대출"/"융자"(이자·이율·금리 표현 제외)가 매치 직전에 있고, 그 뒤부터 매치 시작까지
# 사이에 "%"나 "이자"가 없으면 대출 원금/한도/잔액 자체를 가리키는 것으로 본다.
LOAN_PRINCIPAL_RE = re.compile(r"(?:대출|융자)(?!\s*(?:이자|이율|금리))")
LOAN_CONTEXT_WINDOW = 15

# "최대 5억원 대출 지원", "1억원 한도 융자지원"처럼 "대출"/"융자"가 금액 바로 뒤에
# 붙어 지원 대상 자체가 대출/융자임을 밝히는 경우도 대출 원금이라 제외한다.
LOAN_AFTER_RE = re.compile(r"^\s*(?:대출|융자)\s*(?:지원|지급)")
LOAN_AFTER_WINDOW = 20

# "본인부담"/"자기부담"이 매치 앞쪽(넓은 구간)에 있으면 본인이 내는 돈일 가능성이 있다고
# 보되, 매치 바로 뒤에 "지원"/"지급"이 오면 그 부담금을 대신 지원해준다는 뜻이므로 제외하지 않는다.
SELF_PAY_WORDS = ("본인부담", "자기부담")
SELF_PAY_BEFORE_WINDOW = 45
SELF_PAY_AFTER_WINDOW = 15

# 같은 문장 안에서 "기업은"/"기업이"처럼 기업/업체/사업체가 문장의 주어로 쓰이면, 그 문장이
# 서술하는 지원금은 그 기업이 받는 돈이라고 본다. "기업당"/"업체당"처럼 자기 사업체를
# 가리키는 표현은 주어 조사(은/는/이/가)가 아니라 부사격 조사라 이 패턴에 걸리지 않는다.
BIZ_SUBJECT_RE = re.compile(r"(?:기업|업체|사업체)(?:은|는|이|가)")

# "소득공제" 문맥의 금액은 실제 지원금이 아니라 세금 계산할 때 빼주는 소득 한도이므로
# 제외한다. 같은 문장/줄 안에서만 확인한다(마침표 "다."/줄바꿈이 경계).
INCOME_DEDUCTION_WORD = "소득공제"


def amount_to_won(amount_str, unit):
    """숫자 문자열과 단위(억원/백만원/만원/원)를 원 단위 정수로 변환한다."""
    try:
        value = float(amount_str.replace(",", ""))
    except ValueError:
        return None
    for u, multiplier in UNIT_MULTIPLIER:
        if unit == u:
            return round(value * multiplier)
    return None


# 아래 is_*_context 함수들은 app/services/policy.py의 PolicyService._is_*_context와
# 동일 로직이다(대출원금/본인부담/기업대상/소득공제 문맥이면 지원금 후보에서 제외).

def is_loan_principal_context(text, match_start):
    """매치 앞에 "대출"/"융자"가 있으면 대출 원금/한도/잔액 자체를 가리키는지 확인한다."""
    start = max(0, match_start - LOAN_CONTEXT_WINDOW)
    context = text[start:match_start]
    last_end = -1
    for m in LOAN_PRINCIPAL_RE.finditer(context):
        last_end = max(last_end, m.end())
    if last_end == -1:
        return False
    between = context[last_end:]
    return "%" not in between and "이자" not in between


def is_loan_principal_after_context(text, match_end):
    """매치 바로 뒤에 "대출 지원"/"융자 지급"이 이어지면 지원 대상 자체가 대출 원금인지 확인한다."""
    after = text[match_end:match_end + LOAN_AFTER_WINDOW]
    return bool(LOAN_AFTER_RE.match(after))


def is_self_payment_context(text, match_start, match_end):
    """매치 앞에 "본인부담"/"자기부담"이 있고 뒤에 "지원/지급"이 없으면 본인이 내는 돈인지 확인한다."""
    before = text[max(0, match_start - SELF_PAY_BEFORE_WINDOW):match_start]
    if not any(word in before for word in SELF_PAY_WORDS):
        return False
    after = text[match_end:match_end + SELF_PAY_AFTER_WINDOW]
    return not ("지원" in after or "지급" in after)


def is_business_subject_context(text, match_start):
    """같은 문장에서 기업/업체/사업체가 주어로 쓰였으면(개인이 아닌 기업이 받는 돈인지) 확인한다."""
    before = text[:match_start]
    cut = max(before.rfind("다."), before.rfind("\n"))
    scoped = before[cut + 1:] if cut != -1 else before
    return bool(BIZ_SUBJECT_RE.search(scoped))


def is_income_deduction_context(text, match_start, match_end):
    """같은 문장/줄에 "소득공제"가 있으면(실제 지원금이 아닌 세제 혜택 한도인지) 확인한다."""
    before_cut = max(text.rfind("다.", 0, match_start), text.rfind("\n", 0, match_start))
    start = before_cut + 1 if before_cut != -1 else 0
    after_dot = text.find("다.", match_end)
    after_nl = text.find("\n", match_end)
    boundaries = [b for b in (after_dot, after_nl) if b != -1]
    end = min(boundaries) if boundaries else len(text)
    return INCOME_DEDUCTION_WORD in text[start:end]


def extract_max_support_amount(text):
    """지원내용 텍스트에서 "최대 지원 금액"(원)을 뽑아낸다. 대출원금/본인부담/기업대상/
    소득공제 문맥이면 후보에서 제외하고, 후보가 여러 개면 최댓값을 쓴다."""
    if not text:
        return None
    candidates = []
    for pattern in (MAX_PREFIX_RE, LIMIT_SUFFIX_RE):
        for m in pattern.finditer(text):
            if is_loan_principal_context(text, m.start()):
                continue
            if is_loan_principal_after_context(text, m.end()):
                continue
            if is_self_payment_context(text, m.start(), m.end()):
                continue
            if is_business_subject_context(text, m.start()):
                continue
            if is_income_deduction_context(text, m.start(), m.end()):
                continue
            won = amount_to_won(m.group(1), m.group(2))
            if won is not None:
                candidates.append(won)
    return max(candidates) if candidates else None


def ensure_max_sprt_amt_column(conn) -> None:
    """Base.metadata.create_all은 기존 테이블에 새 컬럼을 추가해주지 않으므로 직접 확인 후 추가."""
    with conn.cursor() as cur:
        cur.execute("SHOW COLUMNS FROM policy LIKE 'maxSprtAmt'")
        if cur.fetchone() is None:
            print("  policy.maxSprtAmt 컬럼이 없어 추가합니다...")
            cur.execute("ALTER TABLE policy ADD COLUMN maxSprtAmt BIGINT NULL")
    conn.commit()


def backfill(conn, dry_run: bool) -> None:
    """전체 정책의 지원내용에서 최대 지원금액을 추출해 maxSprtAmt 컬럼에 채운다.
    재실행해도 결과가 일관되도록 먼저 전부 NULL로 초기화한 뒤 다시 채운다."""
    ensure_max_sprt_amt_column(conn)

    with conn.cursor() as cur:
        cur.execute("SELECT policy_id, plcyNm, plcySprtCn FROM policy")
        rows = cur.fetchall()

    print(f"전체 정책 수: {len(rows)}")

    pairs = []
    preview = []
    for policy_id, plcy_nm, plcy_sprt_cn in rows:
        amount = extract_max_support_amount(plcy_sprt_cn)
        if amount is not None:
            pairs.append((amount, policy_id))
            preview.append((plcy_nm, amount))

    print(f"금액 추출됨: {len(pairs)}건 ({len(pairs) / len(rows) * 100:.1f}%)")

    if dry_run:
        print("\n[--dry-run] 미리보기 10건:")
        for plcy_nm, amount in preview[:10]:
            print(f"  {plcy_nm[:40]:40s} -> {amount:,}원")
        print("\nDB에는 반영하지 않았습니다 (--dry-run).")
        return

    # 재실행 시 이전에는 추출됐지만 지금은 제외 대상이 된 값이 남아있지 않도록 먼저 전부 비운다.
    with conn.cursor() as cur:
        cur.execute("UPDATE policy SET maxSprtAmt = NULL")
    conn.commit()

    if not pairs:
        print("업데이트할 항목이 없습니다.")
        return

    sql = "UPDATE policy SET maxSprtAmt = %s WHERE policy_id = %s"
    with conn.cursor() as cur:
        cur.executemany(sql, pairs)
    conn.commit()
    print(f"{len(pairs)}건 업데이트 완료.")


def main():
    """CLI 진입점: 옵션을 파싱하고 DB에 연결해 backfill을 실행한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="DB에 반영하지 않고 추출 결과만 미리보기")
    args = parser.parse_args()

    conn = pymysql.connect(**DB_CONFIG)
    print(f"DB 연결 성공: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        backfill(conn, args.dry_run)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
