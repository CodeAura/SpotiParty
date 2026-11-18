# SpotiParty Hub op een Linux-server

De Hub zonder scherm, op een server die altijd aan staat. Dashboard: `http://<server>:8770/`, feestscherm:
`http://<server>:8770/scherm/`, gastenpagina: `http://<server>:8770/gast`.

**systemd (Debian, Ubuntu, Fedora, Arch, ...):**

```bash
sudo ./server/install.sh            # installeren of bijwerken; --port, --firewall, --uninstall
```

**Docker (Linux):**

```bash
cd server && docker compose up -d --build
docker compose logs hub             # de PIN
```

| Bestand              | Wat                                                                  |
| -------------------- | -------------------------------------------------------------------- |
| `install.sh`         | Kopieert `hub/` en `web/` naar `/opt/spotiparty`, gebruiker `spotiparty`, dienst `spotiparty-hub`, data in `/var/lib/spotiparty` |
| `Dockerfile`         | `python:3.12-alpine`, alleen de standaardbibliotheek; bouwen vanaf de hoofdmap |
| `docker-compose.yml` | `network_mode: host` (voor de UDP-discovery op 8771), volume `spotiparty-data` |

Uitleg: [docs/hub/linux-server.md](../docs/hub/linux-server.md).
