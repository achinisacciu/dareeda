---
name: qa-framework
description: >
  Use this skill whenever you need to create, scaffold, run, or maintain a QA (quality assurance)
  framework inside a project. Triggers include: any request to write tests, set up linting, run
  audits, check coverage, analyse security, profile performance, or check accessibility. Also
  triggers when the user says things like "scrivi i test per questo", "crea la struttura QA",
  "aggiungi lint al progetto", "fai un audit di sicurezza", "controlla la coverage", or any
  variation. Use this skill even if the user only mentions ONE of the categories (e.g. just "add
  unit tests") because the skill knows how to handle partial setups gracefully. Always read this
  skill before touching anything test/lint/audit related.
---

# QA Framework Skill

Questa skill guida l'agente nella creazione, esecuzione e manutenzione di un framework QA
completo e parametrico all'interno di qualsiasi progetto Python / JavaScript / TypeScript / SQL.

---

## 1. Principi architetturali

- **Tutto vive in `.qa/`** nella root del progetto. Mai sparpagliare config in luoghi diversi.
- **Un file di configurazione governa tutto**: `qa.config.json` nella root del progetto.
- **L'agente legge prima, poi agisce**: sempre ispezionare la struttura esistente prima di creare.
- **Report in Markdown**: ogni run produce file `.md` leggibili in repo/wiki.
- **Idempotente**: rieseguire la stessa operazione non duplica file né rompe nulla.
- **Opinionato ma esplicito**: i tool sono fissi (vedi sezione 3), ma le scelte sono documentate.

---

## 2. Struttura `.qa/` generata

```
.qa/
├── unit/
│   ├── tests/          ← file di test scritti dall'agente
│   └── reports/        ← report Markdown post-run
├── integration/
│   ├── tests/
│   └── reports/
├── e2e/
│   ├── tests/
│   └── reports/
├── lint/
│   ├── configs/        ← file di configurazione lint (eslint, ruff, ecc.)
│   └── reports/
├── security/
│   └── reports/
├── performance/
│   ├── scripts/        ← script di profiling scritti dall'agente
│   └── reports/
├── a11y/
│   ├── scripts/
│   └── reports/
├── coverage/
│   └── reports/
├── scripts/            ← script bash/python orchestratori (run-all.sh, ecc.)
└── README.md           ← indice navigabile di tutto il framework
```

---

## 3. Tool stack opinionato

Leggi `references/toolstack.md` per la lista completa dei tool con versioni, comandi e flag.

**Riassunto rapido:**

| Categoria    | Python              | JS/TS                        | SQL             |
|--------------|---------------------|------------------------------|-----------------|
| Unit test    | pytest              | Jest                         | —               |
| Integration  | pytest + httpx      | Jest + supertest             | —               |
| E2E          | playwright (python) | Playwright (JS)              | —               |
| Lint         | ruff                | ESLint + Prettier            | sqlfluff        |
| Security     | pip-audit + bandit  | npm audit + semgrep          | —               |
| Performance  | py-spy / cProfile   | clinic.js / autocannon       | EXPLAIN ANALYZE |
| A11y         | axe-core (via py)   | axe-core + pa11y             | —               |
| Coverage     | pytest-cov          | Jest --coverage (c8/istanbul) | —               |

---

## 4. Workflow dell'agente — fasi obbligatorie

### FASE 0 — Rilevamento contesto

Prima di qualunque azione, eseguire sempre:

```bash
# 1. Rileva linguaggi nel progetto
find . -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.sql" | head -20

# 2. Leggi la configurazione QA se esiste
cat qa.config.json 2>/dev/null || echo "CONFIG_NOT_FOUND"

# 3. Controlla cosa esiste già in .qa/
ls -la .qa/ 2>/dev/null || echo "QA_DIR_NOT_FOUND"

# 4. Ispeziona package.json o pyproject.toml/requirements.txt
cat package.json 2>/dev/null
cat pyproject.toml 2>/dev/null
cat requirements.txt 2>/dev/null
```

Sulla base di questi output, adatta ogni passo successivo. **Non assumere mai** la struttura del progetto senza averla letta.

### FASE 1 — Bootstrap (solo se `.qa/` non esiste)

1. Creare la struttura directory completa (vedi sezione 2)
2. Generare `qa.config.json` nella root con i default (vedi sezione 5)
3. Installare i tool mancanti (vedi `references/toolstack.md` per i comandi)
4. Generare `.qa/README.md` come indice navigabile
5. Generare `.qa/scripts/run-all.sh` come orchestratore master

### FASE 2 — Scrittura test / script

Seguire le regole in `references/writing-guide.md` per ogni categoria.

Regole universali:
- Ogni file di test deve avere un header con: data, categoria, file sorgente testato
- Naming: `test_<nome_modulo>.py` (Python) / `<nome_modulo>.test.ts` (JS/TS)
- Un test per comportamento, non per funzione
- Mai test che dipendono dall'ordine di esecuzione
- Sempre mockkare dipendenze esterne (DB, API, filesystem) negli unit test

### FASE 3 — Esecuzione

Eseguire i tool nella sequenza standard (vedi sezione 6) e catturare sempre stdout/stderr.

### FASE 4 — Report

Dopo ogni run, generare il report Markdown nella sottocartella `reports/` appropriata.
Seguire il template in `references/report-template.md`.

Nome file report: `YYYY-MM-DD_HH-MM_<categoria>.md`

### FASE 5 — Aggiornamento README.md

Aggiornare `.qa/README.md` con i risultati dell'ultima run (tabella di stato per categoria).

---

## 5. qa.config.json — schema

```json
{
  "project": {
    "name": "nome-progetto",
    "stack": ["python", "typescript"],
    "exclude": ["node_modules", ".venv", "dist", "build", "__pycache__"]
  },
  "coverage": {
    "min_threshold": 80,
    "fail_below": true
  },
  "lint": {
    "python": { "enabled": true, "max_line_length": 100 },
    "typescript": { "enabled": true },
    "sql": { "enabled": false }
  },
  "security": {
    "enabled": true,
    "fail_on_high": true
  },
  "performance": {
    "enabled": true,
    "budget_ms": 200
  },
  "a11y": {
    "enabled": true,
    "wcag_level": "AA"
  }
}
```

L'agente deve **sempre leggere** questo file in FASE 0 e rispettare ogni impostazione.
Se il file non esiste, crearlo con i default sopra e chiedere conferma prima di procedere.

---

## 6. Sequenza di esecuzione standard

Quando si esegue il framework completo, seguire quest'ordine:

1. **Lint** (più veloce, fallisce prima se il codice è malformato)
2. **Unit test + Coverage**
3. **Integration test**
4. **Security audit**
5. **E2E test**
6. **Performance**
7. **A11y**

Se un passo fallisce in modo bloccante (es. lint con errori di sintassi), fermarsi e segnalare
prima di procedere al passo successivo. Usare il giudizio: warning non bloccano, errori sì.

---

## 7. Modalità operative

### Modalità RETROFIT (codice esistente)

Usare quando il progetto ha già codice ma nessun test.

1. Analizzare i file sorgente per capire le unità logiche principali
2. Prioritizzare: funzioni pubbliche > funzioni critiche > edge case
3. Scrivere test che documentano il comportamento **attuale** (non quello desiderato)
4. Eseguire e verificare che passino tutti
5. Segnalare eventuali bug scoperti durante il processo

```bash
# Comando di analisi per identificare cosa testare
# Python
grep -rn "^def \|^class " --include="*.py" src/ | grep -v test | grep -v "__"
# JS/TS
grep -rn "^export " --include="*.ts" --include="*.js" src/ | grep -v test
```

### Modalità TDD (sviluppo nuovo codice)

Usare quando si sviluppa una nuova feature.

1. Leggere la specifica / issue / descrizione della feature
2. Scrivere i test **prima** del codice (red phase)
3. Scrivere il codice minimo per farli passare (green phase)
4. Fare refactor mantenendo i test verdi (refactor phase)
5. Aggiornare i report

---

## 8. Aggiornamento e manutenzione

Quando viene chiesto di aggiornare test esistenti:

1. Leggere il test esistente prima di modificarlo
2. Capire perché sta fallendo (codice cambiato? test sbagliato? regressione?)
3. Non cancellare mai test senza esplicitare il motivo nel commit message / report
4. Aggiornare il report dopo ogni modifica

---

## 9. File di riferimento

Leggere questi file quando serve approfondimento:

- `references/toolstack.md` — tool completi, comandi, flag, versioni
- `references/writing-guide.md` — come scrivere test per ogni categoria e linguaggio
- `references/report-template.md` — template Markdown per i report

---

## 10. Segnali di allerta

L'agente deve segnalare esplicitamente all'utente quando:

- Coverage scende sotto la soglia in `qa.config.json`
- Viene trovata una vulnerabilità di sicurezza `HIGH` o `CRITICAL`
- Un test E2E fallisce in modo non deterministico (flaky test)
- Il tempo di risposta supera il budget in `qa.config.json`
- Esistono file sorgente senza alcun test associato (copertura strutturale zero)