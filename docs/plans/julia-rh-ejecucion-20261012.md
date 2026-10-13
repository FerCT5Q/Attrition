# Ejecución de la revisión de Julia

Modo `presentation`. Población Engineering, Employee, Regular, activa, RF360=0.
Resultado: salida voluntaria en seis meses. Fechas: agosto–diciembre de 2025 y
enero–febrero de 2026, con peso 1/2 por periodo. La documentación previa está en
`output/analysis/engineering/20261012/julia-rh-review-v1/documentacion/`.

Se reutilizan los conceptos, fichas y selecciones existentes. No es un nuevo
assessment de 44 variables y no se asignan scores. La comparación congelada es
CQ, C + ciudad + QVoice y C + ciudad + BU L3 + QVoice. `job_family_detail` queda
excluida. La documentación conserva expresamente el límite de IOS en C.

Comprobaciones previas al cálculo:

- BU L3: `grouped_mapping`, aplicado al cost center de cada persona-foto con
  fechas efectivas. Uso: predictor y ámbito organizacional. Se repiten las
  consultas guardadas de metadata y join de BU L3: cero duplicados, cero
  multi-match, faltantes <=5%, ningún mapping futuro usado como sustituto.
  Los cambios históricos del mapping se conservan; no se emplea el último
  valor como si siempre hubiera sido vigente.
- Conteo de salidas: derivación agregada de eventos únicos, personas con
  evento y exposiciones con evento. SQL:
  `queries/audits/julia_review_unique_events_20261012.sql`. Aceptación para
  identificar personas con evento con salidas únicas: igualdad exacta en
  cada periodo; si falla, los rótulos permanecen separados y se declara el límite.
- Tiempo: entrenamiento con `label_end <= origen`; evaluación sólo con
  seguimiento de seis meses maduro. QVoice usa Y en fotos Y+1 y continuidad
  del episodio. Esta regla no acredita la fecha real de publicación.
- Partición: población exhaustiva, exclusiva, sin padre e hijos simultáneos.
  Padres >=300; hijos >=100 (sensibilidades 150 y 200), al menos dos hijos BU
  identificables. Remanente pequeño implica conservar el padre. Empates de
  riesgo se ponderan uniformemente. Verdadero REST no puede aumentar.
- Calibración: activar con |sesgo| >=0.1 pp e IC95 que excluye cero; máximo
  tres orígenes maduros. Auxiliares con filas y etiquetas anteriores al
  origen; diseño y L2 condicionados a las selecciones congeladas. Adoptar
  sólo como recomendación retrospectiva si mejora calibración sin empeorar
  log-loss/Brier posteriores.
- Incertidumbre: 500 remuestreos de personas compartidos entre modelos y
  periodos. Intervalo del riesgo medio: gradiente R6 y sandwich de ecuaciones
  apiladas con covarianza cruzada RH/QVoice. Se verifica numéricamente.
- Publicación: personas >=30, eventos distintos >=30 para observado;
  supresión complementaria de conteos, tasas, errores e intervalos. Sin filas,
  llaves, scores ni explicaciones individuales en disco.

La primera entrega está congelada antes del cálculo. Las fechas y hashes de
las consultas se registran con los agregados. Los límites dependientes de la
disponibilidad histórica no se resolverán por repetir una métrica.

## Cierre — 13-oct-2026

La revisión y la presentación se completaron. El
[contexto de resultados](../context/julia-rh-review-20261012.md) enlaza el
resumen, las 44 filas, los diagnósticos, fichas y verificaciones.
FQ + BU L3 tiene el menor log-loss medio; CQ sigue elegido. La subdivisión
principal de 100 personas y el escalar R6 no se recomiendan. Las sensibilidades
BU de 150/200 sólo pasan en FQ + BU L3 al 10%.

Desviación registrada: una lectura adicional enfocada en evaluación/QVoice
completó cruces de captura y observado de fichas que faltaban en los agregados
principales, con cero reajustes. Se ejecutó además el agregado de salidas
únicas por grupo, reconciliado con personas y exposiciones. Los modelos
principales respetaron el máximo de cuatro ajustes RH y cuatro Q.

La comparación de enero conserva CQ histórico con base RH de agosto y
reajusta FQ en enero. Es una comparación de estimadores completos y no aísla
ciudad. IOS y la fecha real de publicación QVoice permanecen como límites
de acreditación histórica. No se declara preparación para uso operativo.
