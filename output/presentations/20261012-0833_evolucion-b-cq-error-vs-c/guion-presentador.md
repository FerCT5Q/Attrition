# Guion del presentador · Evolución de B a CQ (Engineering)

Deck en inglés (excepción de idioma registrada en `config/presentations/model-evolution-b-cq-20261010.json`); guion en español. Duración objetivo: 18 minutos.

## Término usado en la presentación

**Higher-risk groups = grupos de riesgo alto.** Grupos con mayor riesgo estimado de salida voluntaria en los próximos 6 meses, seleccionados hasta cubrir el 30% de Engineering. Son los grupos que queremos atender primero. La etiqueta expresa su posición relativa en esta comparación.

## 1. Decisión · 1:00 (acumulado 1:00)

- **Objetivo:** Presentar la elección y su alcance.
- **Explicación:** Primero ordenamos los grupos por riesgo estimado y los seleccionamos hasta reunir el 30% de las personas de Engineering. Después medimos las salidas voluntarias durante los 6 meses siguientes. En promedio, en ese conjunto ocurrió el 43.1% de todas las salidas de la población evaluada. La primera tarjeta compara el error absoluto promedio por grupo y fecha: CQ lo reduce un 2.3% frente al modelo ampliado de RH (C). Con CQ, la diferencia media entre salidas estimadas y observadas equivale aproximadamente a 1 salida por cada 100 personas. Esa reducción relativa se calcula antes de redondear. La segunda tarjeta muestra los 0.7 puntos adicionales de captura que aporta la retroalimentación de los empleados frente a C. Probamos alternativas antes de mantener CQ.
- **Animación:** No hay animación.
- **Cifra para recordar:** 43.1% de las salidas en 30% de la plantilla.
- **Limitación:** Es retrospectivo y promedio; no es la probabilidad de que una persona se vaya ni salidas evitadas. El piloto no ha empezado.
- **Transición:** «Empecemos por el modelo de partida y los puntos que queríamos mejorar.»

## 2. Agenda · 0:45 (acumulado 1:45)

- **Objetivo:** Orientar el recorrido B → C → CQ.
- **Explicación:** Primero, el punto de partida y las primeras pruebas con la encuesta; luego lo que mejoró con C y con CQ; después las pruebas adicionales, y al final la decisión y los pasos siguientes.
- **Animación:** No hay animación.
- **Cifra para recordar:** Hay dos conjuntos de periodos: 4 periodos (feb-2024 a ene-2026) para B–C y 2 periodos recientes para C–CQ–D.
- **Limitación:** Las cifras sólo se comparan dentro de cada conjunto; no forman una serie.
- **Transición:** «Veamos de dónde partimos.»

## 3. Punto de partida y avances · 2:00 (acumulado 3:45)

- **Objetivo:** Recordar cómo B forma los grupos y rendir cuentas de los compromisos.
- **Explicación:** B divide Engineering por años en Qualcomm, salidas en el equipo y nivel. El 2026-07-26 quedaron 22 grupos elegibles, cada uno con al menos 300 personas. Hay 36 cruces posibles; los que no alcanzan ese tamaño se agrupan aparte. Entre los grupos elegibles se seleccionan los grupos de riesgo alto hasta cubrir el 30% de Engineering. A la derecha están los puntos que nos propusimos mejorar. CQ aportó una mejora modesta: ganó en un periodo y empató en el otro; el slide 6 muestra esa comparación. La regla estricta original de ganar en ambos periodos se conserva como antecedente en S01. Sobre la sobreestimación: el promedio de los grupos de riesgo alto mejoró, pero esa comparación no sigue al grupo concreto de mayor riesgo mostrado antes.
- **Animación:** Pulsar Play al explicar la división (≈5 s): todo Engineering → años → salidas del equipo → nivel.
- **Cifra para recordar:** 22 grupos, cada uno con 300 personas o más.
- **Limitación:** Fairness no se encontró en los estudios revisados: queda abierto.
- **Transición:** «La primera pregunta fue qué podíamos aprender de lo que los empleados dijeron en QVoice.»

## 4. Primeras pruebas con encuesta · 2:00 (acumulado 5:45)

- **Objetivo:** Explicar por qué QVoice era útil pero las primeras variantes no se adoptaron.
- **Explicación:** Evaluamos 9 variantes de la encuesta sobre los mismos dos periodos; todas ordenaron mejor el riesgo que B, pero ninguna superó todas las comprobaciones acordadas. Q4 fue la más sencilla y prometedora (7 de 8). Las combinaciones más amplias aportaron información más allá de si la persona respondió, pero el balance de la estimación global seguía limitando. El ajuste a seis meses sólo pudo probarse en ene–feb 2026 (ago–dic 2025 no tenía historia suficiente) y no mejoró el balance.
- **Animación:** No hay animación.
- **Cifra para recordar:** 9 de 9 ordenaron mejor; ninguna pasó todo.
- **Limitación:** No invalida QVoice ni la calibración en general.
- **Transición:** «También ampliamos la información de RH y comprobamos si C mejoraba el balance con las mismas definiciones de grupo.»

## 5. B frente a C · 2:15 (acumulado 8:00)

- **Objetivo:** Mostrar que C acercó las estimaciones con los mismos grupos.
- **Explicación:** Con las mismas definiciones de grupo, C reduce el gap promedio por grupo de 0.9 a 0.8 salidas por cada 100 personas: 11% menos en términos relativos. La proporción de salidas pasa de 45.2% a 45.4%, una diferencia pequeña e incierta (+0.27 puntos, IC95 -0.32 a 0.85; C gana 3 de 4 periodos). La preferencia por C fue práctica (S09). Si preguntan por el escenario de 40%: 56.4% frente a 57.6%.
- **Animación:** No hay animación.
- **Cifra para recordar:** Gap 11% menor con las mismas definiciones.
- **Limitación:** C no ganó todas las medidas en todas las fechas.
- **Transición:** «Con esa base, volvimos a comprobar qué añadía QVoice.»

## 6. C frente a CQ · 3:00 (acumulado 11:00)

- **Objetivo:** Mostrar el aporte modesto de la retroalimentación.
- **Explicación:** En las comprobaciones históricas, 43.1% de las salidas observadas vinieron de grupos de riesgo alto que suman 30% de Engineering. Al azar serían cerca de 30%; añadir la retroalimentación al modelo ampliado agregó unos 0.7 puntos. La línea aleatoria muestra el valor del modelo completo; la diferencia con C muestra el aporte de la encuesta. Mejora en un periodo (42.1% → 43.5%) y empata en el otro (42.8%): es una mejora modesta. El gap promedio por grupo es 2.3% menor.
- **Animación:** Pulsar Play al llegar al gráfico (≈5 s): línea aleatoria → C → CQ (+0.7) → tarjeta y periodos. Show all si se necesita ir directo.
- **Cifra para recordar:** 42.4% → 43.1%; +0.7 puntos.
- **Limitación:** Respaldo si preguntan: en los grupos de riesgo alto, estimado 5.2 vs 5.1 y observado 4.5 vs 4.6 por cada 100 personas (el observado cambia porque cada modelo puede identificar distintos grupos como de riesgo alto); sobreestimación media 0.68 → 0.55 puntos (unos 20% menor, CQ frente a C, grupos de riesgo alto que cubren el 30%). Mayor gap publicable: ago–dic 1.85 → 2.15, ene–feb 2.40 → 2.33; el indicador no sigue siempre al mismo grupo. IC95 de la diferencia de captura: 0.17 a 1.21 puntos, condicionado a los modelos ajustados, los grupos seleccionados por riesgo y los periodos observados.
- **Transición:** «La encuesta refina las estimaciones para identificar los grupos de riesgo alto, que siguen siendo fáciles de describir.»

## 7. Cómo funciona CQ · 2:00 (acumulado 13:00)

- **Objetivo:** Explicar CQ sin tecnicismos y aclarar privacidad.
- **Explicación:** La información de RH y la retroalimentación de los empleados forman la estimación; con ella se ordenan los mismos grupos conocidos y se identifican los grupos de riesgo alto hasta cubrir el 30% de Engineering. Durante el análisis autorizado se procesan respuestas individuales en memoria; no se guardan filas de empleados; los resultados compartidos son agregados por grupo y no se publican puntuaciones individuales. Cada encuesta se usa al año siguiente y las preguntas elegidas variaron entre periodos.
- **Animación:** Pulsar Play (≈3 s): RH → retroalimentación → grupos de riesgo alto.
- **Cifra para recordar:** Sólo resultados por grupo.
- **Limitación:** La versión final de septiembre aún necesita una comprobación con datos posteriores.
- **Transición:** «Antes de cerrar la elección, comprobamos otras combinaciones y modelos.»

## 8. Pruebas adicionales · 3:00 (acumulado 16:00)

- **Objetivo:** Mostrar que las alternativas no justificaron reemplazar CQ.
- **Explicación:** Las filas resumen grupos de pruebas, no un inventario exhaustivo. Fijar las preguntas con un promedio revisado mantiene 43.1% pero aleja las estimaciones (4.1% larger). D acerca un poco las estimaciones (0.8% smaller), pero encuentra menos salidas en ene–feb 2026 (42.1%) y no alcanza su propio umbral de 10%; su diferencia media de captura es -0.3 puntos (IC95 -1 a 0.4). El método alternativo con retroalimentación tiene una proporción similar (43.1%) con 10.3% larger de gap. Su sobreestimación media es la más cercana a cero porque compensa periodos de signo contrario (1.11 y -0.75); por eso la selección usa el error por grupo. Variantes de respaldo: promedio 33 y sin promedio tienen más error; el modelo mensual simple da prácticamente lo mismo que D; C actualizado captura 42.7% con más error.
- **Animación:** No hay animación.
- **Cifra para recordar:** Ninguna alternativa ofreció un balance mejor y estable.
- **Limitación:** Las pruebas negativas también son un resultado del trabajo.
- **Transición:** «Con estas comprobaciones, la decisión se mantiene; el siguiente paso es contrastarla con datos nuevos.»

## 9. Siguientes pasos · 2:00 (acumulado 18:00)

- **Objetivo:** Cerrar con la elección y los pasos propuestos.
- **Explicación:** CQ sigue siendo el modelo seleccionado. Proponemos comprobarlo en un periodo nuevo, revisar diferencias entre grupos, confirmar con RH cómo puede usarse la encuesta y preparar un piloto limitado. Son pasos propuestos, aún sin calendario ni aprobación.
- **Animación:** No hay animación.
- **Cifra para recordar:** CQ seleccionado; ganancia modesta.
- **Limitación:** El efecto de las acciones de retención no se ha medido. Fairness y el acuerdo de uso de QVoice siguen sin confirmar.
- **Transición:** «Cerrar hacia el minuto 18 y abrir preguntas sobre esta diapositiva.»

## Preguntas preparadas

- **¿Quiénes son los grupos de riesgo alto?** Grupos con mayor riesgo estimado de salida voluntaria en los próximos 6 meses, seleccionados hasta cubrir el 30% de Engineering. Son los grupos que queremos atender primero. La etiqueta expresa su posición relativa en esta comparación.
- **¿Por qué no B?** C mantiene las definiciones de grupo y reduce 11% el gap por grupo; el cambio en la proporción de salidas fue pequeño e incierto.
- **¿Por qué CQ si no ganó los dos periodos?** Ganó uno y empató el otro, con +0.7 puntos de media y 2.3% menos de gap. La regla estricta original se conserva como antecedente; la elección ponderó magnitud, error y utilidad (S01).
- **¿Cuánto aporta la encuesta y cuánto el modelo?** Al azar, alrededor de 30%; C, 42.4%; CQ, 43.1%. La encuesta aporta los últimos 0.7 puntos.
- **¿43.1% significa que esas personas se irán?** No. El denominador es el total de salidas voluntarias de la población evaluada durante los 6 meses siguientes. El numerador son las salidas ocurridas en los grupos seleccionados por riesgo estimado, que reúnen el 30% de las personas. Es un promedio histórico.
- **¿Se resolvió la sobreestimación?** En los grupos de riesgo alto, la sobreestimación media de CQ es unos 20% menor que la de C. El grupo con mayor error mejora en un periodo y empeora en el otro, y algunos grupos siguen necesitando trabajo. Esta comparación no sigue al grupo concreto de mayor riesgo mostrado antes.
- **¿Por qué no usar la sobreestimación media para elegir?** Errores de signo contrario se compensan. El método alternativo tiene la media más cercana a cero, pero 10.3% más de error por grupo.
- **¿Y fairness?** No se encontró una evaluación archivada en los estudios revisados; es el paso 2.
- **¿Se usan las respuestas individuales de QVoice?** En el análisis autorizado se procesan en memoria; no se guardan filas de empleados; sólo se reportan resultados por grupo y no se publican puntuaciones individuales.
- **¿D fue peor en todo?** No. Acercó un poco las estimaciones (0.8%), pero no alcanzó su propio umbral de 10% y perdió captura en el periodo reciente.
- **¿QVoice causa las salidas?** No. Son asociaciones predictivas.
- **¿Está probado el modelo final de septiembre?** No. Sus coeficientes requieren datos posteriores a su ajuste.
- **¿Por qué 30%?** Es el escenario de comparación; la capacidad real se define para el piloto.
- **¿Por qué C tiene 45.4% en la diapositiva 5 y 42.4% en la 6?** Son conjuntos de periodos distintos; no es un deterioro.
