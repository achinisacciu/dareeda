#!/bin/bash
set -e
DATE=$(date +%Y-%m-%d_%H-%M)
REPORT=".qa/lint/reports/${DATE}_lint.md"

echo "# Lint Report\n**Data:** ${DATE}\n**Stack:** Python + TypeScript\n" > "$REPORT"

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "## Python (ruff)\n" >> "$REPORT"
PYTHON_SRC="backend"

if command -v ruff >/dev/null 2>&1; then
    ruff check "$PYTHON_SRC" --output-format=github >> "$REPORT" 2>&1 || true
else
    echo "ruff non installato. Esegui: pip install ruff" >> "$REPORT"
fi

echo >> "$REPORT"
echo "## TypeScript (eslint)\n" >> "$REPORT"

if [ -f "frontend/package.json" ]; then
    cd frontend
    if command -v npx >/dev/null 2>&1; then
        npx eslint . --ext .ts,.tsx,.js --format markdown 2>> "../../$REPORT" || true
    else
        echo "npx non disponibile. Installa Node.js." >> "../../$REPORT"
    fi
fi

echo "\n---\n*Report generato dal QA Framework*" >> "$REPORT"
cat "$REPORT"
