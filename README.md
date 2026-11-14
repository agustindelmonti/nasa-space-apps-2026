# Rastrojo

**Rastrojo** es una herramienta de apoyo a la decisión para comparar rotaciones de cultivos en lotes de la zona núcleo pampeana (sur de Santa Fe), usando datos de observación de la Tierra de NASA, información de suelo del productor y las prioridades de cada actor (propietario, arrendatario, cooperativa, banco).

NASA Space Apps Challenge 2026, sede Rosario (UCEL). Desafío "Field Shift: Adapting Farms with NASA Data" y desafío local AgTech con AFA (Gestión hídrica inteligente).

> **Apoya, no reemplaza al agrónomo.** Trabajamos con escenarios históricos reales, no con predicciones. Todo valor que no viene de un dataset o del usuario está marcado como supuesto (`ASSUMPTION`) para validar con agrónomos.

## Demo en vivo

**https://rastrojo.vercel.app** (web estática + API Python en el mismo proyecto de Vercel).

- `GET /api/v1/health`: estado de la API y de cada dataset (FIXTURE, CACHE o EMPTY).
- `POST /api/v1/evaluate`: ranking de rotaciones para un actor, con `input_hash` SHA-256 y `engine_version`.
- `POST /api/v1/ask`: agente con tools (versión guionada, sin LLM) que responde preguntas en lenguaje natural citando la evaluación.

El deploy usa un snapshot climático precomputado (`data/fixtures/demo/engine_climate.json`, generado desde NASA POWER 1981-2025 para el lote demo). Un test verifica que el snapshot coincide con el cálculo en vivo.

## Estado

Especificado con [OpenSpec](https://github.com/Fission-AI/OpenSpec) (17 cambios en `openspec/changes/`, validados con `openspec validate --all --strict`). Implementado: modelos de dominio, ingesta NASA POWER, escenarios climáticos, balance hídrico FAO-56, impacto en suelo, economía, motor de rotaciones, perfiles de actor, explicaciones, API, web demo y agente guionado. Pendiente: WhatsApp real (Twilio), agente con LLM, medición en campo, SMAP/IMERG/GRACE-FO/NDVI (requieren credenciales Earthdata; el motor los reporta como faltantes).

## Cómo correrlo

Requisitos: Python 3.12 con [uv](https://github.com/astral-sh/uv) y Node 22+.

```bash
cp .env.example .env          # opcional; sin credenciales funciona con fixtures
uv sync                       # instala core + data + dev
uv run pytest                 # tests del motor, API y explicaciones
uv run uvicorn rastrojo.adapters.api:app --reload --port 8000

cd web && npm ci
VITE_API_URL=http://localhost:8000 npm run dev
npm test && npm run test:e2e  # vitest + Playwright
```

Sin la API, la web cae a fixtures locales para que la demo no dependa de la red.

## Datos NASA

| Dataset | Uso | Resolución | Limitación principal |
|---|---|---|---|
| NASA POWER | Lluvia, temperatura, ET0, radiación | ~0.5° (meteo) | Grilla gruesa, modelado/reanálisis |
| SMAP L4 (SPL4SMGP) | Humedad de zona de raíces | ~9 km | Modelo asimilado, no mide el lote |
| GPM IMERG | Lluvia diaria | ~0.1° | Estimación satelital, subestima eventos locales |
| GRACE-FO | Anomalía de almacenamiento de agua terrestre | ~300 km efectivos | Señal regional, mensual, huecos 2017-2018 |
| MODIS / HLS NDVI | Cobertura y vigor histórico | 250 m / 30 m | Nubes, mezcla de píxeles |

## Uso de IA

Este repositorio se desarrolla con asistencia de **Claude Code** (Anthropic) para especificación e implementación, bajo revisión del equipo. El motor de decisión es 100 % determinista y no usa modelos de lenguaje.

## Herramientas de diseño

Usamos [Impeccable](https://github.com/pbakaus/impeccable) (Apache 2.0, vendorizado en `.claude/skills/impeccable`, commit 1995764) como skill de diseño para Claude Code. El contexto de producto está en `PRODUCT.md` y el sistema visual en `DESIGN.md`. Para activar el detector de anti-patrones en tu sesión local: `.claude/skills/impeccable/scripts/impeccable hooks on`. Chequeo manual: `.claude/skills/impeccable/scripts/impeccable detect web/src`.

## Licencia

MIT. Ver `LICENSE`. 

### Librerías de terceros (open source)

| Librería | Licencia | Uso |
|---|---|---|
| FastAPI, Starlette, Uvicorn | MIT / BSD-3 | API HTTP |
| Pydantic, pydantic-settings | MIT | Modelos de dominio y configuración |
| PyYAML | MIT | Supuestos, glosario, intents |
| pandas, pyarrow, pandera, httpx | BSD-3 / Apache-2.0 / MIT / BSD-3 | Ingesta y caché de NASA POWER |
| pytest, hypothesis, ruff, mypy | MIT / MPL-2.0 / MIT / MIT | Calidad |
| React, React DOM | MIT | Web |
| Leaflet, react-leaflet | BSD-2 / Hippocratic-2.1 | Mapa |
| lucide-react | ISC | Iconos |
| Fontsource (Schibsted Grotesk, Atkinson Hyperlegible Next, IBM Plex Mono) | OFL-1.1 | Tipografías |
| Vite, TypeScript, Vitest, Playwright | MIT / Apache-2.0 / MIT / Apache-2.0 | Build y tests web |
| Impeccable | Apache-2.0 | Skill de diseño (no se distribuye en la app) |

Capas de mapa: NASA GIBS (dominio público) y Sentinel-2 cloudless de EOX (CC BY-NC-SA 4.0, atribuido en el mapa).
