#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M)
REPORT=".qa/performance/reports/${DATE}_performance.md"

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "# Performance Report\n**Data:** ${DATE}\n" > "$REPORT"

echo "## Python (cProfile)\n" >> "$REPORT"
OUTPUT=".qa/performance/reports/profile.pstats"

if [ -f "backend/main.py" ]; then
    python -m cProfile -o "$OUTPUT" backend/main.py 2>&1 | tee "$REPORT" || true
    python -c "import pstats; p = pstats.Stats('$OUTPUT'); p.sort_stats('cumulative'); p.print_stats(20)" >> "$REPORT" 2>/dev/null || true
else
    echo "backend/main.py non trovato." >> "$REPORT"
fi

echo "\n---\n*Report generato dal QA Framework*" >> "$REPORT"
cat "$REPORT"
