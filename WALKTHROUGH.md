# WeatherWise — 7-minute Loom recording outline

This is a recording script, not an uploaded recording. Open the Vercel full-stack application or run the project locally. Verify `/api/health/` before recording.

## 0:00–0:45 — Problem and architecture

“Truck route choice changes with weather and load. WeatherWise compares alternatives using the forecast at the time the driver reaches each checkpoint. This project has React, Leaflet and Django, with OSRM road routes and Open-Meteo forecasts. The default React build calls the same-origin Django API, including on Vercel.”

Show the labeled demo state. Explain that example geometry/weather are simulated; live mode must be requested.

## 0:45–1:45 — Live planning

Choose Chicago, Illinois → Nashville, Tennessee using geocoding suggestions. Set departure one hour from now, load 32,000 lb, spacing 25 mi. Click “Find the safest route.” Explain loading, cancellation and provider failure handling. Wait for LIVE FORECAST. Explain that providers might return fewer than three genuine alternatives and that the app reports that honestly.

## 1:45–2:45 — Route comparison

Select each route. Show duration, distance, severe/high miles, average risk and ETA. Explain the exact recommendation order: Severe miles, High miles, average risk, travel time, after excluding No Travel and unknown-weather routes. A faster route does not override safer ranking.

## 2:45–3:45 — Checkpoints and ETA

Open Checkpoints. Select a middle checkpoint. Show its mile marker, estimated arrival and wind/rain/snow. Explain that checkpoints use road distance and OSRM segment durations rather than uniform straight-line travel. Change spacing to 10 or 50 miles and replan. More checkpoints increase forecast calls, not forecast certainty.

## 3:45–4:45 — Forecast map

Toggle weather and checkpoints. Move the slider from Now to +24h and +48h. Explain that the heatmap is a sparse forecast-risk surface along the corridor, not radar. It uses a common future time; route risk remains based on each checkpoint's arrival time. Forecast data is prefetched so slider movement makes no requests.

## 4:45–5:45 — Risk rules and edge cases

Open “How risk is calculated.” Show strict weight thresholds. At 45 mph, 30,000 lb is Severe; 30,001 lb is No Travel. At 35 mph, 40,001 lb is Severe. Wind 55 mph blocks all loads. Explain rain/snow boundary assumptions. Use the test files to demonstrate these rules without pretending the current weather contains every condition.

## 5:45–6:30 — Code and tests

Show `src/engine.js`, `backend/routing/engine.py`, the provider adapters and the API input validator. Run `npm test` and `python backend/manage.py test routing`. Explain distance-weighted risk and conservative endpoint interval scoring. Show the health endpoint and a validated plan response in Django mode.

## 6:30–7:00 — Limitations and handoff

Show README startup instructions and Vercel configuration. Explain public API quotas, sparse sampling, missing-weather exclusion and lack of truck clearance / bridge / hazmat restrictions. Share repository, hosted application and final Loom link only after each has actually been published.

## Pre-recording checklist

- Use a near-future departure and current API responses.
- Hide credentials and unrelated browser tabs.
- Confirm the live forecast badge, map tiles and slider work.
- If APIs fail, show the real error and explicitly label any demo fallback.
- Do not describe Sites as a hosted Django server.
