# Experimental walking and routing model

Model: mars-grid-2.1-native-edges. This is a demonstration model, not operational human navigation.

## Terrain and admissibility

The PLACES DEM contains1200×1300 native1m pixels in local Mars metres. The graph has240×260 cells at5m spacing, with eight neighbours. It is built independently of the lightweight display grid.

Each5m block requires all native pixels to be valid and uses the maximum native local slope as a conservative constraint. Local slope is atan(hypot(dz/dx,dz/dy)), using finite differences.

Each graph edge checks its five native subsegments for finite elevations and directional slope. A diagonal subsegment has sqrt(2)m horizontal length. Neither coarse nor native diagonals may cut prohibited corners. NoData, out-of-domain cells and manual exclusions are non-routable. No fallback line or undisclosed threshold relaxation is used.

Requested coordinates are discretized to graph-cell centres, at2.5m modulo5m. Horizontal discretization error is at most3.54m. Published site coordinates remain separately available; admissibility is not landing-site validation.

## Three criteria

For native horizontal length h and elevation change dz, surface length s=sqrt(h²+dz²).

1. Distance minimizes the sum of native surface lengths.
2. Estimated walking time minimizes the sum of s×F.
3. Slope cost minimizes coarse horizontal length×(1+weight×(maximum local slope/30)²).

F=1+3×abs(dz/h)+2×max(dz/h,0). Walking time is sum(s×F)/(nominal speed×visibility), with speed in m/min. This explicitly hypothetical law penalizes ascent more than descent. Uniform simulated visibility lies between0.2 and1. It changes duration without forcing geometric route changes.

A* uses horizontal Euclidean distance as an admissible lower bound for these positive edge costs. Optimality applies to the conservative graph, not every continuous terrain path. Return paths are searched independently because ascent/descent costs are directional.

Exactly identical geometries are deduplicated; three distinct paths are never forced. Similar but non-identical routes can remain separate.

## Metrics and budget

The chosen graph path is densified to native pixel centres without smoothing. Elevations are read from the native DEM. Surface distance sums3D segment lengths; ascent/descent sum positive/negative elevation changes. Profile distance is cumulative horizontal length. Local terrain slope and directional slope are distinct; the constraint maximum refers to conservative blocks.

Total time=walking+remaining observations+elapsed time.

Margin=available time−elapsed−outbound walking−return walking−remaining observations−reserve.

Incompatible routes may be displayed but cannot launch a new simulation. A detour is a new routing calculation with an inserted documented site, including possible insertion on the return leg. Straight-line proximity is reported separately from traversable extra distance, walking time and observation time. The preview order is preserved when saving.

## Playback and adaptation

Playback integrates native time costs and remains stationary during observations. The1×/30×/60×/120× settings accelerate playback, not walking parameters. Position is simulated, never GPS.

Pause/resume preserve progress; reset retains notes. Slowdown, delay and cell blockage are explicit simulated events. Direct return explicitly drops pending objectives, routes from current simulated position and preserves completed sites/history.

A manual blockage can eliminate every path. The reproducible demonstration records this result and explicitly removes that simulated constraint before continuing.

## Versions and caching

Responses contain the model version and abbreviated DEM SHA-256 data version. Segment-cache keys contain discretized positions, criterion, slope limit, weight, blocked cells and data version. The model is fixed within the process. Speed/visibility scale duration after spatial search. Frontend request generations and AbortController discard stale responses; already-running server computation is not cancelled.

No sub-metre obstacle, bearing strength, astronaut physiology, suit resource model or spatial weather field is validated. Unregistered geology and unavailable CRISM classes do not contribute to routing.
