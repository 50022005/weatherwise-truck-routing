# WeatherWise — Weather-Aware Truck Routing

- Hosted application: https://weatherwise-truck-routing.vercel.app
- GitHub repository (private): https://github.com/50022005/weatherwise-truck-routing
- Backend health: https://weatherwise-truck-routing.vercel.app/api/health/
- Review results and limitations: [VERIFICATION.md](VERIFICATION.md)

React 19 + Leaflet frontend, Django 5.2 API, OSRM routing, Open-Meteo geocoding and hourly weather. No API keys are needed for the educational public endpoints. Provider terms, quotas, reliability, and commercial use must be reviewed before a production rollout.

## Run the full React + Django application

Python 3.12+, Node 22+.

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
npm ci
```

Development: start two terminals:

```bash
# Terminal 1
python backend/manage.py runserver
# Terminal 2 (macOS / Linux)
VITE_API_MODE=django npm run dev
# Windows PowerShell: $env:VITE_API_MODE='django'; npm run dev
```

Open the Vite URL. Vite proxies `/api` to Django on port 8000. Geocoding is browser-side; route generation, checkpoint weather, risk, corridor weather and ranking run in Django.

To serve a production-style build from Django:

```bash
VITE_API_MODE=django npm run build
python backend/manage.py collectstatic --noinput
# Set DJANGO_SECRET_KEY and DJANGO_ALLOWED_HOSTS in the hosting environment.
gunicorn --chdir backend config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 240
```

The included Dockerfile builds React in Django mode and serves both from a single Python service. Set `DJANGO_ALLOWED_HOSTS` to the actual hostname and `DJANGO_SECRET_KEY` to a generated secret. PORT is honored. No database or migrations are required: the app is a stateless trip calculator.

## Deploy React + Django on Vercel

The default client calls the same-origin Django API. Vercel runs Django through the root `wsgi.py` entrypoint and serves collected React assets from its CDN. This uses Vercel's Django framework preset; it is a full-stack deployment.

1. Import this GitHub repository into Vercel with the repository root as Root Directory.
2. Keep the checked-in Django framework and build settings from `vercel.json`.
3. Set `DJANGO_SECRET_KEY` to a random secret and `DJANGO_DEBUG=0`. Vercel deployment and production hostnames are read from Vercel system environment variables. Add any custom hostname to `DJANGO_ALLOWED_HOSTS`.
4. Deploy, then verify `/api/health/` returns `weatherwise-django` and submit a live trip.

The build installs JavaScript dependencies and compiles React; Vercel installs Python dependencies and collects static assets. A 300-second function limit accommodates provider requests. Availability still depends on provider quotas. Set `VITE_API_MODE=browser` only for an intentional frontend-only build; that mode does not run Django.

Official setup reference: [Django on Vercel](https://vercel.com/docs/frameworks/full-stack/django).

The initial Chicago–Nashville scenario is explicitly simulated, including its simplified geometry. It makes controls explorable before requesting external APIs. Click **Find the safest route** for live analysis. Provider errors preserve the previous result and show an error; simulated results never masquerade as live results.

## Usage

1. Search origin/destination cities and select an unambiguous result (state/country shown).
2. Pick departure within 48 hours, load in lb, and checkpoint spacing 10/25/50 miles.
3. Plan the trip; compare routes and click any option.
4. Select checkpoints or map markers for ETA and hourly wind/rain/snow.
5. Toggle the corridor layer and move the 0–48h slider. This changes the common-time corridor forecast, not the ETA-based route recommendation.

## Correctness decisions

- OSRM is asked for up to 3 alternatives. If fewer than three routes are returned, two bounded, road-snapped midpoint detour requests are attempted. Routes with the same sampled geometry are deduplicated, and excessively long detours are rejected. The UI reports fewer than three options when necessary; alternatives are never fabricated.
- This uses a **driving profile, not a certified truck profile**. It does not account for height, width, axle loads, bridge restrictions, hazmat, closures, live traffic or mandatory rest. Weight affects weather risk only. Forecast guidance is not a guarantee of safe passage.
- Checkpoints follow cumulative road distance. Segment-level OSRM durations determine ETAs, including both endpoints and the final shorter segment. If annotations do not align with geometry, cumulative geometry distance and proportional route duration are used. Road altitude and driver rest time are excluded.
- Risk uses the maximum of wind, rain, snow and load overrides. Wind bands are continuous: 25–<35, 35–<45, 45–<55, ≥55 mph. The brief overlaps rain/snow endpoints; exact shared boundaries belong to the lower band, except the Low upper thresholds (0.10 rain / 0.5 snow) belong to Moderate. This assumption is visible in the UI.
- Load rules use strict `>` comparisons: 30,000 lb remains Severe at 45 mph, 30,001 becomes No Travel; 40,000 lb remains High at 35 mph, 40,001 becomes Severe. Wind ≥55 is No Travel for any load.
- Open-Meteo is requested in mph and default mm/cm precipitation units. `(rain + showers)/25.4` gives rain inches; `snowfall/2.54` gives snow inches. Hourly amounts are interpreted as in/hr. The hourly interval ending at or immediately after ETA is selected, with no extrapolation beyond returned data.
- Each interval uses the worse of its two checkpoint risks. Miles by risk sum to total route miles, including the terminal partial interval. Average risk is distance-weighted over the full trip. Missing weather makes adjacent interval miles unknown and excludes the route from recommendations; null is never zero-filled.
- Any No Travel checkpoint excludes a route. Remaining routes sort lexicographically by **Severe miles → High miles → average risk → driving seconds**. If none qualify, no recommendation is displayed. No Travel is not traded for a shorter trip.
- Forecast slider is relative to analysis generation time, independent of departure; all displayed timestamps use the device timezone, submitted timestamps use explicit UTC offsets.

## Performance and errors

- Weather requests batch up to 30 coordinates, preserving order; corridor points are capped at 36. Route samples are capped at 220 per route, with an actionable wider-spacing error for long trips.
- Corridor samples cover the route and nearby latitude offsets (~11 miles). Layered Canvas kernels form a sparse spatial heatmap; this is **forecast risk sampling, not radar or a continuous meteorological model**. A failed corridor request does not discard valid route weather.
- Ten-minute provider caches are bounded. Browser timeout: 25 seconds per request; backend timeout: 25 seconds. Requests can be cancelled from the UI. Slider updates reuse the already fetched forecast data, making no network calls.
- A private request URL is not accepted by the backend; provider hosts are fixed. Inputs, coordinates, load, departure, payload size and sampling interval are validated. The stateless endpoint reads forecasts only and creates no session or persistent resource.
- Public services can rate-limit or be unavailable. For heavier use, configure your own OSRM and licensed weather service, plus reverse-proxy rate limits. No services have been purchased.

## API

`GET /api/health/` → `{ "status": "ok", "service": "weatherwise-django" }`

`POST /api/plan/` (JSON):

```json
{
  "origin": {"name":"Chicago, Illinois, United States","coord":[-87.6298,41.8781]},
  "destination": {"name":"Nashville, Tennessee, United States","coord":[-86.7816,36.1627]},
  "departure":"<ISO-8601 timestamp with timezone, in the next 48 hours>",
  "load":32000,
  "spacing":25
}
```

Response contains routes, road geometry, checkpoints, ETA forecast weather, risk, miles by risk, average, unknown miles, eligibility, recommended route id (or null), corridor forecasts, generation time, mode and warnings. Validation errors return 400; provider errors return 502; unsupported methods return 405.

## Validation

```bash
npm test
python backend/manage.py test routing
python backend/manage.py check
npm run build
```

33 JavaScript tests (including 300 cross-language risk cases) and 13 Django tests cover all condition thresholds, strict load boundaries, invalid weather, road/ETA interpolation, rain/snow conversion, forecast horizon, distance weighting, blocked routes and lexicographic ranking. Django tests additionally cover HTTP method guards and input validation. Provider calls are mocked in unit tests; live browser planning is tested separately and depends on public services.

## Repository 

The repository includes GitHub Actions checks for JavaScript and Django tests and the production build. Dependencies, runtime data, local deployment metadata and secrets are excluded by `.gitignore`.



## Sources / attribution

- [OSRM HTTP API](https://project-osrm.org/docs/v26.4.0/http)
- [Open-Meteo forecast API](https://open-meteo.com/en/docs)
- [Open-Meteo geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- Weather data: Open-Meteo (CC BY 4.0), geocoding: GeoNames via Open-Meteo.
- Map data: © OpenStreetMap contributors; standard OSM raster tiles. Respect OSM tile usage policy. Leaflet is BSD-2-Clause.
