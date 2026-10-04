import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import make

TOOL = Path(__file__).resolve().parent.parent / "tools" / "decrypt_log.py"


def test_log_has_no_plaintext_and_is_decryptable(client, log_key, capsys):
    client.post("/customers", json=make(name="秘密の名前", job="極秘職"))
    out = capsys.readouterr().out
    assert "op=create status=201 id=1" in out
    assert "customer_enc=" in out
    for secret in ("秘密の名前", "極秘職"):
        assert secret not in out

    r = subprocess.run(
        [sys.executable, str(TOOL)], input=out, capture_output=True, text=True,
        encoding="utf-8", env={**os.environ, "LOG_ENCRYPTION_KEY": log_key},
    )
    assert r.returncode == 0, r.stderr
    last = r.stdout.strip().splitlines()[-1].replace("->", "", 1).strip()
    assert json.loads(last) == make(name="秘密の名前", job="極秘職")


def test_error_logs_have_no_customer_info(client, capsys):
    client.post("/customers", json=make(name="秘密の名前"))
    client.post("/customers", json=make(name="秘密の名前"))  # DUPLICATE
    client.post("/customers", json=make(name="秘密の名前", age=5000))  # VALIDATION_ERROR
    out = capsys.readouterr().out
    assert "code=DUPLICATE" in out and "code=VALIDATION_ERROR" in out
    assert "秘密の名前" not in out


def test_no_key_never_logs_plaintext(client, monkeypatch, capsys):
    monkeypatch.delenv("LOG_ENCRYPTION_KEY")
    client.post("/customers", json=make(name="秘密の名前"))
    assert "秘密の名前" not in capsys.readouterr().out
