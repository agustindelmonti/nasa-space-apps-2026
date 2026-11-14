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
El nivel q de la cola usada para el expected shortfall MUST ser un supuesto global A-ACT-05 con valor en (0, 1], común a todos los perfiles, y MUST viajar en la entrada del motor.

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
El sistema MUST ofrecer un caso de uso de sensibilidad que, dados una entrada base, un parámetro (α o λ) y una grilla [mín, máx] con n puntos equiespaciados (2 a 41, extremos incluidos, dentro de A-ACT-06), devuelva para cada valor el ranking de ids y los términos del puntaje, manteniendo fijo el resto del perfil.

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
