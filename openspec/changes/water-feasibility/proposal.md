# Proposal: water-feasibility

**Prioridad:** P0 balance y estado por escenario (demo sábado); P1 contexto GRACE-FO, napa y riesgo de helada; P2 vista detallada del balance diario.

## Why

El eje AFA es gestión hídrica: la pregunta real del productor es si le da el agua para el doble cultivo o para un cultivo de servicio sin castigar la soja o el maíz siguiente. Es también la restricción "agua disponible" de la función objetivo. Hace falta un cálculo simple, explicable y determinista que use los datos NASA (ET0 POWER, SMAP L4, lluvia, GRACE-FO) y diga FEASIBLE, RISKY o NOT_FEASIBLE con su porqué.

## What Changes

- Se define un balance hídrico diario tipo balde por campaña: ETc = Kc·ET0 (Kc FAO-56 como supuesto), lluvia efectiva, agua útil del Suelo, estrés cuando el agotamiento supera la fracción fácilmente disponible, drenaje del excedente.
- Se define la humedad inicial desde SMAP L4 (zona de raíces) convertida a mm de agua útil, con respaldo explícito si falta.
- Se evalúa cada campaña en cada escenario histórico (años de `climate-scenarios`) y se agrega a un estado con umbrales supuestos A-WAT-NN.
- Foco en doble cultivo y cultivo de servicio: agua en el perfil a la siembra del cultivo de verano siguiente ("secado del perfil") y consumo del servicio frente a barbecho.
- GRACE-FO como contexto regional que puede subir FEASIBLE a RISKY, nunca decide solo. Napa opcional como atenuante informado.
- Riesgo de helada (T2M_MIN bajo umbral en ventanas sensibles) como Riesgo separado del estado hídrico, cubierto aquí por compartir insumos y escenarios.
- Salida con motivos codificados, evidencia, supuestos usados y faltantes. Puro y testeable sin red.

## Capabilities

### New Capabilities
- `water-feasibility`: balance hídrico simplificado por cultivo y campaña sobre escenarios históricos, estado de factibilidad hídrica con porqué, chequeo de secado del perfil, contexto GRACE-FO, napa y riesgo de helada.

### Modified Capabilities
- Ninguna en specs archivadas. Requiere un agregado compatible en `domain-models` (in-flight): series diarias por escenario (lluvia, ET0, T2M_MIN), humedad inicial SMAP y anomalía TWS dentro de `EngineInput`.

## Impact

- Módulo puro `fieldshift.engine.water` (sin I/O), invocado por `rotation-engine` como restricción y fuente de Riesgo hídrico.
- Consumidores: `rotation-engine` (estado y riesgo), `explanations` (motivos y evidencia), `web-demo` (panel "agua invisible").
- Supuestos nuevos en `assumptions.yaml`: A-WAT-01 a A-WAT-14 y A-CLI-05 a A-CLI-07.

## Fuera de alcance

- Modelos de cultivo completos (rinde por estrés, fenología dinámica por grados día): el rinde por clase de año viene de parámetros económicos.
- Ascenso capilar cuantitativo desde la napa, anegamiento y excesos hídricos.
- Riego.
- Balance multicapa o distribución vertical de raíces.
