# Engineering frente a otras funciones

Se aplica el mismo filtro en cada foto de la comparación.

Modo `presentation`. Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md)

| Elemento | Registro |
|---|---|
| Fuente | hrda.post_hire_monthly_worker_dtls |
| Campos | eng_or_noneng |
| Valores de origen | Engineering es el único valor dentro de la población seleccionada. |
| Representación considerada | Filtro de población; sería categórica fuera de esta población. |
| Transformación aplicada | TRIM(eng_or_noneng)='Engineering' se usa para filtrar; no se agrega una columna constante al modelo. |
| Decisión | Constante dentro de la población |
| Motivo | No permite distinguir riesgos entre personas de Engineering. |
| Acción | Mantener como criterio de población; una comparación entre funciones sería otra población/modelo. |

**Pregunta:** ¿se puede construir una representación autorizada, distinguible y conocida en cada foto?

**Motivo:** evitar llamar «cero» a falta de fuente o presentar una exclusión previa como una prueba de bajo desempeño.

**Método y regla:** se conserva el alcance exacto del audit enlazado y de la autorización. Un timestamp técnico o una estructura parcial no acredita disponibilidad histórica de la variable.

**Métricas y conclusión:** Se aplica el mismo filtro en cada foto de la comparación. No permite distinguir riesgos entre personas de Engineering.

**Resultado predictivo:** no estimado para esta representación; no se afirma que empeore o que no tenga señal.

**Impacto en score:** ninguno.

**Acción:** Mantener como criterio de población; una comparación entre funciones sería otra población/modelo.

## Evidencia

