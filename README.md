# Rastrojo

**Rastrojo** es una herramienta de apoyo a la decisión para comparar rotaciones de cultivos en lotes de la zona núcleo pampeana (sur de Santa Fe), usando datos de observación de la Tierra de NASA, información de suelo del productor y las prioridades de cada actor (propietario, arrendatario, cooperativa, banco).

NASA Space Apps Challenge 2026, sede Rosario (UCEL). Desafío "Field Shift: Adapting Farms with NASA Data" y desafío local AgTech con AFA (Gestión hídrica inteligente).

> **Apoya, no reemplaza al agrónomo.** Trabajamos con escenarios históricos reales, no con predicciones. Todo valor que no viene de un dataset o del usuario está marcado como supuesto (`ASSUMPTION`) para validar con agrónomos.

## Estado

Fase de especificación con [OpenSpec](https://github.com/Fission-AI/OpenSpec). Ver `openspec/changes/` y `docs/brief.md`.

## Datos NASA (planificados)

| Dataset | Uso | Resolución | Limitación principal |
|---|---|---|---|
| NASA POWER | Lluvia, temperatura, ET0, radiación | ~0.5° (meteo) | Grilla gruesa, modelado/reanálisis |
| SMAP L4 (SPL4SMGP) | Humedad de zona de raíces | ~9 km | Modelo asimilado, no mide el lote |
| GPM IMERG | Lluvia diaria | ~0.1° | Estimación satelital, subestima eventos locales |
| GRACE-FO | Anomalía de almacenamiento de agua terrestre | ~300 km efectivos | Señal regional, mensual, huecos 2017-2018 |
| MODIS / HLS NDVI | Cobertura y vigor histórico | 250 m / 30 m | Nubes, mezcla de píxeles |

## Uso de IA

Este repositorio se desarrolla con asistencia de **Claude Code** (Anthropic) para especificación e implementación, bajo revisión del equipo. El motor de decisión es 100 % determinista y no usa modelos de lenguaje.

## Licencia

MIT. Ver `LICENSE`. Librerías de terceros y sus licencias se listarán aquí.
