# Local architecture

The existing application, scientific import, engine, API, missions and audits are retained. No public deployment is involved.

- frontend/Header.tsx and Navigation.tsx: team branding, supplied logos and accessible page navigation.
- frontend/App.tsx: shared mission state, route selection, site information, observations and playback.
- Map2D.tsx: metric SVG and pointer/touch interactions. Terrain3D.tsx: DEM mesh, textures, orbit controls and raycasting.
- coordinates.ts: explicit scientific/scene axes. client.ts: typed API calls and canonical mission signatures. labels.ts: English common labels.
- design.css/workspace.css: dark visual theme, dedicated pages, desktop rail and mobile navigation.
- backend/engine.py: conservative graph, native-edge validation, criteria and metrics. simulation.py: timeline. environment.py: MEDA pressure/XML validation.
- backend/app.py: mission operations, validation, reports, uploads and WMTS. v1.py: pack-contract adapters and aliases.
- presentation.py: English presentation of known legacy application labels while preserving user note text.
- backend/settings.py: portable paths and restricted .env keys. bootstrap.py: local dependency path and loopback server.
- runtime/: derived products, cache and working data. Original pack files remain immutable.

## API

Generated contract: config/openapi.json; interactive documentation:/docs.

Pack endpoints: GET/api/v1/datasets, GET/sites, GET/terrain/sample?x=…&y=…, POST/routes/compare. Coordinates are local Mars metres. Scenario speed in m/s is adapted to the engine in m/min. ordered_site_ids preserves an exact stop order, including insertion on the return leg; its set must match the destination and via sites.

Mission operations: GET/POST/api/v1/missions; GET/PUT/{id}; POST/{id}/progress, /events, /reset, /observations; PUT/{id}/observations/{observation_id}/photo with raw image bytes; GET/{id}/report?format=json|csv. Additional resources include environment/meda, history, terrain/display and scientific opportunities. Historical/api paths remain available.

Pydantic rejects non-finite values, unknown fields, invalid IDs and constraints. Failures never return a decorative replacement route. SQL statements are parameterized and foreign keys enabled.

Photos accept JPEG/PNG/WebP up to5MB and20megapixels, are decoded and re-encoded as JPEG with an internal UUID, and remain local.

## Persistence

The source SQLite database is opened read-only to create runtime/science-working.sqlite. Existing user missions remain in runtime/missions.sqlite, using evas(id,body). Documents include mission parameters, route, versions, progress, history and observations.

backend/schema.sql initializes storage; migrations/002.sql records schema version2 and coordinate conventions. Old routes are recomputed if the model/data version differs, retaining history. Known legacy labels are presented in English. Personal note text is not translated.

A localStorage pointer restores the latest saved mission; clearing it does not delete server notes. Mission listings omit full profiles and history to stay lightweight.

## Execution

Dependencies are fixed in requirements.lock and pnpm-lock.yaml. Synchronous scientific computation uses the FastAPI thread pool. Native arrays load once; segment caching reuses stable work. Client generations and cancellation prevent obsolete results replacing newer requests.

Three.js loads on demand. Its display grid is5m while native computation remains server-side at1m. Large PDFs and regional rasters do not load at startup. Optional2D WMTS uses official Mars capabilities and cache;3D uses local textures.

The alternative viewer supplied by the team provides the camera, fog, lighting and pin style. Existing native positioning, UVs, interactions and routing are retained. Hidden map sizes are ignored so camera aspect stays valid.

This is a local prototype without multiuser authentication or automated backups. Preserve missions.sqlite and uploads; public exposure requires additional access and workload controls.
