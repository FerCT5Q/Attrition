# Antigüedad desde ingreso original

Término obligatorio heredado de B; se conserva su definición y se reajustan sus coeficientes con el pasado de cada corte. Esta ronda no guarda una nueva tabla de cobertura individual para los términos B. Valor o evento disponible en la propia foto t.

Modo `presentation` · variable `tenure_playbook_band` · familia B.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Numérica transformada en bandas nominales |
| Campos de origen | original_hire_date; fis_mo_end_dt |
| Valores de origen | Fecha original de ingreso y fecha de foto. |
| Valores antes de agrupar categorías raras | <1 year; 1-2 years; 2-3 years; 3-5 years; 5-10 years; 10+ years; (unknown) |
| Transformación | DATEDIFF(month, original_hire_date, t); cortes 12, 24, 36, 60 y 120. Cuenta fronteras de mes calendario, no días/365. |
| Faltantes y valores por defecto | Fecha faltante o posterior a t → (unknown). No se imputa cero. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | No se aplica agrupación de categorías raras a este término. |
| Consideraciones | Antigüedad desde ingreso original, no desde la última recontratación. Las seis bandas se conservan como parte de B. |
| Uso en la definición de grupos | Define grupos con las mismas seis bandas, traducidas a español; desconocido → sin dato. |

## Comprobación y decisión

**Pregunta:** ¿Se preservó el término obligatorio y su codificación?

**Motivo:** separar una transformación de datos de su elegibilidad y de su mejora predictiva; dejar verificable por qué se conservó o quedó fuera.

**Método:** inspección del SQL/código congelado, soporte agregado de la carga, registro de selección interna y codificaciones guardadas. La documentación no reconstruye filas ni cambia decisiones a partir de resultados externos.

**Regla de aceptación:** Los diez términos de B deben aparecer en cada artefacto de modelo; no participan en una eliminación de variables.

### Selección en cada corte

| Periodo | Base | Fotos internas observables | Cumple condiciones individual | Lista de seis | Decisión |
|---|---|---|---|---|---|
| aug_dec_2025 | B | — | — | — | Obligatoria en B |
| aug_jan_2024 | B | — | — | — | Obligatoria en B |
| feb_jul_2024 | B | — | — | — | Obligatoria en B |
| feb_jul_2025 | B | — | — | — | Obligatoria en B |
| final | B | — | — | — | Obligatoria en B |
| jan_feb_2026 | B | — | — | — | Obligatoria en B |

- **aug_dec_2025 / B:** Se conserva por instrucción del usuario; esta ronda no elimina términos de B.
- **aug_jan_2024 / B:** Se conserva por instrucción del usuario; esta ronda no elimina términos de B.
- **feb_jul_2024 / B:** Se conserva por instrucción del usuario; esta ronda no elimina términos de B.
- **feb_jul_2025 / B:** Se conserva por instrucción del usuario; esta ronda no elimina términos de B.
- **final / B:** Se conserva por instrucción del usuario; esta ronda no elimina términos de B.
- **jan_feb_2026 / B:** Se conserva por instrucción del usuario; esta ronda no elimina términos de B.

**Frecuencia en selecciones anteriores:** B: seleccionada en 5 de 5 cortes.

**Conclusión de selección final:** Sobre B: Obligatoria en B. Se conserva por instrucción del usuario; esta ronda no elimina términos de B.

**Impacto en score de assessment:** ninguno. Los scores previos no se reasignan con estas pruebas.

**Acción:** Conservar el término de B; no se realizó una prueba para eliminarlo.

## Codificación de los modelos finales

| Modelo | Referencia omitida | Número de indicadores | Niveles aprendidos |
|---|---|---|---|
| final-B-Q | 5-10 years | 5 | 1-2 years; 10+ years; 2-3 years; 3-5 years; 5-10 years; <1 year |
| final-B-RH | 5-10 years | 5 | 1-2 years; 10+ years; 2-3 years; 3-5 years; 5-10 years; <1 year |
| final-B | 5-10 years | 5 | 1-2 years; 10+ years; 2-3 years; 3-5 years; 5-10 years; <1 year |
| final-B_RH-Q | 5-10 years | 5 | 1-2 years; 10+ years; 2-3 years; 3-5 years; 5-10 years; <1 year |

## Fuentes trazables

- [engineering_model_c_qvoice_person_month_20261008.sql](<../../../../../../../queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql>)
- [engineering_playbook_group_selection.py](<../../../../../../../tools/engineering_playbook_group_selection.py>)
- [engineering_c_group_selection.py](<../../../../../../../tools/engineering_c_group_selection.py>)

La referencia de este término es el SQL y los artefactos del modelo B. No se presenta esta ficha como una nueva verificación semántica o de lineage.

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
