# Three-minute demonstration

Start python bootstrap.py and open http://127.0.0.1:8000. Use New mission to avoid resuming an adapted route.

Initial scenario: simulated base(620,−450),Amalik,120min available,20min reserve,35m/min,10min observation,30°slope limit,weight8,visibility1. These are demonstration assumptions.

- **0:00–0:35:** Show the real terrain and DEM boundary on Map. Open Mission and compare the three criteria: approximately1012m/42.6min,1018m/42.5min and1035m/44.2min.
- **0:35–1:05:** Open Science and evaluate Skinner Ridge. Straight-line proximity is about97m; calculated detour adds201m,7.7min walking and10min observation. Margin after reserve is39.8min. Accept; the proposed order is Amalik then Skinner Ridge on the return.
- **1:05–1:35:** Open a site profile, read the Mastcam-Z caption and PDS source. Return to Map; compare3D1×and2D without changing scientific calculations.
- **1:35–2:05:** Open Notebook, choose a point on the map and save a category/note. Show the unverified-user label and optional local photo.
- **2:05–2:40:** Save and start. Exploration provides120×playback, pause/resume, stationary observations, return, elevation profile and remaining-time context.
- **2:40–3:00:** Show direct return if needed, reportJSON/notebookCSV/print, and historical MEDA pressure dated2021. Reload to retrieve the saved mission and notebook.

With a server running, python scripts/demo.py replays the scenario through HTTP and writes demo-results.json/demo-report.json/demo-observations.csv. It also exercises slowdown, a5min delay and a blocked cell. If the block eliminates every path, this is reported and the manual constraint is explicitly lifted before continuing.

Recorded scientific results remain approximately1219.23m/60.21min with the accepted stop. After the scenario events, completion is about77.35min, leaving42.65min including the required20min reserve, or22.65min margin. A/C are completed and the route returns to the base cell centre(622.5,−452.5).

Playback acceleration never changes walking speed or route metrics. Historical measurements never become current observations.
