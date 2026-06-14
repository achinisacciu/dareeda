# Report Template — QA Framework

Usare questo template per ogni report generato in `.qa/*/reports/`.
Sostituire i segnaposto `{{ }}` con i valori reali.

---

## Template standard (per tutte le categorie)

```markdown
# {{ CATEGORIA }} Report

**Progetto:** {{ nome da qa.config.json }}  
**Data:** {{ YYYY-MM-DD HH:MM }}  
**Stack:** {{ python | typescript | sql }}  
**Eseguito da:** agente AI  

---

## Risultato

| Stato | Dettaglio |
|-------|-----------|
| {{ ✅ PASS / ❌ FAIL / ⚠️ WARN }} | {{ breve descrizione }} |

---

## Metriche

<!-- Adattare per categoria — vedi sezioni sotto -->

---

## Problemi trovati

<!-- Se nessuno: scrivere "Nessun problema trovato." -->

### {{ SEVERITY }}: {{ titolo problema }}

- **File / Pacchetto:** `{{ path o nome }}`
- **Riga:** {{ numero riga, se applicabile }}
- **Descrizione:** {{ spiegazione chiara }}
- **Fix suggerito:** {{ comando o modifica da fare }}

---

## Output raw (troncato)

\`\`\`
{{ primi 50 righe di stdout/stderr del tool }}
\`\`\`

---

## Azioni raccomandate

1. {{ azione 1 }}
2. {{ azione 2 }}

---

*Report generato automaticamente dal QA Framework*
```

---

## Metriche specifiche per categoria

### Unit / Integration

```markdown
## Metriche

| Metrica | Valore |
|---------|--------|
| Test totali | {{ N }} |
| Passati | {{ N }} ✅ |
| Falliti | {{ N }} ❌ |
| Saltati | {{ N }} ⏭️ |
| Durata | {{ N }}s |
```

### Coverage

```markdown
## Metriche

| Metrica | Valore | Soglia | Stato |
|---------|--------|--------|-------|
| Lines | {{ N }}% | {{ min_threshold }}% | {{ ✅/❌ }} |
| Branches | {{ N }}% | {{ min_threshold }}% | {{ ✅/❌ }} |
| Functions | {{ N }}% | {{ min_threshold }}% | {{ ✅/❌ }} |

### File con coverage più bassa

| File | Coverage |
|------|----------|
| `src/...` | {{ N }}% |
```

### Security

```markdown
## Metriche

| Severity | Conteggio |
|----------|-----------|
| 🔴 CRITICAL | {{ N }} |
| 🟠 HIGH | {{ N }} |
| 🟡 MEDIUM | {{ N }} |
| 🟢 LOW | {{ N }} |
```

### Performance

```markdown
## Metriche

| Metrica | Valore | Budget | Stato |
|---------|--------|--------|-------|
| Latenza media | {{ N }}ms | {{ budget_ms }}ms | {{ ✅/❌ }} |
| P95 | {{ N }}ms | — | — |
| P99 | {{ N }}ms | — | — |
| Throughput | {{ N }} req/s | — | — |

### Top 5 funzioni più lente

| Funzione | Tempo cumulativo | Chiamate |
|----------|-----------------|----------|
| `module.func` | {{ N }}s | {{ N }} |
```

### A11y

```markdown
## Metriche

| Severity | Violazioni |
|----------|-----------|
| 🔴 critical | {{ N }} |
| 🟠 serious | {{ N }} |
| 🟡 moderate | {{ N }} |
| 🟢 minor | {{ N }} |

**Standard WCAG:** {{ AA | AAA }}  
**Pagine analizzate:** {{ N }}
```

---

## README.md di .qa/ — Template

Il file `.qa/README.md` è l'indice master. Aggiornarlo dopo ogni run.

```markdown
# QA Framework — {{ nome progetto }}

## Stato attuale

*Ultimo aggiornamento: {{ YYYY-MM-DD HH:MM }}*

| Categoria | Stato | Ultimo report |
|-----------|-------|---------------|
| Lint | {{ ✅/❌/⚠️ }} | [{{ data }}](lint/reports/{{ file }}) |
| Unit Test | {{ ✅/❌/⚠️ }} | [{{ data }}](unit/reports/{{ file }}) |
| Coverage | {{ N }}% {{ ✅/❌ }} | [{{ data }}](coverage/reports/{{ file }}) |
| Integration | {{ ✅/❌/⚠️ }} | [{{ data }}](integration/reports/{{ file }}) |
| E2E | {{ ✅/❌/⚠️ }} | [{{ data }}](e2e/reports/{{ file }}) |
| Security | {{ ✅/❌/⚠️ }} | [{{ data }}](security/reports/{{ file }}) |
| Performance | {{ ✅/❌/⚠️ }} | [{{ data }}](performance/reports/{{ file }}) |
| A11y | {{ ✅/❌/⚠️ }} | [{{ data }}](a11y/reports/{{ file }}) |

## Come eseguire

\`\`\`bash
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
\`\`\`

## Configurazione

Vedi `../qa.config.json` nella root del progetto.

## Struttura

\`\`\`
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
\`\`\`
```