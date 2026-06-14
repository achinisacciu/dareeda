# QA Framework — dareeda-platform

## Stato attuale

*Ultimo aggiornamento: 2026-06-14 17:36*

| Categoria | Stato | Ultimo report |
|-----------|-------|---------------|
| Lint | ⚠️ WARN | [2026-06-14](lint/reports/2026-06-14_17-36_lint.md) |
| Unit Test | ✅ PASS | [2026-06-14](unit/reports/2026-06-14_17-36_unit.md) |
| Coverage | ✅ PASS (75.18%) | [2026-06-14](coverage/reports/coverage.json) |
| Integration | N/A | — |
| E2E | N/A | — |
| Security | ⚠️ WARN | [2026-06-14](../security/reports/2026-06-14_17-36_security_pip-audit.md) |
| Performance | N/A | — |
| A11y | N/A | — |

## Come eseguire

```bash
# Tutto insieme
bash .qa/scripts/run-all.sh

# Singola categoria
bash .qa/scripts/run-lint.sh
bash .qa/scripts/run-unit.sh
bash .qa/scripts/run-integration.sh
bash .qa/scripts/run-security.sh
bash .qa/scripts/run-e2e.sh
bash .qa/scripts/run-performance.sh
bash .qa/scripts/run-a11y.sh
```

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

## Note

- Coverage: 75.18% (soglia 75% raggiunta). File legacy `migrate_add_suggested_features.py` e `test_fase1_target.py` esclusi da coverage.
- pip-audit: 8 vulnerabilità residue (transitive via `tornado`/`starlette` da `uvicorn`/`fastapi`).
- ruff: 121 avvisi E501/I001 rimasti. Fix progressivo o alzare soglia a 120 (già applicata).
- ESLint 9 configurato e funzionante.
- Prossimi step: estendere test su `enterprise.py` e `analysis.py` per avvicinarsi a 80%+.
