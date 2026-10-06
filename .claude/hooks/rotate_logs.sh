#!/bin/bash
# PreToolUse hook — rota logs antes de python main.py
# Lee el input del tool desde stdin (JSON con campo "command")
INPUT=$(cat)

# Solo actuar si el comando es python main.py
if ! echo "$INPUT" | grep -q "python main.py"; then
    exit 0
fi

TODAY=$(date +%Y-%m-%d)
LOG_FILE="logs/tableau_scraper_${TODAY}.log"
OLD_LOGS=$(ls logs/tableau_scraper_*.log 2>/dev/null | grep -v "$TODAY")

# Respaldar logs de días anteriores
BACKUP_DIR="logs/backup"
if [ -n "$OLD_LOGS" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "$OLD_LOGS" | xargs -I{} mv {} "$BACKUP_DIR/"
    echo "[hook] Logs anteriores movidos a $BACKUP_DIR/"
fi

# Rotar log de hoy si ya existe (para que el nuevo run empiece limpio)
if [ -f "$LOG_FILE" ]; then
    mkdir -p "$BACKUP_DIR"
    TS=$(date +%H%M%S)
    mv "$LOG_FILE" "$BACKUP_DIR/tableau_scraper_${TODAY}_${TS}.log"
    echo "[hook] Log de hoy respaldado: tableau_scraper_${TODAY}_${TS}.log"
fi

exit 0
