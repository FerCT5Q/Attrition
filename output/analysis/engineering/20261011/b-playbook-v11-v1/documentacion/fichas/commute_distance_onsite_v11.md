# Aproximación postal a oficinas de la ciudad (Onsite)

Primera foto con valor observable en esta carga: 2024-08-25. El soporte se comprueba por año y la elegibilidad se decide sólo con el entrenamiento de cada corte. Componentes registrados en la foto t; oficinas y centroides de catálogos estáticos usados retrospectivamente. No se acredita la dirección de oficina ni el mapping disponibles históricamente en t.

Modo `presentation` · variable `commute_distance_onsite_v11` · familia RH.
Empleados regulares activos de Engineering, excluyendo RF360, en cada foto mensual. Grain: persona-foto. Corte de conocimiento: 2026-09-07.

[Índice del diccionario](../diccionario.md) · [Decisiones completas](../decisiones.csv) · [Codificaciones de cada modelo](../codificaciones.csv)

## Tratamiento efectivo

| Elemento | Qué se hizo |
|---|---|
| Tipo | Distancia aproximada por bandas nominales |
| Campos de origen | country; city; office_site; postal_code (sólo componente efímero en RAM); work_arrangement; catálogos públicos |
| Valores de origen | Modalidad, ubicación laboral y componente postal; ningún domicilio, postal o distancia individual se persiste. |
| Valores antes de agrupar categorías raras | 0–<1 km; 1–<2 km; 2–<3 km; 3–<4 km; 4–<5 km; 5–<6 km; 6–<7 km; 7–<8 km; 8–<9 km; 9–<10 km; 10–<11 km; 11–<12 km; 12–<13 km; 13–<14 km; 14–<15 km; 15–<16 km; 16–<17 km; 17–<18 km; 18–<19 km; 19–<20 km; 20–<21 km; 21–<22 km; 22–<23 km; 23–<24 km; 24–<25 km; 25–<26 km; 26–<27 km; 27–<28 km; 28–<29 km; 29–<30 km; 30+ km; (unknown); (not onsite); (unmapped office); (unmapped postal centroid) |
| Transformación | Sólo Onsite. UPPER/TRIM de componentes; versión postal compacta elimina caracteres fuera de A–Z/0–9. Resuelve oficinas compatibles con ciudad y país laboral; excluye DAL.B. Busca centroide postal por coincidencia exacta/compacta y prefijos o relleno con ceros específicos del país. Orden adicional: US prefijo 5; CA/IE prefijo 3; GB prefijos 4/3/2; NL prefijo 4. Rellena a 6 en CN/IN/SG, a 5 en DE/FR/KR y a 7 en JP. Haversine entre centroide y oficinas; conserva mínimo si hay varias. Reconcilia por producto punto. Cortes de 1 km hasta 30, después 30+. |
| Faltantes y valores por defecto | Otra modalidad válida → (not onsite). Componentes incompletos/ambiguos → (unknown). Oficina o centroide sin mapping tienen estados distintos; no se imputa distancia cero. |
| Codificación para el modelo | Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas. |
| Categorías raras | Sólo incorporaciones RH: conserva categorías con al menos 300 personas distintas en todo el entrenamiento; el resto, incluidas categorías nuevas o desconocidos infrecuentes, se transforma en (other). B y QVoice no usan este pooling. Una persona puede contar en más de una categoría si cambió durante el entrenamiento; no es un mínimo por foto. |
| Consideraciones | Aproximación postal a oficinas de ciudad, no trayecto de commute validado. Todo el mapping observado resolvió por ciudad; no hay país domiciliario estructurado. Catálogo estático 2026, sin historia de direcciones; el mínimo entre oficinas puede subestimar la distancia. Los valores >500 km permanecen en 30+ y se reportan en el audit agregado. |
| Uso en la definición de grupos | Puede modificar la predicción, pero no añade una dimensión de grupo en esta ronda. Los grupos siguen definidos por antigüedad, salidas del equipo y nivel. |

## Comprobación y decisión

**Pregunta:** ¿Qué aporta esta representación al añadirla a la base, con datos conocidos antes de cada corte?

**Motivo:** separar una transformación de datos de su elegibilidad y de su mejora predictiva; dejar verificable por qué se conservó o quedó fuera.

**Método:** inspección del SQL/código congelado, soporte agregado de la carga, registro de selección interna y codificaciones guardadas. La documentación no reconstruye filas ni cambia decisiones a partir de resultados externos.

**Regla de aceptación:** Ajuste válido y elegibilidad; Brier no empeora; PR-AUC ≥99% del control. En validación de seis meses, además: lift al 10% ≥99% del control, MAE de los mismos grupos ≤control+0.1 pp y captura ≥control−0.5 pp. Entre las opciones que cumplen se minimiza log-loss y se aplica parsimonia dentro de una tolerancia relativa exacta de 0.0005. Se escoge la opción con menos incorporaciones dentro de esa ventana; después log-loss e identificador.

La elegibilidad requiere al menos seis fotos observables dentro del entrenamiento de selección y más de una categoría después de agrupar las poco frecuentes. Ese entrenamiento termina antes de la reserva interna; puede ser más corto que el reajuste utilizado para evaluar el periodo externo.

### Métricas observadas de soporte

Son conteos de la representación ya transformada. «Observable» sigue los estados explícitos de ausencia del runner; no prueba por sí solo la definición oficial ni la completitud de eventos. Personas repetidas entre fotos no son personas distintas.

| Año | Persona-fotos | Observables | Cobertura (%) | Fotos observables | Categorías observables |
|---|---|---|---|---|---|
| 2020 | 142933 | 0 | 0 | 0 | 0 |
| 2021 | 307054 | 0 | 0 | 0 | 0 |
| 2022 | 347636 | 0 | 0 | 0 | 0 |
| 2023 | 369603 | 0 | 0 | 0 | 0 |
| 2024 | 363189 | 130182 | 35.8 | 5 | 31 |
| 2025 | 390263 | 322179 | 82.6 | 12 | 31 |
| 2026 | 288586 | 229116 | 79.4 | 8 | 31 |

### Selección en cada corte

| Periodo | Base | Fotos internas observables | Cumple condiciones individual | Lista de seis | Decisión |
|---|---|---|---|---|---|
| aug_dec_2025 | B | 3 | No | No | No seleccionada |
| aug_jan_2024 | B | 0 | No | No | No seleccionada |
| feb_jul_2024 | B | 0 | No | No | No seleccionada |
| feb_jul_2025 | B | 0 | No | No | No seleccionada |
| final | B | 16 | Sí | Sí | Seleccionada |
| jan_feb_2026 | B | 8 | No | No | No seleccionada |

- **aug_dec_2025 / B:** No seleccionada. Sólo 3 fotos observables de entrenamiento; se requieren seis. No entró en las seis primeras para pares y tríos.
- **aug_jan_2024 / B:** No seleccionada. Sólo 0 fotos observables de entrenamiento; se requieren seis. Sólo una categoría después de codificar; no hay contraste aprendible. No entró en las seis primeras para pares y tríos.
- **feb_jul_2024 / B:** No seleccionada. Sólo 0 fotos observables de entrenamiento; se requieren seis. Sólo una categoría después de codificar; no hay contraste aprendible. No entró en las seis primeras para pares y tríos.
- **feb_jul_2025 / B:** No seleccionada. Sólo 0 fotos observables de entrenamiento; se requieren seis. Sólo una categoría después de codificar; no hay contraste aprendible. No entró en las seis primeras para pares y tríos.
- **final / B:** Seleccionada en combinación con Familia de puesto detallada, Ciudad laboral. Prueba individual: La incorporación individual cumple las condiciones de validación.
- **jan_feb_2026 / B:** No seleccionada. No supera: PR-AUC conserva al menos el 99%, Lift al 10% conserva al menos el 99%. No entró en las seis primeras para pares y tríos.

### Resultado externo de añadirla por separado

Cambios respecto a la misma base y población de cada periodo; valores positivos indican mejora de pérdidas o mayor captura. Estas cifras describen el resultado externo y no se emplean para seleccionar.

| Periodo | Base | Mejora log-loss (%) | Mejora Brier (%) | Cambio captura (pp) |
|---|---|---|---|---|
| aug_dec_2025 | B | 0.4 | 0.1 | -0.1 |
| jan_feb_2026 | B | 0.5 | 0.1 | 0 |

Se omiten de la tabla externa los ajustes con historia insuficiente: aug_jan_2024, feb_jul_2024, feb_jul_2025. Sus intentos y soporte siguen en decisiones.json; un ajuste numérico no equivale a una prueba temporal admisible.

**Frecuencia en selecciones anteriores:** B: seleccionada en 0 de 5 cortes.

**Conclusión de selección final:** Sobre B: Seleccionada. Seleccionada en combinación con Familia de puesto detallada, Ciudad laboral.

**Impacto en score de assessment:** ninguno. Los scores previos no se reasignan con estas pruebas.

**Acción:** Conservar como candidata experimental y confirmar en datos posteriores; no sustituye automáticamente el modelo vigente.

## Codificación de los modelos finales

| Modelo | Referencia omitida | Número de indicadores | Niveles aprendidos |
|---|---|---|---|
| final-B-RH | (unknown) | 26 | (not onsite); (other); (unknown); (unmapped office); (unmapped postal centroid); 0–<1 km; 10–<11 km; 11–<12 km; 12–<13 km; 15–<16 km; 16–<17 km; 17–<18 km; 18–<19 km; 19–<20 km; 1–<2 km; 21–<22 km; 23–<24 km; 29–<30 km; 2–<3 km; 30+ km; 3–<4 km; 4–<5 km; 5–<6 km; 6–<7 km; 7–<8 km; 8–<9 km; 9–<10 km |
| final-B_RH-Q | (unknown) | 26 | (not onsite); (other); (unknown); (unmapped office); (unmapped postal centroid); 0–<1 km; 10–<11 km; 11–<12 km; 12–<13 km; 15–<16 km; 16–<17 km; 17–<18 km; 18–<19 km; 19–<20 km; 1–<2 km; 21–<22 km; 23–<24 km; 29–<30 km; 2–<3 km; 30+ km; 3–<4 km; 4–<5 km; 5–<6 km; 6–<7 km; 7–<8 km; 8–<9 km; 9–<10 km |

## Fuentes trazables

- [engineering_b_v11_commute_inputs_20261011.sql](<../../../../../../../queries/profiles/engineering_b_v11_commute_inputs_20261011.sql>)
- [b_v11_commute.py](<../../../../../../../tools/b_v11_commute.py>)
- [build_global_commute_distance_evidence.py](<../../../../../../../tools/build_global_commute_distance_evidence.py>)
- [v11-commute-inputs.json](<../../input-evidence/v11-commute-inputs.json>) · 2026-10-12T14:52:10.808517+00:00 · resultado del control: pass · SQL: [engineering_b_v11_commute_inputs_20261011.sql](<../../../../../../../queries/audits/engineering_b_v11_commute_inputs_20261011.sql>)
- [v11-commute-mapping.json](<../../input-evidence/v11-commute-mapping.json>) · 2026-10-12T15:04:33.336809+00:00 · resultado del control: pass_for_city_proxy_only · SQL: [engineering_b_v11_commute_inputs_20261011.sql](<../../../../../../../queries/profiles/engineering_b_v11_commute_inputs_20261011.sql>)
- [model-v11-commute-transform.json](<../../input-evidence/model-v11-commute-transform.json>) · registro de carga de esta ejecución · resultado del control: pass
- [hr-feature-support.json](<../../input-evidence/hr-feature-support.json>) · registro de carga de esta ejecución

La fecha de la consulta no reemplaza la fecha de conocimiento de la variable. Un control técnico pass sólo respalda la afirmación acotada de su contrato.
