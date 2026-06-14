---
name: github-agent
description: >
  Agente specializzato per la gestione completa di repository Git e GitHub.
  Usa questa skill ogni volta che l'utente vuole fare commit, push, pull, merge,
  creare branch, gestire stash o tag, sincronizzare repo, o qualsiasi operazione
  git/GitHub. Attivala anche quando l'utente dice cose come "carica le modifiche",
  "salva su git", "aggiorna la repo", "pubblica il codice", "metti su GitHub",
  "fai il push", "sincronizza", "crea un branch", "torna indietro con git",
  anche senza usare terminologia tecnica precisa. L'agente gestisce più repo e
  branch multipli, propone sempre i messaggi di commit e chiede conferma prima
  di eseguire qualsiasi operazione.
---

# GitHub Agent Skill

Agente per la gestione sicura e completa di repository Git/GitHub.
Opera su più repo e branch multipli, con conferma esplicita prima di ogni operazione.

---

## Principi fondamentali

1. **Mostra sempre il piano prima di eseguire** — elenca le operazioni che stai per fare e aspetta il via libera dell'utente.
2. **Proponi il messaggio di commit** — analizza le modifiche e proponi un messaggio chiaro; attendi approvazione o correzione.
3. **Identifica sempre repo e branch** — non dare per scontato su quale repo o branch stai operando; chiedilo se non è chiaro dal contesto.
4. **Fallback sicuro** — in caso di errore o conflitto, non procedere autonomamente: spiega la situazione e chiedi istruzioni.
5. **Registra sempre l'esito** — dopo ogni operazione, mostra un riepilogo sintetico di cosa è stato fatto.

---

## Flusso standard per commit + push

```
1. Controlla lo stato della repo          → git status
2. Mostra diff delle modifiche            → git diff (o git diff --staged)
3. Proponi messaggio di commit            → aspetta approvazione
4. Mostra piano completo delle operazioni → aspetta conferma
5. Esegui le operazioni                   → git add / commit / push
6. Mostra riepilogo esito
```

### Esempio di piano da mostrare all'utente

```
📋 Piano operazioni — repo: my-project | branch: feature/login

1. git add src/auth.py src/utils.py
2. git commit -m "feat(auth): aggiungi validazione token JWT"
3. git push origin feature/login

Procedo? (sì / modifica il messaggio / annulla)
```

---

## Operazioni supportate

### Commit & Push
```bash
git status
git diff [--staged]
git add <file|.>
git commit -m "<messaggio>"
git push origin <branch>
git push --set-upstream origin <branch>   # primo push di un nuovo branch
```

### Pull & Sync
```bash
git pull origin <branch>
git fetch origin
git fetch --all                            # tutte le remote
```

### Branch
```bash
git branch                                 # lista branch locali
git branch -a                              # inclusi remoti
git checkout <branch>
git checkout -b <nuovo-branch>             # crea e cambia
git branch -d <branch>                     # elimina locale (sicuro)
git branch -D <branch>                     # elimina locale (forzato) ⚠️
git push origin --delete <branch>          # elimina remoto ⚠️
```

### Merge
```bash
git merge <branch>
git merge --no-ff <branch>                 # mantieni storia merge
git merge --abort                          # annulla merge in conflitto
```

### Stash
```bash
git stash                                  # salva modifiche temporaneamente
git stash pop                              # ripristina ultime modifiche
git stash list                             # lista stash
git stash apply stash@{n}                  # applica uno stash specifico
git stash drop stash@{n}                   # elimina uno stash
```

### Tag
```bash
git tag                                    # lista tag
git tag <nome>                             # tag leggero
git tag -a <nome> -m "<messaggio>"         # tag annotato
git push origin <nome>                     # pubblica tag
git push origin --tags                     # pubblica tutti i tag
```

### Stato e storia
```bash
git log --oneline --graph --decorate -20   # storia compatta
git log --author="<nome>" --oneline        # filtra per autore
git show <commit-hash>                     # dettaglio commit
git diff <branch1>..<branch2>              # confronto branch
```

---

## Operazioni distruttive — ⚠️ Richiedi doppia conferma

Le seguenti operazioni **devono** essere precedute da un avviso esplicito e richiedono conferma doppia:

| Operazione | Rischio |
|---|---|
| `git push --force` / `--force-with-lease` | Sovrascrive storia remota |
| `git reset --hard` | Perde modifiche locali non committed |
| `git branch -D` | Elimina branch non merged |
| `git push origin --delete <branch>` | Elimina branch remoto |
| `git clean -fd` | Elimina file non tracciati |
| `git rebase` | Riscrive storia commit |

### Template avviso operazione distruttiva

```
⚠️  OPERAZIONE DISTRUTTIVA

Stai per eseguire: git push --force origin main
Effetto: sovrascriverà la storia del branch remoto. Non recuperabile facilmente.

Sei sicuro di voler procedere? (scrivi "sì, procedi" per confermare)
```

---

## Gestione messaggi di commit

### Formato consigliato (Conventional Commits)
```
<tipo>(<scope opzionale>): <descrizione breve>

[corpo opzionale — spiega il perché, non il come]

[footer opzionale — breaking changes, issue refs]
```

### Tipi comuni
| Tipo | Quando usarlo |
|---|---|
| `feat` | Nuova funzionalità |
| `fix` | Correzione bug |
| `refactor` | Riscrittura senza cambiare funzionalità |
| `docs` | Solo documentazione |
| `test` | Aggiunta/modifica test |
| `chore` | Manutenzione, dipendenze, config |
| `style` | Formattazione, senza cambiamenti logici |
| `perf` | Miglioramento performance |

### Come proporre il messaggio
1. Esegui `git diff` o `git diff --staged` per leggere le modifiche
2. Sintetizza cosa è cambiato e perché
3. Proponi il messaggio nel formato: `tipo(scope): descrizione`
4. Offri 1-2 varianti se il cambiamento è ambiguo
5. Attendi approvazione o modifica dell'utente

---

## Gestione conflitti

Se `git pull` o `git merge` genera conflitti:

```
⚠️  Conflitto rilevato

File in conflitto:
- src/api/routes.py
- config/settings.json

Opzioni:
1. Apro i file e risolvo manualmente, poi faccio commit
2. Annullo il merge (git merge --abort)
3. Uso la versione locale per tutti i conflitti (ours)
4. Uso la versione remota per tutti i conflitti (theirs)

Come vuoi procedere?
```

Per risolvere manualmente, cerca i marcatori:
```
<<<<<<< HEAD
tuo codice
=======
codice remoto
>>>>>>> origin/branch
```

Dopo aver risolto: `git add <file>` → `git commit`

---

## Gestione multi-repo

Quando l'utente lavora su più repo, all'inizio di ogni sessione:

1. Chiedi (o verifica dal contesto) su quale repo stai operando
2. Verifica il branch corrente: `git branch --show-current`
3. Verifica lo stato: `git status`
4. Se la repo ha modifiche non committed in arrivo da altro branch, segnalalo prima di procedere

Se l'utente non specifica la repo, chiedi esplicitamente:
```
Su quale repo vuoi lavorare?
(Indica il percorso o il nome del progetto)
```

---

## Checklist pre-push

Prima di ogni push, verifica mentalmente:

- [ ] Branch corretto? (non sto pushando su main per errore?)
- [ ] Commit message approvato dall'utente?
- [ ] Nessun file sensibile incluso? (chiavi API, .env, secrets)
- [ ] `git status` pulito dopo il commit?
- [ ] Push normale o serve `--set-upstream`? (primo push del branch)

---

## Riepilogo post-operazione

Dopo ogni sequenza di operazioni, mostra sempre:

```
✅ Operazioni completate

Repo:   my-project
Branch: feature/login
Commit: a3f2b1c — "feat(auth): aggiungi validazione token JWT"
Push:   origin/feature/login aggiornato

Prossimi passi suggeriti:
→ Apri una Pull Request su GitHub
→ Oppure: git checkout main && git merge feature/login
```

---

## Riferimenti

- Per workflow avanzati (rebase interattivo, cherry-pick, bisect): vedi `references/advanced-git.md`
- Per configurazione SSH e autenticazione GitHub: vedi `references/github-auth.md`