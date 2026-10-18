"""Fire geometry for the map layer: ODF danger zones and NIFC active perimeters, from the newest stored responses."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.sources import nifc, odf_fire

router = APIRouter()


@router.get("/fire/map")
def fire_map(session: Session = Depends(get_session)):
    z, f = odf_fire.map_features(session), nifc.map_features(session)
    return {"zones": {"type": "FeatureCollection", "features": z["features"]}, "zones_as_of": z["as_of"],
            "fires": {"type": "FeatureCollection", "features": f["features"]}, "fires_as_of": f["as_of"]}
