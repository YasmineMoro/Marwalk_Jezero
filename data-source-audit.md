# Scientific source audit — 15 November 2026

The 120 release files were checked against their SHA-256 manifest. Bounded HTTP requests, CORS headers, response codes and checksums are recorded in runtime/network-audit.json and runtime/source-checks/. A 206 response validates a ranged request, not a complete import.

Full product metadata are exposed in runtime/datasets.json and /api/v1/datasets. Native raster properties are recorded in runtime/raster-audit.json.

| Product | Integration | Resolution / scale | Verified result |
|---|---|---|---|
| HiRISE | VERIFIED_USED | 0.25 m nominal mosaic; delivered cache ~1.2 m; display 2 m | Offline source reprojected to PLACES; registration residual unknown |
| CTX | VERIFIED_USED | 6 m nominal mosaic; delivered cache ~10 m; display resampled 2 m | Offline source reprojected to PLACES; registration residual unknown |
| PLACES DEM | VERIFIED_USED | native 1 m; conservative routing grid 5 m | No resampling of native elevations in supplied clip; source crop provenance supplied by pack |
| SIM3464 | VERIFIED_USED | 1:75,000 | 1304 authoritative polygons; transformed/clipped to five ROI polygons; unregistered |
| CTX DEM catalog | VERIFIED_NOT_USED | 20 m | Official download link identified (~87 MB); local routing instead uses PLACES 1 m |
| HiRISE DTM candidate | VERIFIED_NOT_USED | 1 m nominal | Catalog checked, 381 MB DTM not downloaded; not equated to PLACES by identity |
| Murray DEM | UNAVAILABLE | 1 m per requested catalog; not verified here | TLS certificate verification failed; no bypass |
| CRISM | VERIFIED_NOT_USED | 18 m class mapping | Core ZIP downloaded, published MD5 matched. All three class rasters: ZERO valid pixels in ROI. No local mineral layer. |
| Mastcam-Z figures | VERIFIED_USED | Image figures; not georeferenced raster | Three figures preserved with legends, instrument/sols/sequences in config/site-image-metadata.json |
| MEDA | VERIFIED_USED | historical time series at rover | Pressure only: XML confirms pascal; 50,926 valid samples, 729.2–755.4 Pa. Humidity absent; questionable uncertainty unit excluded; TIRS not converted to temperature. Not current ROI weather. |
| EVA scenario | SIMULATED | 5 m conservative graph; every edge and profile checked on native 1 m DEM | Base, walking law, speed, stops, reserve, visibility and events are demonstration hypotheses. User notes are unverified. |

## Selected area

The PLACES DEM rectangle is within the supplied HiRISE/CTX coverage. All 1,560,000 native cells are valid. Five original USGS polygons intersect this area. All three published sample sites are within coverage. Reprojection was checked; fine registration was not independently established. The human base is a simulation assumption.

## Specific checks

WMTS capabilities: default style, default028mm matrix set, PNG; HiRISE levels0–17 and CTX0–13. The published double slash in ResourceURL is preserved. Tested tiles returned image/png and Access-Control-Allow-Origin: *. The service uses Mars geographic coordinates, not terrestrial Web Mercator. Nominal source resolution differs from cached image resolution.

CRISM: the 1.3 MB core archive was downloaded and its published MD5 5d923ebaf76804a184b4a3a1911e5214 matched. The three class maps, nominally18m with NoData0, have zero valid pixels in the selected area despite overlapping rectangular bounds. Evidence: runtime/crism-coverage.json. No replacement mineral map was invented.

USGS: the local archive is349336873bytes, pamphlet728435bytes and map36406378bytes. Original polygons contain1304 features versus1308 in a web export, so OBJECTID joins are excluded. Unit descriptions are joined by name and interpreted regionally. SIM3464 is unregistered with a possible100–200m offset and is excluded from fine routing.

Catalogue creation dates and the PLACES label observation window are not individual orbital acquisition dates. Unknowns remain explicit. No real-time data or RGB-derived elevations are claimed.
