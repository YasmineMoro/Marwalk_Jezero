# Executed validation

## Automated checks

The English/branding update passes **21 tests**, including legacy label presentation without changing personal notes, English scientific summaries, metadata and MEDA warnings. The final run completed in 18.13 seconds with one pre-existing Starlette/TestClient deprecation warning. Machine report: docs/test-results.xml.

The suite covers analytic terrain, NoData, diagonal corners, native spikes between graph nodes, bounds, impossible constraints, independently recomputed metrics, walking times, return/reserve, deduplication, exact stop order, events, timeline, migrations/persistence, Mars/Three/SVGcoordinates, native sampling, API adapters, MEDA/XML, photo rejection, retained notes and coordinate-labelled exports.

TypeScript and Vite build succeed. The3Dmodule loads on demand and remains approximately537kBminified/136kBgzip. Vite reports a chunk-size warning, without build failure. Versions remain locked.

The initial pack verification checked120files by SHA-256. Scientific originals remain immutable; English presentation data are separate.

## Reproducible HTTP demonstration

python scripts/demo.py exercises Amalik, a Skinner Ridge detour, observation,20%progress, slowdown, delay, explicit blockage handling and completion. Exact results are in the generatedJSON/CSVfiles. Model:mars-grid-2.1-native-edges; DEM data version:70dbfd4583136f8f.

Initial measured route results:
|Criterion|Surface distance|Walking+observation|Margin after20min reserve|
|---|---:|---:|---:|
|Distance|1012.456m|42.613min|57.387min|
|Time|1018.259m|42.512min|57.488min|
|Slope cost|1035.302m|44.218min|55.782min|

Skinner Ridge insertion adds200.969m,7.698minwalking and10minobservation, leaving39.790minmargin. Preview/save geometry equality is asserted. A blocked cell can produce no path; the demonstration explicitly removes the simulated constraint instead of inventing a fallback.

Earlier local comparison HTTP timings were1904.4mscold,110.6msand63.2mswarm. Earlier3Dinitialization measured147.7ms and data loading119.1mswith caches. These are observations, not guaranteed performance.

## Browser validation

The dedicated-page version was checked at1440×1000and390×844. Mission columns, science profiles/detours, notebook save/reload, pause/resume, MEDA, sources,2D/3Dtoggle and zoom/recenter were exercised. Mobile document width was390pxwithout horizontal overflow.

The English/branding pass checked navigation, mission forms, translated site content/captions, MEDA warnings, source labels, both loaded header images and team credit. At 390 px the document width remains 390 px, with a 96 px header and navigation directly beneath it. No browser console errors were recorded in the final check. Screenshots: english-branding-desktop.jpg and english-branding-mobile.jpg.

The English HTTP demonstration completed successfully. Current comparison timings were 5673.4 ms for the first request, then 181.4 ms and 196.7 ms, under the local test workload. The model and route metrics are unchanged. The final source check confirms all 120 scientific release files remain intact.

Earlier source-network checks verified official Mars Trek/USGS/HiRISE/CTX/CRISM endpoints, WMTS capabilities/CORS, cachePNGand9/9HiRISElevel17tiles. Evidence:runtime/network-audit.json, runtime/crism-coverage.json and docs/wmts-browser-check.txt. These are historical checks, not live-health claims for every launch.

Browser checks are assisted manual QA, not a standaloneE2Esuite. No operational navigation, physical-phone or comprehensiveWCAGcertification is claimed.
