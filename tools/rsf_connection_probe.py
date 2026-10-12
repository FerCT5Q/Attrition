"""Diagnostico minimo del cliente autorizado, sin datos ni credenciales en salida."""
import json
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.codex/skills/attrition-redshift-db/scripts'))
import run_readonly_query as db
start = time.perf_counter()
result = {}
try:
    conn = db.connect()
    conn.set_session(readonly=True,autocommit=True)
    with conn.cursor() as cursor:
        cursor.execute(db.validate_readonly('SELECT 1 AS connection_check'))
        result['outcome'] = 'pass' if cursor.fetchone()[0]==1 else 'fail'
    conn.close()
except db.psycopg2.Error as error:
    message = str(error).lower()
    result = {'outcome':'fail','error_type':type(error).__name__,'pgcode':error.pgcode,
              'categories':[key for key in ['timeout','timed out','ssl','server closed','refused','translate host',
                  'network','authentication','connection reset','eof','canceling statement'] if key in message]}
result['seconds'] = time.perf_counter()-start
print(json.dumps(result))
