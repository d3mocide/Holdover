# Waterbody pins: review list

Generated 2026-10-18 from `app/seed.py`. Coordinates marked Verified were matched to a same-named lake, pond or reservoir in the OpenStreetMap data inside the basemap (`scripts/check_coords.py`); Snapped means the nearest point on the same-named river or creek line. **This is a cross-check against OSM, not a field survey**: OSM label points sit inside the water but not necessarily where you fish.

Fix or place any pin without a code change. It needs an admin session (there is no token any more), so sign in with a cookie jar first:

    curl -c jar -X POST localhost:8010/api/auth/login -H 'X-Holdover: 1' -H 'content-type: application/json' \
      -d '{"username": "YOU", "password": "..."}'
    curl -b jar -X POST localhost:8010/api/admin/waterbodies/<id>/coords -H 'X-Holdover: 1' -H 'content-type: application/json' \
      -d '{"lat": 44.0, "lon": -123.0}'      # {"lat": null, "lon": null} removes the pin

`GET /api/waterbodies` lists the ids (no sign-in needed). The seed only corrects a row that still holds its original hand-entered value, so a pin you set this way is never overwritten.

| Status | Waterbody | Kind | Lat | Lon |
| --- | --- | --- | --- | --- |
| NO PIN | Haldeman Pond | pond |  |  |
| NO PIN | Hartman Pond (Wahkeena Lake) | pond |  |  |
| NO PIN | Huddleston Pond (Hampton Pond) | pond |  |  |
| NO PIN | Salmonberry Lake | lake |  |  |
| NO PIN | Silver Creek Reservoir | reservoir |  |  |
| NO PIN | Small Fry Lake | lake |  |  |
| NO PIN | Sunnyside Park Pond | pond |  |  |
| Likely: check | Bethany Pond | pond | 45.5569 | -122.8719 |
| Likely: check | Freeway Lakes, East | lake | 44.5908 | -123.0653 |
| Likely: check | Salish Pond, West | pond | 45.5307 | -122.4448 |
| Likely: check | Smith River Reservoir | reservoir | 44.3202 | -122.0463 |
| Unverified (hand-entered) | Alton Baker Canal | river | 44.0535 | -123.0650 |
| Unverified (hand-entered) | Clear Lake (McKenzie) | lake | 44.3690 | -121.9920 |
| Unverified (hand-entered) | EE Wilson Pond | pond | 44.7200 | -123.2300 |
| Unverified (hand-entered) | Estacada Lake | lake | 45.2910 | -122.3300 |
| Unverified (hand-entered) | Junction City Pond | pond | 44.2200 | -123.2000 |
| Unverified (hand-entered) | Mt Hood Pond (MHCC campus) | pond | 45.5230 | -122.4430 |
| Unverified (hand-entered) | Progress Lake | lake | 45.4560 | -122.7950 |
| Unverified (hand-entered) | Roaring River Park Pond | pond | 44.5930 | -122.7470 |
| Unverified (hand-entered) | Row River Nature Park (Cottage Grove Pond) | pond | 43.7900 | -123.0440 |
| Unverified (hand-entered) | Sheridan Pond | pond | 45.0990 | -123.3980 |
| Unverified (hand-entered) | St Louis Ponds | pond | 45.1590 | -122.9860 |
| Unverified (hand-entered) | Trojan Recreation Lake | lake | 46.0320 | -122.8870 |
| Snapped to channel | Blue River | river | 44.1689 | -122.3305 |
| Snapped to channel | Breitenbush River | river | 44.7582 | -122.1183 |
| Snapped to channel | Fall Creek (Willamette R) | creek | 43.9459 | -122.7583 |
| Snapped to channel | McKenzie River (above Leaburg Dam) | river | 44.1319 | -122.4997 |
| Snapped to channel | McKenzie River (below Leaburg Dam) | river | 44.0609 | -122.8065 |
| Snapped to channel | Quartzville Creek | creek | 44.5480 | -122.4311 |
| Snapped to channel | Salmon Creek | creek | 43.7524 | -122.4016 |
| Snapped to channel | Santiam River, North Fork | river | 44.7842 | -122.6083 |
| Snapped to channel | Willamette River, Coast Fork | river | 43.8144 | -123.0446 |
| Verified (OSM name match) | Benson Lake | lake | 45.5776 | -122.1239 |
| Verified (OSM name match) | Blue Lake | lake | 45.5539 | -122.4478 |
| Verified (OSM name match) | Blue River Reservoir | reservoir | 44.1883 | -122.2658 |
| Verified (OSM name match) | Canby Pond | pond | 45.2529 | -122.7043 |
| Verified (OSM name match) | Carmen Reservoir | reservoir | 44.3400 | -122.0038 |
| Verified (OSM name match) | Commonwealth Lake | lake | 45.5119 | -122.8080 |
| Verified (OSM name match) | Cottage Grove Reservoir | reservoir | 43.6971 | -123.0708 |
| Verified (OSM name match) | Detroit Reservoir | reservoir | 44.7113 | -122.1819 |
| Verified (OSM name match) | Dexter Reservoir | reservoir | 43.9162 | -122.7988 |
| Verified (OSM name match) | Dorena Reservoir | reservoir | 43.7704 | -122.9151 |
| Verified (OSM name match) | Dorman Pond | pond | 45.6128 | -123.2457 |
| Verified (OSM name match) | Fall Creek Reservoir | reservoir | 43.9499 | -122.7422 |
| Verified (OSM name match) | Faraday Lake | lake | 45.2627 | -122.3068 |
| Verified (OSM name match) | Foster Reservoir | reservoir | 44.4185 | -122.6388 |
| Verified (OSM name match) | Green Peter Reservoir | reservoir | 44.4897 | -122.4155 |
| Verified (OSM name match) | Harriet Lake | lake | 45.0738 | -121.9619 |
| Verified (OSM name match) | Henry Hagg Lake | lake | 45.4865 | -123.2208 |
| Verified (OSM name match) | Hills Creek Reservoir | reservoir | 43.6882 | -122.4521 |
| Verified (OSM name match) | Leaburg Lake | lake | 44.1414 | -122.5949 |
| Verified (OSM name match) | North Fork Reservoir | reservoir | 45.2330 | -122.2558 |
| Verified (OSM name match) | Timber Linn Lake | lake | 44.6380 | -123.0554 |
| Verified (OSM name match) | Timothy Lake | lake | 45.1262 | -121.7884 |
| Verified (OSM name match) | Trillium Lake | lake | 45.2699 | -121.7394 |
| Verified (OSM name match) | Turner Lake | lake | 44.8584 | -122.9559 |
| Verified (OSM name match) | Walter Wirth Lake | lake | 44.9095 | -122.9891 |
| Verified (OSM name match) | Waverly Lake | lake | 44.6405 | -123.0697 |

Counts: NO PIN 7, Likely: check 4, Unverified (hand-entered) 12, Snapped to channel 9, Verified (OSM name match) 26

## Still needs you

- **No pin (7):** the OSM data has no usable match. Most are small ponds named by a park or by an old name (Hampton Pond, Wahkeena Lake). Find each on a map and set it with the command above.
- **Likely (4):** the OSM name differs from ODFW's label, so confirm it is the same water.
- **Unverified (12):** no OSM match to check against. Most are small ponds, plus the Alton Baker Canal.
