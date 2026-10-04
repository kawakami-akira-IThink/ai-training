"""暗号化ログの復号ツール。

使い方: python tools/decrypt_log.py [ログファイル]   （省略時は標準入力）
環境変数 LOG_ENCRYPTION_KEY が必要。customer_enc=<暗号文> を復号して次の行に表示する。
"""
import os
import re
import sys

from cryptography.fernet import Fernet

PATTERN = re.compile(r"customer_enc=(\S+)")


def main() -> None:
    fernet = Fernet(os.environ["LOG_ENCRYPTION_KEY"].encode())
    sys.stdout.reconfigure(encoding="utf-8")
    src = open(sys.argv[1], encoding="utf-8") if len(sys.argv) > 1 else sys.stdin
    for line in src:
        line = line.rstrip("\n")
        m = PATTERN.search(line)
        if m:
            line += "\n  -> " + fernet.decrypt(m.group(1).encode()).decode()
        print(line)


if __name__ == "__main__":
    main()
