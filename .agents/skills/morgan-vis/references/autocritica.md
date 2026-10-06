# Guía de autocrítica

Adaptación de los prompts del método original. Allí se entregaban a otra IA;
aquí son preguntas que el agente responde sobre su propio trabajo. Registra la
respuesta sólo cuando cambie una decisión o deje un riesgo pendiente.

## 1. Explorar los datos

Antes de proponer un mensaje:

- ¿Qué ambigüedades tiene el diccionario de datos o la definición de la
  medida?
- ¿Cuáles son los patrones más fuertes para la pregunta de negocio?
- ¿Dónde se concentra cada patrón?, ¿contra qué se compara?, ¿cómo cambió?
- ¿Qué hipótesis explican el patrón, ordenadas por fuerza de evidencia?
- ¿Qué explicaciones alternativas existen?, ¿qué datos las confirmarían o
  descartarían?
- ¿Qué cálculos sostienen cada afirmación importante?

No infieras causalidad por asociación o coincidencia temporal.

## 2. Poner a prueba el mensaje

Con el mensaje propuesto en una frase, intenta refutarlo:

- ¿Qué partes sostienen los datos?
- ¿Qué partes son demasiado fuertes o amplias?
- ¿Qué explicación alternativa produciría el mismo gráfico?
- ¿Qué limitaciones de muestra, cobertura o ventana lo debilitan?
- ¿Cuál es la redacción más defendible?

## 3. Comparar bocetos

Cuando haya más de una representación razonable, compara:

- alineación entre tipo de gráfico y mensaje;
- velocidad de comprensión;
- riesgo de interpretación engañosa;
- accesibilidad y etiquetado;
- desorden y complejidad innecesaria.

Elige, justifica y anota los trade-offs de la opción elegida.

## 4. Revisar el gráfico terminado

Revisa preferentemente una captura renderizada al tamaño de destino:

- ¿La conclusión es evidente en pocos segundos?
- ¿El tipo de gráfico sigue siendo el adecuado con los datos reales?
- ¿Las escalas y los intervalos de tiempo son honestos?
- ¿Etiquetas, colores, anotaciones y benchmarks son útiles?
- ¿Qué se puede quitar?
- ¿Qué riesgos de accesibilidad existen?
- ¿Algún elemento sugiere causalidad no demostrada o exagera el patrón?

Para cada cambio, anota motivo y costo. No asumas que tu primera
recomendación es correcta.
