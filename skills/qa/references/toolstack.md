# Tool Stack — Riferimento Completo

Questo file contiene i tool esatti, i comandi di installazione, i comandi di esecuzione
e i flag consigliati per ogni categoria e linguaggio.

---

## LINT

### Python — ruff

**Perché ruff**: rimpiazza flake8 + isort + pyupgrade in un unico tool, 10-100x più veloce.

```bash
# Installazione
pip install ruff

# Config (generare in .qa/lint/configs/ruff.toml)
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "UP", "B", "SIM"]
exclude = ["migrations", "__pycache__", ".venv"]

# Esecuzione
ruff check . --output-format=github 2>&1 | tee .qa/lint/reports/YYYY-MM-DD_lint_python.md

# Fix automatico (proporre all'utente prima di applicare)
ruff check . --fix
```

### JavaScript / TypeScript — ESLint + Prettier

```bash
# Installazione
npm install --save-dev eslint prettier @typescript-eslint/parser @typescript-eslint/eslint-plugin eslint-config-prettier

# Config ESLint (generare in .qa/lint/configs/eslint.config.js)
import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';
export default [
  { files: ['**/*.ts', '**/*.tsx'],
    languageOptions: { parser: tsparser },
    plugins: { '@typescript-eslint': tseslint },
    rules: { ...tseslint.configs.recommended.rules } }
];

# Config Prettier (generare in .qa/lint/configs/.prettierrc)
{ "semi": true, "singleQuote": true, "tabWidth": 2, "printWidth": 100 }

# Esecuzione
npx eslint . --ext .ts,.tsx,.js --format markdown > .qa/lint/reports/YYYY-MM-DD_lint_ts.md
npx prettier --check . 2>&1 >> .qa/lint/reports/YYYY-MM-DD_lint_ts.md
```

### SQL — sqlfluff

```bash
# Installazione
pip install sqlfluff

# Config (generare in .qa/lint/configs/.sqlfluff)
[sqlfluff]
dialect = postgres
templater = jinja
max_line_length = 120

# Esecuzione
sqlfluff lint . --dialect postgres --format markdown > .qa/lint/reports/YYYY-MM-DD_lint_sql.md
```

---

## UNIT TEST

### Python — pytest

```bash
# Installazione
pip install pytest pytest-cov pytest-asyncio

# Esecuzione con coverage
pytest .qa/unit/tests/ \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=json:.qa/coverage/reports/coverage.json \
  --cov-fail-under=80 \
  -v 2>&1 | tee .qa/unit/reports/YYYY-MM-DD_unit.md

# Config (generare in pyproject.toml o pytest.ini)
[tool.pytest.ini_options]
testpaths = [".qa/unit/tests"]
asyncio_mode = "auto"
```

### JavaScript / TypeScript — Jest

```bash
# Installazione
npm install --save-dev jest ts-jest @types/jest

# Config (generare in .qa/unit/jest.config.ts)
export default {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/.qa/unit/tests/**/*.test.ts'],
  collectCoverageFrom: ['src/**/*.ts'],
  coverageThreshold: { global: { lines: 80 } },
  coverageReporters: ['json', 'text'],
  coverageDirectory: '.qa/coverage/reports'
};

# Esecuzione
npx jest --coverage --verbose 2>&1 | tee .qa/unit/reports/YYYY-MM-DD_unit.md
```

---

## INTEGRATION TEST

### Python — pytest + httpx

```bash
# Installazione
pip install pytest httpx pytest-asyncio

# Pattern: usare fixture per avviare l'app e httpx.AsyncClient
# Esempio struttura test:
# .qa/integration/tests/test_api_users.py

# Esecuzione
pytest .qa/integration/tests/ -v -m integration \
  2>&1 | tee .qa/integration/reports/YYYY-MM-DD_integration.md
```

### JavaScript / TypeScript — Jest + Supertest

```bash
# Installazione
npm install --save-dev supertest @types/supertest

# Esecuzione (config separata da unit)
npx jest --config .qa/integration/jest.integration.config.ts \
  2>&1 | tee .qa/integration/reports/YYYY-MM-DD_integration.md
```

---

## E2E TEST — Playwright

Playwright è usato sia per Python che per JS/TS (stesso tool, due binding).

### Python

```bash
# Installazione
pip install playwright pytest-playwright
playwright install chromium

# Esecuzione
pytest .qa/e2e/tests/ -v --headed=false \
  2>&1 | tee .qa/e2e/reports/YYYY-MM-DD_e2e.md
```

### JavaScript / TypeScript

```bash
# Installazione
npm install --save-dev @playwright/test
npx playwright install chromium

# Config (generare in .qa/e2e/playwright.config.ts)
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: '.qa/e2e/tests',
  reporter: [['markdown', { outputFile: '.qa/e2e/reports/YYYY-MM-DD_e2e.md' }]],
  use: { headless: true, baseURL: 'http://localhost:3000' }
});

# Esecuzione
npx playwright test
```

---

## SECURITY AUDIT

### Python — pip-audit + bandit

```bash
# Installazione
pip install pip-audit bandit

# Dipendenze vulnerabili
pip-audit --format=markdown > .qa/security/reports/YYYY-MM-DD_security.md

# Vulnerabilità nel codice sorgente
bandit -r src/ -f txt >> .qa/security/reports/YYYY-MM-DD_security.md
```

### JavaScript / TypeScript — npm audit + semgrep

```bash
# npm audit (built-in, nessuna installazione)
npm audit --json | npx npm-audit-markdown > .qa/security/reports/YYYY-MM-DD_security.md

# semgrep (analisi statica pattern)
pip install semgrep  # semgrep è un tool Python anche per JS
semgrep --config=p/javascript --config=p/typescript src/ \
  --output .qa/security/reports/YYYY-MM-DD_security_semgrep.md \
  --markdown
```

**Soglie di allerta (da rispettare sempre):**
- `CRITICAL` → bloccare, segnalare immediatamente
- `HIGH` → segnalare, non procedere se `fail_on_high: true` in config
- `MEDIUM` / `LOW` → loggare nel report, non bloccare

---

## PERFORMANCE / PROFILING

### Python — cProfile + py-spy

```bash
# cProfile (built-in, nessuna installazione per script)
python -m cProfile -o .qa/performance/reports/profile.pstats src/main.py
python -c "import pstats; p = pstats.Stats('.qa/performance/reports/profile.pstats'); p.sort_stats('cumulative'); p.print_stats(20)" \
  > .qa/performance/reports/YYYY-MM-DD_performance.md

# py-spy (profiling di processi già in esecuzione)
pip install py-spy
py-spy record -o .qa/performance/reports/flamegraph.svg -- python src/main.py
```

### JavaScript / TypeScript — clinic.js + autocannon

```bash
# Installazione
npm install --save-dev clinic autocannon

# Profiling server HTTP
npx clinic doctor -- node dist/server.js 2>&1 &
npx autocannon -c 100 -d 10 http://localhost:3000/api/health \
  > .qa/performance/reports/YYYY-MM-DD_performance.md
kill %1  # ferma il server

# Budget: confrontare con performance.budget_ms in qa.config.json
```

### SQL — EXPLAIN ANALYZE

```bash
# Script Python per eseguire EXPLAIN ANALYZE sulle query critiche
# L'agente scrive .qa/performance/scripts/sql_explain.py
# con le query da analizzare, poi esegue:
python .qa/performance/scripts/sql_explain.py \
  > .qa/performance/reports/YYYY-MM-DD_sql_performance.md
```

---

## ACCESSIBILITÀ (A11Y)

### JavaScript / TypeScript — axe-core + pa11y

```bash
# Installazione
npm install --save-dev @axe-core/playwright pa11y

# Con Playwright (integrato nei test E2E)
# L'agente aggiunge axe-core ai test Playwright esistenti

# pa11y per audit standalone
npx pa11y http://localhost:3000 --reporter markdown \
  > .qa/a11y/reports/YYYY-MM-DD_a11y.md

# Standard: WCAG 2.1 AA (default in qa.config.json)
npx pa11y http://localhost:3000 --standard WCAG2AA --reporter markdown \
  >> .qa/a11y/reports/YYYY-MM-DD_a11y.md
```

### Python — axe-playwright-python

```bash
pip install axe-playwright-python

# L'agente scrive .qa/a11y/scripts/axe_check.py
# che usa playwright + axe per ogni pagina da testare
python .qa/a11y/scripts/axe_check.py \
  > .qa/a11y/reports/YYYY-MM-DD_a11y.md
```

---

## Script orchestratore — run-all.sh

L'agente genera `.qa/scripts/run-all.sh`:

```bash
#!/bin/bash
set -e
DATE=$(date +%Y-%m-%d_%H-%M)
echo "# QA Run — $DATE" > .qa/last-run-summary.md

echo "## 1. Lint" && bash .qa/scripts/run-lint.sh && echo "✅ Lint" >> .qa/last-run-summary.md
echo "## 2. Unit + Coverage" && bash .qa/scripts/run-unit.sh && echo "✅ Unit" >> .qa/last-run-summary.md
echo "## 3. Integration" && bash .qa/scripts/run-integration.sh && echo "✅ Integration" >> .qa/last-run-summary.md
echo "## 4. Security" && bash .qa/scripts/run-security.sh && echo "✅ Security" >> .qa/last-run-summary.md
echo "## 5. E2E" && bash .qa/scripts/run-e2e.sh && echo "✅ E2E" >> .qa/last-run-summary.md
echo "## 6. Performance" && bash .qa/scripts/run-performance.sh && echo "✅ Performance" >> .qa/last-run-summary.md
echo "## 7. A11y" && bash .qa/scripts/run-a11y.sh && echo "✅ A11y" >> .qa/last-run-summary.md

echo "QA completato. Report in .qa/last-run-summary.md"
```