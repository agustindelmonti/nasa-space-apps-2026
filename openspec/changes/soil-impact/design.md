# Design: soil-impact

## Context

Ver proposal.md. El índice vive en `fieldshift.engine.soil` (puro, sin I/O). Recibe una Rotación ya validada por domain-models, el Suelo, la serie NDVI resuelta (opcional) y los supuestos `A-SOIL-*` resueltos dentro de `EngineInput`. La escala [-100, +100] por ciclo y el uso de α en USD/ha por punto vienen de xcut.md.

## Goals / Non-Goals

**Goals:** índice reproducible, acotado, monótono donde importa, explicable por componente y por campaña, con cero números agronómicos en el código.

**Non-Goals:** predecir MO o carbono en t/ha a futuro; dinámica multi-año (el índice describe la intensidad del ciclo, no su acumulación en H años; la acumulación la decide el actor vía α).

## Decisions

### 1. Fórmula del índice

Sea L la longitud del ciclo (campañas), C_p el conjunto de cultivos de la campaña p.

```
ΔSuelo(r) = 100 · Σ_k w_k · s_k(r)          k ∈ {cov, carb, n, weed, root}
Σ_k w_k = 1, w_k >= 0                         (A-SOIL-01)
s_k = clamp((x_k − ref_k) / scale_k, −1, 1)   para cov, carb, n
s_k = 2·x_k − 1                               para weed, root (x_k ∈ [0, 1])
```

Componentes brutos:

- **Cobertura.** Para cada campaña p, `Cov_p = |∪_{c ∈ C_p} [siembra_c, cosecha_c + persist_c]| / 365` sobre un calendario de 365 días que empieza en el mes 1 de campaña (julio); los intervalos que cruzan el fin de campaña se recortan y el excedente se suma a la campaña siguiente del ciclo (módulo L). `x_cov = (1/L)·Σ_p Cov_p`. Fechas de siembra y cosecha: A-AGR-01 (calendario único de domain-models). `persist_c`: A-SOIL-02. `ref_cov`, `scale_cov`: A-SOIL-03.
- **Carbono.** `x_carb = (1/L)·Σ_p Σ_{c ∈ C_p} Caporte_c` en kg C/ha/año (A-SOIL-04). `ref_carb` (mantenimiento) y `scale_carb`: A-SOIL-05.
- **Nitrógeno.** `x_n = (1/L)·Σ_p Σ_{c ∈ C_p} Nbal_c` en kg N/ha/año (A-SOIL-06, signo dado por el supuesto). `ref_n = 0` por definición (balance neutro) y `scale_n`: A-SOIL-07.
- **Malezas.** `D` = especies distintas (soja, maíz, trigo, vicia, centeno, avena), `f_w` = fracción de campañas con cultivo de invierno. `x_weed = β·min(1, (D−1)/(D_max−1)) + (1−β)·f_w`, con `D_max` y `β ∈ [0,1]` en A-SOIL-08.
- **Raíces.** `x_root = (1/L)·Σ_p min(1, Σ_{c ∈ C_p} ρ_c)`, con `ρ_c ∈ [0,1]` en A-SOIL-09.

Contribución por campaña: cada componente lineal en la campaña (cov, carb, n, root) se reparte proporcional a su aporte bruto de la campaña; el de malezas, que es de ciclo, se reparte en partes iguales. Se informa para que explanations diga "el centeno de la campaña 2 aporta X puntos".

Invariancia al orden: todas las fórmulas son promedios o conjuntos sobre las campañas; el único acoplamiento (rastrojo que cruza a la campaña siguiente) es cíclico, por lo que rotar el ciclo no cambia el resultado.

### 2. Monotonicidad (argumento)

Agregar un cultivo de servicio c* a una campaña sin invierno: la unión de intervalos solo crece (cov no baja); `Caporte_c* >= 0` se valida al cargar el supuesto (carb no baja); `f_w` sube y `D` no baja (weed no baja); `ρ_c* >= 0` y el min(1, ·) es monótono (root no baja). Nbal puede ser negativo (inmovilización en centeno) y por eso el total no se garantiza: se documenta y se testea explícitamente. Alternativa descartada: forzar Nbal >= 0 para servicios (sería inventar agronomía para que cierre una propiedad).

### 3. NDVI: evidencia, no entrada

El NDVI del lote describe la rotación actual, no las alternativas: usarlo como entrada favorecería o castigaría solo a la actual y rompería la comparación contrafactual. Se usa para (a) Evidencia de cobertura observada (fracción de compuestos MODIS 16 días o HLS con NDVI > umbral A-SOIL-10 por campaña) y (b) chequeo de consistencia contra `Cov_p` modelado de la rotación actual, con tolerancia A-SOIL-11. El resumen mensual llega ya resuelto en EngineInput (nasa-ingestion), el motor no lo busca.

### 3b. Calendario de suelo desnudo

Con los mismos intervalos de la cobertura, por mes calendario m (1 a 12): `bare_m` = días del mes sin cultivo vivo y `uncovered_m` = días sin cultivo vivo ni rastrojo persistente (A-SOIL-02), ambos promediados sobre las L campañas del ciclo. La evidencia observada sale del resumen NDVI mensual del lote: fracción de compuestos válidos con NDVI < A-SOIL-10 por mes, solo para la rotación actual. No se agregan supuestos. Alternativa descartada: calendario por campaña de julio a junio (menos legible para el productor que meses calendario).

### 3b2. Lluvia sobre suelo desnudo (P0 la métrica, P1 el visual)

Con los intervalos del calendario de suelo desnudo, para cada escenario s y día d de la campaña: `rain_bare_s = Σ_d P_s,d · 1[d sin cultivo vivo ni rastrojo]`, con P la lluvia diaria POWER PRECTOTCORR que ya viaja en `EngineInput` (la misma fuente de la clasificación de años, no la regla conservadora de water-feasibility, que es para el balance). Se promedia sobre las L campañas del ciclo y se pondera con w_s; también por mes calendario. No se agregan supuestos. Alternativas descartadas: sumarla a ΔSuelo (duplica el componente de cobertura y mete mm en un índice adimensional); usar IMERG (menos años de serie).

### 3c. Pesos efectivos por prioridades

soil-impact recibe los w_k efectivos ya re-ponderados por actor-profiles (A-ACT-07, una prioridad por componente) y verifica que sumen 1. La re-ponderación no toca los componentes, así que cotas y monotonicidad de componentes se mantienen.

### 4. Errores

`MissingAssumptionError(missing: list[(assumption_id, crop)])` recolecta todos los faltantes antes de fallar. `InvalidAssumptionError` para pesos que no suman 1 (tolerancia 1e-9) o coeficientes fuera de dominio. rotation-engine decide qué hacer (ver su spec).

### Alternativas descartadas

- **Índice multiplicativo** (producto de factores): un componente en cero anula todo y es difícil de explicar en una frase.
- **Soil Conditioning Index (NRCS)** tal cual: requiere erosión y operaciones de labranza que no tenemos; tomamos su idea (MO, operaciones, erosión) pero simplificada y declarada.
- **Escala sin acotar (kg C/ha)**: α tendría unidades distintas por componente y el slider no sería comparable entre actores.
- **Calcular sobre H años**: duplicaría el efecto del horizonte que ya modela el actor; se mantiene por ciclo.

## Supuestos introducidos (registro `assumptions.yaml`, todos PENDING_AFA)

| id | descripción | unidad | fuente inicial |
|---|---|---|---|
| A-SOIL-01 | pesos w_k de los 5 componentes (ejemplo: 0.25/0.25/0.15/0.20/0.15) | adim. | pendiente AFA |
| A-SOIL-02 | persistencia de cobertura del rastrojo post cosecha por cultivo | días | pendiente AFA; literatura de cobertura de rastrojos en SD |
| A-SOIL-03 | referencia y escala de fracción cubierta | fracción | pendiente AFA |
| A-SOIL-04 | aporte de C de rastrojo/biomasa por cultivo (gramíneas > leguminosas) | kg C/ha | pendiente AFA; índices de cosecha publicados (ej. INTA) |
| A-SOIL-05 | aporte de C de mantenimiento de MO y escala | kg C/ha/año | pendiente AFA |
| A-SOIL-06 | balance neto de N por cultivo (fijación, extracción, inmovilización) | kg N/ha | pendiente AFA |
| A-SOIL-07 | escala de normalización del balance de N | kg N/ha/año | pendiente AFA |
| A-SOIL-08 | D_max de especies y peso β diversidad vs invierno | adim. | pendiente AFA |
| A-SOIL-09 | coeficiente de efecto radicular por cultivo (fasciculada vs pivotante) | [0,1] | pendiente AFA |
| A-SOIL-10 | umbral de NDVI para considerar suelo cubierto | NDVI | pendiente AFA; literatura MODIS |
| A-SOIL-11 | tolerancia entre cobertura modelada y observada | fracción | pendiente AFA |

## Risks / Trade-offs

- [Coeficientes inventados parecen verdad] → todos con `validation_status` visible en la salida y en el README; los valores de ejemplo solo en fixtures de demo.
- [Índice domina o desaparece según α] → actor-profiles expone sensibilidad sobre α; explanations muestra el término en USD/ha.
- [Ventanas de cultivo duplicadas entre módulos] → única fuente: A-AGR-01, compartido con water-feasibility y economics.

## Open Questions (para AFA)

- ¿La compactación cambia la rotación en la práctica? Si sí, pasa de riesgo a componente con peso.
- Valores y fuente de persistencia de rastrojo y aporte de C en sur de Santa Fe.
- ¿Conviene diferenciar vicia (leguminosa) de centeno/avena en N con inmovilización explícita?
