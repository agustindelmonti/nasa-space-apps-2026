# Tasks: field-measurement (P2)

## 1. Modelos y supuestos (P2)

- [ ] 1.1 Usar `FIELD_HAMMER` del enum de datasets de `domain-models` y definir modelos frozen `FieldSession`, `FieldPoint`, `Impact`, `PointSummary`; verificar con tests de validación (escenarios "Muestreo insuficiente", "Altura distinta de la estándar de v0" y "Punto fuera del lote")
- [ ] 1.2 Cargar A-FLD-01 a A-FLD-06 en `assumptions.yaml` (PENDING_AFA), con A-FLD-02 corregido a masa ~2 kg, alturas 150, 300 y 450 mm y estándar v0 150 mm; verificar con test que la aplicación los resuelve y que A-FLD-02 ya no dice 30 cm

## 2. Procesamiento (P2)

- [ ] 2.1 Implementar descarte de asentamiento, golpes saturados, mediana y coeficiente de variación por punto; verificar con tests "Sensor saturado", "Pocos golpes válidos", "Punto consistente" y "Punto inconsistente"
- [ ] 2.2 Implementar normalización relativa por sesión con categorías por terciles de posición y procedencia DERIVED con A-FLD-05; verificar con tests "Índice relativo", "Muy pocos puntos", "Sin mezcla de sesiones" y "Procedencia del índice"
- [ ] 2.3 Implementar lista fija de limitaciones y la tarjeta campo vs satélite con SMAP desde caché; verificar con tests "Limitaciones presentes", "Tarjeta campo vs satélite", "Sin SMAP para la fecha" y "Humedad del suelo como advertencia"

## 3. API y almacenamiento (P2)

- [ ] 3.1 Implementar guardado idempotente en `data/field/` y rutas POST/GET con errores tipados; verificar con tests de API "Sesión válida", "Lote inexistente", "Reenvío por mala conexión" y "Mismo id, otro contenido"
- [ ] 3.2 Verificar aislamiento del motor con test "Ranking intacto" (misma salida y `input_hash` antes y después de registrar una sesión)

## 4. Captura web (P2)

- [ ] 4.1 Pantalla de captura con DeviceMotion (permiso iOS, medición de frecuencia efectiva, detección de impactos) y fixture de sesión de ejemplo para la demo offline; verificar en un celular real contra el deploy HTTPS y con un test de componente que procesa una señal grabada

## 5. Demo de cajas (P2)

- [ ] 5.1 Armar el accesorio v0 (carro de ~2 kg, riel o tubo, tope a 150 mm), grabar la sesión con caja suelta y compactada (2 puntos por caja) y guardarla como fixture; verificar con tests "Suelta contra compactada" y "Cajas con orden invertido"
