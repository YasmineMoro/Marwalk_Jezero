# Coordinate reference

Body: Mars, sphere radius3396190m. The pack uses an equirectangular projection with standard parallel18.4663° and central meridian0°. This is neither terrestrial EPSG:4326 nor Web Mercator. The full WKT is in config/roi.json and geometric JSON exports.

Projected northwest exterior origin: (4351286,1094535)m.

x_local=x_projected−4351286; y_local=y_projected−1094535.

Scientific axes are x east, y north, z up, in metres. The DEM spans x0–1200m and y−1300–0m; routing enforces its explicit pixel-boundary rules.

SVG displays (x,−y). Three.js displays (x−600,z+2500,−y−650), with the second component vertical. Inverse functions are centralized in backend/coordinates.py and frontend/coordinates.ts. Terrain, texture, routes, markers and raycasting use the same mapping. Texture UVs are x/1200 and1+y/1300. Vertical exaggeration is visual only, default1×.

The lightweight display grid starts at native pixel centre(0.5,−0.5)m and advances5m, producing62400 real-DEM vertices. The separate conservative routing graph uses centres(2.5,−2.5) modulo5m and verifies every edge at1m. Elevation samples and profiles use native raster values. RGB imagery is never interpreted as altitude.

A/B/C identify Skinner Ridge/Wildcat Ridge/Amalik. The adapter retains the pack field conventions while exposing name, image_path and local position. English presentation summaries are separate from the immutable source files. Published sample positions are not validated human parking positions.

SIM3464 is reprojected and clipped from original polygons. Reprojection does not correct its100–200m registration offset. No arbitrary shift or mismatched web-export OBJECTID join is used.

Geometry exports explicitly identify local Mars metres, origin and WKT. They are not RFC7946 terrestrial GeoJSON. CSV fields include x_local_m/y_local_m and the coordinate convention.

Executable checks cover local/projected and local/Three round trips, SVG north/south, site positions, native elevations, edges, NoData and diagonal corners.
