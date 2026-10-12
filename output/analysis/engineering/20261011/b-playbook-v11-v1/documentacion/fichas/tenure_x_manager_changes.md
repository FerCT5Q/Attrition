# Interacción: antigüedad y cambios de manager

Término obligatorio heredado de B; se conserva su definición y se reajustan sus coeficientes con el pasado de cada corte. Esta ronda no guarda una nueva tabla de cobertura individual para los términos B. Valor o evento disponible en la propia foto t.

Modo `presentation` · variable `tenure_x_manager_changes` · familia B.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Interacción categórica explícita |
| Campos de origen | tenure_playbook_band; manager_changes_12m |
| Valores de origen | Categorías ya preparadas de los dos términos de B. |
| Valores antes de agrupar categorías raras | Combinaciones observadas a \| b cuando ambos difieren de sus referencias; ref |
| Transformación | Construye a \| b sólo si ambas categorías difieren de la referencia de sus términos principales; el resto se codifica ref. Después se omite la categoría más frecuente de la interacción. |
| Faltantes y valores por defecto | Los estados desconocidos se tratan como categorías de los términos de origen. Combinación no aprendida → indicadores cero. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | No se aplica agrupación de categorías raras a este término. |
| Consideraciones | Se conservan las dos interacciones de B. Añadir pares o tríos de candidatas no crea interacciones nuevas entre ellas. |
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
| final-B-Q | ref | 10 | 1-2 years \| 1; 1-2 years \| 2+; 10+ years \| 1; 10+ years \| 2+; 2-3 years \| 1; 2-3 years \| 2+; 3-5 years \| 1; 3-5 years \| 2+; <1 year \| 1; <1 year \| 2+; ref |
| final-B-RH | ref | 10 | 1-2 years \| 1; 1-2 years \| 2+; 10+ years \| 1; 10+ years \| 2+; 2-3 years \| 1; 2-3 years \| 2+; 3-5 years \| 1; 3-5 years \| 2+; <1 year \| 1; <1 year \| 2+; ref |
| final-B | ref | 10 | 1-2 years \| 1; 1-2 years \| 2+; 10+ years \| 1; 10+ years \| 2+; 2-3 years \| 1; 2-3 years \| 2+; 3-5 years \| 1; 3-5 years \| 2+; <1 year \| 1; <1 year \| 2+; ref |
| final-B_RH-Q | ref | 10 | 1-2 years \| 1; 1-2 years \| 2+; 10+ years \| 1; 10+ years \| 2+; 2-3 years \| 1; 2-3 years \| 2+; 3-5 years \| 1; 3-5 years \| 2+; <1 year \| 1; <1 year \| 2+; ref |

## Fuentes trazables

- [engineering_model_c.py](<../../../../../../../tools/engineering_model_c.py>)
- [engineering_b_incremental.py](<../../../../../../../tools/engineering_b_incremental.py>)

La referencia de este término es el SQL y los artefactos del modelo B. No se presenta esta ficha como una nueva verificación semántica o de lineage.

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
