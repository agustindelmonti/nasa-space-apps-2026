# Spec Delta

## Purpose

Calcula un índice ΔSuelo adimensional, acotado y explicable por componentes para cada rotación, de modo que el motor pueda ponderar la salud del suelo con α y la explicación pueda mostrar qué suma y qué resta, con todos los coeficientes trazables a supuestos validables por AFA.

## ADDED Requirements

### Requirement: Índice ΔSuelo acotado por rotación y ciclo
El sistema MUST calcular para cada rotación un índice ΔSuelo adimensional por ciclo, acotado en el intervalo cerrado [-100, +100], como suma ponderada de cinco componentes normalizados en [-1, +1]: cobertura, carbono, nitrógeno, malezas y raíces. Los pesos MUST ser no negativos y sumar 1. El índice MUST ser independiente del orden en que se listan las campañas del ciclo.

#### Scenario: Índice dentro de cotas
- **GIVEN** cualquier rotación válida del catálogo y un juego de supuestos A-SOIL válido
- **WHEN** se calcula ΔSuelo
- **THEN** el valor está entre -100 y +100 inclusive y cada componente está entre -1 y +1

#### Scenario: Rotación de campañas equivalente
- **GIVEN** la rotación [maíz temprano], [soja de primera] y la rotación [soja de primera], [maíz temprano]
- **WHEN** se calcula ΔSuelo para ambas
- **THEN** los índices y los componentes son idénticos

#### Scenario: Pesos inválidos
- **WHEN** el juego de supuestos trae pesos de componentes que suman 0.9
- **THEN** el cálculo falla con un error tipado que nombra el supuesto de pesos (ejemplo A-SOIL-01)

### Requirement: Componente de cobertura
El componente de cobertura MUST derivarse de la fracción anual promedio de días con suelo cubierto, contando días de cultivo vivo (según ventanas de siembra y cosecha del catálogo) más días de persistencia de rastrojo posteriores a la cosecha, como unión de intervalos en el calendario de cada campaña (un día cubierto dos veces cuenta una vez).

#### Scenario: Soja continua con barbecho invernal
- **GIVEN** soja de primera sola, con ventana y persistencia de rastrojo tomadas de los supuestos
- **WHEN** se calcula la fracción de días cubiertos
- **THEN** los días del barbecho invernal sin cultivo ni rastrojo persistente no suman cobertura

#### Scenario: Superposición no se cuenta doble
- **GIVEN** un cultivo de servicio cuyo intervalo se superpone con la persistencia del rastrojo del cultivo anterior
- **WHEN** se calcula la cobertura
- **THEN** los días superpuestos se cuentan una sola vez

### Requirement: Componente de carbono por rastrojo y biomasa
El componente de carbono MUST derivarse del aporte anual promedio de carbono de rastrojo y biomasa de los cultivos de la rotación, usando un aporte por cultivo dado por supuesto (A-SOIL-04), normalizado contra un valor de referencia y una escala también supuestos (A-SOIL-05).

#### Scenario: Gramínea aporta más que leguminosa
- **GIVEN** supuestos donde el aporte de carbono del maíz es mayor que el de la soja
- **WHEN** se compara soja continua contra maíz/soja
- **THEN** el componente de carbono de maíz/soja es mayor o igual que el de soja continua

### Requirement: Componente de balance de nitrógeno
El componente de nitrógeno MUST derivarse del balance neto anual promedio de N por cultivo dado por supuesto (A-SOIL-06), donde leguminosas y gramíneas tienen coeficientes propios, normalizado por una escala supuesta (A-SOIL-07). El signo del coeficiente MUST provenir del supuesto, no del código.

#### Scenario: Vicia como leguminosa de servicio
- **GIVEN** un supuesto con balance de N positivo para vicia
- **WHEN** se agrega vicia antes de la soja en una rotación
- **THEN** el componente de nitrógeno no disminuye

### Requirement: Componente de malezas por diversidad
El componente de malezas MUST combinar la cantidad de especies distintas del ciclo (soja de primera y de segunda cuentan como una especie; maíz temprano y tardío como una) relativa a un máximo supuesto, y la fracción de campañas con cultivo de invierno (renta o servicio), con pesos supuestos (A-SOIL-08).

#### Scenario: Soja continua en el mínimo
- **WHEN** se calcula el componente de malezas para soja continua sin cultivo de invierno
- **THEN** el componente vale -1

#### Scenario: Rotación diversa con invierno
- **GIVEN** trigo/soja de segunda → maíz temprano
- **WHEN** se calcula el componente de malezas
- **THEN** el valor es mayor que el de soja continua y maíz/soja

### Requirement: Componente de raíces y compactación
El componente de raíces MUST derivarse, por campaña, de la suma acotada a 1 de los coeficientes de efecto radicular de sus cultivos (A-SOIL-09, en [0, 1]), promediada sobre las campañas del ciclo. Un indicador de compactación del Suelo MUST NOT modificar el índice; si existe y es alto MUST generar una entrada de riesgo de suelo para la explicación.

#### Scenario: Compactación informada
- **GIVEN** un Suelo con indicador de compactación alto
- **WHEN** se calcula ΔSuelo
- **THEN** el índice es igual al calculado sin el indicador y la salida incluye un riesgo de tipo suelo que cita el indicador

### Requirement: Monotonicidad al agregar cultivo de servicio
Agregar un cultivo de servicio a una campaña que no tenía cultivo de invierno MUST NOT reducir los componentes de cobertura, carbono, malezas ni raíces. Si el componente de nitrógeno o el índice total disminuyen por el signo de un supuesto, la salida MUST seguir siendo válida y el caso MUST quedar cubierto por un test que documente la causa.

#### Scenario: Centeno sobre soja continua
- **GIVEN** soja continua y la misma rotación con centeno de servicio antes de la soja
- **WHEN** se calcula ΔSuelo para ambas con cualquier juego de supuestos válido
- **THEN** cobertura, carbono, malezas y raíces de la segunda son mayores o iguales que los de la primera

### Requirement: Supuestos explícitos y sin valores por defecto
Todo coeficiente usado por el índice MUST llegar en la entrada del motor como supuesto resuelto con id `A-SOIL-NN`, valor, unidad y fuente o "pendiente AFA". Si falta un coeficiente para un cultivo presente en la rotación, el cálculo MUST fallar con un error tipado que liste todos los ids y cultivos faltantes, sin usar valores por defecto.

#### Scenario: Falta el aporte de carbono del centeno
- **GIVEN** una rotación con centeno y un juego de supuestos sin aporte de carbono para centeno
- **WHEN** se calcula ΔSuelo
- **THEN** el cálculo falla con un error tipado que menciona A-SOIL-04 y COVER_RYE

### Requirement: Salida con procedencia y desglose
La salida MUST incluir ΔSuelo como valor con procedencia DERIVED que lista los ids de supuestos usados y el método, el valor bruto y normalizado de cada componente, su peso y su contribución al índice, y la contribución por campaña del ciclo. La suma de contribuciones MUST coincidir con el índice con la precisión declarada.

#### Scenario: Desglose suma al total
- **WHEN** se calcula ΔSuelo para maíz/soja con cultivo de servicio
- **THEN** la suma de las contribuciones por componente es igual al índice redondeado a 2 decimales

### Requirement: NDVI como evidencia de cobertura observada
El NDVI histórico MUST NOT ser entrada del índice. Cuando la entrada traiga la serie NDVI del lote, el sistema MUST calcular la fracción de días con NDVI sobre un umbral supuesto (A-SOIL-10) como cobertura observada de la rotación actual, emitirla como Evidencia OBSERVED/DERIVED y, si difiere de la cobertura modelada más que una tolerancia supuesta (A-SOIL-11), emitir un Faltante.

#### Scenario: Discrepancia entre modelo y satélite
- **GIVEN** una rotación actual declarada como soja continua y una serie NDVI que muestra verde en invierno todos los años
- **WHEN** se calcula ΔSuelo con chequeo NDVI
- **THEN** el índice no cambia, se emite Evidencia de cobertura observada y un Faltante que pide confirmar la rotación actual

#### Scenario: Sin serie NDVI
- **WHEN** la entrada no trae NDVI
- **THEN** el índice se calcula igual y se registra un Faltante de baja severidad sobre cobertura observada
