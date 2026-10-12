# Nivel agrupado

Término obligatorio heredado de B; se conserva su definición y se reajustan sus coeficientes con el pasado de cada corte. Esta ronda no guarda una nueva tabla de cobertura individual para los términos B. Valor o evento disponible en la propia foto t.

Modo `presentation` · variable `level_grouped` · familia B.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Categoría nominal |
| Campos de origen | level_grouped |
| Valores de origen | Etiqueta agrupada registrada; vocabulario abierto, sin recodificarla como número. |
| Valores antes de agrupar categorías raras | Etiquetas registradas de level_grouped; (unknown) |
| Transformación | TRIM; blanco se convierte en nulo. Se conserva la etiqueta de la foto. No se añaden ni fusionan niveles de B en esta ronda. |
| Faltantes y valores por defecto | Nulo o blanco → (unknown). La referencia se aprende en cada entrenamiento. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | No se aplica agrupación de categorías raras a este término. |
| Consideraciones | Es el nivel agrupado de B; no se sustituye por compensation_grade ni por job_level_primary_position. |
| Uso en la definición de grupos | Para agrupar toma el prefijo anterior a « - »: 1/2/3 → alto; 5/6 → medio; 7/8 → entrada; otros → otro. El modelo conserva sus etiquetas detalladas. |

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
| final-B-Q | 7 - Senior & Lead | 7 | 1 - VP & Above; 2 - Sr Dir; 3 - Princ/Directors; 5 - Sr Staff & /Mgr; 6 - Staff & /Mgr; 7 - Senior & Lead; 8 - Assoc & Int/Eng; Misc |
| final-B-RH | 7 - Senior & Lead | 7 | 1 - VP & Above; 2 - Sr Dir; 3 - Princ/Directors; 5 - Sr Staff & /Mgr; 6 - Staff & /Mgr; 7 - Senior & Lead; 8 - Assoc & Int/Eng; Misc |
| final-B | 7 - Senior & Lead | 7 | 1 - VP & Above; 2 - Sr Dir; 3 - Princ/Directors; 5 - Sr Staff & /Mgr; 6 - Staff & /Mgr; 7 - Senior & Lead; 8 - Assoc & Int/Eng; Misc |
| final-B_RH-Q | 7 - Senior & Lead | 7 | 1 - VP & Above; 2 - Sr Dir; 3 - Princ/Directors; 5 - Sr Staff & /Mgr; 6 - Staff & /Mgr; 7 - Senior & Lead; 8 - Assoc & Int/Eng; Misc |

## Fuentes trazables

- [engineering_model_c_qvoice_person_month_20261008.sql](<../../../../../../../queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql>)
- [engineering_playbook_group_selection.py](<../../../../../../../tools/engineering_playbook_group_selection.py>)
- [engineering_c_group_selection.py](<../../../../../../../tools/engineering_c_group_selection.py>)

La referencia de este término es el SQL y los artefactos del modelo B. No se presenta esta ficha como una nueva verificación semántica o de lineage.

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
