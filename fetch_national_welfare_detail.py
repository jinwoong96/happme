"""
중앙부처 복지서비스 상세조회 API를 servId별로 호출해서, National_welfare_data.json
(목록, WELFARE2.py로 받은 것)에 있는 각 서비스에 상세정보를 덧붙여
National_welfare_data_detail.json 으로 저장하는 스크립트.

fetch_welfare_detail.py(지자체용)와 완전히 동일한 구조이고, 대상 API만 다르다.

주의: 상세조회 API URL(NationalWelfaredetailedV001)은 목록 API(NationalWelfarelistV001)와
같은 B554287 제공기관, 같은 명명 규칙(Lcgv~list/Lcgv~detailed 페어와 동일 패턴)을 따른다는
전제로 추론한 값입니다. 실제로 호출해본 적은 없으니, 전체를 돌리기 전에 반드시
--peek 으로 1건 먼저 확인하세요. 404/에러가 나면 공공데이터포털의 "한국사회보장정보원_
중앙부처복지서비스" API 문서에서 정확한 상세조회 엔드포인트 경로를 확인해서
DETAIL_API_URL만 고치면 됩니다(나머지 로직은 그대로 재사용 가능).

사전 준비:
    pip install requests xmltodict python-dotenv
    (.env의 WELFARE_API_KEY 그대로 사용 - 지금 값은 팀원에게 받은 새 키)

사용법:
    python fetch_national_welfare_detail.py --peek
        # servId 1건만 호출해서 상세 응답 구조 확인 (엔드포인트가 맞는지부터 확인)

    python fetch_national_welfare_detail.py
        # National_welfare_data.json 전체 순회, National_welfare_data_detail.json에 저장
        # (이미 저장된 servId는 건너뛰고 이어서 진행)

주의(할당량):
    data.go.kr류 API는 보통 일일 호출 한도가 있습니다. 지자체 상세조회(fetch_welfare_detail.py)와
    이 스크립트가 같은 WELFARE_API_KEY를 같이 쓴다면 하루 한도를 나눠 쓰게 되는 셈이니,
    같은 날 둘 다 대량으로 돌리면 한쪽이 먼저 막힐 수 있습니다.
"""

import os
import sys
import json
import time
import argparse

import requests
import xmltodict
from dotenv import load_dotenv

load_dotenv()

DETAIL_API_URL = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfaredetailedV001"
API_KEY = os.getenv("WELFARE_API_KEY")

LIST_FILE = "National_welfare_data.json"
OUTPUT_FILE = "National_welfare_data_detail.json"
SLEEP_SEC = 0.2


def load_summary_list() -> list:
    with open(LIST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    try:
        items = data["wantedList"]["servList"]
    except (KeyError, TypeError):
        sys.exit(f"{LIST_FILE}에서 wantedList.servList를 찾지 못했습니다. 파일 구조를 확인하세요.")
    if isinstance(items, dict):
        # servList가 1건뿐이면 xmltodict가 list가 아니라 dict로 반환할 수 있음
        items = [items]
    return items


def extract_detail(raw: dict) -> dict:
    """응답 루트 태그가 항상 wantedDtl이라는 보장이 없어 방어적으로 처리."""
    if "wantedDtl" in raw:
        return raw["wantedDtl"]
    if len(raw) == 1:
        return next(iter(raw.values()))
    return raw


def fetch_detail(serv_id: str, max_retries: int = 3) -> dict:
    params = {"serviceKey": API_KEY, "servId": serv_id}
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(DETAIL_API_URL, params=params, timeout=15)
            resp.raise_for_status()
            parsed = xmltodict.parse(resp.text)
            return extract_detail(parsed)
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 * attempt
                print(f"  [{serv_id}] 요청 실패 ({e}), {wait}초 후 재시도 ({attempt}/{max_retries})")
                time.sleep(wait)
        except Exception as e:
            # xmltodict 파싱 실패 등 - 재시도해도 똑같을 가능성이 높아 바로 포기
            last_error = e
            print(f"  [{serv_id}] 응답 파싱 실패: {e}")
            break
    raise last_error if last_error else RuntimeError(f"{serv_id} 상세조회 실패")


def load_existing_output() -> dict:
    """이미 만들어둔 output 파일이 있으면 servId -> record로 불러와서 이어서 진행."""
    if not os.path.exists(OUTPUT_FILE):
        return {}
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        return {rec["servId"]: rec for rec in existing if rec.get("servId")}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}


def save_output(records: list):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--peek", action="store_true", help="1건만 호출해서 응답 구조 확인")
    parser.add_argument("--start-index", type=int, default=0, help="이 인덱스부터 강제로 다시 시작 (기본: 이어서 진행)")
    parser.add_argument("--save-every", type=int, default=20, help="몇 건마다 중간 저장할지")
    args = parser.parse_args()

    if not API_KEY:
        sys.exit("WELFARE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

    summary_items = load_summary_list()
    print(f"{LIST_FILE}에서 {len(summary_items)}건 로드")

    if args.peek:
        first = summary_items[0]
        detail = fetch_detail(first["servId"])
        print(json.dumps({"servId": first["servId"], "summary": first, "detail": detail}, ensure_ascii=False, indent=2))
        return

    existing = load_existing_output()
    if existing:
        print(f"기존 {OUTPUT_FILE}에서 {len(existing)}건 이미 완료된 것 확인, 이어서 진행합니다.")

    records = list(existing.values())
    done_ids = set(existing.keys())

    total = len(summary_items)
    fail_count = 0
    for idx, item in enumerate(summary_items):
        if idx < args.start_index:
            continue
        serv_id = item.get("servId")
        if not serv_id or serv_id in done_ids:
            continue

        try:
            detail = fetch_detail(serv_id)
        except Exception as e:
            fail_count += 1
            print(f"[{idx + 1}/{total}] {serv_id} 최종 실패: {e} - 건너뜀")
            continue

        records.append({"servId": serv_id, "summary": item, "detail": detail})
        done_ids.add(serv_id)
        print(f"[{idx + 1}/{total}] {serv_id} 완료 (누적 {len(records)}건)")

        if len(records) % args.save_every == 0:
            save_output(records)

        time.sleep(SLEEP_SEC)

    save_output(records)
    print(f"완료. 총 {len(records)}건 저장 -> {OUTPUT_FILE} (실패 {fail_count}건)")


if __name__ == "__main__":
    main()
