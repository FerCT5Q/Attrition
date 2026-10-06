# Aplicabilidad a Critical Tech

## Regla de scope

Critical Tech se aplica como filtro de población usando `hrda.critical_tech`.
No se debe inferir membership por títulos o nombres parecidos.

## Implicaciones estadísticas

- Critical Tech reduce heterogeneidad de mercado laboral frente a toda la
  compañía.
- El modelo pooled conserva potencia para segmentos pequeños.
- Las métricas se deben reportar por segmento y family cuando el tamaño lo
  permita.
- Los segmentos con pocos eventos se poolen y no se interpretan por separado.
- La definición del catálogo debe ser versionada antes de comparar años.

## Implicaciones de People Analytics

El valor del modelo no está sólo en ordenar riesgo. Debe identificar grupos
con un patrón interpretable y una palanca posible: carrera, manager, equipo,
engagement, movilidad, compensación relativa o diseño del trabajo.

## Limitación vigente

La tabla actual tiene una key sin match exacto a `job_family`. Además, el
archive y el catálogo actual aún no están reconciliados al mismo grain. Por
ello, la pertenencia histórica debe tratarse con cautela.

## Contexto geográfico y auditoría

- La evidencia de embeddedness multipaís no autoriza asumir que un mismo driver
  tiene el mismo sentido o magnitud en cada región. Toda interacción se
  preespecifica, se valida temporalmente y sólo se reporta si la cohorte es
  suficiente.
- Fairness no se resuelve suprimiendo una categoría sin más. Los atributos
  protegidos permanecen fuera del targeting y sólo se usan, con autorización,
  para auditorías agregadas de cobertura, desempeño y calibración.
