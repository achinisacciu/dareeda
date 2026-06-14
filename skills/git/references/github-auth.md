# GitHub Auth — Configurazione e troubleshooting

## Verifica autenticazione attuale
```bash
git remote -v                        # vedi URL remoti (SSH vs HTTPS)
ssh -T git@github.com                # testa connessione SSH
gh auth status                       # se usi GitHub CLI
```

## SSH (raccomandato)
```bash
# Genera chiave
ssh-keygen -t ed25519 -C "tua@email.com"

# Avvia ssh-agent e aggiungi chiave
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copia chiave pubblica → incollala su GitHub Settings > SSH Keys
cat ~/.ssh/id_ed25519.pub

# Converti repo da HTTPS a SSH
git remote set-url origin git@github.com:<user>/<repo>.git
```

## HTTPS con token (Personal Access Token)
```bash
# Crea PAT su: GitHub > Settings > Developer settings > Personal access tokens
# Poi usalo come password quando git chiede credenziali

# Salva credenziali in cache (non riscrivere ogni volta)
git config --global credential.helper store       # permanente (plaintext)
git config --global credential.helper cache        # temporaneo (in memoria)

# Oppure includi token nell'URL (non farlo su repo pubblici)
git remote set-url origin https://<token>@github.com/<user>/<repo>.git
```

## GitHub CLI (gh)
```bash
gh auth login                        # login interattivo
gh auth logout
gh pr create                         # crea Pull Request
gh pr list
gh repo clone <user>/<repo>
```

## Errori comuni

| Errore | Causa | Soluzione |
|---|---|---|
| `Permission denied (publickey)` | SSH key non configurata | Segui setup SSH sopra |
| `remote: Repository not found` | URL sbagliato o no accesso | Verifica `git remote -v` |
| `Authentication failed` | Token/password scaduto | Rinnova PAT su GitHub |
| `failed to push: rejected` | Branch remoto avanti rispetto al locale | `git pull --rebase` poi push |
| `SSL certificate problem` | Proxy/rete aziendale | `git config --global http.sslVerify false` (solo in ambienti fidati) |