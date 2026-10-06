# Extensiones para Attrition y datos de RH

El método de Julia es general. Estas reglas lo completan para este proyecto y
no sustituyen a [AGENTS.md](../../../../AGENTS.md), que prevalece.

## Clasificar el entregable antes de graficar

- `presentation` es el modo por defecto: slides, entregas compartibles o
  destino poco claro. Suprime o anonimiza etiquetas de categorías protegidas.
- `internal_analysis` sólo aplica cuando el usuario lo declara expresamente.
  Márcalo de forma visible en el artefacto.
- En ambos modos: nada de filas, IDs, nombres, correos, domicilios, texto
  libre ni valores individuales. Compensación sólo en bandas, percentiles o
  estadísticos agregados.
- Cohortes compartidas de al menos 30. Una excepción debe estar registrada en
  `config/` y citarse en la evidencia; no la extiendas a otro uso.

## Mensajes sobre tasas y cohortes

- Toda tasa declara numerador, denominador, población y ventana, por ejemplo
  «salidas voluntarias en los 12 meses siguientes / empleados regulares
  activos al snapshot». Una tasa sin ventana no es comparable.
- Muestra el n de cada barra o cohorte cuando la comparación dependa de su
  tamaño; marca como no estimables las cohortes debajo del mínimo en lugar de
  graficarlas.
- Distingue employee-snapshot rows de empleados distintos; no los mezcles en
  un mismo eje.
- Compara contra un baseline explícito (población total, cohorte comparable o
  periodo previo) y rotúlalo. El lift sin baseline no se interpreta.
- No cambies denominadores, periodos ni poblaciones para mejorar la historia.
  Si dos gráficos usan poblaciones distintas, dilo en el subtítulo.
- Las diferencias entre cohortes son asociaciones. Evita títulos de causa
  («el trabajo remoto provoca salidas»); usa concentración o asociación.

## Color con significado en Attrition

- Si la historia usa colores para clasificar tasas de attrition frente a una
  referencia, reutiliza la política vigente en `config/` (por ejemplo
  `config/attrition_color_policy_v8.json`) con su fórmula, materialidad y
  estado gris para no comparable. No inventes umbrales nuevos.
- Fuera de esa semántica, aplica el principio de Julia: un color de énfasis y
  gris de contexto, consistentes en toda la historia.

## Formato de cifras visibles

- Enteros sin decimales; números no enteros con un máximo de un decimal. Aplica
  a etiquetas, ejes, KPIs, tooltips y tablas. Los cálculos y la evidencia
  conservan la precisión necesaria.
- Un valor positivo que redondea a cero se muestra como `<0.1%`, no como `0%`.
- Todo el texto visible, títulos, notas y limitaciones en español; los
  identificadores técnicos pueden quedar en inglés.

## Evidencia visible

- Cada gráfico con datos cita, al menos en nota: fuente o consulta guardada,
  fecha de ejecución, población y ventana.
- Presentar un assessment no cambia sus scores. Una corrección visual no
  convierte evidencia histórica en evidencia vigente.
