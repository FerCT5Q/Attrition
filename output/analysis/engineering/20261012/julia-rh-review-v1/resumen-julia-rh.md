# Resumen para Julia y RH

**FQ + BU L3 estima mejor en promedio; CQ continúa elegido.** FQ reduce log-loss ×1000 de 137.7 a 136.4; añadir BU L3 a FQ lo reduce a 136. Los intervalos pareados del cambio excluyen cero. Al atender 30%, los tres capturan alrededor de 43.1% de las exposiciones con salida. El empate de captura no elimina la mejora de estimación. En enero CQ conserva su base RH de agosto y FQ la reajusta: la comparación frente a CQ no aísla el aporte de ciudad.

**Conservar la agrupación principal.** La subdivisión de 100 personas no cumple las guardas en ambos periodos. Con FQ + BU L3 y capacidad 10%, las sensibilidades de 150 y 200 sí cumplen; son escenarios limitados para validar, sin adoptar retrospectivamente un mínimo como ganador general. El verdadero REST se conserva.

**No aplicar el escalar R6 probado.** La corrección aprendida en tres orígenes anteriores empeora el sesgo absoluto y log-loss de enero–febrero de 2026 para los tres modelos. Las brechas locales siguen visibles.

**La ausencia QVoice requiere atención específica.** No activa automáticamente el modelo RH. Se separan completa/parcial/ausente y se comparan riesgo, pérdidas y captura frente a RH sobre las mismas cohortes. El cambio de diciembre a enero coincide con nueva encuesta y nuevo modelo.

**Cómo empezar con RH.** Revisar las fichas históricas de los grupos priorizados: continuidad después de salidas, soporte de incorporación o acceso a desarrollo, según el grupo. RH y la función operativa propuesta contrastan la hipótesis en 30 días y siguen los acuerdos a 90 días. No se atribuye causalidad ni se interpretan personas individualmente.

Antes de un uso operativo, acreditar disponibilidad histórica de IOS y fecha real de publicación QVoice, confirmar capacidad y responsables, y evaluar una cohorte posterior al ajuste. Los resultados son retrospectivos y condicionales a las variables y reglas elegidas.

- [Informe y comparación](informe.md).
- [44 variables en Excel](documentacion/variables-44.xlsx) y [tabla final con enlaces](documentacion/variables-44-final.md).
- [Matriz inicial de comentarios](documentacion/matriz-comentarios.md) y [cierre](cierre-comentarios.md).
- [Fichas históricas](fichas/indice.md).
- [Diagnósticos completos](diagnosticos-completos.md), [segmentos](segmentos.md) y [anexo reproducible](anexo-tecnico.md).

Validación: CQ histórico reproducido en ambos periodos; capacidad, población y particiones reconciliadas; 500 remuestreos por persona y siete pruebas numéricas/sintéticas. Los intervalos observados y del riesgo medio tienen etiquetas y métodos distintos. Sólo modelos y agregados persistidos.
