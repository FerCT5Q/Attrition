# C + BU L3 con y sin QVoice

Ejecución `engineering-c-bu-isolation-20261013-v1`, 13-oct-2026, modo
`presentation`. Responde a la pregunta explícita sobre **C + BU sin QVoice**.
La ronda v7 no había reportado ese modelo separado de la corrección QVoice.

**BU mejora las probabilidades frente a C, pero C + BU sin QVoice no supera
a CQ.** Al añadir QVoice mejora tanto la pérdida predictiva como la captura.
Ciudad todavía aporta una mejora adicional sobre C + BU + QVoice.

| Modelo | Log-loss ×1000 ↓ | Brier ×1000 ↓ | Captura al 30% ↑ | Error grupo-mes ↓ |
|---|---:|---:|---:|---:|
| C reajustado al mismo corte | 138.8 | 30.7 | 42.4% | 0.9 pp |
| C + BU L3, sin QVoice | 138 | 30.7 | 42.7% | 1 pp |
| CQ | 137.7 | 30.7 | 43.1% | 1 pp |
| C + BU L3 + QVoice | 137 | 30.6 | 43.1% | 0.9 pp |
| C + ciudad + QVoice | 136.4 | 30.6 | 43.1% | 0.9 pp |
| C + ciudad + BU L3 + QVoice | 136 | 30.6 | 43.1% | 0.9 pp |

La tabla redondeada no muestra todas las diferencias. C + BU frente a C
reajustado reduce log-loss ×1000 en 0.8, IC95 de la diferencia [−1.1, −0.5],
pero aumenta el error de grupo-mes: diferencia exacta +0.0546 pp,
IC95 [0.0216, 0.0968]. Su mejora de captura frente a C es incierta.

Frente a CQ, C + BU sin QVoice pierde 0.45 pp de captura,
IC95 [−0.8035, −0.0428]. Su log-loss es mayor, pero el intervalo de esa
diferencia incluye cero: no se concluye deterioro estadísticamente resuelto
en todas las métricas. Añadir QVoice a C + BU reduce log-loss ×1000 en 1,
IC95 [−1.5, −0.6], y aumenta captura en 0.4 pp, IC95 [0.1, 0.7].

Sobre C + BU + QVoice, añadir ciudad reduce log-loss ×1000 en 1,
IC95 [−1.3, −0.6], y mejora Brier en ambos periodos. La captura cambia muy
poco y su intervalo incluye cero. FQ + BU tiene la menor pérdida predictiva
media; FQ tiene un error de grupo-mes medio ligeramente menor. No existe un
ganador universal para cada grupo y capacidad. **CQ sigue elegido**; la
ejecución no adopta otro modelo ni constituye validación prospectiva.

## Comparabilidad y alcance

Mismas personas, fechas, outcome y grupos de antigüedad × salidas del equipo
× nivel, mínimo 300. Ingeniería, activo, Employee, Regular, sin RF360.
Agosto–diciembre 2025 y enero–febrero 2026; salida voluntaria en seis meses,
con igual peso por periodo. Los horizontes se superponen: captura de
exposiciones con evento, no salidas únicas de una cohorte conjunta.

Se ajustaron cuatro bases RH y dos correcciones QVoice con composición y L2
congelados. Dos bases son controles C con la misma fecha que C + BU; así se
separa la incorporación de BU del reajuste temporal. CQ conserva en enero
su base RH de agosto. El contraste directo con CQ compara estimadores
completos. Ciudad frente a C + BU + QVoice comparte fechas RH y selección Q.
No se utilizó `job_family_detail` ni se repitió la búsqueda de variables.

500 remuestreos por persona compartidos entre modelos y periodos, con
modelos y prioridades fijos. Las fuentes guardadas se preservaron; CQ, FQ y
FQ + BU se reprodujeron dentro de 1e−8. Se verificaron población, fechas,
etiquetas maduras, capacidad y serialización. Sólo agregados y parámetros
persistidos, bajo la autorización de entrenamiento en RAM del 1-oct-2026.

La auditoría as-of de BU se reejecutó antes de ajustar. Los límites de IOS
y fecha real de publicación QVoice siguen pendientes; esta prueba no eleva
scores de disponibilidad ni demuestra efectos causales. La subdivisión y
el escalar R6 corresponden a la revisión previa CQ/FQ/FQ+BU; no se atribuye
esa validación al nuevo C + BU sin encuesta.

- [Informe con precisión completa y diferencias pareadas](../../output/analysis/engineering/20261013/c-bu-isolation-v1/informe.md).
- [Resultados por periodo y capacidad](../../output/analysis/engineering/20261013/c-bu-isolation-v1/results.json).
- [Configuración](../../config/engineering_c_bu_isolation_20261013.json), [plan](../plans/c-bu-isolation-20261013.md) y [verificación](../../output/analysis/engineering/20261013/c-bu-isolation-v1/verification.json).
- [Guía de 44 variables ampliada](../../output/analysis/engineering/20261013/c-bu-isolation-v1/documentacion/variables-44-ampliada.xlsx): conserva las 44 filas y añade roles y codificaciones de C + BU con/sin QVoice en ambos cortes.
- [Presentación corregida de nueve slides](../../output/presentations/20261013-1100_transfer-sensitivity/presentacion-eng.html), sobre la base original de nueve; sustituye como entrega a la expansión de 16. La comparación usa grupos comunes. Para la audiencia de RH, el contenido visible usa `Base`, `Enhanced` y `Enhanced + QVoice`; las variantes posteriores se presentan como pruebas de BU, work city, combinación y sensibilidad de retirar Transfers. Los códigos B, C, CQ y FQ se conservan sólo en la trazabilidad técnica. El panel de ocho comprobaciones, las cifras y la decisión vigente permanecen sin cambios.

Consulta guardada: `queries/profiles/engineering_bu_l3_person_month_20261012.sql`.
Auditorías: `queries/audits/engineering_bu_l3_metadata_20261012.sql` y
`queries/audits/engineering_bu_l3_join_20261012.sql`. Métricas, hashes, fecha
y parámetros ejecutados en `input-evidence/`, `source/`, `models/` y manifest.
