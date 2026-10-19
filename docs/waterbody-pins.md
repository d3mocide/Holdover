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


## Central zone (added 2026-10-18)

From ODFW's Central zone stocking schedule (36 labels, 35 waterbodies) matched to same-named OpenStreetMap features in the basemap, narrowed to each label's ODFW district (`scripts/propose_zone.py`). Nothing was placed from memory. 13 waters have no pin and are listed under "no map location yet" until you place them (same `POST /api/admin/waterbodies/<id>/coords` as above). Pins marked Likely deserve a look.

| Status | Waterbody | Kind | Lat | Lon | How |
| --- | --- | --- | --- | --- | --- |
| NO PIN | Baker Pond | pond |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Bikini Pond | pond |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Century Gravel Pond | pond |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Cottonwood Pit | pond |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | East Lake | lake |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Fall River | river |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Metolius Pond | pond |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Middle Fork Pond (Hood River) | pond |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Prineville Fishing Pond | pond |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Redmond Fireman South Pond | pond |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Rock Creek Reservoir | reservoir |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Sprague Pit Pond | pond |  |  | no same-named OSM feature in the label's ODFW district |
| NO PIN | Three Creeks Lake | lake |  |  | no same-named OSM feature in the label's ODFW district |
| Likely: check | Antelope Flat Reservoir | reservoir | 44.0057 | -120.3800 | two same-named OSM points about 6 km apart; took the one on the water layer |
| Likely: check | Frog Lake | lake | 45.2187 | -121.6948 | three OSM 'Frog Lake' features in the district; took the one beside Clear Lake (Wasco) |
| Likely: check | Lava Lake | lake | 43.9211 | -121.7730 | two OSM 'Lava Lake' features; took the Cascade Lakes one (ODFW's Bend district) |
| Likely: check | Pine Nursery Pond | pond | 44.0911 | -121.2681 | OSM 'Pine Nursery Park' (the pond is in the park) |
| Likely: check | Shevlin Pond | pond | 44.0886 | -121.3678 | OSM 'Shevlin Park' (the pond is in the park) |
| Likely: check | Smock Prairie Reservoir | reservoir | 45.1503 | -121.3765 | OSM 'Smock Reservoir', 1 km from 'Smock Prairie' |
| Verified (OSM name match) | Clear Lake (Wasco) | lake | 45.1826 | -121.7061 | OSM 'Clear Lake', Mt Hood side |
| Verified (OSM name match) | Cultus Lake | lake | 43.8380 | -121.8625 | OSM 'Cultus Lake' |
| Verified (OSM name match) | Deer Lake | lake | 43.8199 | -121.8939 | OSM 'Deer Lake', Deschutes side |
| Verified (OSM name match) | Devils Lake | lake | 44.0349 | -121.7622 | two OSM 'Devils Lake' features; took the Deschutes one on the Cascade Lakes side |
| Verified (OSM name match) | Hosmer Lake | lake | 43.9676 | -121.7818 | OSM 'Hosmer Lake' |
| Verified (OSM name match) | Kingsley Reservoir (Upper) | reservoir | 45.6378 | -121.6786 | OSM 'Kingsley Reservoir' (the label says Upper) |
| Verified (OSM name match) | Laurance Lake | lake | 45.4593 | -121.6659 | OSM 'Laurance Lake' |
| Verified (OSM name match) | Lost Lake | lake | 45.4893 | -121.8236 | OSM 'Lost Lake', Hood River County |
| Verified (OSM name match) | Ochoco Reservoir | reservoir | 44.3037 | -120.6967 | OSM 'Ochoco Reservoir' |
| Verified (OSM name match) | Olallie Lake | lake | 44.8069 | -121.7874 | OSM 'Olallie Lake' |
| Verified (OSM name match) | Paulina Lake | lake | 43.7194 | -121.2599 | OSM 'Paulina Lake' |
| Verified (OSM name match) | Pine Hollow Reservoir | reservoir | 45.2477 | -121.2944 | OSM 'Pine Hollow Reservoir' |
| Verified (OSM name match) | Taylor Lake | lake | 45.6427 | -121.2071 | OSM 'Taylor Lake' |
| Verified (OSM name match) | Twin Lake, North | lake | 43.7276 | -121.7665 | OSM 'North Twin Lake' |
| Verified (OSM name match) | Twin Lake, South | lake | 43.7140 | -121.7663 | OSM 'South Twin Lake' |
| Verified (OSM name match) | Walton Lake | lake | 44.4355 | -120.3355 | OSM 'Walton Lake' |


## Northwest zone (added 2026-10-18)

From ODFW's Northwest zone stocking schedule (33 labels, 33 waterbodies), same method as Central (`scripts/propose_zone.py`). 11 waters have no pin; the 9 marked Likely are same-named points of interest or a choice between candidates.

| Status | Waterbody | Kind | Lat | Lon | How |
| --- | --- | --- | --- | --- | --- |
| NO PIN | Big Creek Reservoir | reservoir |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Buck Lake | lake |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Devil South Lake | lake |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Dune Lake | lake |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Loren South Pond | pond |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Nedonna Pond | pond |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Perkins Lake | lake |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Scout Lake | lake |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Spring Lake | lake |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Sunset Lake (North Coast Range) | lake |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| NO PIN | Thissel Pond | pond |  |  | no same-named OSM feature in the label's district (or two far-apart candidates) |
| Likely: check | Alder Lake | lake | 44.0705 | -124.1039 | OSM point 'Alder Lake' (a point of interest, not a polygon), Newport district |
| Likely: check | Carter Lake | lake | 43.8527 | -124.1472 | OSM point 'Carter Lake' (point of interest), Newport district |
| Likely: check | Elbow Lake | lake | 43.7868 | -124.1490 | OSM point 'Elbow Lake' (point of interest), Newport district |
| Likely: check | Hebo Lake | lake | 45.2310 | -123.7959 | OSM point 'Hebo Lake' (the town 'Hebo' is 5 km away; took the lake) |
| Likely: check | Lost Lake (Northwest) | lake | 45.8243 | -123.5789 | OSM point 'Lost Lake' in the Tillamook district; there is another Lost Lake in Central |
| Likely: check | North Lake | lake | 45.2157 | -123.7204 | OSM point 'North Lake'; the schedule gives no district, this one is beside South Lake and Hebo Lake |
| Likely: check | South Lake | lake | 45.2017 | -123.7216 | OSM point 'South Lake' beside North Lake and Hebo Lake (another 'South Lake' exists 45 km east) |
| Likely: check | Tahoe Lake | lake | 45.3497 | -123.6013 | OSM point 'Lake Tahoe' in the Tillamook district (the name matches the famous one, so check) |
| Likely: check | Town Lake | lake | 45.2247 | -123.9559 | OSM point 'Town Lake', Tillamook district |
| Verified (OSM name match) | Cape Meares Lake | lake | 45.5087 | -123.9481 | OSM water 'Cape Meares Lake' |
| Verified (OSM name match) | Cleawox Lake | lake | 43.9390 | -124.1184 | OSM water 'Cleawox Lake' |
| Verified (OSM name match) | Coffenbury Lake | lake | 46.1696 | -123.9602 | OSM water 'Coffenbury Lake' |
| Verified (OSM name match) | Cullaby Lake | lake | 46.0853 | -123.9044 | OSM water 'Cullaby Lake' |
| Verified (OSM name match) | Eckman Lake | lake | 44.4121 | -124.0346 | OSM water 'Eckman Lake' |
| Verified (OSM name match) | Lytle Lake | lake | 45.6235 | -123.9400 | OSM water 'Lake Lytle' |
| Verified (OSM name match) | Mercer Lake | lake | 44.0552 | -124.0560 | OSM water 'Mercer Lake' |
| Verified (OSM name match) | Munsel Lake | lake | 44.0086 | -124.0812 | OSM water 'Munsel Lake' |
| Verified (OSM name match) | Olalla Creek Reservoir | reservoir | 44.6867 | -123.9229 | OSM water 'Olalla Reservoir' |
| Verified (OSM name match) | Siltcoos Lake | lake | 43.8723 | -124.0938 | OSM water 'Siltcoos Lake' |
| Verified (OSM name match) | Sutton Lake | lake | 44.0591 | -124.0901 | OSM water 'Sutton Lake' |
| Verified (OSM name match) | Vernonia Lake | lake | 45.8548 | -123.1737 | OSM water 'Vernonia Lake' |
| Verified (OSM name match) | Woahink Lake | lake | 43.9183 | -124.0956 | OSM water 'Woahink Lake' |
