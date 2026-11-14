# Tasks: water-feasibility

## 1. Modelos e insumos (P0)

- [ ] 1.1 Consumir los campos de `EngineInput` acordados en `domain-models` (series diarias por año con T2M_MAX e IMERG opcional, humedad inicial SMAP, anomalía TWS, supuestos resueltos); verificar con test de validación de un `EngineInput` de ejemplo
- [ ] 1.2 Definir modelos frozen de salida (`WaterAssessment`, `CampaignWater`, `ScenarioWater`, `Reason`) en `fieldshift.engine.water`; verificar con test que rechaza campos extra y exige procedencia en cada número
- [ ] 1.3 Cargar A-WAT-01 a A-WAT-15 y A-CLI-05 a A-CLI-10 en `assumptions.yaml` (PENDING_AFA, fuente FAO-56 donde aplica); verificar con test que la aplicación los resuelve y el formato de id es válido

## 2. Balance diario (P0)

- [ ] 2.1 Implementar curva de Kc por etapas con rampas y barbecho; verificar con test de Kc por día para un cultivo de ejemplo y escenario "Barbecho entre cultivos"
- [ ] 2.2 Implementar el paso diario del balde (lluvia efectiva, ETc, Ks, drenaje) con sumas cronológicas; verificar con tests "Excedente drenado", "Sin estrés", "Perfil vacío" y "Fracción fija de ejemplo"
- [ ] 2.3 Implementar agua inicial desde SMAP y respaldos A-WAT-12, A-WAT-13, A-WAT-14; verificar con tests "Conversión de SMAP", "Sin SMAP disponible" y "Suelo sin agua útil"

## 3. Escenarios y estado (P0)

- [ ] 3.1 Implementar simulación de campaña por año con exclusión `MISSING_WEATHER` y renormalización 1/N'; verificar con tests "Resultado por año" y "Año sin ET0 completa"
- [ ] 3.2 Implementar etiquetas MODERATE/SEVERE, estado por campaña, peor campaña y `INSUFFICIENT_SCENARIOS`; verificar con tests "Doble cultivo riesgoso", "Peor campaña manda" y "Pocos escenarios válidos"
- [ ] 3.3 Implementar chequeo de secado del perfil y terminación del servicio; verificar con tests "Centeno seca el perfil en años secos" y "Terminación del servicio"
- [ ] 3.4 Implementar simulación paralela con barbecho y diferencia de agua a la siembra; verificar con test "Costo hídrico del servicio"
- [ ] 3.5 Implementar el estado por (cultivo, posición, escenario) para el motor, con UNKNOWN para escenarios excluidos; verificar con tests "Soja de segunda en un año severo", "Perfil seco a la siembra" y "Escenario excluido"
- [ ] 3.6 Implementar calendario mensual de vulnerabilidad con helada y déficit hídrico; verificar con tests "Déficit en enero para la soja de segunda", "Mes fuera del ciclo" y "Calendario determinista"
- [ ] 3.7 Implementar salida con motivos, Evidencias y supuestos usados; verificar con tests "Porqué legible" y "Supuestos listados" y snapshot de la salida canónica del lote de demo
- [ ] 3.8 Implementar rango hídrico por clase anual (déficit y agua a la siembra); verificar con tests "Rango de agua a la siembra" y "Clase sin escenarios válidos"
- [ ] 3.9 Implementar UNKNOWN por campaña (menos de A-CLI-03 escenarios) con orden de peor estado NOT_FEASIBLE > UNKNOWN > RISKY > FEASIBLE y Faltante; verificar con tests "Sin clima suficiente no es no apto", "Datos completos no producen UNKNOWN" y "GRACE-FO no toca UNKNOWN" (P0)
- [ ] 3.10 Marcar `SOIL_AWC_FROM_SOILGRIDS` con Faltante cuando el agua útil viene de SoilGrids; verificar con test "Agua útil desde SoilGrids" (P1)

## 4. Contexto y riesgos (P1)

- [ ] 4.1 Implementar regla GRACE-FO (solo FEASIBLE a RISKY) y Faltante sin dato; verificar con los cuatro escenarios de GRACE-FO del spec
- [ ] 4.2 Implementar napa como atenuante y Faltante de napa; verificar con tests "Napa somera" y "Napa desconocida"
- [ ] 4.3 Implementar Riesgo de helada por ventanas sensibles; verificar con tests "Heladas en floración de trigo" y "Helada no cambia factibilidad"

- [ ] 4.4 Agregar al calendario estrés térmico en floración (T2M_MAX) y lluvia extrema (percentil IMERG); verificar con tests "Calor en floración del maíz", "Años sin IMERG" y "Sin IMERG en la entrada"
- [ ] 4.5 Cargar A-WAT-16 e implementar la regla de lluvia conservadora POWER vs IMERG por escenario con fuente declarada; verificar con tests "IMERG más seca en un año", "Año sin IMERG" y "Regla apagada sin IMERG en la entrada"

## 5. Determinismo e integración (P0 para 5.1, P1 para 5.2)

- [ ] 5.1 Agregar test de determinismo (dos procesos, comparación byte a byte) y test con red bloqueada; verificar con `uv run pytest tests/engine/water -q` en verde
- [ ] 5.2 Integrar con `rotation-engine` como submódulo del motor: el estado por escenario se traduce en ajustes NOT_SOWN y FORCE_DRY (el déficit no entra al Riesgo de forma directa); verificar con test de integración del lote de demo donde R_WHEAT_SOY2_MAIZE y R_MAIZE_SOY_COVER traen estado y motivos

## 6. Vista del balance (P2)

- [ ] 6.1 Exponer la serie diaria del balance de un año elegido para el panel "agua invisible"; verificar con test de la API que devuelve la serie con procedencia
