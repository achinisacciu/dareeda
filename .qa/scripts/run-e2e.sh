#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M)
REPORT=".qa/e2e/reports/${DATE}_e2e.md"

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "# E2E Test Report\n**Data:** ${DATE}\n" > "$REPORT"

if command -v playwright >/dev/null 2>&1; then
    if [ -d ".qa/e2e/tests" ]; then
        pytest .qa/e2e/tests -v --headed=false 2>&1 | tee -a "$REPORT" || true
    else
        echo "Nessun test E2E configurato." >> "$REPORT"
    fi
else
    echo "playwright non installato." >> "$REPORT"
fi

echo "\n---\n*Report generato dal QA Framework*" >> "$REPORT"
cat "$REPORT"
