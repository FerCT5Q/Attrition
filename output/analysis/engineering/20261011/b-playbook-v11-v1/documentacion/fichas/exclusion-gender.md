# Género

La autorización de procesamiento excluye atributos protegidos como features en toda la ronda.

Modo `presentation`. Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md)

| Elemento | Registro |
|---|---|
| Fuente | hrda.post_hire_monthly_worker_dtls |
| Campos | gender |
| Valores de origen | Etiquetas protegidas no enumeradas en un entregable presentation. |
| Representación considerada | Atributo protegido, no autorizado como predictor. |
| Transformación aplicada | No se incorpora al diseño, no se codifica y no se estima un efecto. |
| Decisión | Fuera de autorización de predicción |
| Motivo | La autorización vigente excluye su uso como predictor; no es un resultado de desempeño. |
| Acción | Conservar fuera del modelo bajo la autorización vigente. |

**Pregunta:** ¿se puede construir una representación autorizada, distinguible y conocida en cada foto?

**Motivo:** evitar llamar «cero» a falta de fuente o presentar una exclusión previa como una prueba de bajo desempeño.

**Método y regla:** se conserva el alcance exacto del audit enlazado y de la autorización. Un timestamp técnico o una estructura parcial no acredita disponibilidad histórica de la variable.

**Métricas y conclusión:** La autorización de procesamiento excluye atributos protegidos como features en toda la ronda. La autorización vigente excluye su uso como predictor; no es un resultado de desempeño.

**Resultado predictivo:** no estimado para esta representación; no se afirma que empeore o que no tenga señal.

**Impacto en score:** ninguno.

**Acción:** Conservar fuera del modelo bajo la autorización vigente.

## Evidencia

- [attrition_model_in_memory_training_authorization_20261001.json](<../../../../../../../config/attrition_model_in_memory_training_authorization_20261001.json>)
