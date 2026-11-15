# Limitations

The central2D/3D mapping, routing, mission, detour, notebook, historical MEDA, persistence and export features are implemented. Working software does not establish human navigation safety.

- CRISM: the downloaded core archive matches its published MD5, but all three inspected class maps have zero valid pixels in this area. The layer remains unavailable. Large fused products were not imported.
- SIM3464: regional1:75000 geology is unregistered, with a possible100–200m offset. It is excluded from fine routing and cannot identify a rock beneath an observer.
- Imagery: nominal HiRISE mosaic resolution is25cm; the delivered local cache is approximately1.2m and displayed at2m. Zoom cannot recover missing detail. Optional WMTS is2D only and requires network/cache.
- DEM: real PLACES1m data; conservative5m graph with native edge validation;5m display mesh. Aggregation can exclude otherwise traversable narrow passages. Sub-metre obstacles, bearing strength and absolute accuracy/datum are not independently validated.
- Walking: the explicit law, speed, autonomy, reserve, visibility and base are demonstration assumptions. There are no invented suit, oxygen or physiological measurements.
- MEDA: only historical sol29 pressure at the rover is plotted. Humidity is absent; inconsistent uncertainty units are excluded; TIRS irradiance is not temperature. No current or spatialized weather is claimed.
- New observations are manually entered and unverified. There is no automatic rock detection or claim of life. Existing personal notes remain in their original language.
- Identical routes are deduplicated; similar non-identical paths may remain distinct.
- English is the application language. Original scientific archives and source captions remain unchanged; they may retain their source language.
- Keyboard labels, visible focus, textual route criteria and reduced-motion support are included. No exhaustive external WCAG audit or physical-device test is claimed.
- SQLite is local, without account synchronization or automatic backup. Preserve the user database and uploaded photos.
- The graphical lighting does not model a dated Sun position.
- Automated algorithm/API tests and assisted browser checks are documented; there is no complete standalone browser E2E suite or performance guarantee.

The Murray catalogue request failed TLS verification without bypass. A separate CTX20m DEM and HiRISE DTM candidate were identified but not independently imported; routing uses the supplied PLACES DEM.

The two supplied header images are presentation assets. Their display does not imply NASA certification of the application or simulated routes.
