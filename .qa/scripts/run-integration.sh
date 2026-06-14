#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M)
REPORT=".qa/integration/reports/${DATE}_integration.md"

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "# Integration Test Report\n**Data:** ${DATE}\n" > "$REPORT"

if command -v pytest >/dev/null 2>&1; then
    if [ -d "backend/tests" ]; then
        pytest backend/tests -v -m integration 2>&1 | tee -a "$REPORT" || true
    else
        echo "Nessun test di integrazione trovato." >> "$REPORT"
    fi
else
    echo "pytest non installato." >> "$REPORT"
fi

echo "\n---\n*Report generato dal QA Framework*" >> "$REPORT"
cat "$REPORT"
