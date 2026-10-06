# Plan: Persistencia completa de outputs + fix BUG-01

## Diagnóstico

### Estado actual — qué se persiste y qué no

| Tipo de output | Persiste en disco | fill_gaps lo recupera |
|---------------|-------------------|-----------------------|
| Screenshots / data_chart | Sí — PNG directo | Sí — filesystem |
| compute_text | No (determinista) | Sí — recalcula |
| set_text estático | No (está en config) | Sí — vía `collect()` |
| set_text con `{{vars}}` | **PARCIALMENTE** | Sí, si y solo si también hay `extract_text` |
| extract_text variables | Sí — `_texts.json` | Sí — `_load_extracted_texts` |

### El problema concreto

`_get_expected_outputs()` incluye `_texts.json` en sus expected outputs **solo cuando hay `extract_text` steps** (`_has_extract_text_steps()`). Esto es correcto porque `_texts.json` solo existe si hay `extract_text`.

**Pero**: en `_process_global_only()`, el fast path (líneas 488-507) llama:
```python
builders[leader_id].collect(rendered, list(global_cache.values()))
_fill_gaps_compute_text(rendered.steps, builders[leader_id], leader, {})
```
…y NO llama `_resolve_set_texts_from_disk()`. Si un dashboard global-only tuviera `extract_text` + `set_text`, el fast path los perdería.

**En cut-mode, el mecanismo está completo**: `_inject_outputs_from_disk()` cubre los tres casos (PNGs + compute_text + set_text desde disco). El gap es solo en `_process_global_only` fast path.

### Bugs identificados

**BUG-01 (simple)**: En el bloque `if args.report` (línea 1074-1078), se usa `all_cut_dashboards` pero debería usar `cut_dashboards` (los filtrados por `--dashboards`). Si el usuario pasa `--dashboards ta_dashboard_offers`, el reporte debería mostrar solo ese dashboard, no todos.

**BUG-02 (global-only fast path)**: `_process_global_only` fast path no llama `_resolve_set_texts_from_disk()`. Como ningún dashboard global-only tiene `extract_text` steps actualmente, no tiene impacto hoy — pero viola el principio arquitectural y es un bug latente.

---

## Solución

### Fix BUG-01 — `--report` usa cut_dashboards

**Archivo**: `main.py`, línea 1074-1078

Cambiar `all_cut_dashboards` por `cut_dashboards` en el bloque `if args.report`:

```python
# ANTES:
if args.report:
    cut_loader = CutLeaderLoader(excel_path=args.excel)
    leaders_cache, _ = _preload_leaders(all_cut_dashboards, {d.id for d in all_cut_dashboards}, cut_loader, args, sql_service=None)
    _print_missing_outputs_report(all_cut_dashboards, leaders_cache, output_config, template_engine)
    return

# DESPUÉS:
if args.report:
    cut_loader = CutLeaderLoader(excel_path=args.excel)
    leaders_cache, _ = _preload_leaders(cut_dashboards, {d.id for d in cut_dashboards}, cut_loader, args, sql_service=None)
    _print_missing_outputs_report(cut_dashboards, leaders_cache, output_config, template_engine)
    return
```

### Fix BUG-02 — global-only fast path llama `_resolve_set_texts_from_disk`

**Archivo**: `main.py`, líneas 504-506

En `_process_global_only()` fast path, agregar llamada a `_resolve_set_texts_from_disk()`:

```python
# ANTES:
builders[leader_id].collect(rendered, list(global_cache.values()))
_fill_gaps_compute_text(rendered.steps, builders[leader_id], leader, {})

# DESPUÉS — usar _inject_outputs_from_disk() que ya cubre los 3 casos:
global_context_id = f"{dashboard.id}_global"
_inject_outputs_from_disk(rendered, global_output, global_context_id, builders[leader_id], leader, {})
```

`_inject_outputs_from_disk()` ya hace exactamente las tres cosas necesarias:
1. `builder.collect(rendered, image_paths)` — PNGs
2. `_fill_gaps_compute_text(...)` — compute_text
3. `_resolve_set_texts_from_disk(...)` — set_text con vars

Esto elimina la duplicación de lógica y hace que global-only fast path sea uniforme con cut-mode.

---

## Cambios en código

**Solo 2 archivos, solo `main.py`:**

1. **Línea ~1075**: `all_cut_dashboards` → `cut_dashboards` en bloque `args.report` (2 líneas)
2. **Líneas ~504-506**: Reemplazar `collect() + _fill_gaps_compute_text()` por `_inject_outputs_from_disk()` (refactor, misma cantidad de líneas)

**Sin cambios en**: `_get_expected_outputs`, `_accumulate_leader_results`, `pptx_builder.py`, `_inject_outputs_from_disk` — todo eso ya funciona correctamente.

---

## Riesgos

- **BUG-01**: Riesgo mínimo — solo afecta el modo `--report` que no toca el pipeline
- **BUG-02**: Riesgo mínimo — ningún dashboard activo tiene `extract_text` en `global_steps`. El cambio simplifica código (menos líneas, usa función ya testeada)
- **Regresión posible**: `_inject_outputs_from_disk` requiere que `output_config.output_dir` esté apuntando al directorio global (`_global/{dashboard_id}`). Verificar que `global_output` (ya definido en línea 486) sea el argumento correcto para `output_config` — sí lo es.

---

## Pasos de implementación

1. Fix BUG-01: cambiar 2 ocurrencias de `all_cut_dashboards` en bloque `args.report`
2. Fix BUG-02: en `_process_global_only` fast path, reemplazar 2 líneas por llamada a `_inject_outputs_from_disk`
3. Verificar que `global_output` y `global_context_id` sean los argumentos correctos
