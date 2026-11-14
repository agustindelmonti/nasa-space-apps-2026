# Spec Delta

## Purpose

Define los perfiles de actor (propietario, arrendatario, cooperativa, banco y personalizados) que parametrizan la función objetivo, valida los sliders y expone cómo cambia el ranking al variar α o λ, para mostrar el trade-off sin que la herramienta decida.

## ADDED Requirements

### Requirement: Perfiles predefinidos como supuestos
El sistema MUST ofrecer los perfiles OWNER, TENANT, COOP y BANK, cada uno con H, α (USD/ha por punto de ΔSuelo), λ, i y restricciones (doble cultivo, cultivo de servicio, capital máximo o sin tope). Cada valor MUST tener procedencia ASSUMPTION con su id (A-ACT-01 a A-ACT-04), fuente o "pendiente AFA" y estado de validación.

#### Scenario: Listado de perfiles
- **WHEN** se piden los perfiles predefinidos
- **THEN** se obtienen exactamente OWNER, TENANT, COOP y BANK, en ese orden, cada parámetro con su assumption_id y estado PENDING_AFA mientras AFA no lo valide

#### Scenario: Horizontes contrastantes
- **GIVEN** los valores de ejemplo de los supuestos (OWNER H=10, TENANT H=1)
- **WHEN** se cargan los perfiles
- **THEN** el H de OWNER es mayor que el de TENANT y ambos vienen del registro de supuestos, no del código

### Requirement: Nivel de cola del Riesgo
El nivel q de la cola usada para el expected shortfall de márgenes MUST ser un supuesto global A-ACT-05 con valor en (0, 1], común a todos los perfiles, y MUST viajar en la entrada del motor. El Riesgo MUST NOT definirse como el margen de los años de clase DRY.

#### Scenario: q fuera de rango
- **WHEN** el registro trae q = 0
- **THEN** la carga falla con un error tipado que nombra A-ACT-05

### Requirement: Perfil personalizado validado
Un perfil personalizado MUST construirse desde un perfil base predefinido más modificaciones de H, α, λ, i y restricciones. Cada valor MUST estar dentro de los límites de slider A-ACT-06 (H entero). Los campos modificados MUST tener procedencia USER_INPUT, los no modificados MUST conservar la del base, y el perfil MUST identificarse como CUSTOM con referencia a su base.

#### Scenario: Slider fuera de rango
- **GIVEN** límites de ejemplo λ en [0, 3]
- **WHEN** se pide un perfil personalizado con λ = 5
- **THEN** la validación falla indicando el campo λ y el rango permitido

#### Scenario: Personalizado desde TENANT
- **WHEN** se crea un perfil desde TENANT cambiando solo α a 2
- **THEN** el perfil es CUSTOM con base TENANT, α tiene procedencia USER_INPUT y H, λ, i conservan sus assumption_id de TENANT

### Requirement: Arrendatario sin arrendamiento
Cuando el perfil efectivo es TENANT o un CUSTOM con base TENANT y los parámetros económicos no traen arrendamiento, la evaluación MUST incluir un Faltante que explique que el margen y el capital de trabajo se calcularon sin arrendamiento.

#### Scenario: TENANT sin alquiler cargado
- **GIVEN** perfil TENANT y parámetros sin arrendamiento
- **WHEN** se evalúa el lote
- **THEN** la salida incluye el Faltante de arrendamiento y la evaluación se completa

### Requirement: Rankings distintos entre actores en la demo
Con el lote demo y sus fixtures, MUST existir al menos un par de perfiles predefinidos cuyos rankings difieran (distinto orden de ids elegibles o distinta primera opción). Un test automatizado MUST verificarlo sin red. Si deja de cumplirse, MUST corregirse revisando datos o supuestos documentados, nunca con un ajuste oculto.

#### Scenario: OWNER y TENANT difieren
- **GIVEN** el fixture del lote demo-casilda
- **WHEN** se evalúa con los cuatro perfiles predefinidos
- **THEN** al menos dos de los cuatro rankings son distintos y el test informa qué par difiere

### Requirement: Sensibilidad en grilla determinista
El sistema MUST ofrecer un caso de uso de sensibilidad, expuesto en `POST /api/v1/sensitivity`, que dados una entrada base, un parámetro (α o λ) y una grilla [mín, máx] con n puntos equiespaciados (2 a 41, extremos incluidos, dentro de A-ACT-06) devuelva por valor el ranking de ids y los términos del puntaje, con el resto del perfil fijo.

#### Scenario: Grilla sobre λ
- **GIVEN** la entrada demo con perfil OWNER
- **WHEN** se pide sensibilidad sobre λ de 0 a 2 con 5 puntos
- **THEN** la respuesta trae los valores 0, 0.5, 1, 1.5, 2 en ese orden, cada uno con su ranking

#### Scenario: Grilla inválida
- **WHEN** se pide sensibilidad con n = 1
- **THEN** la validación falla indicando el rango permitido de n

### Requirement: Puntos de quiebre exactos
Como el puntaje es lineal en α y en λ, la sensibilidad MUST informar los puntos de quiebre exactos dentro del rango pedido donde dos elegibles intercambian posición, calculados sobre puntajes sin redondear, ordenados por valor y luego por par de ids.

#### Scenario: Quiebre analítico
- **GIVEN** dos elegibles A y B con VAN−λ·Riesgo fijos y ΔSuelo de ejemplo 10 y 30, con A − B = 100 USD/ha en α=0
- **WHEN** se pide sensibilidad sobre α en [0, 10]
- **THEN** se informa un quiebre en α = 5 donde B pasa a A

### Requirement: Sensibilidad sin efectos colaterales
La sensibilidad MUST ser determinista y pura como el motor: misma entrada y grilla, mismos bytes. La elegibilidad de cada candidata MUST NOT cambiar a lo largo de la grilla porque α y λ no intervienen en las restricciones.

#### Scenario: Repetición idéntica
- **WHEN** se ejecuta dos veces la misma sensibilidad
- **THEN** las salidas canónicas son idénticas byte a byte

### Requirement: Pesos de prioridades del productor
Un perfil MUST admitir pesos opcionales en [0, 1] para EROSION_COVER, OM_CARBON, NITROGEN, WEED_CONTROL y ROOTS, uno por componente de ΔSuelo (cobertura, carbono, N, malezas, raíces). Las prioridades MUST solo re-ponderar los w_k de A-SOIL-01 con A-ACT-07 y renormalizar. El puntaje MUST seguir siendo VAN + α·ΔSuelo − λ·Riesgo sin términos agregados. Con todo en 0 la salida MUST ser idéntica a sin prioridades.

#### Scenario: Prioridades nulas no cambian nada
- **GIVEN** la entrada demo con OWNER
- **WHEN** se evalúa con todas las prioridades en 0 y sin prioridades
- **THEN** puntajes, ranking, desglose y pesos efectivos son idénticos y los pesos efectivos coinciden con A-SOIL-01

#### Scenario: Prioridad de nitrógeno
- **GIVEN** A-SOIL-01 de ejemplo con peso de N 0.15, A-ACT-07 = 1 y prioridad NITROGEN = 1
- **WHEN** se calculan los pesos efectivos
- **THEN** el peso de N es 0.30 / 1.15 antes de redondear, los pesos suman 1 y el resto baja en la misma proporción

#### Scenario: Prioridad de agua rechazada en el perfil
- **WHEN** se crea un perfil con una prioridad WATER o SUPPLEMENTAL_INCOME
- **THEN** la validación falla por campo no declarado, porque esas preferencias son de presentación y viajan fuera de `EngineInput`

#### Scenario: Monotonicidad preservada
- **GIVEN** cualquier juego de prioridades válido
- **WHEN** se corren las propiedades de λ y α de quality
- **THEN** ambas siguen valiendo, porque las prioridades solo cambian los pesos de ΔSuelo y no agregan términos que dependan de α ni λ

### Requirement: Indicador de robustez del ranking
El sistema MUST ofrecer un caso de uso determinista que, para una entrada base, informe por rotación en cuántas clases de año (DRY, NORMAL y WET, vía `year_class_filter`) sale primera entre las elegibles con el perfil efectivo, y en cuántos de los 4 perfiles predefinidos sale primera sin filtro. Una clase sin escenarios MUST excluirse del denominador. MUST NOT emitir porcentajes ni etiquetas de confianza.

#### Scenario: Conteo de robustez
- **GIVEN** la entrada demo donde R_MAIZE_SOY_COVER sale primera con filtro DRY y NORMAL pero no con WET, y primera para OWNER, COOP y BANK pero no para TENANT
- **WHEN** se calcula la robustez
- **THEN** R_MAIZE_SOY_COVER informa 2 de 3 clases y 3 de 4 perfiles, con la lista de clases y perfiles donde gana

#### Scenario: Clase sin años
- **GIVEN** una entrada sin escenarios WET
- **WHEN** se calcula la robustez
- **THEN** el denominador de clases es 2 y la salida declara que WET no tuvo escenarios

#### Scenario: Robustez reproducible
- **WHEN** se calcula dos veces la robustez con la misma entrada
- **THEN** las salidas canónicas son idénticas byte a byte y el puntaje de la entrada base no cambia

### Requirement: Ventanas de maquinaria del productor
El perfil MUST admitir ventanas de maquinaria opcionales (meses 1 a 12 por operación SOWING y HARVEST) como USER_INPUT, MUST copiarlas al perfil efectivo de `EngineInput` y rotation-engine MUST aplicarlas como restricción. Sin ventanas MUST NOT haber restricción de maquinaria.

#### Scenario: Ventanas en el perfil efectivo
- **WHEN** se crea un perfil personalizado con siembra disponible en octubre y noviembre
- **THEN** el perfil efectivo trae esas ventanas con procedencia USER_INPUT y el `input_hash` cambia respecto del perfil sin ventanas

#### Scenario: Elegibilidad estable en la sensibilidad
- **GIVEN** un perfil con ventanas de maquinaria que excluyen una candidata
- **WHEN** se corre la sensibilidad sobre λ
- **THEN** esa candidata sigue no elegible en todos los puntos de la grilla
