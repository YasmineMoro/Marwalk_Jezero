# Feature status

Real source products, computed results and simulation assumptions are kept distinct. Completion never means NASA certification.

| Feature | Working implementation | Scientific / simulation limit |
|---|---|---|
| Local application | React/TypeScript, FastAPI, SQLite, one launch command | Local prototype, no public deployment |
| Navigation | Dedicated Map, Mission, Science, Exploration, Notebook, Environment and Sources pages | Shared state and saved missions retained |
| English and branding | English interface, site summaries, errors, report labels and documentation; team credit and supplied logos | Original source files and personal notes preserved |
| Source import |120checksums, rasters/GPKG/XML, reproducible scripts | Full reconstruction without supplied pack not automated |
|2D map | Zoom/pan/pinch, recenter, markers and layers | Local Mars metric extent |
|3D terrain |62400real-DEM vertices, orbit controls, raycasting, alternative-viewer style |5m display,1×default, graphical lighting |
| Imagery | Real local HiRISE/CTX and PLACES texture | Delivered-cache resolution differs from nominal mosaic |
| WMTS | Optional2D network/cache using official capabilities | Historical level17tile test; not a3D streaming layer |
| Geology | Original regional USGS polygons and descriptions | Unregistered100–200m; excluded from route cost |
| CRISM | Coverage absence explicitly reported | No valid class pixels in inspected products |
| Scientific sites | Skinner Ridge, Wildcat Ridge, Amalik, source figures/captions | Sample positions, not human parking sites |
| Simulated spacecraft | Relocation and DEM checks | Hypothetical landing position |
| Routing | A*distance/time/slope criteria, independently calculated return | Conservative5m graph, native1m edges; experimental |
| Metrics | Surface distances, elevation profile, ascent/descent, slopes and margin | Walking law is a demonstration assumption |
| Budget | Return, observations and reserve included; incompatible launch blocked | No certified human autonomy |
| Detours | Real inserted-site routing and before/after costs | Only the three documented sites |
| Playback | Start/pause/resume/reset, timed stops and direct return | Simulated position and acceleration |
| Events | Slowdown, delay and manual cell blockage | Explicit artificial constraints |
| Notebook | Chosen point, note/category/UTC/photo, markers and reload | Unverified user observations |
| MEDA | XML-validated historical pressure graph | Sol29rover measurement; no current regional weather |
| Visibility | Uniform speed multiplier | Artificial scenario, no weather obstacle map |
| API | Typed/api/v1contract and historical aliases | ordered_site_ids extension documented |
| Persistence | Migration2, source working copy, restored saved missions | Local documentary SQLite |
| Exports | JSON, coordinate-labelled CSV and printable briefing | Local Mars coordinates, not terrestrial GeoJSON |
| Responsive | Desktop1440and mobile390browser checks | Emulation, not every physical device |
| Validation |21tests, TypeScript/build and assisted browser checks | No operational safety certification |

Detailed validation and remaining limitations are recorded separately.
