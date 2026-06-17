# QA Framework — dareeda-platform

## Stato attuale

*Ultimo aggiornamento: 2026-06-15*

| Categoria | Stato | Ultimo report |
|-----------|-------|---------------|
| Lint | ✅ PASS | [2026-06-15](lint/reports/) |
| Unit Test | ✅ PASS (120/120) | [2026-06-15](unit/reports/) |
| Coverage | ⚠️ PASS (75% ≥ 75%) | [2026-06-15](coverage/reports/coverage.json) |
| Integration | N/A | — |
| E2E | N/A | — |
| Security | ⚠️ WARN | [2026-06-14](security/reports/2026-06-14_18-03_security.md) |
| Performance | N/A | — |
| A11y | N/A | — |

## Come eseguire

```bash
# Linux/macOS/Git Bash
bash .qa/scripts/run-all.sh

# Windows (PowerShell) — singole categorie
python -m pytest .qa/unit/tests -v --cov=backend --cov-report=term-missing --cov-report=json:.qa/coverage/reports/coverage.json
ruff check backend
cd frontend && npx eslint . --ext .ts,.tsx
pip-audit
```

> **Nota Windows:** gli script `.sh` richiedono line ending LF (configurato in `.gitattributes`).
> Su Windows senza bash, eseguire i comandi sopra manualmente o via Git Bash.

## Configurazione

Vedi `../../qa.config.json` nella root del progetto.

## Struttura

```
.qa/
├── unit/         ← test unitari
├── integration/  ← test di integrazione
├── e2e/          ← test end-to-end
├── lint/         ← configurazioni e report lint
├── security/     ← report audit sicurezza
├── performance/  ← script e report profiling
├── a11y/         ← script e report accessibilità
├── coverage/     ← report copertura codice
└── scripts/      ← script orchestratori
```

## Azioni completate

### Lint (RISOLTO)
- **Python:** E501 fixate in `data_quality.py`, `enterprise.py`, `insights.py`, `ml_exploratory.py`, `multivariate.py`, `overview.py`, `univariate.py`
- **Python:** Import ordinati in tutti i file di test
- **TypeScript:** ESLint configurato con `globals.browser` per risolvere errori `no-undef`

### Coverage (RISOLTO - 75% raggiunto)
- Aggiunti test per `run_analysis_stateless` con accepted_features e cleaning_actions
- Coverage migliorata da 70% a 75%
