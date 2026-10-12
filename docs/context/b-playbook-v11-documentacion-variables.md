# Qué se hizo con las variables del playbook V11

La comparación y la documentación terminaron el 12-oct-2026. Se conservaron
los ocho predictores y las dos interacciones de B y se examinaron 41
incorporaciones RH y 51 de QVoice, individualmente y en pares/tríos de las
seis candidatas de cada reserva interna. Los artefactos permanecen como
experimentales.

Modo `presentation`. Población: empleados regulares activos de Engineering,
excluyendo RF360, por foto mensual. Resultado: salida voluntaria en los seis
meses siguientes. Corte de conocimiento: 7-sep-2026. Sólo se publican
agregados y metadatos del modelo.

## Archivos para revisar

- [Diccionario en Excel](../../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/diccionario.xlsx): filtros por variable, decisiones, codificaciones, correspondencia con V11 y exclusiones.
- [Índice de las fichas](../../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/diccionario.md): explicación del tratamiento efectivo de cada representación.
- [Informe de resultados](../../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/informe.md): comparación temporal y gráficos con ejes compatibles con un decimal.
- [Verificación de la documentación](../../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/verification.json) y [manifest del suplemento](../../output/analysis/engineering/20261011/b-playbook-v11-v1/documentacion/manifest.json).

La referencia es el [playbook V11](../../output/distribution/attrition-43-variable-distributions-v11.html).
El nombre «43 variables» identifica ese archivo, que contiene 42 vistas
analíticas. Hay vistas con varias preguntas y vistas que comparten un
concepto. El diccionario cubre 102 representaciones, incluidos los diez
términos de B, y siete conceptos o representaciones excluidos. Ese conteo no
equivale a 102 variables independientes añadidas a B.

## Tratamiento documentado

Cada ficha registra origen y valores, tipo de entrada, fórmula, bandas y
categorías, faltantes y valores por defecto, fecha de conocimiento,
consideraciones, resultados y motivo de selección o exclusión por corte.
Los niveles y referencias se extraen de los modelos realmente guardados;
una variable ausente de los modelos finales no recibe una referencia final
inventada.

Todas las entradas se codificaron como categorías con indicadores 0/1. Una
binaria con un estado desconocido puede generar más de un indicador. Las
bandas numéricas no se trataron como una escala ordinal continua. Las
categorías RH poco frecuentes se agruparon usando sólo entrenamiento.

Se distingue entre una exclusión previa, una prueba con historia insuficiente,
una incorporación que no pasa las condiciones y una opción admisible que
pierde frente a otra combinación. No se reasignan scores de assessment.

## Resultado y alcance

La captura usa grupos que cubren el 30% de las personas por foto. Cada grupo
elegible tiene al menos 300 personas; se da igual peso a cada periodo.

| Evaluación | B | B + RH | B + RH + QVoice |
|---|---:|---:|---:|
| Captura en cinco periodos RH, feb-2024 a feb-2026 (%) | 44.6 | 45.1 | No corresponde |
| Captura en los dos periodos QVoice, ago-dic-2025 y ene-feb-2026 (%) | 41.6 | 42 | 42.8 |

En RH, la ganancia media de captura es 0.5 pp; su intervalo bootstrap del 95%
va de −0.1 a 1 pp e incluye cero. El Brier disminuye un 0.4% relativo. En las
dos ventanas QVoice, B + RH + QVoice gana 1.2 pp frente a B, con intervalo
de 0.2 a 2.1 pp. Son intervalos condicionales a las selecciones realizadas,
con 500 remuestreos pareados por persona; requieren confirmación posterior.

Al corte final se eligieron familia de puesto detallada, ciudad laboral y
aproximación postal a oficinas para Onsite. QVoice añadió las preguntas de
permanecer en Qualcomm (Q4) y poca intención de buscar otro empleo (Q12),
tanto sobre B como sobre B + RH. La evaluación anterior mide el procedimiento
de selección en cada corte, no estos coeficientes finales aplicados al pasado.

La distancia tiene una limitación material: usa catálogos estáticos de 2026,
centroides postales y el mínimo entre oficinas posibles de la ciudad; no
representa un trayecto de commute validado. La ficha conserva esta limitación
aunque la representación haya sido seleccionada.

Los grupos elegibles variaron entre 19 y 21; no se forzó 22. Se conservaron
sus dimensiones de antigüedad, salidas del equipo y nivel. Para B + RH,
la captura diagnóstica al ordenar predicciones fue 51.5%, frente a 45.1%
con esos grupos, a la misma capacidad del 30%. Esta diferencia justifica
evaluar otra agrupación; todavía no demuestra cuál funciona mejor ni un
óptimo global.

Fuente de las cifras: [results.json](../../output/analysis/engineering/20261011/b-playbook-v11-v1/results.json),
generado el 12-oct-2026; consultas y evidencia de entradas en
[evidence-ledger.json](../../output/analysis/engineering/20261011/b-playbook-v11-v1/evidence-ledger.json).

## Verificación y reproducción

La ejecución conserva sus fuentes y resultados en el
[manifest original](../../output/analysis/engineering/20261011/b-playbook-v11-v1/manifest.json).
La verificación final confirmó los 18 modelos, B completo, las reservas
temporales, la serialización, los hashes y la conservación de los modelos
anteriores. El registro previo contiene 101 pruebas aprobadas.

El suplemento reconcilió 612 decisiones, 217 registros de codificación y los
valores de las siete hojas del Excel. Se comprobaron 1085 enlaces locales,
sin enlaces rotos, y se revisaron las fichas y los gráficos renderizados.
No se persistieron filas de empleados ni predicciones individuales.

El generador está en
[build_b_playbook_variable_documentation.py](../../tools/build_b_playbook_variable_documentation.py).
Lee una ejecución terminada, verifica sus hashes y se niega a sobrescribir
un suplemento existente. La documentación tiene su propio manifest; no
modifica el registro ni las decisiones del entrenamiento.
