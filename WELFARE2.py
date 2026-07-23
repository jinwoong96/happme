# 복지로 중앙부처 복지서비스 목록 API(NationalWelfarelistV001)를 호출해
# National_welfare_data.json으로 저장한다. fetch_national_welfare_detail.py가
# 이 목록을 읽어 servId별 상세정보를 이어서 수집한다.

import requests
import os
import json
import xmltodict
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("WELFARE_API_KEY")

url = 'https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfarelistV001'
params = {
    "serviceKey": api_key,
    "callTp": "L",
    "pageNo": 1,
    "numOfRows": 300,
    "srchKeyCode": "001",
    "lifeArray": "004",
}

# API 요청 (XML 응답)
response = requests.get(url, params=params)

print("Status Code:", response.status_code)

# XML -> Python dict 변환
data = xmltodict.parse(response.text)

# JSON 파일 저장
with open("National_welfare_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Nationalwelfare_data.json 저장 완료!")