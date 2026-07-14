import requests
import os
import json
import xmltodict
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("WELFARE_API_KEY")

url = 'https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist?serviceKey=' + api_key + '&lifeArray=004'

params = {
    "serviceKey": api_key,
    "pageNo": 1,
    "numOfRows": 2000
}

# API 요청 (XML 응답)
response = requests.get(url, params=params)

print("Status Code:", response.status_code)

# XML -> Python dict 변환
data = xmltodict.parse(response.text)

# JSON 파일 저장
with open("welfare_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("welfare_data.json 저장 완료!")