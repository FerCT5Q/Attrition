# Backlog de revisión de variables

Las siguientes variables fueron priorizadas por su evaluación previa, pero todavía requieren una revisión conceptual separada. El orden proviene del último workbook validado y no constituye aprobación para modelado.

| Orden | Variable | Revisión necesaria |
|---:|---|---|
| 1 | Transfer within past year | Confirmar definición HRIS, persistencia del evento y cálculo trailing 12 months. |
| 2 | Location | Definir granularidad permitida, tratamiento de office site faltante y cohort minimum. |
| 3 | Time since last promotion | Confirmar acumulación del último evento sin leakage ni left-censoring. |
| 4 | Manager change | Separar evento mensual, recencia y conteo de cambios; validar cambios retroactivos. |

La revisión de `Layers from CEO` ya fue consolidada en [organizational-layers](organizational-layers/README.md). Su decisión pendiente es elegir entre el campo directo de organización supervisora y la derivación recursiva de managers hasta CEO.
