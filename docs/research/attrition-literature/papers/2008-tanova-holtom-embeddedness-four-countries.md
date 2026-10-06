# Using job embeddedness factors to explain voluntary turnover in four European countries

## Ficha

- Autores: Cem Tanova y Brooks C. Holtom
- Año: 2008
- Revista: *The International Journal of Human Resource Management*, 19(9), 1553–1568
- DOI: `10.1080/09585190802294820`
- URL oficial: https://doi.org/10.1080/09585190802294820
- Fuente consultada: Crossref, OpenAlex work `W2155796824` y ficha del repositorio institucional de Eastern Mediterranean University
- Fecha de consulta: 2026-09-24
- Estado de acceso: abstract y metadatos visibles. OpenAlex indexa una versión de repositorio `CC BY-NC-ND`, pero la ficha consultada no expone un bitstream descargable; no se trató como texto completo.
- Etiquetas: `embeddedness`, `turnover-voluntario`, `multipaís`, `geografía`, `hipótesis`

## Abstract y resumen

### Abstract original

El abstract visible describe un estudio europeo amplio y multipaís sobre
turnover voluntario. Indica apoyo al modelo tradicional de deseabilidad y
facilidad de movimiento, y reporta que job embeddedness añade varianza por
encima de variables demográficas y tradicionales.

### Resumen en español

El trabajo es útil porque pone la retención de talento calificado en un marco
internacional y no reduce la salida a satisfacción o a oportunidades externas.
Presenta job embeddedness como complemento del modelo tradicional de turnover.
Sin embargo, con el material accesible no se confirmaron países, tamaño,
instrumentos, horizonte, modelo estadístico ni tamaños de efecto; por ello no
se importan componentes, pesos ni una escala de embeddedness al modelo propio.

## Pregunta y datos

- Pregunta: si factores de job embeddedness contribuyen a explicar turnover voluntario más allá de demografía y del modelo tradicional de movimiento, en cuatro países europeos.
- Población: dataset europeo amplio y multipaís; el abstract menciona escasez de talento calificado e ICT como contexto, pero no permite confirmar la composición exacta de la muestra.
- Tamaño: no confirmado con la evidencia accesible.
- Grain: no confirmado con la evidencia accesible.
- Target y horizonte: turnover voluntario; no se pudo confirmar si el evento proviene de registros administrativos, encuesta o qué ventana temporal usa.
- Censura o competing risks: no confirmado.

## Método y validación

- Método: comparación conceptual entre un modelo tradicional de turnover y factores de job embeddedness; la especificación estadística no fue visible en el material consultado.
- Variables: facilidad y deseabilidad de movimiento, demografía y factores de embeddedness; las definiciones operativas y escalas no fueron accesibles.
- Split temporal: no confirmado. No se asume validación temporal por el título ni por el abstract.
- Métricas: no confirmadas.
- Resultados: el abstract reporta soporte al modelo tradicional y contribución incremental de embeddedness; no se usan cifras, significancia ni causalidad porque el texto completo no estuvo disponible.

## Limitaciones

- Leakage: no se pudo revisar fecha de medición, secuencia predictor-evento ni controles de información posterior a la salida.
- Sesgos: países, sectores, muestreo y equivalencia de escalas no fueron confirmados; una asociación multipaís no demuestra invariancia geográfica.
- Generalización: no confirma transferencia a empleados Regular de Critical Tech ni a la definición interna de attrition voluntario.
- Fairness/privacidad: país o región pueden funcionar como contexto o proxy; cualquier análisis por grupos debe ser agregado, con cohortes reportables y sin targeting individual.

## Aplicabilidad a Attrition

- Relación con Critical Tech: respalda tratar región/mercado laboral como posible modificador de una hipótesis de retención, no como una explicación universal para todos los segmentos.
- Variables disponibles relacionadas: región, segmento, job family, tenure, movilidad y señales de equipo pueden representar bloques de hipótesis distintos; no equivalen automáticamente a una escala validada de embeddedness.
- Qué adoptar: documentar el contexto geográfico y evaluar estabilidad por región/segmento sólo cuando la cobertura y los eventos lo permitan.
- Qué probar como challenger: un bloque de proxies observados y fechados, más interacciones preespecificadas con región, contra el mismo holdout temporal del baseline reejecutado de fase 1.
- Qué posponer: un índice de job embeddedness, pesos publicados, comparaciones entre países y cualquier inferencia causal hasta contar con medidas, población y evaluación locales.

## Acción y decisión

- Señal asociada: vínculos, ajuste y costos percibidos de salida son un marco de hipótesis, no variables ya medidas ni drivers confirmados.
- Palanca potencial: carrera interna, movilidad, conexión con equipo y claridad de rol; cada una requiere una fuente y una evaluación propia.
- Acción candidata: revisar en cohortes agregadas si los bloques de carrera, movilidad y equipo aportan señal estable de manera heterogénea por región.
- Métrica de seguimiento: PR-AUC, Brier, calibración, lift y estabilidad temporal/geográfica; ninguna métrica del paper se traslada.
- Decisión: `referencia conceptual` para heterogeneidad geográfica y job embeddedness; `probar como challenger` sólo mediante proxies internos validados.

## Trazabilidad

- Evidencia consultada: Crossref para autores, revista y paginación; OpenAlex para DOI, abstract indexado y estado OA; repositorio EMU `https://hdl.handle.net/11129/14067` para la ficha de acceso.
- Sección/página si el texto completo fue revisado: no aplica; sólo abstract y metadatos visibles.
- Limitaciones de acceso: la ficha de repositorio no devolvió bundles/bitstreams públicos al consultarla. No se conservó una copia local ni se presentaron detalles no verificables como resultados del paper.
