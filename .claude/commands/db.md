---
description: Conecta a Redshift y ejecuta queries para validar hipótesis o explorar datos
---

# Skill: /db — Database Explorer

Ejecuta queries en Redshift para responder la pregunta del usuario: validar hipótesis, contar registros, explorar columnas, verificar datos.

**Pregunta o tarea:** `$ARGUMENTS`

---

## Conexión

**Base de datos:** Amazon Redshift  
**Credenciales:** en `.env` (root del proyecto)  
**Schema por defecto:** `hrda` (variable `REDSHIFT_SCHEMA`)  
**Tabla principal:** `hrda.post_hire_monthly_worker_dtls`

Para conectarse, usa `SqlService` del proyecto — ya carga las credenciales del `.env` automáticamente:

```python
import sys, os
sys.path.insert(0, r"C:\Dev\Python\Slides")
os.chdir(r"C:\Dev\Python\Slides")
from dotenv import load_dotenv
load_dotenv()

from src.data.sql_service import SqlService

with SqlService() as svc:
    rows = svc.query("SELECT ...")
    # o: df = svc.query_df("SELECT ...")
```

Ejecuta este código via Bash con `python -c "..."` o escribiendo un script temporal en `/tmp/db_check.py` y corriendo `python /tmp/db_check.py`.

---

## Procedimiento

1. **Entender la pregunta** — ¿qué quiere validar el usuario?
2. **Escribir la query** — usar `hrda.post_hire_monthly_worker_dtls` como tabla base salvo que el contexto indique otra
3. **Ejecutar** — conectar con `SqlService`, correr la query
4. **Responder** — reportar el resultado directamente, en español, de forma concisa

Si la query falla, inspeccionar el error y reintentar con ajustes. Si la conexión falla, revisar que `.env` existe y tiene las variables `REDSHIFT_*`.

---

## Schema conocido — tabla principal

`hrda.post_hire_monthly_worker_dtls`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `employee_id` | VARCHAR | ID único del empleado |
| `executive_name` | VARCHAR | Nombre del líder/ejecutivo |
| `job_level` | VARCHAR | Nivel: "Assoc/Int", "Sr/Lead", "Manager", "ET3", "ET4", etc. |
| `employee_type` | VARCHAR | "Regular", "Intern", "Temp" |
| `reg_non_intern_dir_reports` | INT | Reportes directos sin interns |
| `fis_mo_end_dt` | DATE | Fin de mes fiscal |

Si necesitas explorar el schema real (columnas exactas), correr:
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
ORDER BY ordinal_position;
```

---

## Patrones de query frecuentes

**Contar registros:**
```sql
SELECT COUNT(*) FROM hrda.post_hire_monthly_worker_dtls;
```

**Ver meses disponibles:**
```sql
SELECT DISTINCT fis_mo_end_dt ORDER BY 1 DESC LIMIT 12;
```

**Líderes únicos:**
```sql
SELECT DISTINCT executive_name FROM hrda.post_hire_monthly_worker_dtls ORDER BY 1;
```

**Distribución por nivel:**
```sql
SELECT job_level, COUNT(*) as n
FROM hrda.post_hire_monthly_worker_dtls
GROUP BY job_level ORDER BY n DESC;
```

**Datos de un líder específico:**
```sql
SELECT * FROM hrda.post_hire_monthly_worker_dtls
WHERE executive_name = 'Nombre Apellido'
  AND fis_mo_end_dt = (SELECT MAX(fis_mo_end_dt) FROM hrda.post_hire_monthly_worker_dtls)
LIMIT 20;
```

---

## Importante

- El usuario `hrda_tableau_ro` es **read-only** — solo SELECT, nunca INSERT/UPDATE/DELETE
- Si hay varias tablas candidatas y no estás seguro, primero lista las tablas del schema:
  ```sql
  SELECT table_name FROM information_schema.tables WHERE table_schema = 'hrda' ORDER BY 1;
  ```
- Para queries lentas o tablas grandes, usar `LIMIT` hasta confirmar que la query es correcta
