# HR Analytics — Reusable Playbook

Lecciones aprendidas de este proyecto de Promotion & Attrition (2020–2026) que aplican a futuros proyectos de People Analytics en Qualcomm.

---

## 1. Definición de Métricas Críticas

### 1.1 Tasa de Promoción

**Fórmula oficial:**
```
Promotion Rate (Year Y) = promoted_Y / ar_participants_november_Y
```

- **Numerador:** empleados con `annual_review_report.promotion_yes_no = 'Yes'` en el ciclo AR del año Y. Usar snapshot de **noviembre**.
- **Denominador:** empleados con `in_annual_review == 1` en el snapshot de **noviembre** del año Y.
- **NO usar** `Workday_Promotion`, `Daily_Promotion`, ni `Transfer_Promotion` como fuente del numerador.

**Por qué importa:** `Workday_Promotion` es poco confiable — 213 de 542 casos tenían el grade NUMBER igual (solo cambió letra o job_family). Son movimientos laterales, no promociones reales.

### 1.2 Tasa de Attrition Voluntaria

- Usar **únicamente** `term_type == "Voluntary"`.
- Excluir `"Voluntary Exception"` — es una categoría separada que no cuenta como attrition voluntaria regular.
- Confirmar esta distinción con HR Business Partner al inicio de cualquier nuevo proyecto.

### 1.3 Ciclo del Annual Review

- El AR corre en **octubre–noviembre**.
- Los grade changes se reflejan entre **octubre y diciembre** (99.8% de los promovidos tienen cambio confirmado en ese rango).
- AMERICAS: grade change ocurre en **noviembre**.
- INDIA, APAC, EMEA: grade change puede ocurrir en **noviembre o diciembre**.

---

## 2. Clasificación de Movimientos de Carrera (Cascade)

### 2.1 Jerarquía de fuentes

| Prioridad | Fuente | Uso |
|-----------|--------|-----|
| 1 | `annual_review_report` | Fuente oficial de `is_promotion` |
| 2 | `workers_ios_transfers` | Fuente oficial para lateral moves, country moves, transfer promotions, down levels |
| 3 | Workday flags / Daily events | Solo gap-filling y respaldo |



### 2.3 Reglas de negocio clave

**ACQSNT (adquisiciones):** Si `prev_job_family_short = 'ACQSNT'`, clasificar como `Acquisition_Adjustment`, no como career event. Los empleados adquiridos reciben reclasificaciones administrativas al integrarse.

**System_Update_Post_Hire (4 meses):** `months_since_max_hire_rehire <= 4`. Crítico: usar `NaN` (no `0`) para snapshots ANTERIORES a `max_hire_rehire_date`. Si se usa `clip(lower=0)`, todo el historial previo al rehire dispara incorrectamente la regla.

**Job_Redefinition:** `changed_compensation_grade == 1 AND changed_job_family == 0`. Un cambio de grade sin cambio de job_family es una reestructuración corporativa, no un evento de carrera.

**Job_Family_Rename:** Si ≥60% de los empleados con el mismo `prev_job_family` en el mismo mes cambian al mismo nuevo job_family (mínimo 5 empleados) → es un rename administrativo.

**System_Glitch_Revert:** Si job_family cambia y en los próximos 1–3 snapshots revierte al valor anterior → es un error de sistema, no un evento real.

---

## 3. Filtros de Extracción

Aplicar siempre en el WHERE de SQL:

```sql
WHERE worker_type = 'Employee'
  AND employee_type IN ('Regular', 'Fixed Term Contract', 'Expatriate')
  AND is_rf360_yes_no = 0   -- excluye empleados en sistema RF360
```

- `is_rf360_yes_no = 0` debe ir en toda re-extracción. Los empleados RF360 tienen un sistema de grades diferente y contaminan la clasificación.

---

## 4. Significado de las Letras de Grade

| Letra | Org | Nivel |
|-------|-----|-------|
| R | Engineering (CTO) | Individual Contributor |
| T | Engineering (CTO) | Management |
| P | Corp Fxn / BU | Individual Contributor |
| M | Corp Fxn / BU | Management |
| S | Corp Fxn / BU | Support |
| V | Corp Fxn / BU | VP/SVP |

---

## 5. Estilo de Gráficas

La tesis debe ser, menos tinta. No usar gridlines a menos que se especifique

### 5.1 Paleta de colores por segmento

Usar siempre esta paleta para consistencia entre charts:

```python
SEGMENT_COLORS = {
    "Total Company":        "#2A2AEA",  # Qualcomm royal blue
    "All Never Promoted":   "#2A2AEA",  # mismo — contexto empresa total
    "INDIA":                "#020B3F",  # navy
    "ROW":                  "#006B6F",  # teal
    "AMERICAS":             "#843AFF",  # violet
    "EMEA":                 "#E67E22",  # orange
    "APAC":                 "#16A085",  # teal green
    "Corp":                 "#546E7A",  # slate blue-gray
    "CTO":                  "#1B5E20",  # deep forest green
}
```

### 5.2 Reglas de etiquetas

- **Nunca** usar "AR" como abreviación. Siempre escribir "Annual Review" completo.
- **Nunca** usar "Non-Eng", "Non_Engineering", ni "Non-Engineering" en etiquetas visibles.
  - Grades R/T → usar prefijo "Eng …" (e.g., "Eng Individual Contributor")
  - Grades M/P → usar etiquetas neutrales  "Corp" ("Manager / Director", "Professional")
  - Para splits de org → usar "CTO" y "Corp Fxn & BU" (nunca "Non-Engineering")
- **No usar emojis** en textos de matplotlib (títulos, leyendas, etiquetas de celdas). DejaVu Sans no los renderiza — aparecen como cuadros vacíos.

### 5.3 Fondo transparente (estilo slide)

Para charts que se insertan en slides con fondo gris-azulado:

```python
fig.patch.set_alpha(0)
ax.set_facecolor("none")
ax.grid(False)

fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="none", transparent=True)

# Leyendas:
ax.legend(framealpha=0, edgecolor="none")
```

### 5.4 Líneas en charts multi-segmento

- Todas las líneas deben tener el mismo grosor (`lw=2.5` como default).
- Usar estilo de línea (`ls="--"` vs `ls="-"`) para distinguir la línea agregada/referencia, no el grosor.


### 5.6 Shading sutil (fill_between)

Cuando se usa `fill_between` para indicar un gap decorativo (no como elemento de datos primario), usar `alpha ≤ 0.05`. Valores de 0.10+ se ven demasiado fuertes.

---

## 6. Anti-Patrones de Código

### 6.1 Identificar promovidos — forma incorrecta vs correcta

 # INCORRECTO — cuenta todas las filas del período, no promotions
  promoted_ids = df.groupby("employee_id")["movement_type"].count().gt(0)

  # CORRECTO — is_promotion del ciclo AR del año Y (sin restricción de mes)
  promoted_ids = (
      df[
          (df["is_promotion"] == 1) &
          (df["snapshot_year"] == YEAR)
      ][["employee_id"]].drop_duplicates().assign(promoted=1)
  )

  is_promotion e in_annual_review son flags del ciclo AR — la unidad es el año, no el mes. drop_duplicates() sobre employee_id es suficiente para deduplicar cuando hay múltiples snapshots mensuales.

### 6.2 Career path arrows (transiciones) — regiones INDIA/APAC/EMEA

No filtrar transiciones con `prev_compensation_grade != compensation_grade` solo en el snapshot de noviembre. En esas regiones el grade change llega en diciembre, haciendo que el filtro elimine todas sus flechas.

```python
# Forma correcta: buscar grade change en Nov O Dec del mismo año
_promo_emps = df[
    (df["is_promotion"] == 1) &
    df["snapshot_year"].between(2020, 2025)
][["employee_id", "snapshot_year"]].drop_duplicates()

_gc = df[
    df["prev_compensation_grade"].notna() &
    (df["prev_compensation_grade"] != df["compensation_grade"]) &
    df["snapshot_month_num"].isin([11, 12]) &
    df["snapshot_year"].between(2020, 2025)
].copy()

transitions = (
    _promo_emps.merge(_gc, on=["employee_id", "snapshot_year"], how="inner")
    .sort_values("snapshot_month_num")
    .drop_duplicates(subset=["employee_id", "snapshot_year"])
)
```

---



