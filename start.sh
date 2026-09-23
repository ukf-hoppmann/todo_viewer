#!/bin/bash
# Kompatibilitäts-Alias: der Viewer läuft jetzt in Docker, siehe ./todo.sh
set -e
cd "$(dirname "$0")"
exec ./todo.sh start
