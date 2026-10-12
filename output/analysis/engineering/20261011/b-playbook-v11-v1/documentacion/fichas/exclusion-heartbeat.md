# Heartbeat exacto de QVoice

2024 tiene cero escalas ordinales reconocidas; 2025 tiene 52 de 53 y falta Q42. La wave 2026 sólo corresponde a 2027.

Modo `presentation`. Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md)

| Elemento | Registro |
|---|---|
| Fuente | Workbooks QVoice y diccionario de encuesta |
| Campos | scale_Q1 … scale_Q53 |
| Valores de origen | Escalas ordinales 1, 2, 3, 4, 5; blanks/255/otros inválidos fuera del dominio. |
| Representación considerada | Signo relativo de cada pregunta respecto al promedio personal de la escala. |
| Transformación aplicada | Definición propuesta: signo de pregunta−promedio personal; requiere las 53 columnas y al menos 38 respuestas válidas. No se calcula como candidata en esta ronda. |
| Decisión | Excluida antes de selección |
| Motivo | No se dispone de la estructura exacta requerida para las waves elegibles. |
| Acción | Recuperar la estructura faltante o definir y validar una medida diferente; no cambiar silenciosamente el denominador. |

**Pregunta:** ¿se puede construir una representación autorizada, distinguible y conocida en cada foto?

**Motivo:** evitar llamar «cero» a falta de fuente o presentar una exclusión previa como una prueba de bajo desempeño.

**Método y regla:** se conserva el alcance exacto del audit enlazado y de la autorización. Un timestamp técnico o una estructura parcial no acredita disponibilidad histórica de la variable.

**Métricas y conclusión:** 2024 tiene cero escalas ordinales reconocidas; 2025 tiene 52 de 53 y falta Q42. La wave 2026 sólo corresponde a 2027. No se dispone de la estructura exacta requerida para las waves elegibles.

**Resultado predictivo:** no estimado para esta representación; no se afirma que empeore o que no tenga señal.

**Impacto en score:** ninguno.

**Acción:** Recuperar la estructura faltante o definir y validar una medida diferente; no cambiar silenciosamente el denominador.

## Evidencia

- [v11-heartbeat-headers.json](<../../input-evidence/v11-heartbeat-headers.json>) · 2026-10-12T15:22:07.506025+00:00 · fail
- [b-heartbeat-v11-20261012.md](<../../../../../../../docs/variables/qvoice-model/b-heartbeat-v11-20261012.md>)
