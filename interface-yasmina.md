# Interface and alternative3D integration

The existing MarsWalk backend, native routing, scientific import, missions, photos, reports and API remain the project foundation. The supplied alternative project does not replace the user database.

Map is the primary3Dscreen. Mission, Science, Exploration, Notebook, Environment and Sources are separate, clearly labelled spaces. URL fragments preserve deep links and browser-back navigation. Shared parameters stay in memory; saved missions and notes are recoverable after reload. The map remains mounted across spaces so camera state survives.

The original alternative viewer is retained as a non-executed reference in references/yasmina/Viewer3D.original.tsx.txt. Its camera45°/(200,750,700), exponential fog0.0004, ambient0.85, warm directional light1.8, damping, roughness0.85/metalness0.1and pin style were adapted. PCFShadowMap is used for compatibility.

The existing native pixel-centre positions and UVs are retained instead of stretching the grid to exterior edges. All coordinate conversions, raycasting, layers, route/profile interactions and calculations remain aligned. Exaggeration defaults to1×; lighting is graphical.

The English update adds frontend/Header.tsx, the MarsWalk by KAWKAB ZOMORODA credit and two small supplied logos at the top right. Common labels, pages, maps, site summaries, error messages and reports use English. Known legacy application-generated mission labels are presented in English; personal note text and original scientific files remain unchanged.

The earlier source snapshot is backups/marswalk-before-yasmina-layout.zip,68files, excluding dependencies, the scientific pack and user data. It is not a complete database backup.

Assisted browser checks cover desktop1440×1000and mobile390×844, page navigation, mission comparison, site/detour access, observation persistence, playback, MEDA,2D/3Dswitching and zoom/recenter. No physical-phone multitouch or exhaustive accessibility audit is claimed.

The current validation report records English/branding checks and build/test results. No public deployment was performed.
