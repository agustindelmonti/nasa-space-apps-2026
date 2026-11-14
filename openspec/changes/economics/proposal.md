# Proposal: economics

**Prioridad:** P0 (el VAN del margen es el término dominante del puntaje y la base del Riesgo).

## Why

La comparación de rotaciones solo es creíble si el margen se calcula con parámetros visibles, con fuente y fecha, y nunca con precios o retenciones escondidos en el código. Además el desafío pide mirar corto vs largo plazo y capital de trabajo por mes, que es justo lo que separa al arrendatario del propietario.

## What Changes

- Margen bruto por cultivo, campaña y escenario climático: rinde según la clase de año × precio neto de retención, menos costos directos, cosecha, comercialización y flete; arrendamiento opcional a nivel campaña.
- Todo parámetro sale de ParámetrosEconómicos con procedencia, fuente y fecha; ningún valor por defecto sin marca.
- VAN a tasa i y horizonte H, repitiendo el ciclo de la rotación y promediando sobre las fases de inicio para tratar ciclos parciales sin depender del orden en que se escribió la rotación.
- Capital de trabajo por mes desde un calendario de egresos e ingresos (supuesto), con pico de necesidad financiera usado como restricción del actor.
- Error tipado `MissingEconomicParameter` que lista todos los faltantes de una rotación de una vez; rotation-engine lo convierte en rotación no elegible con Faltantes.
- Base de precio declarada (FOB vs disponible/FAS) para no aplicar la retención dos veces.

## Capabilities

### New Capabilities
- `economics`: margen bruto por cultivo/campaña/escenario, VAN, capital de trabajo mensual y manejo de parámetros faltantes.

### Modified Capabilities
- Ninguna.

## Impact

- Módulo puro `fieldshift.engine.economics`. Depende de `domain-models` (ParámetrosEconómicos, Rotación, EscenarioClimático, PValue) y de la clase de año por estación que produce `climate-scenarios`.
- Consumidores: `rotation-engine` (E[Margen], VAN, Riesgo, restricción de capital), `explanations`, `actor-profiles` (arrendamiento para TENANT).
- Usa los agregados acordados en domain-models: base de precio, modo de costo de cosecha, comercialización, flete por t y arrendamiento opcional.
- La matriz (posición, año) también alimenta el rango de margen por clase anual que arma rotation-engine para explicar la incertidumbre.

## Fuera de alcance

- Precios futuros, curvas forward, inflación o tipo de cambio: todo en USD constantes de la fecha de referencia.
- Impuestos a las ganancias, amortizaciones, costos fijos de estructura (margen bruto, no resultado neto).
- Seguros agrícolas y coberturas de precio.
- Descarga automática de precios de pizarra: los parámetros los carga el usuario o el fixture de demo.
