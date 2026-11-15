# Scientific rationale

MarsWalk compares deposits of Jezero’s western delta associated with ancient aqueous environments. It does not claim current liquid water or detected life. The human base at(620,−450)local metres is a scenario assumption, not a validated landing site.

The selected area is the available native PLACES DEM rectangle within supplied HiRISE/CTX image coverage. Projection and bounds are recorded in config/roi.json. All three published targets lie within this area and are routable at the experimental30°threshold. Sites were not moved to obtain a favourable result. Graph-cell markers are discretized simulation positions; absolute positional accuracy remains unquantified.

| Target / sample | Published Mars latitudeN, longitudeE | PDS PDF pages | Scientific comparison |
|---|---|---|---|
|Skinner Ridge / Swift Run|18.458931,77.40617078|report14;figure24|Fine- to medium-grained Lower Rockytop sandstone; compare grains and prodelta layering|
|Wildcat Ridge / Hazeltop|18.45863707,77.40588851|report58;figure68|Fine sulfate-bearing Hogwallow Flats rock; discuss possible lake deposition and aqueous changes|
|Amalik / Shuyak|18.45068954,77.40143171|report100;figure109|Fine olivine-bearing sedimentary rock; compare mineral preservation and alteration|

The [PDS Initial Reports, Volume2 Release2](https://pds-geosciences.wustl.edu/missions/mars2020/Mars%202020%20Initial%20Reports%20Volume%202%20Release%202.pdf) supports the supplied site summaries. Context-image dates differ from sampling dates.

config/site-image-metadata.json retains Mastcam-Z sequences and sols:466/492for Skinner Ridge,513for Wildcat Ridge,557/565/582for Amalik. Enhanced-colour figures include captions and context. Individual image pixels are not independently geolocated. Chemical composition is not inferred from RGB values. English summaries are presentation translations of the supplied descriptions.

Sun and Stack2020SIM3464 is regional1:75000context. The pipeline clips original GeoPackage polygons, retaining identifiers, names and symbols. Published descriptions are joined by unit name, not row ID. Unregistered geology cannot determine metre-scale traversability or a particular rock’s composition.

The CRISM metadata/core archive was downloaded, MD5 checked and ROI windows inspected. All three class maps contain zero valid pixels in the selected area despite overlapping rectangular bounds. Catalogue IDs FRT00005850,HRL000040FF,FRS0002FE75andFRS00031442 do not establish usable coverage at the three sites. No compatible replacement spectral mosaic has been prepared.

The optional scientific optimizer uses declared, subjective team scores: ancient-water relevance2/site, novelty1/site, capped contextual evidence2and number of distinct lithologies. Score=sum(relevance)+distinct lithologies+maximum evidence+sum(novelty). Repeated diversity is not double-counted. Exhaustive subsets/orders are searched for at most three sites, with return and budget constraints and shorter duration as a tie-breaker. These scores are not NASA measurements.
