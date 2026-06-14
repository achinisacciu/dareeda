# Advanced Git — Riferimento rapido

## Rebase interattivo
```bash
git rebase -i HEAD~<n>    # modifica ultimi n commit
```
Comandi disponibili nell'editor:
- `pick` — usa commit così com'è
- `reword` — usa commit, modifica messaggio
- `squash` / `fixup` — unisci con commit precedente
- `drop` — elimina commit

⚠️ Non fare rebase di branch già pushati/condivisi.

## Cherry-pick
```bash
git cherry-pick <hash>              # applica commit specifico sul branch corrente
git cherry-pick <hash1>..<hash2>    # range di commit
git cherry-pick --abort             # annulla
```

## Bisect (trova il commit che ha introdotto un bug)
```bash
git bisect start
git bisect bad                      # commit corrente è buggato
git bisect good <hash>              # ultimo commit buono noto
# Git fa checkout di un commit intermedio; testa e dì:
git bisect good / git bisect bad
# Ripeti fino a trovare il commit colpevole
git bisect reset                    # torna alla normalità
```

## Reflog (recupera commit "persi")
```bash
git reflog                          # storia di tutto quello che HEAD ha puntato
git checkout <hash>                 # recupera stato
git branch recovery-branch <hash>   # crea branch da commit "perso"
```

## Worktree (lavora su più branch contemporaneamente)
```bash
git worktree add ../altra-cartella <branch>
git worktree list
git worktree remove ../altra-cartella
```

## Patch
```bash
git format-patch -1 <hash>          # esporta commit come file .patch
git am <file.patch>                 # applica patch
```