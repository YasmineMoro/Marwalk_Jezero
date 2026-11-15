# MarsWalk by KAWKAB ZOMORODA

A local Jezero exploration application with a React/TypeScript interface, 2D map, real DEM-based Three.js terrain, FastAPI routing, and persistent SQLite missions and observations. The covered area is 1.2 × 1.3 km. No private API key or paid account is required.

## Start here — project demonstration

**[View our seven-slide project demo](submission/output/MarsWalk_KAWKAB_ZOMORODA_Demo.pdf)**

Explore how MarsWalk uses real Mars observations to help astronauts plan and rehearse a simulated science mission in Jezero Crater. Compare routes, evaluate scientific detours, rehearse disruptions, and save observations. The human mission is simulated and is not validated for operational astronaut use.

This repository contains the application source code. It does not host a running web service. The PDF can be viewed without installing the application.

![MarsWalk desktop interface with 3D terrain](docs/english-branding-desktop.jpg)

### Team

**KAWKAB ZOMORODA** — HIBA BOUADDI · YASMINE MORO · SALMA KERRACHI · OUMAIMA RAKKAS · YASSMINE AALLA

### Scientific data required for installation

The original **MarsWalk_Pack_Developpement_v1.zip** is required to reproduce the local application. It is approximately 505 MB and is distributed separately from this source repository. Before submitting, the repository owner must add a public download link to that original archive here. A fresh source download alone does not contain the scientific pack.

### Development assistance

AI-assisted coding tools supported implementation, debugging, documentation, and presentation preparation. Scientific claims should be checked against the attributed source products and the documented audit. AI output is not a scientific data source. Mission assumptions and unresolved limitations are identified in this repository.

## Run the prepared project

In PowerShell, from the project folder:

```powershell
python bootstrap.py
```

Open [MarsWalk](http://127.0.0.1:8000) or [API documentation](http://127.0.0.1:8000/docs). Stop with Ctrl+C. After an update, restart the Python server and refresh the browser. The server listens only on the local loopback interface.

## Reproducible installation

Python3.13, Node24 and pnpm11 were used. Rasterio/PyProj Windows wheels provide GDAL/PROJ without a separate system installation. Install pnpm or npm before building the frontend if neither is available.

```powershell
python -m pip install --target .deps -r requirements.lock
python scripts/extract_pack.py "PATH_TO_ARCHIVE/MarsWalk_Pack_Developpement_v1.zip"
python scripts/import_data.py
python scripts/build_catalog.py
python scripts/frontend.py install
python scripts/frontend.py build
python bootstrap.py
```

The archive is extracted under data/MarsWalk_Data_Release and its120 file checksums are verified. For another pack location, copy .env.example to .env and set MARSWALK_DATA. Relative paths resolve from the project root. MARSWALK_DB and MARSWALK_RUNTIME are also configurable. Prepare the destination folder before importing.

Installation requires Internet access. The main experience works offline after preparation. Optional2D WMTS detail uses network/cache. The browser never downloads the full505MB scientific pack. Stop Python before updating its local wheels on Windows.

## Navigation

- **Map:** main3D terrain view,2D toggle, layers and route summary.
- **Mission:** simulated base, destination, time budget, constraints, route comparisons and saved missions.
- **Science:** documented sites and calculated detours.
- **Exploration:** playback, elevation profile, pause/resume/reset and return.
- **Notebook:** manually located observations, optional photos and exports.
- **Environment:** historical MEDA pressure, separated from simulated conditions.
- **Sources:** provenance, resolution and limitations.

For the demonstration, choose Amalik,120min available,20min reserve,35m/min nominal speed,10min observation,30° slope limit and slope weight8. Evaluate Skinner Ridge before accepting the detour. These are demonstration assumptions, not certified human EVA parameters.

The3D presentation adapts the camera, fog, warm lighting and pins of the supplied alternative project while keeping the existing coordinates, routing and persistence. Vertical exaggeration defaults to1× and never changes scientific metrics. Lighting is graphical, not a dated solar model.

The header reads MarsWalk by KAWKAB ZOMORODA and displays the two supplied images. Branding does not change scientific data attribution. The interface, application-generated reports and documentation are in English. Original source files and personal note text are preserved.

## Verify and replay

```powershell
python scripts/run_tests.py
python scripts/frontend.py build
python scripts/demo.py
```

The HTTP demonstration requires a running server. Set MARSWALK_URL to another local API URL when testing on a separate port. It creates a new mission and writes docs/demo-results.json, docs/demo-report.json and docs/demo-observations.csv.

Keep runtime/missions.sqlite and runtime/uploads to preserve user work. runtime/science-working.sqlite is a separate copy of the immutable scientific database. Source code before the navigation changes is retained in backups/marswalk-before-yasmina-layout.zip; that archive excludes dependencies and scientific/user data.

Optional source checks: python scripts/audit_sources.py and python scripts/inspect_crism.py. The latter downloads only the small metadata/core archive and verifies its published MD5.

## Scientific status

HiRISE/CTX imagery, PLACES1m elevations, SIM3464 geology, site coordinates and Mastcam-Z figures are real source products. Routes, profiles and distances are calculated. The5m routing graph conservatively aggregates native constraints and checks every edge against the1m DEM.

The base, walking law, speed, reserve, visibility and events are simulation assumptions. SIM3464 may be offset by100–200m and is excluded from fine routing. The inspected CRISM maps have no valid class pixels in this area. MEDA shows historical rover pressure from sol29, never current regional weather. Human traversability is not validated.

See [feature status](docs/feature-status.md), [validation](docs/validation.md), [walking model](docs/models.md), [coordinates](docs/geospatial-reference.md), [architecture](docs/architecture.md), [source audit](docs/data-source-audit.md), [limitations](docs/limitations.md), [demonstration](docs/demo-script.md), [credits](docs/attributions.md) and [interface update](docs/interface-yasmina.md).
