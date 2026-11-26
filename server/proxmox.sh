#!/usr/bin/env bash
# The SpotiParty Hub on Proxmox VE, in a small Debian container (LXC). Run it in the shell of the Proxmox host
# (Datacenter → your node → Shell), as root:
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/CodeAura/SpotiParty/main/server/proxmox.sh)"
#
# or, with options (after downloading it):
#
#   bash proxmox.sh --ctid 120 --ip 192.168.1.50/24 --gw 192.168.1.1
#
#   --ctid N          container number (default: the next free one)
#   --hostname NAME   name of the container (default: spotiparty)
#   --storage NAME    storage for the container's disk (default: local-lvm, else the first that can hold one)
#   --bridge NAME     network bridge (default: vmbr0)
#   --ip dhcp|CIDR    dhcp (default) or a fixed address like 192.168.1.50/24 (then also --gw)
#   --gw ADDRESS      gateway for a fixed address
#   --vlan N          VLAN tag on the network card
#   --memory MB       memory (default 512)    --disk GB  disk (default 4)    --cores N  cores (default 1)
#   --port N          port of the dashboard (default 8770)
#   --no-auto-update  no nightly update to the newest release inside the container
#
# What it does: downloads the newest Debian 12 template if needed, makes an unprivileged container that starts with
# Proxmox, installs git and Python in it, clones SpotiParty (the newest release) and runs server/install.sh there.
# The container gets its own address on your network, so TVs and phones find the Hub like any other computer.
# Remove it again with:  pct stop <ctid> && pct destroy <ctid>
set -euo pipefail

REPO=https://github.com/CodeAura/SpotiParty.git
CTID="" HOSTNAME_CT=spotiparty STORAGE="" BRIDGE=vmbr0 IP=dhcp GW="" VLAN="" MEMORY=512 DISK=4 CORES=1 PORT=8770
AUTOUPDATE=1
while [ $# -gt 0 ]; do
  case "$1" in
    --ctid) CTID="$2"; shift ;;
    --hostname) HOSTNAME_CT="$2"; shift ;;
    --storage) STORAGE="$2"; shift ;;
    --bridge) BRIDGE="$2"; shift ;;
    --ip) IP="$2"; shift ;;
    --gw) GW="$2"; shift ;;
    --vlan) VLAN="$2"; shift ;;
    --memory) MEMORY="$2"; shift ;;
    --disk) DISK="$2"; shift ;;
    --cores) CORES="$2"; shift ;;
    --port) PORT="$2"; shift ;;
    --no-auto-update) AUTOUPDATE=0 ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) echo "Onbekende optie: $1 (zie --help)" >&2; exit 2 ;;
  esac
  shift
done

say() { printf '\033[1;32m→\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mFout:\033[0m %s\n' "$*" >&2; exit 1; }

# ---------- checks ----------
[ "$(id -u)" -eq 0 ] || die "start dit script als root in de shell van de Proxmox-host."
command -v pct >/dev/null && command -v pveam >/dev/null && command -v pvesm >/dev/null \
  || die "dit is geen Proxmox VE-host (pct, pveam en pvesm ontbreken). Op een gewone Linux-server: zie server/install.sh."
for n in "$MEMORY" "$DISK" "$CORES" "$PORT"; do
  case "$n" in ''|*[!0-9]*) die "--memory, --disk, --cores en --port zijn getallen." ;; esac
done
if [ "$IP" != dhcp ]; then
  case "$IP" in */*) ;; *) die "--ip is dhcp of een adres met netmasker, zoals 192.168.1.50/24." ;; esac
  [ -n "$GW" ] || die "bij een vast adres hoort ook --gw (de gateway, meestal je router)."
fi
ip link show "$BRIDGE" >/dev/null 2>&1 || die "de netwerkbrug $BRIDGE bestaat niet (kies er een met --bridge)."

if [ -z "$CTID" ]; then
  CTID="$(pvesh get /cluster/nextid)"
fi
case "$CTID" in ''|*[!0-9]*) die "--ctid is een getal." ;; esac
if pct status "$CTID" >/dev/null 2>&1; then
  die "container $CTID bestaat al. Kies een ander nummer met --ctid."
fi

if [ -z "$STORAGE" ]; then
  if pvesm status -content rootdir 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx local-lvm; then
    STORAGE=local-lvm
  else
    STORAGE="$(pvesm status -content rootdir 2>/dev/null | awk 'NR>1 && $3=="active" {print $1; exit}')"
  fi
fi
[ -n "$STORAGE" ] || die "geen opslag gevonden waar een container op kan (kies er een met --storage)."

# ---------- template ----------
TSTORE="$(pvesm status -content vztmpl 2>/dev/null | awk 'NR>1 && $3=="active" {print $1; exit}')"
[ -n "$TSTORE" ] || die "geen opslag voor container-templates gevonden (zet bij een opslag 'Container template' aan)."
say "Lijst met templates bijwerken"
pveam update >/dev/null
TEMPLATE="$(pveam available --section system | awk '{print $2}' | grep -E '^debian-12-standard_.*_amd64\.tar\.(zst|gz|xz)$' \
  | sort -V | tail -1)"
[ -n "$TEMPLATE" ] || die "geen Debian 12-template gevonden in 'pveam available'."
if ! pveam list "$TSTORE" | awk '{print $1}' | grep -q "/$TEMPLATE\$"; then
  say "Template downloaden: $TEMPLATE"
  pveam download "$TSTORE" "$TEMPLATE" >/dev/null
fi

# ---------- container ----------
NET="name=eth0,bridge=$BRIDGE,ip=$IP"
[ "$IP" = dhcp ] || NET="$NET,gw=$GW"
[ -z "$VLAN" ] || NET="$NET,tag=$VLAN"
say "Container $CTID ($HOSTNAME_CT) maken op $STORAGE: $CORES core, $MEMORY MB, $DISK GB"
pct create "$CTID" "$TSTORE:vztmpl/$TEMPLATE" \
  --hostname "$HOSTNAME_CT" --cores "$CORES" --memory "$MEMORY" --swap 256 \
  --rootfs "$STORAGE:$DISK" --net0 "$NET" --unprivileged 1 --features nesting=1 \
  --onboot 1 --description "SpotiParty Hub: http://<adres>:$PORT/ (https://github.com/CodeAura/SpotiParty)" >/dev/null
pct start "$CTID"

say "Wachten op het netwerk in de container"
ok=0
for _ in $(seq 1 60); do
  if pct exec "$CTID" -- getent hosts github.com >/dev/null 2>&1; then ok=1; break; fi
  sleep 2
done
[ "$ok" = 1 ] || die "de container komt niet op internet (DHCP, gateway of DNS?). Kijk met: pct enter $CTID"

# ---------- SpotiParty in the container ----------
run() { pct exec "$CTID" -- env LANG=C.UTF-8 LC_ALL=C.UTF-8 DEBIAN_FRONTEND=noninteractive bash -c "$1"; }
say "Git en Python installeren"
run "apt-get update -qq && apt-get install -y -qq git python3 ca-certificates >/dev/null"
say "SpotiParty ophalen (de nieuwste release)"
run "git clone -q $REPO /usr/local/src/SpotiParty && cd /usr/local/src/SpotiParty \
  && latest=\$(git tag -l 'v[0-9]*' --sort=-v:refname | head -1) \
  && { [ -z \"\$latest\" ] || git -c advice.detachedHead=false checkout -q \"\$latest\"; }"
say "De Hub installeren"
OPTS="--port $PORT"
[ "$AUTOUPDATE" = 1 ] || OPTS="$OPTS --no-auto-update"
run "/usr/local/src/SpotiParty/server/install.sh $OPTS" | sed 's/^/   /'

ADDR="$(pct exec "$CTID" -- hostname -I 2>/dev/null | awk '{print $1}')"
[ -n "$ADDR" ] || ADDR="<adres-van-container-$CTID>"
echo
printf '\033[1;32mKlaar!\033[0m De SpotiParty Hub draait in container %s.\n' "$CTID"
echo
echo "  1. Open het dashboard:   http://$ADDR:$PORT/"
echo "     Kies daar meteen je PIN (twee keer invullen): tot dan kan iedereen in je netwerk hem kiezen."
echo "  2. Koppel Spotify en zet je Jam-link erin (zie de rondleiding in het dashboard)."
echo "  3. Schermen: de tv-app vindt de Hub vanzelf; een browser of smart-tv opent http://$ADDR:$PORT/scherm/"
echo
echo "  In de container:  pct enter $CTID     Logboek:  pct exec $CTID -- journalctl -u spotiparty-hub -f"
[ "$AUTOUPDATE" = 1 ] && echo "  Updates gaan vanzelf, elke nacht rond 04:30 (als er geen muziek speelt)."
[ "$IP" = dhcp ] && echo "  Tip: geef de container een vast adres in je router (DHCP-reservering), dan blijft het dashboard op hetzelfde adres."
echo "  Verwijderen:  pct stop $CTID && pct destroy $CTID"
