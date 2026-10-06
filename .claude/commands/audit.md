Audita el scope indicado en profundidad: mapea flujos, lanza sub-agentes por flujo, sintetiza hallazgos y genera un plan de mejoras priorizado.

**Restricciones absolutas — NO modificar nada, solo leer, analizar y reportar.**

Scope: `$ARGUMENTS` — si está vacío, audita el proyecto completo (main.py + módulos core).

---

## Fase 1 — Mapear flujos

Leer CLAUDE.md (Architecture section) y los archivos del scope. Identificar los flujos distintos: cada flujo es una cadena lógica de responsabilidades con inicio y fin claros.

---

## Fase 2 — Análisis por flujo (sub-agentes en paralelo)

Por cada flujo, lanzar un sub-agente (`Agent tool`, `subagent_type=Explore`).

**Contexto que el agente principal prepara para cada sub-agente:**
- Archivos exactos del flujo
- Resumen de arquitectura relevante (extraído de CLAUDE.md)
- Rol esperado del flujo y cómo encaja en el sistema
- Gotchas de CLAUDE.md aplicables al scope
- Lista de los otros flujos (para detectar duplicación cross-flujo)

**El sub-agente reporta hallazgos sobre:**
- Legibilidad — ¿un dev nuevo puede entenderlo en 5 min?
- Lógica duplicada con otros flujos que podría unificarse en un servicio
- Bugs o errores silenciosos
- Acoplamiento innecesario
- Violaciones de los gotchas de CLAUDE.md

El sub-agente lee el código completo en su propio contexto aislado. Al agente principal solo regresa el reporte — nunca código fuente en bruto.

---

## Fase 3 — Síntesis

Con los reportes de todos los sub-agentes, el agente principal:

1. Identifica patrones cross-flujo — lógica similar que justifique extraer un servicio
2. Detecta el problema raíz de cada hallazgo (no solo el síntoma)
3. Diseña refactors simples — preferir soluciones que reduzcan líneas y aumenten claridad
4. Propone mejoras de arquitectura cuando el problema es estructural

---

## Fase 4 — Reporte de salida

### Hallazgos

Cada hallazgo tiene un código único por categoría. Formato compacto: 4-5 líneas por hallazgo, auto-contenido para poder actuar después sin releer el código.

Prefijos:
- `BUG-01` — bugs o errores silenciosos
- `ARCH-01` — arquitectura o diseño
- `DUP-01` — lógica duplicada
- `SEC-01` — seguridad
- `DEBT-01` — deuda técnica, dead code

Campos por hallazgo:
- **Código** / **Severidad**: 🔴 Alta / 🟡 Media / 🟢 Baja
- **Flujo** / **Dónde**: `src/module.py:42`
- **Qué**: qué está mal (1-2 líneas)
- **Por qué**: impacto concreto (1 línea)
- **Dirección**: cómo resolverlo (1 línea)
- **Similar en**: si hay duplicación, dónde (opcional)

### Plan de mejoras

Lista priorizada de mayor a menor impacto. Cada acción incluye: título, qué cambiar, por qué (beneficio concreto), y archivos afectados. Hallazgos con raíz común se agrupan en una sola acción unificada.
