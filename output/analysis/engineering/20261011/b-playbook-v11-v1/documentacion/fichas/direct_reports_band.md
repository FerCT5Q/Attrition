# Reportes directos

Término obligatorio heredado de B; se conserva su definición y se reajustan sus coeficientes con el pasado de cada corte. Esta ronda no guarda una nueva tabla de cobertura individual para los términos B. Valor o evento disponible en la propia foto t.

Modo `presentation` · variable `direct_reports_band` · familia B.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Conteo transformado en categoría |
| Campos de origen | reg_non_intern_dir_reports |
| Valores de origen | Conteo directo regular/no intern registrado en la foto. |
| Valores antes de agrupar categorías raras | 0; 1-5; 6+; (unknown) |
| Transformación | Después de separar nulos y cero, valores ≤5 van a 1-5; el resto va a 6+. La transformación no añade un filtro separado para negativos. |
| Faltantes y valores por defecto | Nulo → (unknown). Cero es un valor observado distinto. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | No se aplica agrupación de categorías raras a este término. |
| Consideraciones | Describe los reportes directos de la persona focal; es distinto del tamaño del equipo de su manager. |
| Uso en la definición de grupos | Puede modificar la predicción, pero no añade una dimensión de grupo en esta ronda. Los grupos siguen definidos por antigüedad, salidas del equipo y nivel. |

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
| final-B-Q | 0 | 2 | 0; 1-5; 6+ |
| final-B-RH | 0 | 2 | 0; 1-5; 6+ |
| final-B | 0 | 2 | 0; 1-5; 6+ |
| final-B_RH-Q | 0 | 2 | 0; 1-5; 6+ |

## Fuentes trazables

- [engineering_model_c_qvoice_person_month_20261008.sql](<../../../../../../../queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql>)

La referencia de este término es el SQL y los artefactos del modelo B. No se presenta esta ficha como una nueva verificación semántica o de lineage.

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
