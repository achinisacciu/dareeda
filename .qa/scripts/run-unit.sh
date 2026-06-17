#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M)
REPORT=".qa/unit/reports/${DATE}_unit.md"
COVERAGE_JSON=".qa/coverage/reports/coverage.json"

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "# Unit Test Report\n**Data:** ${DATE}\n" > "$REPORT"

PYTEST_CMD="pytest .qa/unit/tests -v --cov=backend --cov-report=json:$COVERAGE_JSON --cov-report=term-missing --cov-fail-under=75 2>&1 | tee .qa/last-run-raw.txt"

if command -v pytest >/dev/null 2>&1; then
    eval "$PYTEST_CMD" | tee .qa/unit/reports/tmp.txt || true
else
    echo "pytest non installato." >> "$REPORT"
    exit 1
fi

if [ -f ".qa/unit/reports/tmp.txt" ]; then
    cat .qa/unit/reports/tmp.txt >> "$REPORT" 2>/dev/null || true
    rm .qa/unit/reports/tmp.txt
fi

echo "\n---\n*Report generato dal QA Framework*" >> "$REPORT"
cat "$REPORT"
