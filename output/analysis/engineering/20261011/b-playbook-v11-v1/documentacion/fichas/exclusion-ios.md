# Movimientos IOS

Las cargas y modificaciones actuales son de 2026-10-11; no acreditan disponibilidad de cada evento en las fotos anteriores.

Modo `presentation`. Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md)

| Elemento | Registro |
|---|---|
| Fuente | hrda.workers_ios_transfers |
| Campos | business_process_reason; effective_date; timestamps de carga/modificación |
| Valores de origen | Seis motivos descriptivos de movimiento; no se exporta aquí un dominio de empleados. |
| Representación considerada | Eventos por motivo; la variante antigua ios_12m también se excluyó. |
| Transformación aplicada | No se construye columna seleccionable en esta ronda; no se imputa no movimiento. |
| Decisión | Excluida antes de selección |
| Motivo | No se verificó conocimiento histórico de las resoluciones IOS. |
| Acción | Obtener historia de versiones o calendario oficial de disponibilidad antes de modelar eventos as-of. |

**Pregunta:** ¿se puede construir una representación autorizada, distinguible y conocida en cada foto?

**Motivo:** evitar llamar «cero» a falta de fuente o presentar una exclusión previa como una prueba de bajo desempeño.

**Método y regla:** se conserva el alcance exacto del audit enlazado y de la autorización. Un timestamp técnico o una estructura parcial no acredita disponibilidad histórica de la variable.

**Métricas y conclusión:** Las cargas y modificaciones actuales son de 2026-10-11; no acreditan disponibilidad de cada evento en las fotos anteriores. No se verificó conocimiento histórico de las resoluciones IOS.

**Resultado predictivo:** no estimado para esta representación; no se afirma que empeore o que no tenga señal.

**Impacto en score:** ninguno.

**Acción:** Obtener historia de versiones o calendario oficial de disponibilidad antes de modelar eventos as-of.

## Evidencia

- [v11-ios-knowledge.json](<../../input-evidence/v11-ios-knowledge.json>) · 2026-10-12T03:23:53.605365+00:00 · fail
- [engineering_b_v11_ios_knowledge_20261011.sql](<../../../../../../../queries/audits/engineering_b_v11_ios_knowledge_20261011.sql>)
- [b-model-v11-20261011.md](<../../../../../../../docs/variables/ios-movement/b-model-v11-20261011.md>)
