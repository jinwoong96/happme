from pydantic import BaseModel


class LocalProgramItem(BaseModel):
    id: int
    svcnm: str
    placenm: str | None = None
    areanm: str | None = None
    majorCategory: str | None = None
    minorCategory: str | None = None
    svcstatnm: str | None = None
    rcptStartDate: str | None = None
    rcptEndDate: str | None = None
    svcStartDate: str | None = None
    svcEndDate: str | None = None
    applyUrl: str | None = None
    lat: float
    lng: float
    distanceKm: float | None = None


class LocalProgramSearchResponse(BaseModel):
    count: int
    results: list[LocalProgramItem]
