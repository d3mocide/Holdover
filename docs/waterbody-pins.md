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


## Southwest zone (added 2026-10-18)

43 waterbodies from ODFW's Southwest stocking schedule, same method as Central. 21 have no pin; 7 are marked Likely. Pins are matches to OpenStreetMap, not a field survey.

| Status | Waterbody | Kind | Lat | Lon | How |
| --- | --- | --- | --- | --- | --- |
| NO PIN | Burma Pond (L) | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Clearwater Bay | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Cooper Creek Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Empire Lake, Lower | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Expo Pond 1 (Rogue) | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Hemlock Lake (Hemlock Meadow Reservoir) | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Johnsons Mill Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Laird Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Lake in the Woods | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Libby Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Lost Creek Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Medco Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Plat I Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Powers Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Red Top Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Reinhart Park Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Rogue River (above Lost Creek) | river |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | SRU Lake (formerly USFS Lake) | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Spalding Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Weaver Road Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Willow Lake (formerly Willow Creek Reservoir) | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| Likely: check | Arizona Pond | pond | 42.6166 | -124.3953 | OSM point 'Arizona Pond' (point of interest) |
| Likely: check | Bluebill Lake | lake | 43.4471 | -124.2606 | OSM point 'Bluebill Lake' (point of interest) |
| Likely: check | Bradley Lake | lake | 43.0653 | -124.4272 | OSM point 'Bradley Lake' (point of interest) |
| Likely: check | Butterfield Lake | lake | 43.5202 | -124.2222 | OSM point 'Butterfield Lake' (point of interest) |
| Likely: check | Empire Lake, Upper | lake | 43.3960 | -124.2559 | OSM point 'Upper Empire Lake' (point of interest) |
| Likely: check | Fish Lake (Southwest) | lake | 42.3858 | -122.3350 | three OSM 'Fish Lake' features in the district; took the Jackson County one on the water layer |
| Likely: check | Lake Marie | lake | 43.6591 | -124.1946 | OSM point 'Lake Marie' (point of interest); another 'Marie Lake' exists in the Cascades |
| Verified (OSM name match) | Applegate Reservoir | reservoir | 42.0333 | -123.1456 | OSM water 'Applegate Lake' |
| Verified (OSM name match) | Ben Irving Reservoir | reservoir | 43.0461 | -123.5750 | OSM water 'Ben Irving Reservoir' |
| Verified (OSM name match) | Eel Lake | lake | 43.6147 | -124.1732 | OSM water 'Eel Lake' |
| Verified (OSM name match) | Emigrant Reservoir | reservoir | 42.1479 | -122.6155 | OSM water 'Emigrant Lake' (two points 1.4 km apart on the same lake; took the first) |
| Verified (OSM name match) | Floras Lake | lake | 42.8936 | -124.5043 | OSM water 'Floras Lake' |
| Verified (OSM name match) | Galesville Reservoir | reservoir | 42.8375 | -123.1581 | OSM water 'Galesville Reservoir' |
| Verified (OSM name match) | Garrison Lake | lake | 42.7534 | -124.5052 | OSM water 'Garrison Lake' |
| Verified (OSM name match) | Howard Prairie Reservoir | reservoir | 42.2367 | -122.4059 | OSM water 'Howard Prairie Lake' |
| Verified (OSM name match) | Hyatt Reservoir | reservoir | 42.1860 | -122.4488 | OSM water 'Hyatt Reservoir' |
| Verified (OSM name match) | Lake Selmac | lake | 42.2607 | -123.5780 | OSM water 'Lake Selmac' |
| Verified (OSM name match) | Lemolo Reservoir | reservoir | 43.3113 | -122.1801 | OSM water 'Lemolo Lake' |
| Verified (OSM name match) | Loon Lake | lake | 43.5872 | -123.8379 | two OSM 'Loon Lake' features; took the water-layer one in the Umpqua basin |
| Verified (OSM name match) | Saunders Lake | lake | 43.5347 | -124.2189 | OSM water 'Saunders Lake' |
| Verified (OSM name match) | Tenmile Lake, North | lake | 43.5960 | -124.1179 | OSM water 'North Tenmile Lake' |
| Verified (OSM name match) | Tenmile Lake, South | lake | 43.5596 | -124.1362 | OSM water 'South Tenmile Lake' |


## Northeast zone (added 2026-10-18)

49 waterbodies from ODFW's Northeast stocking schedule, same method as Central. 40 have no pin; 3 are marked Likely. Pins are matches to OpenStreetMap, not a field survey.

| Status | Waterbody | Kind | Lat | Lon | How |
| --- | --- | --- | --- | --- | --- |
| NO PIN | Aldrich Ponds | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Anson Wright Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Brandon South Pond (JD Screen Shop Pond) | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Cutsforth Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Hog Creek Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Holliday Park Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Honeymoon Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Hunter Pond (Starkey Forest Ponds) | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Kinney Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Ladd Peach Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Long Creek Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Lost Lake (Northeast) | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Luger Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Marr Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | McGraw Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | McNary Channel Ponds | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Morrow County OHV Park Pond 1 (Trout Lake) | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Morrow County OHV Park Pond 2 (Red Rock) | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Morrow County OHV Park Pond 3 (OBrien) | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Morrow County OHV Park Pond 4 (Wilson) | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Penland Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Roulet Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Rowe Creek Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Salt Creek Summit Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Seventh Street Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Tatone Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Teepee Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Trout Farm Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Twin Ponds | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Umapine Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Umatilla Forest Ponds, North | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Umatilla Forest Ponds, South | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Victor Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Walla Walla Forest Ponds, North | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Walla Walla Forest Ponds, South | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Wallowa Wildlife Pond (Weavers Pond) | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Weston Highway Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Wildcat Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Willow Creek | river |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Willow Creek Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| Likely: check | Bull Prairie Reservoir | reservoir | 44.9744 | -119.6632 | OSM point 'Bull Prairie Lake' (point of interest) |
| Likely: check | Grande Ronde Lake | lake | 44.9782 | -118.2437 | OSM point 'Grande Ronde Lake' (point of interest) |
| Likely: check | Hat Rock Pond | pond | 45.9170 | -119.1706 | OSM point 'Hat Rock' (the state park holds the pond) |
| Verified (OSM name match) | Fish Lake (Northeast) | lake | 45.0468 | -117.0924 | OSM water 'Fish Lake' in the La Grande district |
| Verified (OSM name match) | Jubilee Lake | lake | 45.8320 | -117.9602 | OSM water 'Jubilee Lake' |
| Verified (OSM name match) | Magone Lake | lake | 44.5489 | -118.9120 | OSM water 'Magone Lake' |
| Verified (OSM name match) | Morgan Lake | lake | 45.3015 | -118.1363 | OSM water 'Morgan Lake' |
| Verified (OSM name match) | Olive Lake | lake | 44.7820 | -118.6029 | two OSM 'Olive Lake' features; took the Grant County one on the water layer |
| Verified (OSM name match) | Wallowa Lake | lake | 45.3081 | -117.2075 | OSM water 'Wallowa Lake' |


## Southeast zone (added 2026-10-18)

36 waterbodies from ODFW's Southeast stocking schedule, same method as Central. 23 have no pin; 3 are marked Likely. Pins are matches to OpenStreetMap, not a field survey.

| Status | Waterbody | Kind | Lat | Lon | How |
| --- | --- | --- | --- | --- | --- |
| NO PIN | Anthony Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Balm Creek Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Becker Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Bully Creek Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Burns Gravel Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Campbell Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Deadhorse Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Drews Gap Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Fish Lake (Southeast) | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Haines Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Heart Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Highway 203 Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Holbrook Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Murray Reservoir (formerly Hardy Murray Reservoir) | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | North Powder Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Poison Creek Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Taylor Green Pond | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Thief Valley Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Thompson Valley Reservoir | reservoir |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Tipton Pond, North | pond |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Twin Lake (Southeast) | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Vee Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| NO PIN | Yellow Jacket Lake | lake |  |  | no same-named OSM feature in the label's district, or several far-apart candidates |
| Likely: check | Ana River | river | 42.9329 | -120.7797 | a point along the OSM line 'Ana River' (it is a short spring-fed river; check) |
| Likely: check | Miller Lake | lake | 43.2286 | -121.9574 | two OSM 'Miller Lake' features; took the Klamath County one on the water layer |
| Likely: check | Powder River | river | 44.7358 | -118.2040 | a point along the OSM line 'Powder River' in the La Grande district |
| Verified (OSM name match) | Ana Reservoir | reservoir | 42.9973 | -120.7575 | OSM water 'Ana Reservoir' |
| Verified (OSM name match) | Chickahominy Reservoir | reservoir | 43.5603 | -119.6316 | OSM water 'Chickahominy Reservoir' |
| Verified (OSM name match) | Delintment Lake | lake | 43.8925 | -119.6266 | OSM water 'Delintment Lake' |
| Verified (OSM name match) | Duncan Reservoir | reservoir | 43.0683 | -120.9459 | OSM water 'Duncan Reservoir' |
| Verified (OSM name match) | Fourmile Lake | lake | 42.4665 | -122.2526 | OSM water 'Fourmile Lake' |
| Verified (OSM name match) | Krumbo Reservoir | reservoir | 42.9550 | -118.8070 | OSM water 'Krumbo Reservoir' |
| Verified (OSM name match) | Lake of the Woods | lake | 42.3661 | -122.2146 | OSM water 'Lake of the Woods' |
| Verified (OSM name match) | Lofton Reservoir | reservoir | 42.2639 | -120.8184 | OSM water 'Lofton Reservoir' |
| Verified (OSM name match) | Phillips Reservoir | reservoir | 44.6776 | -118.0504 | OSM water 'Phillips Lake' |
| Verified (OSM name match) | Priday Reservoir | reservoir | 42.3389 | -119.8961 | OSM water 'Priday Reservoir' |
