# Talent index

Una tabla con 64 columnas y tres timestamps técnicos; no se identificó fecha de negocio ni snapshot del índice.

Modo `presentation`. Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md)

| Elemento | Registro |
|---|---|
| Fuente | hrda.master_talent_index |
| Campos | metadata de columnas y timestamps técnicos |
| Valores de origen | No se extrae el dominio individual del índice: la revisión de esta ronda se detuvo en metadata. |
| Representación considerada | Índice almacenado; escala, fórmula y versiones sin acreditar para uso temporal. |
| Transformación aplicada | Sin columna de modelo, sin imputación, bandas ni efecto estimado. |
| Decisión | Excluida antes de selección |
| Motivo | No hay ancla de negocio suficiente para reproducir lo conocido en cada foto. |
| Acción | Definir fórmula, grain, fecha de disponibilidad e historia de versiones antes de probarlo. |

**Pregunta:** ¿se puede construir una representación autorizada, distinguible y conocida en cada foto?

**Motivo:** evitar llamar «cero» a falta de fuente o presentar una exclusión previa como una prueba de bajo desempeño.

**Método y regla:** se conserva el alcance exacto del audit enlazado y de la autorización. Un timestamp técnico o una estructura parcial no acredita disponibilidad histórica de la variable.

**Métricas y conclusión:** Una tabla con 64 columnas y tres timestamps técnicos; no se identificó fecha de negocio ni snapshot del índice. No hay ancla de negocio suficiente para reproducir lo conocido en cada foto.

**Resultado predictivo:** no estimado para esta representación; no se afirma que empeore o que no tenga señal.

**Impacto en score:** ninguno.

**Acción:** Definir fórmula, grain, fecha de disponibilidad e historia de versiones antes de probarlo.

## Evidencia

- [v11-talent-metadata.json](<../../input-evidence/v11-talent-metadata.json>) · 2026-10-12T15:23:09.395020+00:00 · pass
- [engineering_b_v11_talent_metadata_20261012.sql](<../../../../../../../queries/audits/engineering_b_v11_talent_metadata_20261012.sql>)
- [b-model-v11-20261012.md](<../../../../../../../docs/variables/talent-index/b-model-v11-20261012.md>)
