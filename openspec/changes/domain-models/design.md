# Design: domain-models

## Context

Repo vacío. Ver proposal.md. El resto de las capabilities importa estos modelos, así que se implementan primero y se congelan temprano (cambios posteriores solo aditivos).

## Goals / Non-Goals

**Goals:** un único paquete de dominio sin dependencias de I/O; procedencia uniforme; hash y serialización canónica reutilizables por motor, API y tests.

**Non-Goals:** ORM, persistencia, versionado de esquemas entre releases.

## Decisions

1. **Pydantic v2 con `ConfigDict(frozen=True, extra="forbid", strict=True)`** en una base común `DomainModel`. Alternativa descartada: dataclasses + validación manual (más código, sin JSON Schema gratis para el front).
2. **`PValue` (valor con procedencia)** genérico: `value: float`, `unit: Unit (Literal)`, `provenance: Provenance`. `Provenance` es una unión discriminada por `kind` para que OBSERVED exija `source`, ASSUMPTION exija `assumption_id`, DERIVED exija `derived_from` + `method`. Alternativa descartada: un solo modelo con todos los campos opcionales (deja pasar estados inválidos).
3. **Registro de supuestos** (`assumptions.yaml` versionado en el repo) cargado por `data/` y referenciado por id. El dominio solo valida el formato del id; la existencia del id la valida la capa de aplicación. Esto deja el catálogo editable por agrónomos sin tocar código.
4. **Catálogo de cultivos como `StrEnum`** (`SOY_1ST`, `SOY_2ND`, `MAIZE_EARLY`, `MAIZE_LATE`, `WHEAT`, `COVER_VETCH`, `COVER_RYE`, `COVER_OAT`) + tabla de atributos estáticos (estación, tipo, familia). Atributos agronómicos con números (Kc, ventanas) viven en supuestos, no en el enum.
5. **Floats, no Decimal**, con redondeo en la serialización canónica (`round(x, ndigits)` por campo vía `Annotated` + metadata). Decimal complica numpy/pandas; el determinismo se garantiza en un mismo runtime y el redondeo absorbe ruido de orden de operaciones. El motor fija el orden de suma (sumas en orden de lista estable, `math.fsum`).
6. **JSON canónico propio**: `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` sobre `model_dump(mode="json")` post-redondeo. Hash = `sha256(canonical_bytes).hexdigest()`.
7. **Fechas** como `date` ISO; no se usa `datetime.now()` en ningún modelo (sin `default_factory` con reloj).
8. **Bounding box de Argentina** aproximada (lat -55.1 a -21.7, lon -73.6 a -53.6) como constante documentada.

## Risks / Trade-offs

- [Floats distintos entre plataformas] → redondeo canónico + `math.fsum` + test de determinismo en CI.
- [Modelos demasiado estrictos frenan la velocidad del equipo] → cambios solo aditivos, revisados por el dueño del dominio.
- [Supuestos que nunca se validan] → campo `validation_status` (PENDING_AFA, VALIDATED, REJECTED) visible en salida y README.

## Open Questions

- Nombre final del paquete (`fieldshift` tentativo).
