#!/bin/bash
# 天命鑑定書 生成スクリプト
# Usage: bash run.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
"$DIR/.venv/bin/python3" "$DIR/generate_reading.py"
