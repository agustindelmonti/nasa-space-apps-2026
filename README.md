# Rastrojo

**Rastrojo** is a decision-support tool that compares crop rotations for farm fields in the core Pampas region of Argentina (southern Santa Fe), using NASA Earth observation data, the farmer's soil information and the priorities of each decision-maker (owner, tenant, cooperative, bank).

NASA Space Apps Challenge 2026, Rosario local event (UCEL). Challenge: "Field Shift: Adapting Farms with NASA Data", plus the local AgTech challenge with the AFA farmers' cooperative (smart water management).

> **It supports, not replaces, the agronomist.** We work with real historical seasons, not forecasts. Every value that does not come from a dataset or from the user is flagged as an assumption (`ASSUMPTION`) to be validated with agronomists.

## Live demo

**https://rastrojo.vercel.app** (static web app plus a Python API in the same Vercel project). The web interface is in Spanish, for farmers in Argentina.

**Demo deck (7 slides, English):** [Google Slides](https://docs.google.com/presentation/d/1yFjG1d9fvnVsJwipsKSfAucojNGYETwSkc_mntoAZwo/edit?usp=sharing) · [PDF copy in this repo](docs/pitch/rastrojo-demo-deck-en.pdf)

- `GET /api/v1/health`: status of the API and of each dataset (FIXTURE, CACHE or EMPTY).
- `POST /api/v1/evaluate`: rotation ranking for a decision-maker, with an `input_hash` (SHA-256) and an `engine_version`.
- `POST /api/v1/ask`: tool-using agent (rule-based version, no LLM) that answers natural-language questions by citing the evaluation.

The deployment uses a precomputed climate snapshot (`data/fixtures/demo/engine_climate.json`, generated from NASA POWER for the demo field). A test checks that the snapshot matches the live calculation.

## How it works

1. **Climate:** NASA POWER daily data at the field point, 1984-2024. 41 real growing seasons, classified as dry, normal or wet by rainfall terciles.
2. **Water:** daily FAO-56 soil water balance with Penman-Monteith reference evapotranspiration (ET0) and crop coefficients. GPM IMERG daily rainfall is wired into the balance for the demo field.
3. **Soil:** a soil index from -100 to +100 (cover, carbon, nitrogen, weeds, roots), months of bare soil and rain on bare soil.
4. **Economics:** gross margin per season by type of year.
5. **Decision:** `Score(r) = Margin + alpha * dSoil - lambda * Risk`, maximized over the feasible rotations. The horizon, rate, alpha and lambda depend on who decides. Risk is the expected shortfall of the worst third of seasons.
6. **Today's water:** NASA GRACE-FO total water storage and SMAP L4 root-zone soil moisture for the field, with their percentile.
7. **Search:** all 385 rotations of 1 to 3 seasons from the crop catalog are evaluated; the Pareto front (margin, soil, risk) is precomputed.

The engine is 100% deterministic: same input, same output, no language model in the calculation.

## Status

Specified with [OpenSpec](https://github.com/Fission-AI/OpenSpec) (changes in `openspec/changes/`, validated with `openspec validate --all --strict`). Implemented: domain models, NASA POWER ingestion, climate scenarios, FAO-56 water balance, GPM IMERG rainfall, GRACE-FO and SMAP L4 water status for the demo field, soil impact, economics, rotation engine, exhaustive rotation search with Pareto front, decision-maker profiles, explanations, API, web demo and rule-based agent. Pending: real WhatsApp channel (Twilio), LLM-backed agent, field measurements, and integrating the MODIS NDVI field-history prototype into the main app.

## How to run it

Requirements: Python 3.12 with [uv](https://github.com/astral-sh/uv) and Node 22+.

```bash
cp .env.example .env          # optional; works with fixtures without credentials
uv sync                       # installs core + data + dev
uv run pytest                 # engine, API and explanation tests
uv run uvicorn rastrojo.adapters.api:app --reload --port 8000

cd web && npm ci
VITE_API_URL=http://localhost:8000 npm run dev
npm test && npm run test:e2e  # vitest + Playwright
```

Without the API, the web app falls back to local fixtures so the demo does not depend on the network.

## NASA data

| Dataset | Use | Resolution | Main limitation |
|---|---|---|---|
| NASA POWER | Rain, temperature, ET0, radiation, root-zone wetness | ~0.5° (meteorology) | Coarse grid, modeled/reanalysis |
| GPM IMERG | Daily rainfall in the water balance | ~0.1° | Satellite estimate, underestimates local events |
| SMAP L4 (SPL4SMGP) | Current root-zone soil moisture | ~9 km | Assimilation model, does not measure the field |
| GRACE-FO | Terrestrial water storage anomaly | ~300 km effective | Regional, monthly signal, 2017-2018 gap |
| MODIS MOD13Q1 NDVI | Field-history prototype, map layers | 250 m | Clouds, mixed pixels |
| NASA GIBS / Worldview | Map layers (MODIS, NDVI, SMAP, IMERG) | varies | Visual context only |

## Use of AI

This repository was developed with the assistance of **Claude Code** (Anthropic) for specification and implementation, under team review. The decision engine is 100% deterministic and does not use language models. See `AI_USE.md`.

## Design tools

We used [Impeccable](https://github.com/pbakaus/impeccable) (Apache 2.0, vendored in `.claude/skills/impeccable`, commit 1995764) as a design skill for Claude Code. Product context is in `PRODUCT.md` and the visual system in `DESIGN.md`.

## License

MIT. See `LICENSE`.

### Third-party libraries (open source)

| Library | License | Use |
|---|---|---|
| FastAPI, Starlette, Uvicorn | MIT / BSD-3 | HTTP API |
| Pydantic, pydantic-settings | MIT | Domain models and configuration |
| PyYAML | MIT | Assumptions, glossary, intents |
| pandas, pyarrow, pandera, httpx | BSD-3 / Apache-2.0 / MIT / BSD-3 | NASA POWER ingestion and cache |
| pytest, hypothesis, ruff, mypy | MIT / MPL-2.0 / MIT / MIT | Quality |
| React, React DOM | MIT | Web |
| Leaflet, react-leaflet | BSD-2 / Hippocratic-2.1 | Map |
| lucide-react | ISC | Icons |
| Fontsource (Schibsted Grotesk, Atkinson Hyperlegible Next, IBM Plex Mono) | OFL-1.1 | Fonts |
| Vite, TypeScript, Vitest, Playwright | MIT / Apache-2.0 / MIT / Apache-2.0 | Web build and tests |
| Impeccable | Apache-2.0 | Design skill (not shipped in the app) |

Map layers: NASA GIBS (public domain) and Sentinel-2 cloudless by EOX (CC BY-NC-SA 4.0, credited on the map).
