#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/backend"
echo "Starting EASYConvert at http://127.0.0.1:8000"
uvicorn main:app --host 127.0.0.1 --port 8000
