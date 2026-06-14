#!/bin/bash
set -e
DATE=$(date +%Y-%m-%d_%H-%M)
echo "# QA Run - $DATE" > .qa/last-run-summary.md

echo "## 1. Lint" && bash .qa/scripts/run-lint.sh && echo "done" >> .qa/last-run-summary.md
echo "## 2. Unit + Coverage" && bash .qa/scripts/run-unit.sh && echo "done" >> .qa/last-run-summary.md
echo "## 3. Integration" && bash .qa/scripts/run-integration.sh && echo "done" >> .qa/last-run-summary.md
echo "## 4. Security" && bash .qa/scripts/run-security.sh && echo "done" >> .qa/last-run-summary.md
echo "## 5. E2E" && bash .qa/scripts/run-e2e.sh && echo "done" >> .qa/last-run-summary.md
echo "## 6. Performance" && bash .qa/scripts/run-performance.sh && echo "done" >> .qa/last-run-summary.md
echo "## 7. A11y" && bash .qa/scripts/run-a11y.sh && echo "done" >> .qa/last-run-summary.md

echo "QA completato. Report in .qa/last-run-summary.md"
