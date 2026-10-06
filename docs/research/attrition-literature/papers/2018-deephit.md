# DeepHit: A Deep Learning Approach to Survival Analysis With Competing Risks

## Ficha

- Autores: Changhee Lee, William Zame, Jinsung Yoon y Mihaela van der Schaar
- Año: 2018
- Publicación: AAAI
- DOI: `10.1609/aaai.v32i1.11842`
- Texto abierto: https://ojs.aaai.org/index.php/AAAI/article/view/11842
- Consultado: 2026-09-07
- Acceso: Open Access
- Etiquetas: `challenger`, `deep-survival`, `competing-risks`

## Resumen

DeepHit usa una red neuronal para aprender directamente una distribución
discreta de tiempo hasta el evento. Puede modelar relaciones no lineales entre
covariables y riesgos que cambian a través del tiempo, y permite múltiples
causas competidoras.

La función de pérdida combina ajuste de probabilidad con un componente de
ranking. El resultado es flexible, pero más difícil de gobernar y explicar que
un modelo de hazard regularizado.

## Aplicabilidad a Attrition

Podría servir en una fase avanzada si se necesitan causas múltiples y el
volumen de Critical Tech justifica deep learning. Para el MVP es demasiado
complejo y no resuelve por sí mismo la traducción de drivers a acciones.

## Decisión

`línea futura`; no usar como champion inicial.
