#!/usr/bin/env python3
"""Valide les ports, UID et absence de publication accidentelle via Docker inspect."""
import json
import subprocess
import sys


def docker(*args: str):
    p = subprocess.run(["docker", *args], check=True, capture_output=True, text=True)
    return json.loads(p.stdout)


def main():
    names = ["app1", "app1b", "app2"]
    for optional in ("app3", "non-expose"):
        ident = subprocess.check_output(
            ["docker", "compose", "ps", "-q", optional], text=True
        ).strip()
        if ident:
            names.append(optional)
    for name in names:
        ident = subprocess.check_output(["docker", "compose", "ps", "-q", name], text=True).strip()
        if not ident:
            raise RuntimeError(f"Le conteneur {name} est absent")
        c = docker("inspect", ident)[0]
        ports = c["NetworkSettings"].get("Ports") or {}
        published = {p: bindings for p, bindings in ports.items() if bindings}
        if published:
            raise AssertionError(f"Ports de {name} publiés : {published}")
        user = c["Config"].get("User", "")
        if user not in ("101", "101:101"):
            raise AssertionError(f"{name}: utilisateur inattendu {user!r}")
        if not c["HostConfig"].get("ReadonlyRootfs"):
            raise AssertionError(f"{name}: read_only non actif")
        if "ALL" not in (c["HostConfig"].get("CapDrop") or []):
            raise AssertionError(f"{name}: cap_drop ALL non actif")
        security_opt = c["HostConfig"].get("SecurityOpt") or []
        if not any("no-new-privileges" in option for option in security_opt):
            raise AssertionError(f"{name}: no-new-privileges non actif")
        if any("docker.sock" in mount.get("Source", "") for mount in c.get("Mounts", [])):
            raise AssertionError(f"{name}: socket Docker monté dans une application")
        if not c["State"].get("Health", {}).get("Status") == "healthy":
            raise AssertionError(f"{name}: healthcheck non healthy")
        print(
            f"{name}: pas de port hôte/socket, user={user}, read_only, "
            "cap_drop=ALL, no-new-privileges, healthy"
        )
    idt = subprocess.check_output(["docker", "compose", "ps", "-q", "traefik"], text=True).strip()
    t = docker("inspect", idt)[0]
    ports = t["NetworkSettings"].get("Ports") or {}
    for internal in ("80/tcp", "443/tcp", "8080/tcp"):
        bindings = ports.get(internal) or []
        if not bindings or any(x.get("HostIp") != "127.0.0.1" for x in bindings):
            raise AssertionError(f"Traefik: {internal} pas strictement lié à 127.0.0.1")
    if not t["HostConfig"].get("ReadonlyRootfs"):
        raise AssertionError("Traefik: read_only non actif")
    if not any(
        "no-new-privileges" in option
        for option in (t["HostConfig"].get("SecurityOpt") or [])
    ):
        raise AssertionError("Traefik: no-new-privileges non actif")
    for mount in t.get("Mounts", []):
        if mount.get("Source") == "/var/run/docker.sock" and mount.get("RW") is not False:
            raise AssertionError("Traefik: socket Docker non monté en lecture seule")
    print(
        "Traefik: ports 80/443/8080 en loopback, read_only, "
        "no-new-privileges, montages sensibles en lecture seule"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
