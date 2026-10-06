Operaciones Git del proyecto. Uso: `/git <subcomando> [argumentos]`

> **`save` siempre ejecuta `/document` antes de commitear** — nunca omitir este paso.

## Configuración del proyecto

- **Rama activa**: `claude` — nunca tocar `main`/`master` salvo que se pida explícitamente
- **Cuenta remota**: `FerCT5Q/Slides` en GitHub
- **Antes de push**: verificar cuenta con `gh auth switch --user FerCT5Q`

---

## Subcomandos

### `save [descripción]`

Commit de todos los cambios actuales sin push. Siempre actualiza la documentación primero.

1. Ejecutar el skill `/document` — actualiza `docs/` con los cambios pendientes
2. `git status` — mostrar qué se va a commitear (incluye los docs recién actualizados)
3. `git add -A`
4. `git commit -m "checkpoint: <descripción>"` — si no hay descripción, generarla automáticamente basada en los archivos modificados

---

### `push [descripción]`

Commit (si hay cambios pendientes) + push a la cuenta configurada.

1. `git status` — verificar estado
2. Si hay cambios sin commitear: `git add -A` + `git commit -m "checkpoint: <descripción>"`
3. `gh auth switch --user FerCT5Q`
4. `git push origin claude`

---

### `check`

Estado actual del repositorio.

1. `git branch` — rama activa
2. `git log -1 --oneline` — último commit
3. `git status` — cambios pendientes (staged, unstaged, sin trackear)
4. Mostrar resumen legible: rama, último commit, N archivos con cambios

---

### `sync`

Traer cambios del remoto para estar al día.

1. `gh auth switch --user FerCT5Q`
2. `git fetch origin`
3. `git pull origin claude`
4. Reportar si hubo cambios o ya estaba al día

---

Subcomando recibido: $ARGUMENTS
