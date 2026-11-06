"""Non-runtime tests: inspect the actual deliverable, no Docker required."""
from pathlib import Path
import re
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
C = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
STATIC = yaml.safe_load((ROOT / "config/traefik.yaml").read_text(encoding="utf-8"))
DYNAMIC = yaml.safe_load((ROOT / "config/dynamic/https.yaml").read_text(encoding="utf-8"))
SERVICES = C["services"]


def test_yaml_documents_load():
    assert isinstance(C, dict) and isinstance(STATIC, dict) and isinstance(DYNAMIC, dict)


def test_all_required_services_exist():
    assert {"traefik", "app1", "app1b", "app2", "app3", "non-expose"} <= set(SERVICES)


def test_traefik_version_matches_subject():
    assert SERVICES["traefik"]["image"] == "traefik:v3.7.17"


@pytest.mark.parametrize("internal", [80, 443, 8080])
def test_traefik_ports_are_loopback(internal):
    assert f"127.0.0.1:{internal}:{internal}" in SERVICES["traefik"]["ports"]


@pytest.mark.parametrize("name", ["app1", "app1b", "app2", "app3", "non-expose"])
def test_nginx_has_no_published_host_port(name):
    assert not SERVICES[name].get("ports")
    assert "8080" in SERVICES[name]["expose"]


@pytest.mark.parametrize("name", ["app1", "app1b", "app2", "app3", "non-expose"])
def test_nginx_non_root_read_only(name):
    s = SERVICES[name]
    assert s["user"] == "101:101"
    assert s["read_only"] is True
    assert "ALL" in s["cap_drop"]
    assert "no-new-privileges:true" in s["security_opt"]
    assert "healthcheck" in s
    assert not any("docker.sock" in m for m in s.get("volumes", []))


def test_traefik_security_flags_and_socket_caveat():
    s = SERVICES["traefik"]
    assert s["read_only"] is True
    assert "no-new-privileges:true" in s["security_opt"]
    assert any(m.endswith("docker.sock:ro") for m in s["volumes"])
    assert "socket" in (ROOT / "docs/ARCHITECTURE_SECURITE.md").read_text().lower()


def test_provider_docker_opt_in():
    provider = STATIC["providers"]["docker"]
    assert provider["exposedByDefault"] is False
    assert provider["network"] == "frontend"


def test_aliasing_headers_are_rejected():
    assert STATIC["global"]["aliasHeadersStrategy"] == "reject"


def test_provider_file_and_certificates():
    assert STATIC["providers"]["file"]["directory"] == "/etc/traefik/dynamic"
    certs = DYNAMIC["tls"]["certificates"]
    assert certs[0]["certFile"].endswith("localhost.crt")
    assert certs[0]["keyFile"].endswith("localhost.key")
    assert DYNAMIC["tls"]["options"]["default"]["minVersion"] == "VersionTLS12"


def test_dashboard_is_explicit_lab_only():
    assert STATIC["api"] == {"dashboard": True, "insecure": True}
    assert "127.0.0.1:8080:8080" in SERVICES["traefik"]["ports"]


def test_entrypoints_web_and_secure():
    assert STATIC["entryPoints"]["web"]["address"] == ":80"
    assert STATIC["entryPoints"]["websecure"]["address"] == ":443"


@pytest.mark.parametrize("name,router,hostname", [
    ("app1", "app1", "app1.localhost"),
    ("app2", "app2", "app2.localhost"),
    ("app3", "app3secure", "app3.localhost"),
])
def test_host_rules_and_opt_in(name, router, hostname):
    labels = SERVICES[name]["labels"]
    assert labels["traefik.enable"] == "true"
    assert labels[f"traefik.http.routers.{router}.rule"] == f"Host(`{hostname}`)"


def test_app1_b_replicas_share_same_labels():
    assert SERVICES["app1"]["labels"] == SERVICES["app1b"]["labels"]
    assert SERVICES["app1"]["labels"]["traefik.http.services.app1-svc.loadbalancer.server.port"] == "8080"


def test_unlabelled_app_is_not_explicitly_exposed():
    labels = SERVICES["non-expose"]["labels"]
    assert "traefik.enable" not in labels
    assert SERVICES["non-expose"]["profiles"] == ["audit"]


def test_app3_requires_tls_and_external_auth():
    labels = SERVICES["app3"]["labels"]
    assert labels["traefik.http.routers.app3secure.tls"] == "true"
    assert "admin-auth@file" in labels["traefik.http.routers.app3secure.middlewares"]
    auth = DYNAMIC["http"]["middlewares"]["admin-auth"]["basicAuth"]
    assert auth["usersFile"] == "/etc/traefik/secrets/app3.htpasswd"
    assert auth["removeHeader"] is True
    assert SERVICES["app3"]["profiles"] == ["evolution"]


def test_secure_header_middleware():
    h = DYNAMIC["http"]["middlewares"]["secure-headers"]["headers"]
    assert h["contentTypeNosniff"] is True
    assert h["frameDeny"] is True
    assert "redirect-to-https" in DYNAMIC["http"]["middlewares"]


@pytest.mark.parametrize("name,text", [
    ("app1", "App1 - Instance A"),
    ("app1b", "App1 - Instance B"),
    ("app2", "App2 - Bonjour"),
    ("app3", "App3 - Zone protegee"),
])
def test_app_files_are_distinguishable(name, text):
    assert text in (ROOT / name / "index.html").read_text()


def test_no_secret_in_labels():
    labels = "\n".join(f"{k}={v}" for s in SERVICES.values() for k,v in s.get("labels",{}).items())
    assert not re.search(r"(?:password|passwd|token|private.key)\s*[:=]", labels, re.I)
    assert "htpasswd" not in labels.lower()


def test_generated_secrets_not_required_in_source_checkout():
    # Ne doit PAS echouer apres un bootstrap local qui cree les fichiers ignores.
    assert (ROOT / "secrets/README.md").exists()
    assert (ROOT / "certs/README.md").exists()


def test_gitignore_protects_certs_and_hashes():
    content = (ROOT / ".gitignore").read_text()
    assert "certs/*" in content and "secrets/*" in content
    assert "*.htpasswd" in content
    assert ".env" in content


def test_21_question_answers_present():
    text = (ROOT / "QUESTIONS_REPONSES.md").read_text()
    found = re.findall(r"^\*\*(\d{1,2})\.\s", text, flags=re.M)
    assert found == [str(i) for i in range(1,22)]


def test_all_five_exercises_documented():
    text = (ROOT / "CORRECTION_EXERCICES.md").read_text()
    for i in range(1,6):
        assert f"Exercice {i}" in text


def test_security_matrix_has_10_lines():
    text = (ROOT / "docs/ARCHITECTURE_SECURITE.md").read_text()
    assert text.count("| P1 |") >= 7
    assert text.count("| P2 |") >= 2


@pytest.mark.parametrize("script", sorted((ROOT / "scripts").glob("*.sh")))
def test_shell_scripts_syntax(script):
    subprocess.run(["bash", "-n", str(script)], check=True)
