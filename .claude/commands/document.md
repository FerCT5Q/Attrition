Revisa los cambios de código desde el último commit y actualiza la documentación para que refleje el estado actual del sistema — simple, clara, estructurada y al día.

**Restricciones absolutas — NO modificar código fuente, solo archivos en `docs/` y `CLAUDE.md`.**

---

## Fase 1 — Identificar cambios

Ejecutar en paralelo:
- `git diff HEAD --stat` — resumen de líneas cambiadas por archivo
- `git status --short` — archivos nuevos sin trackear

**Evaluar si los cambios justifican documentar.** Son significativos si alguna condición es verdad:
- Hay archivos `.py` modificados con cambios de comportamiento (nueva función, flujo alterado, parámetro nuevo)
- Se agregaron archivos `.py` o de configuración nuevos
- Se modificaron `dashboards.json`, `.env.example` o `CLAUDE.md`

**No son significativos** (→ terminar aquí, sin tocar ningún doc):
- Solo cambios dentro de `docs/` — ya es documentación
- Typos, renombrados de variables, ajustes de formato sin impacto en comportamiento
- Cambios de <5 líneas en `.py` que no alteran comportamiento externo

Si no hay cambios significativos, reportar: `Sin cambios que justifiquen actualización de documentación.` y detener.

Si hay cambios significativos, leer los archivos modificados para entender qué cambió y por qué. Si el cambio es menor (nuevo campo, ajuste de comportamiento puntual), documentar de forma compacta. Si es estructural (nuevo módulo, flujo rediseñado, feature completa), prepararse para revisión profunda.

---

## Fase 2 — Evaluar impacto en documentación

Por cada cambio identificado, determinar:

1. **¿Qué docs están desactualizados?** — revisar `docs/DOCUMENTATION_INDEX.md` para mapear qué secciones cubren el área modificada
2. **¿El cambio justifica reestructurar algún doc?** — si la explicación actual ya no es clara, o si el contenido está en el apartado equivocado, proponer reorganización
3. **¿Hay conceptos que ahora se pueden explicar más simple?** — simplificar siempre que sea posible sin perder precisión

Archivos de documentación en scope:
- `docs/DOCUMENTATION_INDEX.md` — índice maestro, siempre revisar
- `docs/CHANGELOG.md` — entrada por cada cambio significativo
- Docs especializados: `ARCHITECTURE.md`, `CONFIG_GUIDE.md`, `STEPS_GUIDE.md`, `BATCH_MODE_GUIDE.md`, `VARIABLE_SUBSTITUTION.md`, `POWERPOINT_GUIDE.md`, `TROUBLESHOOTING.md`
- `CLAUDE.md` — si cambia arquitectura, gotchas, o action types

---

## Fase 3 — Actualizar documentación

Aplicar los cambios necesarios:

**Para cambios menores** (bug fix, ajuste de comportamiento, nuevo campo):
- Actualizar la sección relevante del doc especializado
- Agregar entrada en `CHANGELOG.md`
- Actualizar `DOCUMENTATION_INDEX.md` si la sección cambió de nombre o se movió

**Para cambios estructurales** (nuevo módulo, flujo rediseñado, feature completa):
- Reescribir la sección afectada del doc especializado — claridad sobre completitud
- Revisar si el contenido pertenece al doc actual o debería moverse
- Actualizar diagramas o flujos en `ARCHITECTURE.md` si aplica
- Agregar entrada detallada en `CHANGELOG.md`
- Actualizar índice y navegación en `DOCUMENTATION_INDEX.md`

**Principios de escritura:**
- Simple sobre completo — si algo puede explicarse en 2 líneas, no usar 6
- Estructurado — headers claros, listas cuando hay múltiples items, código cuando hay sintaxis
- Sin redundancia — si algo ya está en `CLAUDE.md`, referenciar en lugar de duplicar
- Al día — eliminar referencias a comportamiento antiguo que ya no aplica

---

## Fase 4 — Reporte de salida

Listar qué se cambió en la documentación:

```
Archivos modificados:
- docs/STEPS_GUIDE.md — sección X actualizada por cambio en Y
- docs/CHANGELOG.md — entrada agregada: [descripción]
- docs/DOCUMENTATION_INDEX.md — índice actualizado

Reestructuraciones:
- [si aplica] doc A: sección X movida a doc B porque ...

Sin cambios necesarios:
- [docs que se revisaron pero no requerían actualización]
```
