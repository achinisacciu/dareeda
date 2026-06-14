#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M)
REPORT=".qa/security/reports/${DATE}_security.md"

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "# Security Audit Report\n**Data:** ${DATE}\n" > "$REPORT"
echo "## Python dependencies (pip-audit)\n" >> "$REPORT"

if command -v pip-audit >/dev/null 2>&1; then
    pip-audit --format=markdown >> "$REPORT" 2>&1 || true
else
    echo "pip-audit non installato. Installa con: pip install pip-audit" >> "$REPORT"
fi

echo "\n## Source code (bandit)\n" >> "$REPORT"
if command -v bandit >/dev/null 2>&1; then
    bandit -r backend/ -f markdown >> "$REPORT" 2>&1 || true
else
    echo "bandit non installato. Installa con: pip install bandit" >> "$REPORT"
fi

echo "\n## Node dependencies (npm audit)\n" >> "$REPORT"
if [ -f "frontend/package.json" ]; then
    cd frontend
    if command -v npm >/dev/null 2>&1; then
        npm audit --json 2>/dev/null | npx -y npm-audit-markdown --output "../../$REPORT" 2>/dev/null || true
    fi
fi

echo "\n---\n*Report generato dal QA Framework*" >> "$REPORT"
cat "$REPORT"
