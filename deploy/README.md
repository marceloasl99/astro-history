# Deploy (v6) — endurecimento do serviço

Estes arquivos **não são aplicados automaticamente**: alteram a infraestrutura do servidor de produção.

## O que muda em relação ao serviço legado

| Item | Legado | v6 |
|---|---|---|
| Bind | `0.0.0.0:81` (exposto) | `127.0.0.1:8000` atrás do nginx |
| Usuário | `root` | `astro` (sem shell) |
| Proteção de `/api/*` | só middleware da aplicação | middleware **+** nginx (404) |
| Logs | access log padrão (query string com dados de nascimento) | `--no-access-log` no uvicorn; nginx sem `$args` em `/natal/*` |
| Rate limit | nenhum | nginx 30 r/min em `/natal/*` e `/simulator`, 60 r/min em `/natal/places` (+ limite da aplicação) |
| Sandbox | nenhum | `ProtectSystem=strict`, `NoNewPrivileges`, `ReadWritePaths` só em `data/` e `db/` |

## Passos (após o merge da branch em `main`)

```bash
sudo useradd --system --home /home/astro --shell /usr/sbin/nologin astro
sudo chown -R astro:astro /home/astro/data /home/astro/db
sudo cp deploy/astro-history.service /etc/systemd/system/astro-history.service
sudo cp deploy/nginx-astrohistory.conf /etc/nginx/sites-available/astrohistory
sudo ln -sf /etc/nginx/sites-available/astrohistory /etc/nginx/sites-enabled/astrohistory
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl daemon-reload && sudo systemctl restart astro-history
# Efemérides completas e gazetteer (uma vez):
/home/astro/.venv/bin/python scripts/install_ephemeris.py
/home/astro/.venv/bin/python scripts/build_gazetteer.py   # requer data/external/geonames/*
/home/astro/.venv/bin/python scripts/build_natal_grid.py
```

Depois, feche a porta 81 no firewall/Cloudflare e aponte a origem para a porta 80 do nginx.
