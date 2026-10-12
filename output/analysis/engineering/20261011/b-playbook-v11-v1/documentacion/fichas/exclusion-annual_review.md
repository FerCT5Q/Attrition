# Flag de promoción de Annual Review

AR20–AR24 tienen carga/modificación 2025-06-25; AR25, 2025-11-09. No se acreditó el calendario original de publicación ni versiones por ciclo.

Modo `presentation`. Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md)

| Elemento | Registro |
|---|---|
| Fuente | hrda.annual_review_report |
| Campos | promotion_yes_no; cycle_name; grade; last_modified_date; airflow_execution_date |
| Valores de origen | YES/NO después de UPPER/TRIM; ciclos AR20–AR25. |
| Representación considerada | Binaria por persona y ciclo, enlazada al último ciclo conocido. |
| Transformación aplicada | El audit normaliza YES/NO; no se traslada este flag al modelo. La promoción is_promo de B permanece como concepto diferente. |
| Decisión | Representación exacta excluida; concepto parcialmente cubierto |
| Motivo | El grain y el dominio pasan el control técnico, pero esos timestamps no habilitan usar el flag en años anteriores. |
| Acción | Obtener publicación/versiones históricas; conservar promoción de B y probar por separado track y entrada observada al grado. |

**Pregunta:** ¿se puede construir una representación autorizada, distinguible y conocida en cada foto?

**Motivo:** evitar llamar «cero» a falta de fuente o presentar una exclusión previa como una prueba de bajo desempeño.

**Método y regla:** se conserva el alcance exacto del audit enlazado y de la autorización. Un timestamp técnico o una estructura parcial no acredita disponibilidad histórica de la variable.

**Métricas y conclusión:** AR20–AR24 tienen carga/modificación 2025-06-25; AR25, 2025-11-09. No se acreditó el calendario original de publicación ni versiones por ciclo. El grain y el dominio pasan el control técnico, pero esos timestamps no habilitan usar el flag en años anteriores.

**Resultado predictivo:** no estimado para esta representación; no se afirma que empeore o que no tenga señal.

**Impacto en score:** ninguno.

**Acción:** Obtener publicación/versiones históricas; conservar promoción de B y probar por separado track y entrada observada al grado.

## Evidencia

- [v11-annual-review-history.json](<../../input-evidence/v11-annual-review-history.json>) · 2026-10-12T15:20:53.688965+00:00 · pass
- [engineering_b_v11_annual_review_history_20261012.sql](<../../../../../../../queries/audits/engineering_b_v11_annual_review_history_20261012.sql>)
- [b-model-annual-review-v11-20261012.md](<../../../../../../../docs/variables/promotion-history-by-compensation-grade/b-model-annual-review-v11-20261012.md>)
