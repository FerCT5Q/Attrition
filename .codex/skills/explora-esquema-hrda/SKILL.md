---
name: explora-esquema-hrda
description: Descubre tablas y columnas del esquema hrda de Redshift y busca datos con consultas agregadas y de solo lectura. Usalo cuando pidan revisar las tablas de HRDA, localizar donde existe un dato o analizarlo de forma agregada; no para devolver registros de empleados.
---

# Explora Esquema Hrda

Permite atender solicitudes como: `Revisa las tablas de HRDA y encuentra datos sobre X`. El alcance es el esquema completo `hrda`; no asumas que la informacion esta en `post_hire_monthly_worker_dtls` ni uses esa tabla como punto de partida salvo que el descubrimiento la identifique como candidata.

## Conexion

- Antes de acceder a Redshift, carga el skill local `attrition-redshift-db` y sigue sus reglas de privacidad y de consultas de solo lectura.
- Ejecuta las consultas mediante el helper protegido existente, con el entorno virtual del proyecto:

  ```powershell
  & .venv\Scripts\python.exe -B '.codex\skills\attrition-redshift-db\scripts\run_readonly_query.py' --sql "<SQL>" --max-rows 100
  ```

- El helper reutiliza las credenciales desde `C:\Dev\Python\Slides\.env`. Nunca copies, muestres ni guardes sus valores. El esquema objetivo es `hrda`.
- No uses conexión directa, sentencias de escritura ni `SELECT *`.

## Flujo

1. Interpreta el dato buscado y sus sinonimos. Si falta el dato concreto, pide esa precision antes de buscar contenido.
2. Descubre las tablas del esquema con `information_schema.tables`; despues, usa `information_schema.columns` para ubicar las candidatas por nombre de tabla o columna. Estas consultas de metadatos no dependen de una tabla principal.
3. Confirma el grain, las fechas disponibles y el significado del campo en la tabla candidata antes de extraer metricas. Los nombres de columnas son una hipotesis, no una definicion de negocio.
4. Para el resultado, devuelve solamente conteos, rangos de fechas, cobertura, distribuciones o tasas agregadas. No devuelvas filas de trabajadores ni valores de identidad, contacto, demografia protegida, compensacion exacta o texto libre. Manten cohortes compartidas de al menos 30.
5. Explica en espanol las tablas y columnas candidatas, la SQL ejecutada o su ruta, la ventana temporal, las metricas y las limitaciones. Distingue entre conteos de filas y personas distintas cuando aplique.

Cuando la peticion sea una evaluacion formal de disponibilidad, definicion, cobertura, missingness, consistencia, historia, joins o score de una variable, carga tambien `evaluate-attrition-variable` y conserva sus artefactos y validaciones requeridas.
