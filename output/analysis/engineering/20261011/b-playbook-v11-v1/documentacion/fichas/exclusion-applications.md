# Solicitudes de empleo

applications termina el 2024-10-29 y no tiene eventos de marzo–septiembre de 2026. La vista alternativa llega a 2026, sin historia verificada de enlace y completitud.

Modo `presentation`. Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md)

| Elemento | Registro |
|---|---|
| Fuente | hrda.applications; alternativa hrda.job_applications_vw |
| Campos | fechas de solicitud; llave de enlace (sólo dentro de SQL) |
| Valores de origen | Eventos de solicitudes; no se exportan requisiciones ni datos de postulantes. |
| Representación considerada | Presencia/conteo de solicitudes anteriores a la foto. |
| Transformación aplicada | No se construye columna seleccionable; la ausencia de feed o enlace no se convierte en cero. |
| Decisión | Excluida antes de selección |
| Motivo | Falta continuidad del feed exacto V11 y evidencia temporal suficiente de la alternativa. |
| Acción | Reconstruir fuente histórica y observabilidad del enlace para distinguir ninguna solicitud de dato no disponible. |

**Pregunta:** ¿se puede construir una representación autorizada, distinguible y conocida en cada foto?

**Motivo:** evitar llamar «cero» a falta de fuente o presentar una exclusión previa como una prueba de bajo desempeño.

**Método y regla:** se conserva el alcance exacto del audit enlazado y de la autorización. Un timestamp técnico o una estructura parcial no acredita disponibilidad histórica de la variable.

**Métricas y conclusión:** applications termina el 2024-10-29 y no tiene eventos de marzo–septiembre de 2026. La vista alternativa llega a 2026, sin historia verificada de enlace y completitud. Falta continuidad del feed exacto V11 y evidencia temporal suficiente de la alternativa.

**Resultado predictivo:** no estimado para esta representación; no se afirma que empeore o que no tenga señal.

**Impacto en score:** ninguno.

**Acción:** Reconstruir fuente histórica y observabilidad del enlace para distinguir ninguna solicitud de dato no disponible.

## Evidencia

- [v11-applications-history.json](<../../input-evidence/v11-applications-history.json>) · 2026-10-12T15:16:15.306878+00:00 · fail
- [engineering_b_v11_applications_history_20261011.sql](<../../../../../../../queries/audits/engineering_b_v11_applications_history_20261011.sql>)
- [v11-applications-metadata.json](<../../input-evidence/v11-applications-metadata.json>) · 2026-10-12T15:14:43.663625+00:00 · pass
- [engineering_b_v11_applications_metadata_20261011.sql](<../../../../../../../queries/audits/engineering_b_v11_applications_metadata_20261011.sql>)
- [b-model-v11-20261011.md](<../../../../../../../docs/variables/more-than-3-job-applications/b-model-v11-20261011.md>)
