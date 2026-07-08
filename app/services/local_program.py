import math
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.local_program import LocalProgramCrud
from app.db.models.local_program import LocalProgram
from app.db.scheme.local_program import LocalProgramItem, LocalProgramSearchResponse


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 좌표 사이의 직선거리(km) 계산"""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _fmt_date(value) -> str | None:
    return value.strftime("%Y-%m-%d") if value else None


def _to_item(row: LocalProgram, distance_km: float | None) -> LocalProgramItem:
    return LocalProgramItem(
        id=row.local_program_id,
        svcnm=row.svcnm,
        placenm=row.placenm,
        areanm=row.areanm,
        majorCategory=row.maxclassnm,
        minorCategory=row.minclassnm,
        svcstatnm=row.svcstatnm,
        rcptStartDate=_fmt_date(row.rcptbgndt),
        rcptEndDate=_fmt_date(row.rcptenddt),
        svcStartDate=_fmt_date(row.svcopnbgndt),
        svcEndDate=_fmt_date(row.svcopnenddt),
        applyUrl=row.svcurl,
        lat=float(row.latitude),
        lng=float(row.longitude),
        distanceKm=round(distance_km, 2) if distance_km is not None else None,
    )


class LocalProgramService:

    @staticmethod
    async def search_svc(
        db: AsyncSession,
        keyword: str,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        radius: Optional[float] = None,
    ) -> LocalProgramSearchResponse:
        rows = await LocalProgramCrud.search_by_keyword(db, keyword)

        items: list[LocalProgramItem] = []
        for row in rows:
            distance_km = None
            if lat is not None and lng is not None:
                distance_km = haversine(lat, lng, float(row.latitude), float(row.longitude))
                if radius is not None and distance_km > radius:
                    continue
            items.append(_to_item(row, distance_km))

        if lat is not None and lng is not None:
            items.sort(key=lambda i: i.distanceKm)

        return LocalProgramSearchResponse(count=len(items), results=items)
