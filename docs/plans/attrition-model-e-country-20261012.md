# Modelo E: país laboral añadido sobre C

## Objetivo

Comprobar si `work_country`, una señal con histórico confiable, conserva
información incremental al añadirse al modelo C. La comparación es experimental
y se entrega en modo
`presentation`; no publica filas, identificadores ni scores individuales.

La primera preparación quedó conservada en
`output/analysis/engineering/20261012/c-signal-expansion-v1/`. Esa corrida sólo
cargó y validó las entradas y terminó antes de ajustar un modelo porque el
arnés comprobaba como columnas físicas las dos interacciones que C construye
internamente. No se usan sus artefactos como resultados de modelado.

## Diseño congelado

Se reutilizan los cuatro cortes externos y las selecciones de variables y L2
archivadas en `output/analysis/engineering/20261008/model-c-v2/selection/`.
Para cada corte se reajusta C y después se reajusta una variante: C más
`work_country`. Las reglas de grupos permanecen en
antigüedad × salidas del equipo × nivel, con capacidad principal del 30%.

La comparación mide Brier, log-loss, PR-AUC, lift, captura al 30% y error de
grupo en los mismos cortes temporales. Se calcula un intervalo pareado por
persona para cada variante, conservando las observaciones mensuales juntas.
Los resultados externos no se usan para volver a seleccionar C ni para
promover una variante.

## Señal probada

- `work_country`: país laboral categórico derivado de `country`, normalizado y
  agrupado con categorías raras usando sólo el entrenamiento de cada corte.

No se usa `job_family_detail`, `work_city` ni ninguna señal histórica del
manager en esta corrida. No se reconstruyen filas ni se calculan scores fuera
de memoria.

## Regla de lectura

Una señal se considera candidata a una ronda posterior si mejora de forma
consistente la pérdida y/o la captura, sin empeorar materialmente el error de
grupo. Una mejora sobre C no se interpreta como causalidad ni como garantía de
mejora sobre C + QVoice.

La configuración ejecutable está en
`config/engineering_model_e_country_20261012.json`.
