import json

from app.core.settings import settings


class PolicyLoaderService:
    """
    정책 전체 데이터를 로드/보관합니다.
    무거운 리소스이므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    (추후 S3 등 다른 소스로 교체 시 이 클래스만 바꾸면 됩니다.)
    """

    def __init__(self):
        with open(settings.policy_json_path, encoding="utf-8") as f:
            self.policies: list[dict] = json.load(f)
        self._by_plcyno: dict[str, dict] = {
            str(p.get("plcyNo")): p for p in self.policies if p.get("plcyNo") is not None
        }

    def get_policies(self) -> list[dict]:
        return self.policies

    def get_policy_by_plcyno(self, plcy_no: str) -> dict | None:
        return self._by_plcyno.get(str(plcy_no))
