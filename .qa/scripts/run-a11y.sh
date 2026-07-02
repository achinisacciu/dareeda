#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M)
REPORT=".qa/a11y/reports/${DATE}_a11y.md"

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "# A11y Report\n**Data:** ${DATE}\n" > "$REPORT"
echo "Standard: WCAG 2.1 AA\n" >> "$REPORT"

if command -v pa11y >/dev/null 2>&1; then
    PORT=5173
    npx --yes vite preview --port "$PORT" --host 0.0.0.0 &
    VITE_PID=$!
    sleep 3
    npx --yes pa11y "http://localhost:${PORT}" --standard WCAG2AA --reporter markdown >> "$REPORT" 2>/dev/null || true
    kill "$VITE_PID" 2>/dev/null || true
else
    echo "pa11y non installato." >> "$REPORT"
fi

echo "\n---\n*Report generato dal QA Framework*" >> "$REPORT"
cat "$REPORT"
