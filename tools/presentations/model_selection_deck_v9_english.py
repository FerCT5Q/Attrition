"""Traducción breve de la v9; conserva los datos y la estructura del original."""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser


TEXT = {
    # Portada y agenda.
    "Modelo de attrition voluntaria de Engineering: qué elegimos y por qué (v9)":
        "Engineering attrition: our recommended model (v9 · English)",
    "People Analytics · Engineering · salidas voluntarias a 6 meses · octubre 2026":
        "People Analytics · Engineering · voluntary exits over 6 months · October 2026",
    "Propuesta de portada: enero a julio de 2026":
        "Cover proposal: January to July 2026",
    "Enero a julio de 2026": "January to July 2026",
    "1. Enero a julio de 2026": "1. January to July 2026",
    "Engineering · 25-ene a 25-jul de 2026 · salidas voluntarias":
        "Engineering · Jan 25 to Jul 25, 2026 · voluntary exits",
    "El modelo estimó casi las mismas salidas que ocurrieron":
        "The six-month estimate was close to actual exits",
    "estimado de salidas voluntarias": "estimated voluntary exits",
    "real: 1,192 salidas voluntarias": "actual: 1,192 voluntary exits",
    "personas activas en la foto de enero": "people active at the January snapshot",
    "Seguimos a las mismas personas durante los 6 meses posteriores a la foto de enero. Modelo entrenado con historia hasta julio de 2025.":
        "We followed the January group for 6 months. The model was trained on data through July 2025.",
    "Fuente: prueba histórica de Engineering del 3-oct-2026, foto del 25-ene-2026.":
        "Source: Engineering test, Oct 3, 2026. Snapshot: Jan 25, 2026.",
    "Recomendamos un modelo que identifica los grupos de Engineering con más attrition, y que acertó al probarlo en 4 periodos pasados que no conocía":
        "We recommend a model that finds higher-risk Engineering groups and held up in 4 past tests",
    "cuánta attrition estimó contra la que hubo en el último periodo":
        "estimated vs. actual exits in the latest test",
    "estimado vs. real · 25-ene a 25-jul de 2026":
        "estimated vs. actual exits · Jan 25–Jul 25, 2026",
    "los 5 grupos de mayor riesgo reúnen al 19% de las personas y concentraron el 31% de las salidas reales":
        "the 5 highest-risk groups held 19% of people and 31% of actual exits",
    "22 grupos": "22 groups",
    "con datos que RH ya tiene: antigüedad, salidas en el equipo y nivel; cada uno con más de 300 personas":
        "using data HR already has: time at the company, team exits and level; over 300 people per group",
    "Cómo lo probamos:": "How we tested it:",
    "le dimos la historia sólo hasta una fecha, estimó los 6 meses siguientes y lo comparamos con lo que pasó; lo repetimos 4 veces, con periodos de feb-2024 a ene-2026. Partimos de 43 trabajos de investigación y comparamos 4 tipos de modelo. Antes de usarlo falta afinar el grupo más alto y revisar que sea justo con todos los grupos.":
        "At each date, we used only past data, predicted the next 6 months and checked actual exits. We repeated this 4 times, Feb 2024–Jan 2026. Informed by 43 studies; 4 model types tested. Before use: reduce overestimates in the highest-risk group and check fairness across groups.",
    "De la literatura a un modelo listo para piloto, en cinco partes":
        "From research to the pilot plan, in five steps",
    "Cada parte responde una pregunta de la decisión; las cifras vienen de los datos de Engineering, no de los papers":
        "Each step supports the decision. All results come from Engineering data.",
    "Cómo nos documentamos": "Research and selection",
    "Diapositivas 3–4": "Slides 3–4",
    "43 trabajos, criterios de búsqueda y de 10 familias de modelos a una.":
        "43 studies, search rules and 10 model types narrowed to one.",
    "El modelo elegido": "The chosen model",
    "Diapositivas 5–6": "Slides 5–6",
    "Cómo estima el riesgo mes a mes, lo acumula a 6 meses y lo resume por grupo.":
        "From monthly risk to a 6-month estimate for each group.",
    "Qué grupos encuentra": "The groups it finds",
    "Diapositiva 7": "Slide 7",
    "Los 5 grupos de Engineering con más riesgo a 6 meses y cómo los elegimos.":
        "Engineering’s 5 highest-risk groups and how we chose them.",
    "Qué tan bueno es": "How well it works",
    "Diapositiva 8": "Slide 8",
    "Si ordena bien el riesgo y si le atina a cuántos se van, en 4 pruebas.":
        "Does it find higher-risk groups and estimate exits well? Results from 4 tests.",
    "Próximos pasos": "Next steps",
    "Diapositiva 9": "Slide 9",
    "Lo que haremos en las siguientes 2 semanas.": "Our plan for the next 2 weeks.",
    "Clasificación: presentación. Sólo resultados agregados por grupo.":
        "Presentation · Group-level results only.",

    # Investigación y elección del modelo.
    "Revisamos 43 trabajos de investigación: nos dijeron qué tipo de modelo usar y qué datos probar; los datos de Engineering decidieron la versión final":
        "43 studies guided our choices; Engineering data shaped the final model",
    "Dimos prioridad a trabajos con métodos reproducibles, datos longitudinales y salidas reales":
        "We favored repeatable methods, data tracked over time and actual exits.",
    "líneas de búsqueda": "search themes",
    "Supervivencia, turnover, talento técnico, riesgos competitivos, ML, constructos de RH, causalidad, fairness y texto":
        "Time to exit, turnover, technical talent, exit types, advanced models, HR factors, retention impact, fairness and text",
    "búsquedas registradas": "logged searches",
    "Crossref, OpenAlex, editoriales, JSTOR, arXiv, PubMed Central y repositorios; Scholar sólo para descubrir":
        "Crossref, OpenAlex, publishers, JSTOR, arXiv, PubMed Central and repositories; Scholar for discovery",
    "criterios de inclusión": "inclusion rules",
    "Estudia turnover o retención, método longitudinal, censura o riesgo temporal, constructos de RH, o gobierno":
        "Turnover or retention, data over time, partial follow-up or changing risk, HR factors, or governance",
    "trabajos, de 1972 a 2026": "studies, 1972–2026",
    "42 con ficha revisada y 1 sin texto accesible. Se excluyeron estudios sin método, duplicados y modelos sin validación":
        "42 reviewed; 1 full text unavailable. Excluded duplicates, unclear methods and untested models.",
    "Trabajos por tema y qué decidió cada tema": "What each research theme informed",
    "Cómo medir el riesgo en el tiempo": "Risk over time",
    "Seguir a cada persona mes a mes, aunque todavía no se haya ido":
        "Follow people month by month, including those who stay",
    "Eligió calcular el riesgo mes a mes": "Led us to monthly risk estimates",
    "Estudios de rotación en empresas": "Workplace turnover",
    "Las salidas llegan en olas y se miden con salidas reales":
        "Exits come in waves; test against actual exits",
    "Confirmaron que ese método funciona con datos de RH":
        "Supported this approach for HR data",
    "Modelos más complejos (machine learning)": "More complex models",
    "Comparados con modelos simples en las mismas condiciones":
        "Compared with simpler models under the same conditions",
    "Ganan poco: los usamos sólo como punto de comparación":
        "Small gains; kept as a benchmark",
    "Qué explica que alguien se vaya": "Why people leave",
    "Carrera, jefe y equipo, compromiso, arraigo":
        "Career, manager and team, engagement and ties to work",
    "Agrupó las variables de la lluvia de ideas y del playbook en bloques y dio el orden para probarlos":
        "Grouped candidate signals and set their test order",
    "Uso responsable": "Responsible use",
    "Privacidad de las personas y trato parejo": "Privacy and fair treatment",
    "Sólo resultados por grupo y revisar que sea justo con todos":
        "Report by group and check fairness",
    "No copiamos ningún modelo ni sus datos: revisamos cada trabajo y lo usamos para aportar ideas. Los modelos que probamos se construyeron y ajustaron con los datos de Qualcomm.":
        "The studies informed our approach. Every model was built and fitted with Qualcomm data.",
    "De 10 familias de modelos estadísticos, probamos 4 y elegimos el riesgo mes a mes":
        "We tested 4 of 10 model types and chose monthly risk",
    "5 descartadas y 1 pendiente · criterios fijados el 30-sep-2026, antes de ver resultados · pruebas con datos de Engineering (diapositiva 8)":
        "5 ruled out; 1 pending · criteria set Sep 30, 2026, before results · Engineering tests on slide 8",
    "Familias de modelos, desviación del total real y decisión de evaluación":
        "Model types, error vs. actual exits and test status",
    "Familia de modelos": "Model type",
    "Estado": "Status",
    "Desviación": "Estimation error",
    "vs. total real · menor es mejor": "vs. actual exits · lower is better",
    "Motivo": "Reason",
    "Riesgo mes a mes (hazard discreto)": "Monthly risk",
    "Probada": "Tested",
    "Usa cada mes (C1), menor desviación (C2) y mejor orden del riesgo (C3)":
        "Uses each month (C1); lowest error (C2); best risk ranking (C3)",
    "Regresión logística a 6 meses": "6-month logistic model",
    "Descarta meses recientes (C1, C7); más desviación (C2)":
        "Drops recent months (C1, C7); larger error (C2)",
    "Gradient boosting (LightGBM)": "LightGBM",
    "Difícil de explicar (C5); más desviación (C2)":
        "Harder to explain (C5); larger error (C2)",
    "Promedio histórico": "Historical average",
    "No distingue grupos de riesgo (C3)": "Does not separate risk groups (C3)",
    "Pendiente": "Pending",
    "Sin prueba": "Not tested",
    "Pendiente de prueba": "Test pending",
    "Cox de riesgos proporcionales": "Cox model",
    "Descartada": "Ruled out",
    "Menos adecuado para datos mensuales (C1)": "Less suited to monthly data (C1)",
    "Riesgos competitivos y multiestado": "Exit types and transitions",
    "Falta definir tipos de salida": "Exit types still need to be defined",
    "Deep learning y texto": "Deep learning and text",
    "Difícil de explicar (C5); sin texto libre (C6)":
        "Hard to explain (C5); free text excluded (C6)",
    "Causal y uplift": "Impact of retention actions",
    "Sin acciones de retención registradas": "No recorded retention actions",
    "Ecuaciones estructurales y mediación": "HR relationship models",
    "Explica relaciones, no estima riesgo (C3)": "Explains relationships, not exit risk (C3)",
    "Desviación:": "Estimation error:",
    "% de diferencia entre las salidas estimadas y las reales (promedio de 4 pruebas).":
        "% difference between estimated and actual exits, averaged over 4 tests.",
    "Qué buscamos en el modelo": "What we need from the model",
    "Aprovecha la historia mensual.": "Uses monthly history.",
    "Estima bien la attrition total y por grupo.": "Estimates exits overall and by group.",
    "Identifica los grupos de mayor riesgo.": "Finds the highest-risk groups.",
    "Funciona al probarlo en otras fechas.": "Works across different test dates.",
    "Es sencillo de entender.": "Is easy to understand.",
    "Protege la privacidad y permite revisar el trato justo.":
        "Protects privacy and supports fairness checks.",
    "Funciona aun con datos incompletos.": "Works with incomplete data.",
    "Es fácil de actualizar.": "Is easy to update.",
    "Tiene respaldo en estudios de salidas reales.": "Is backed by studies of actual exits.",
    "Desviación: comparación de los modelos base con datos de Engineering, 1-oct-2026.":
        "Error: comparison of base models using Engineering data, Oct 1, 2026.",

    # Señales y cálculo.
    "El modelo estima el riesgo de renunciar cada mes con 8 señales y 2 combinaciones, y lo acumula a 6 meses":
        "8 signals and 2 combinations estimate monthly risk, then risk over 6 months",
    "Riesgo mes a mes, también llamado hazard discreto · especificación final del 3-oct-2026":
        "Monthly chance of a voluntary exit · final model as of Oct 3, 2026",
    "1 · Datos": "1 · Data",
    "Fotos mensuales de Engineering": "Monthly Engineering records",
    "1,880,719 personas-mes, de jul-2021 a jul-2026. Para cada persona y mes: sus señales y si salió de forma voluntaria antes de la foto siguiente.":
        "1,880,719 monthly person records, Jul 2021–Jul 2026. Each shows the known signals and any voluntary exit before the next record.",
    "2 · Modelo": "2 · Model",
    "Una regresión, como la logística": "One statistical formula",
    "Cada señal suma un coeficiente y la fórmula convierte la suma en un riesgo mensual entre 0 y 1.":
        "Each signal adds to a score. A formula turns the total into a monthly probability from 0 to 1.",
    "3 · Riesgo mensual": "3 · Monthly risk",
    "Cambia con el calendario": "Risk changes through the year",
    "El mismo grupo tiene un riesgo distinto en mayo que en octubre: el mes del año es una señal.":
        "The same group can have different risk in May and October. Month of year is one signal.",
    "4 · Riesgo a 6 meses": "4 · Risk over 6 months",
    "Se acumula mes a mes": "Monthly risks combine",
    "Se encadenan los 6 riesgos mensuales; la misma fórmula da el riesgo a 3 o 12 meses sin reentrenar.":
        "Combine the 6 monthly risks. The same formula covers 3 or 12 months without rebuilding the model.",
    "Las señales": "The signals",
    "Nivel": "Level",
    "7 grupos, de Associate a VP, y «otros»": "7 groups, Associate to VP, plus “other”",
    "Level grouped": "Level grouped",
    "8 grupos": "8 groups",
    "8 grupos, incluidos «otros» (Misc)": "8 groups, including “other” (Misc)",
    "Antigüedad en la empresa": "Time at the company",
    "cortes del playbook: <1, 1-2, 2-3, 3-5, 5-10, 10+ años":
        "playbook bands: <1, 1–2, 2–3, 3–5, 5–10, 10+ years",
    "Mes del año": "Month of year",
    "la temporada de salidas": "seasonal patterns in exits",
    "Cambios de manager": "Manager changes",
    "en los últimos 12 meses: 0, 1, 2+": "over the last 12 months: 0, 1, 2+",
    "Salidas del equipo": "Team exits",
    "renuncias en 12 meses en el equipo del manager actual: 0, 1, 2+":
        "voluntary exits in the current manager’s team over 12 months: 0, 1, 2+",
    "Reportes directos": "Direct reports",
    "personas a cargo: 0, 1 a 5, 6+": "people managed: 0, 1–5, 6+",
    "Desde la última promoción": "Time since last promotion",
    "<1, 1-2, 2-3, 3+ años, o sin promoción": "<1, 1–2, 2–3, 3+ years, or no promotion",
    "Recontratación": "Rehire",
    "si ya había trabajado antes en la empresa": "previously worked at the company",
    "Nivel × antigüedad": "Level × time at company",
    "Level grouped × antigüedad": "Level grouped × time at company",
    "la antigüedad pesa distinto en cada nivel": "time at the company matters differently by level",
    "Antigüedad × cambios de manager": "Time at company × manager changes",
    "cambiar de manager pesa distinto según la antigüedad":
        "manager changes matter differently by time at the company",
    "Nuevo frente a la versión anterior: cortes del playbook, promoción y recontratación; ganó en las 4 pruebas.":
        "New: playbook bands, promotion and rehire. Improved results in all 4 tests.",
    "Fuente: análisis de Engineering del 1 al 3-oct-2026. Sin segmento, job family ni atributos protegidos como señal.":
        "Source: Engineering analysis, Oct 1–3, 2026. Segment, job family and protected traits are excluded.",

    # Ejemplos ficticios y gráfico interactivo.
    "El modelo estima el riesgo mes a mes, lo acumula a 6 meses y lo resume por grupo":
        "From monthly risk to a 6-month view for each group",
    "Tablas: foto del 25-ene-2026, riesgo de febrero a julio con el modelo entrenado hasta jul-2025 · plano: foto del 26-jul-2026 · Engineering":
        "Tables: Jan 25, 2026 snapshot; Feb–Jul risk; trained through Jul 2025 · Chart: Jul 26, 2026 snapshot · Engineering",
    "Paso 1": "Step 1",
    "Riesgo de cada persona, mes a mes": "Monthly risk for each person",
    "· empleados ficticios": "· fictional examples",
    "Riesgo mensual de 6 empleados ficticios": "Monthly risk for 6 fictional employees",
    "Persona y grupo": "Person and group",
    "Abr": "Apr",
    "R₆ feb–jul": "R₆ Feb–Jul",
    "3-5 años · nivel 8 · 2+ salidas en su equipo, 1 cambio de manager, sin reportes, sin promoción registrada":
        "3–5 years · level 8 · 2+ team exits, 1 manager change, no direct reports, no recorded promotion",
    "3-5 años · nivel 8 · 2+ salidas en su equipo": "3–5 years · level 8 · 2+ team exits",
    "3-5 años · nivel 7 · 1 salida en su equipo, sin cambio de manager, sin reportes, promoción hace 1-2 años":
        "3–5 years · level 7 · 1 team exit, no manager change, no direct reports, promoted 1–2 years ago",
    "3-5 años · nivel 7 · 1 salida en su equipo": "3–5 years · level 7 · 1 team exit",
    "5-10 años · nivel 7 · sin salidas en su equipo, 1 cambio de manager, sin reportes, promoción hace 3+ años":
        "5–10 years · level 7 · no team exits, 1 manager change, no direct reports, promoted 3+ years ago",
    "5-10 años · nivel 7 · sin salidas en su equipo": "5–10 years · level 7 · no team exits",
    "5-10 años · nivel 8 · sin salidas en su equipo, sin cambio de manager, sin reportes, promoción hace 2-3 años, recontratado":
        "5–10 years · level 8 · no team exits, no manager change, no direct reports, promoted 2–3 years ago, rehired",
    "5-10 años · nivel 8 · sin salidas en su equipo": "5–10 years · level 8 · no team exits",
    "10+ años · nivel 6 · sin salidas en su equipo, sin cambio de manager, 1-5 reportes, promoción hace 3+ años":
        "10+ years · level 6 · no team exits, no manager change, 1–5 direct reports, promoted 3+ years ago",
    "10+ años · nivel 6 · sin salidas en su equipo": "10+ years · level 6 · no team exits",
    "10+ años · nivel 5 · sin salidas en su equipo, sin cambio de manager, 6+ reportes, promoción hace <1 año":
        "10+ years · level 5 · no team exits, no manager change, 6+ direct reports, promoted <1 year ago",
    "10+ años · nivel 5 · sin salidas en su equipo": "10+ years · level 5 · no team exits",
    "Paso 2": "Step 2",
    "Riesgo del grupo: promedio de sus personas, mes a mes": "Monthly average risk for each group",
    "Riesgo mensual promedio por grupo": "Average monthly risk by group",
    "Grupo": "Group",
    "3-5 años · con salidas · niveles 7–8": "3–5 yrs · team exits · levels 7–8",
    "5-10 años · sin salidas · niveles 7–8": "5–10 yrs · no exits · levels 7–8",
    "10+ años · sin salidas · niveles 5–6": "10+ yrs · no exits · levels 5–6",
    "Real": "Actual",
    "Todo Engineering": "All Engineering",
    "Grupo I: el modelo estimó que de cada 100 se irían 7.2 entre febrero y julio; se fueron 5.5 (el exceso de los niveles 7–8, diapositiva 8).":
        "Group I: 7.2 exits estimated per 100 people, Feb–Jul; 5.5 actually left. Levels 7–8 are overestimated (slide 8).",
    "Paso 3": "Step 3",
    "Cómo se forman los grupos": "How we form the groups",
    "· cada punto = 100 personas": "· each dot = 100 people",
    "Cortes del plano": "Group the chart by",
    "Todos": "All",
    "+ Antigüedad": "+ Years here",
    "+ Salidas en el equipo": "+ Team exits",
    "+ Nivel": "+ Level",
    "▶ Ver los cortes": "▶ Play the steps",
    "Nube de puntos de Engineering que se separa en grupos por antigüedad, salidas en el equipo y nivel":
        "Engineering dots grouped by time at the company, team exits and level",
    "grupo": "group",
    "riesgo del grupo más alto": "highest group risk",
    "de lo que ordena el modelo persona por persona (árbol automático: 85%)":
        "of individual risk ranking kept (automatic grouping: 85%)",
    "Personas ficticias: nombres y señales inventados; su riesgo es el que da el modelo real a esas señales. R₆ del grupo con el promedio mensual; promediar el R₆ de cada persona da lo mismo. Real sólo con 30+ salidas. En el plano, los puntos de un grupo se juntan alrededor de su riesgo promedio: la posición no es el riesgo de una persona. Probamos 58 formas de agrupar; ésta conservó más. Fuente: análisis de Engineering del 1 al 3-oct-2026.":
        "Fictional names and profiles; risks come from the real model. Group R₆ combines monthly averages. Actual rates shown with 30+ exits. Dots sit around group averages, not individual risk. This grouping kept the most of the model’s ranking across 58 options. Source: Engineering analysis, Oct 1–3, 2026.",

    # Grupos prioritarios, resultados y próximos pasos.
    "Los 5 grupos de mayor riesgo reúnen al 19.3% de Engineering y concentraron el 31.3% de las salidas reales; 4 tienen renuncias recientes en su equipo":
        "The top 5 risk groups held 19.3% of people and 31.3% of actual exits",
    "% que se estima saldrá en 6 meses · foto del 26-jul-2026 · 37,221 personas · grupos por antigüedad, salidas en el equipo y nivel":
        "Estimated % leaving within 6 months · Jul 26, 2026 snapshot · 37,221 people · grouped by years here, team exits and level",
    "Antigüedad": "Years here",
    "Salidas en su equipo": "Team exits",
    "Riesgo estimado a 6 meses · línea: promedio 2.8%":
        "Estimated 6-month risk · line: average 2.8%",
    "Personas": "People",
    "Última prueba": "Latest test",
    "estimado · real": "estimated · actual",
    "Con salidas": "With exits",
    "Sin salidas": "No exits",
    "Se muestran los 5 grupos de mayor riesgo de 22; los otros 17 tienen menos riesgo. 4 de los 5 son de los niveles 7–8.":
        "Top 5 of 22 groups; the other 17 have lower risk. Four have recent team exits; 4 of 5 are levels 7–8.",
    "de las salidas reales de la última prueba, con el 19.3% de las personas; ordenando persona por persona habría sido 31.9%":
        "of actual exits in the latest test, with 19.3% of people; ranking individuals would capture 31.9%",
    "Qué niveles incluye cada bloque": "Levels in each band",
    "En naranja, estimado 1 punto o más arriba del real: el modelo exagera algo los niveles 7–8 (diapositiva 8).":
        "Orange: estimate is 1 percentage point or more above actual. The model overestimates levels 7–8 (slide 8).",
    "Elegimos esta forma de agrupar entre 58 opciones, incluido un árbol: conserva el 91% de lo que ordena el modelo en las 4 pruebas (el árbol, 85%). Salidas en el equipo = 1 o más renuncias en 12 meses en el equipo del manager actual (con 2 o más, el riesgo mensual sube +86%). Cada persona cae en un solo grupo; grupos de 300+ personas y 30+ salidas en la última prueba. Fuente: análisis de Engineering del 1 al 3-oct-2026.":
        "Chosen from 58 options: keeps 91% of the model’s risk ranking across 4 tests (automatic grouping: 85%). Team exits = 1+ resignations in the current manager’s team over 12 months; 2+ are linked to +86% monthly risk. One group per person; 300+ people and 30+ exits in the latest test. Source: Engineering analysis, Oct 1–3, 2026.",
    "Qué tan bueno es: los que marca con más riesgo se van 4 veces más que los de menor riesgo, y estima un poco más salidas de las que hubo":
        "The highest-risk group had 4 times the exits of the lowest; estimates ran slightly high",
    "4 pruebas con datos que el modelo no vio, de feb-2024 a ene-2026 · de cada 100 personas, cuántas se fueron en 6 meses · Engineering":
        "4 tests on unseen data, Feb 2024–Jan 2026 · exits per 100 people over 6 months · Engineering",
    "Se fueron (real)": "Actual exits",
    "Estimado por el modelo": "Model estimate",
    "de cada 100 personas, en 6 meses": "per 100 people, over 6 months",
    "Menor riesgo": "Lowest risk",
    "2º": "2nd",
    "3º": "3rd",
    "4º": "4th",
    "Mayor riesgo": "Highest risk",
    "Personas ordenadas por el riesgo que estimó el modelo, en 5 grupos del mismo tamaño":
        "People ranked by estimated risk, in 5 equal-sized groups",
    "1 · Ordena bien": "1 · Finds higher-risk groups",
    "De cada 100 personas, en el grupo de menor riesgo se fue 1.3; en el de mayor riesgo, 5.5. El promedio de Engineering es 3.":
        "Per 100 people, 1.3 left in the lowest-risk group and 5.5 in the highest. Engineering’s average is 3.",
    "2 · Le atina a cuántos se van": "2 · Estimates are close, but high",
    "Estimó un poco de más en todos los grupos: entre 4% y 11% más salidas en total. La mayor diferencia está en el grupo de mayor riesgo; es la primera corrección pendiente.":
        "Estimates ran high in every group: 4% to 11% above total exits. The highest-risk group has the largest gap and is our first fix.",
    "Aun en el grupo de mayor riesgo, 95 de cada 100 se quedan: el modelo sirve para elegir grupos donde actuar, no personas.":
        "Even in the highest-risk group, 95 of 100 stay. Use the model to choose groups for support, not individuals.",
    "Cada grupo tiene 30+ salidas en cada prueba; en cada una, el modelo se entrenó sólo con la historia anterior. Fuente: análisis de Engineering del 1 al 3-oct-2026.":
        "Each group has 30+ exits in every test. Each model used only earlier data. Source: Engineering analysis, Oct 1–3, 2026.",
    "Próximos pasos: en las siguientes 2 semanas": "Next steps: the next 2 weeks",
    "Mejorar, corregir o cambiar el modelo antes de usarlo":
        "Improve, fix or replace the model before use",
    "Revisar otros modelos": "Test the remaining model",
    "Random survival forest, la única familia de modelos que falta probar":
        "Random survival forest is the only model family still untested",
    "Validar otras variables": "Check more signals",
    "como QVoice (intención de quedarse) y tiempo en el nivel":
        "QVoice (intent to stay) and time at current level",
    "Corregir y validar": "Fix and validate",
    "bajar el exceso estimado en el grupo de mayor riesgo y revisar que trate igual a todos los grupos":
        "Reduce overestimates in the highest-risk group and check fairness across groups",
    "Elegir la versión final": "Choose the final version",
    "con las mismas 4 pruebas; lo nuevo entra sólo si mejora al modelo actual":
        "Use the same 4 tests; adopt changes only if they improve today’s model",
    "Después, con el modelo final: piloto en 1 o 2 grupos y actualización periódica.":
        "Then pilot the final model in 1 or 2 groups and update it regularly.",

    # Navegación y temas; los identificadores internos se conservan.
    "Diapositivas": "Slides",
    "Navegación": "Navigation",
    "1. Recomendación": "1. Recommendation",
    "2. Agenda": "2. Agenda",
    "3. Cómo nos documentamos": "3. Research",
    "4. De 10 familias de modelos a una": "4. Choosing a model",
    "5. El modelo elegido": "5. The chosen model",
    "6. Cómo calcula el riesgo": "6. How it works",
    "7. Grupos de mayor riesgo": "7. Highest-risk groups",
    "8. Qué tan bueno es": "8. Test results",
    "9. Próximos pasos": "9. Next steps",
    "Tema": "Theme",
    "Claro – Clásico": "Light – Classic",
    "Claro – Azul suave": "Light – Soft Blue",
    "Oscuro – Real": "Dark – Royal",
    "Oscuro – Carbón": "Dark – Carbon",
}

UNCHANGED = {
    "3.1% vs 3%", "3.3% vs 3.4%", "Random survival forest", "Engineering", "Feb", "Mar", "May", "Jun", "Jul",
    "Fernando", "Julia", "Leah", "Ana", "Carlos", "Sofía", "I", "II", "III",
    "8 - Assoc & Int/Eng", "7 - Senior & Lead", "6 - Staff & /Mgr", "5 - Sr Staff & /Mgr",
    "3 - Princ/Directors", "2 - Sr Dir", "1 - VP & Above",
    "h = 1 − exp(−exp(α + Σ βx))", "R₆ = 1 − (1−h₁)(1−h₂)…(1−h₆)",
    "Julia: R₆ = 1 − (1−0.8%)(1−1.4%)(1−0.9%)(1−0.7%)(1−1.7%)(1−1%) ≈ 6.3%",
}


def group_label(value: str) -> str:
    """Sólo etiquetas de presentación; nunca cambia las claves de los agregados."""
    return (value.replace("años", "years").replace("año", "year")
            .replace("con salidas", "with team exits").replace("sin salidas", "no team exits")
            .replace("niveles", "levels").replace("Niveles", "Levels").replace("resto", "other groups"))


def english_text(value: str) -> str:
    key = " ".join(value.split())
    if key in TEXT:
        return TEXT[key]
    if key in UNCHANGED or re.fullmatch(r"C[1-9]", key) or not re.search(r"[A-Za-zÀ-ÿ]", key):
        return key
    if match := re.fullmatch(r"Desviación media del total real de salidas: ([\d.]+%)", key):
        return f"Average error vs. actual exits: {match[1]}"
    if match := re.fullmatch(r"([\d,]+) personas en la foto", key):
        return f"{match[1]} people at snapshot"
    if re.fullmatch(r"(?:[\d+<–-]+ años?(?: · (?:con|sin) salidas · niveles [\d–-]+)?|Niveles [\d–-]+)", key):
        return group_label(key)
    raise ValueError(f"Texto pendiente de traducción: {key!r}")


JS_TEXT = {
    "'Riesgo estimado a 6 meses del grupo'": "'Estimated 6-month group risk'",
    "'promedio '": "'average '",
    ".text(function (t) { return t; })": ".text(function (t) { return data.names[t] || t; })",
    "'Toda Engineering junta, en el riesgo promedio.'": "'All Engineering at its average risk.'",
    "'Primer corte: antigüedad. Cada franja es un tramo y se mueve a su riesgo.'":
        "'First split: years at the company. Each band moves to its average risk.'",
    "'<i></i>con salidas en su equipo<i class=\"ctx\"></i>sin salidas: cada franja se parte en dos.'":
        "'<i></i>with team exits<i class=\"ctx\"></i>no team exits: each band splits in two.'",
    "'<i></i>5 grupos de mayor riesgo<i class=\"ctx\"></i>otros grupos · tenues: grupos de menos de 300 personas (resto)'":
        "'<i></i>5 highest-risk groups<i class=\"ctx\"></i>other groups · faint: groups under 300 people'",
    "'Resto: grupos de menos de 300 personas · '": "'Other: groups under 300 people · '",
    "' personas'": "' people'",
    "'grupo' : 'grupos'": "'group' : 'groups'",
}


class EnglishDeck(HTMLParser):
    """Reemplaza texto por posición; preserva estilos, geometría, datos y lógica."""

    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.offsets = [0]
        for line in source.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.edits: list[tuple[int, int, str]] = []
        self.special: str | None = None
        self.script_id: str | None = None
        self.slides = 0
        self.data_blocks = 0
        self.chart_blocks = 0

    def source_position(self) -> int:
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in ("style", "script"):
            self.special = tag
            self.script_id = attributes.get("id")
        if "slide-stage" in (attributes.get("class") or "").split():
            self.slides += 1
        raw = self.get_starttag_text()
        result = raw
        if tag == "html":
            result = re.sub(r'\blang="es"', 'lang="en"', result, count=1)
        for attribute in ("title", "aria-label", "alt"):
            if attributes.get(attribute):
                translated = html.escape(english_text(attributes[attribute]), quote=True)
                pattern = r"\b" + re.escape(attribute) + r"=(['\"])(.*?)\1"
                result = re.sub(pattern, lambda _: f'{attribute}="{translated}"', result, count=1, flags=re.DOTALL)
        if result != raw:
            self.edits.append((self.source_position(), self.source_position() + len(raw), result))

    def handle_endtag(self, tag: str) -> None:
        if tag in ("style", "script"):
            self.special = None
            self.script_id = None

    def handle_data(self, data: str) -> None:
        if self.special == "style":
            return
        if self.special == "script":
            if self.script_id == "wt-data":
                payload = json.loads(data)
                payload["names"] = {key: group_label(value) for key, value in payload["names"].items()}
                translated = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
                self.edits.append((self.source_position(), self.source_position() + len(data), translated))
                self.data_blocks += 1
            elif "document.getElementById('wt-data')" in data:
                translated = data
                for old, new in JS_TEXT.items():
                    if old not in translated:
                        raise ValueError(f"Cambió el gráfico; falta el texto {old!r}")
                    translated = translated.replace(old, new)
                self.edits.append((self.source_position(), self.source_position() + len(data), translated))
                self.chart_blocks += 1
            return
        if not data.strip():
            return
        start = self.source_position()
        end = self.source.find("<", start)
        if end < 0:
            end = len(self.source)
        raw = self.source[start:end]
        prefix = re.match(r"\s*", raw)[0]
        suffix = re.search(r"\s*$", raw)[0]
        translated = prefix + html.escape(english_text(data), quote=False) + suffix
        if translated != raw:
            self.edits.append((start, end, translated))


def translate(source: str, *, january_cover_preview: bool = False) -> str:
    parser = EnglishDeck(source)
    parser.feed(source)
    parser.close()
    expected = (1, 0, 0) if january_cover_preview else (9, 1, 1)
    if (parser.slides, parser.data_blocks, parser.chart_blocks) != expected:
        raise ValueError(f"Estructura inesperada: se esperaban {expected} (diapositivas, datos, gráficos).")
    if january_cover_preview and "<title>Propuesta de portada: enero a julio de 2026</title>" not in source:
        raise ValueError("Se esperaba la propuesta de portada de enero a julio de 2026.")
    result = source
    previous = len(source)
    for start, end, replacement in sorted(parser.edits, reverse=True):
        if end > previous:
            raise ValueError("Reemplazos superpuestos; se cancela la traducción.")
        result = result[:start] + replacement + result[end:]
        previous = start
    if '<html lang="en">' not in result:
        raise ValueError("No se pudo declarar el idioma inglés.")
    return result
