"""Small geometry helpers for GeoJSON polygons (WGS84 degrees)."""
from app.scoring import haversine_km


def rings(geometry: dict) -> list[list[list[float]]]:
    """Every ring (outer and inner) of a Polygon or MultiPolygon."""
    coords = geometry.get("coordinates") or []
    polys = [coords] if geometry.get("type") == "Polygon" else coords
    return [ring for poly in polys for ring in poly]


def contains(lat: float, lon: float, geometry: dict) -> bool:
    """Even-odd point-in-polygon over all rings, so holes toggle the result back."""
    inside = False
    for ring in rings(geometry):
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i][0], ring[i][1]
            x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
            if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def nearest_vertex_km(lat: float, lon: float, geometry: dict) -> float:
    """Distance to the closest polygon vertex. The services simplify geometry to a few tens of metres, so vertices
    are dense enough for a distance that is shown to the nearest kilometre."""
    return min((haversine_km(lat, lon, p[1], p[0]) for r in rings(geometry) for p in r), default=float("inf"))
