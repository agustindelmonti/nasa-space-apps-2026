# Tasks: explanations

## 1. Formato numérico y citas (P0)

- [ ] 1.1 Implementar `format_ar` con tabla de decimales por unidad y `parse_ar_numbers`; tests de "Margen con miles", "NDVI con decimales", "Año sin separador" e ida y vuelta (hypothesis) en verde
- [ ] 1.2 Implementar documento citable (salida + entrada con mismo `input_hash`), resolución por JSON Pointer y registro de citas; test que falla si los hashes no coinciden y test de resolución de ruta en verde
- [ ] 1.3 Implementar lista blanca de tokens con dígitos y el test de trazabilidad genérico (extraer, excluir, buscar en citas); test "Número inventado detectado" en verde con una plantilla trampa

## 2. Explicación por rotación (P0)

- [ ] 2.1 Definir modelos Pydantic `Explanation`, `RotationExplanation`, `Citation`, `Disclaimer` (frozen, extra=forbid); test de "Hash de entrada propagado" en verde
- [ ] 2.2 Plantillas de "por qué" (posición, actual, factibilidad, término dominante, diferencia contra la actual desde `score_delta_vs_current` o comparación cualitativa); tests "Término dominante de suelo", "Rotación no factible", "Diferencia contra la actual citada" y "Comparación sin número disponible" en verde
- [ ] 2.3 Plantillas de evidencia (con limitación desde catálogo de datasets), beneficios, faltantes y riesgos con marca de supuesto; tests "Evidencia de humedad SMAP", "Riesgo basado en supuesto" y "Faltantes vacíos" en verde
- [ ] 2.4 Resumen comparativo y leyendas obligatorias; tests "Rotación actual en tercer lugar" y presencia de `disclaimers` en verde

- [ ] 2.5 Plantillas de incertidumbre (rango de margen y rango hídrico por clase) y de riesgo como cola de márgenes; tests "Rango de margen citado", "Rango hídrico citado", "Clase vacía" y "Riesgo con su definición" en verde
- [ ] 2.6 Plantillas de calendario de suelo desnudo (con evidencia NDVI) y de vulnerabilidad (helada y déficit; calor y lluvia extrema cuando vengan en la salida); tests "Invierno desnudo en soja continua", "Vulnerabilidad por mes" y "Calendario sin meses vulnerables" en verde
- [ ] 2.7 Tarjeta fija de 5 secciones con rótulos constantes y leyenda de cierre, y frase de factibilidad desconocida; tests "Cinco secciones presentes", "Tarjeta cierra con la leyenda" y "Factibilidad desconocida" en verde
- [ ] 2.8 Plantillas de años con pérdida, peor año y lluvia sobre suelo desnudo; tests "Pérdida en años reales", "Sin años con pérdida" y "Servicio contra soja continua" en verde

- [ ] 2.9 Crear `data/forbidden_phrases.yaml` con la lista mínima (incluidas "% de confianza", "predice" y "garantiza") y el test de lenguaje sobre todas las plantillas y fixtures; tests "Expresión prohibida en plantilla" y "Porcentaje de confianza prohibido" en verde

## 3. Formatos de salida (P0)

- [ ] 3.1 Renderizador de texto web con marcado mínimo y lista de supuestos; tests "Sin HTML embebido" y "Precio supuesto en texto web" en verde; snapshot de la fixture `demo-casilda` generado
- [ ] 3.2 Renderizador WhatsApp y particionador determinista; tests "Texto que entra en un mensaje", "Texto largo partido", "Partición estable", "Leyendas en WhatsApp particionado" y "Supuestos en WhatsApp" en verde
- [ ] 3.3 Test de determinismo: generar los tres formatos en dos subprocesos y comparar bytes; test "Sin acceso a red" con socket bloqueado en verde

## 4. Glosario (P1)

- [ ] 4.1 Escribir `data/glossary.yaml` con las 8 entradas (incluidas `heat_stress` y el párrafo de combinación satélite y campo) y huecos al catálogo de datasets; tests "Glosario completo", "Combinar satélite y campo" y "Definición corta para WhatsApp" en verde
- [ ] 4.2 Resolver huecos de resolución desde el catálogo de `nasa-ingestion`; test "Resolución desde el catálogo" en verde
- [ ] 4.3 Remisión al glosario en la primera mención de cada término; test "Término técnico con remisión" en verde

## 5. Propietario vs arrendatario, miradas y robustez (P1)

- [ ] 5.1 Sección comparativa OWNER vs TENANT con validación de lote; tests "Ranking que cambia por horizonte" y "Salidas de lotes distintos" en verde
- [ ] 5.2 Tres miradas deterministas en el estructurado y el texto web; tests "Miradas completas" y "Mirada sin contenido" en verde
- [ ] 5.3 Plantillas de robustez, de lluvia POWER vs IMERG y de orden de presentación; tests "Robustez citada", "Discrepancia contada" y "Primero las no riesgosas en agua" en verde

## 6. Ficha y pulido (P2)

- [ ] 6.1 Revisión de redacción rioplatense con alguien del equipo no técnico; bump de `templates_version` y snapshots regenerados sin otros diffs (`uv run pytest -k explanations`)
- [ ] 6.2 Implementar `export_sheet` con JSON canónico y texto con marcado mínimo; tests "Ficha completa y trazable" y "Ficha con factibilidad desconocida" en verde
