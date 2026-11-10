# WeatherWise verification — November 10, 2026

Application: https://weatherwise-truck-routing.vercel.app

Repository: https://github.com/50022005/weatherwise-truck-routing (private)

## Result

The core assignment behavior is implemented and the React + Django application is deployed on Vercel. The production health endpoint confirms the Django service. GitHub Actions passes the frontend tests, backend tests, Django checks and production build.

## Checks completed

- 33 JavaScript tests, including 300 Python/JavaScript risk parity fixtures, passed.
- 13 Django tests passed, covering risk boundaries, load overrides, ETA sampling, precipitation conversion, distance weighting, recommendation priority, missing weather, input validation, oversized requests and distinct route selection.
- Live Chicago–Nashville analysis returned three road routes, 19–20 checkpoints per route, no unknown route miles, and 30 corridor forecast locations. Classified miles summed to each route's length. One local provider check took approximately 8 seconds; this is a single observation, not a load benchmark.
- Production browser planning completed through Django, switched from labeled demo data to live forecasts, and showed three route summaries and a recommendation.
- Production map tiles loaded. The forecast control reached +48 hours, and a selected checkpoint displayed its ETA, wind, rain, snow and risk.
- Production homepage, JavaScript bundle and `/api/health/` returned HTTP 200.

## Corrections made during review

- Made Django the default client API, with an explicit browser-only opt-in.
- Added Vercel's Django entrypoint, Python dependencies, static collection and function duration configuration.
- Fixed cross-origin referrer headers so Django's security middleware does not cause OpenStreetMap tiles to be blocked.
- Deduplicated initial provider routes and preserved genuinely different alternatives with similar lengths.
- Returned JSON HTTP 413 for oversized trip requests and rejected blank place names.
- Fixed Windows compatibility of the cross-language engine test.
- Updated deployment documentation and excluded local metadata and secrets from Git.
- Removed full multi-day checkpoint forecast copies and unused routing annotations from API responses to reduce transfer size; corridor forecasts remain available for the slider.

## Limits relevant to evaluation

- Three options are requested and bounded detours are attempted, but public routing coverage cannot guarantee three distinct routes for every origin/destination. The UI reports shortages.
- OSRM uses a driving profile. Truck clearance, bridge/axle restrictions, hazmat, traffic and mandatory rest are outside this implementation.
- The corridor heatmap visualizes sparse forecast samples; it is not radar or a continuous weather model. Slider interaction was checked, but no formal frame-rate or load benchmark was run.
- Shared rain/snow endpoints in the brief overlap. The documented implementation assigns shared endpoints to the lower band, with the Low cutoff assigned to Moderate.
- A seven-minute walkthrough script is supplied in `WALKTHROUGH.md`. An actual Loom recording has not been created or uploaded.
