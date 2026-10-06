# Discrete-Time Methods for the Analysis of Event Histories

## Ficha

- Autor: Paul D. Allison
- Año: 1982
- Revista: Sociological Methodology
- DOI: `10.2307/270718`
- URL: https://doi.org/10.2307/270718
- Consultado: 2026-09-07
- Acceso: JSTOR; normalmente restringido
- Etiquetas: `fundacional`, `discrete-time`, `person-period`

## Resumen

El trabajo presenta métodos para analizar eventos observados en tiempo
discreto. La transformación clave es pasar de una fila por persona a una fila
por persona-periodo, indicando si el evento ocurre en ese intervalo.

El enfoque permite incorporar covariables que cambian por periodo, manejar
censura y modelar la dependencia entre la probabilidad del evento y el tiempo.
Las formulaciones logística y complementary log-log son alternativas naturales
para distintos supuestos sobre el proceso continuo subyacente.

## Aplicabilidad a Attrition

Es una referencia directa para construir el dataset employee-snapshot mensual y
el target de salida entre el snapshot actual y el siguiente. También respalda
la inclusión de baseline temporal y variables conocidas al cierre de cada
snapshot.

## Limitaciones

El paper es metodológico y no responde qué acciones retienen empleados. La
construcción correcta de la ventana, el evento y la información conocida sigue
siendo responsabilidad del proyecto.

## Decisión

`adoptar` como fundamento del grain y del hazard mensual.
