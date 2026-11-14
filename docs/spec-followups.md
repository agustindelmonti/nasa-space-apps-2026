# Ajustes pendientes a las specs (derivados del enunciado oficial)

Se aplican cuando terminen los agentes que escriben las specs, antes de implementar.

1. **Calendario de suelo desnudo** (soil-impact + explanations + web-demo): días por mes con suelo sin cultivo vivo por rotación, con NDVI histórico del lote como evidencia observada. Pedido explícito del enunciado. P0.
2. **Calendario de vulnerabilidad** (water-feasibility o nuevo `climate-risk`): por mes y por cultivo, riesgo de helada (T2M_MIN), estrés térmico en floración (T2M_MAX, ej. maíz en enero), déficit hídrico y lluvia extrema (IMERG p95). P0 helada y déficit; P1 calor y extremos.
3. **Incertidumbre explicada** (explanations): rango entre años secos y húmedos del margen y del balance hídrico, no solo el valor esperado. P0.
4. **Filtro por clase de año** (actor-profiles/api/web-demo): ver ranking solo con años secos o solo húmedos. P1.
5. **Prioridades del productor más allá de H/α/λ** (actor-profiles): pesos opcionales para agua, N, erosión, MO e ingreso suplementario, mapeados a componentes del ΔSuelo y del margen. P1. Actualizado: las prioridades solo re-ponderan los w_k de ΔSuelo (cobertura y erosión, carbono y MO, N, malezas, raíces); agua e ingreso suplementario pasan a preferencias de presentación (`display_preferences` en api) y A-ACT-08 y A-ACT-09 quedan retirados.
6. **SRTM** (nasa-ingestion): pendiente y posición en el relieve (bajo/loma) del lote como contexto de anegamiento y erosión. P1.
7. **ECOSTRESS** (nasa-ingestion): LST/ET como evidencia de estrés, sin entrar al motor. P2.
8. **Armonización de resoluciones** (nasa-ingestion design): documentar la grilla común y el muestreo al punto del lote. P0 documental.
9. **Restricción de maquinaria** (actor-profiles): ya prevista vía ventanas de siembra; hacerla explícita como input del productor. P1.
10. **Recursos argentinos equivalentes** (docs/challenge.md) visibles en README y pitch. P0 documental.
