"""
Mahalliy DEV profil almashtirish (Akbarali ↔ yangi test user).
Sirlar chatga chiqarilmaydi; backup `.local/dev_env_backup` da saqlanadi.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
BACKUP_PATH = ROOT / ".local" / "dev_env_backup"
LOCAL_DIR = ROOT / ".local"

# Bazada yo‘q, test uchun band qilingan ID (Akbarali qatoriga tegmaydi)
TEST_DEV_TELEGRAM_ID = 9123456789


def _read_env() -> str:
    if not ENV_PATH.is_file():
        raise SystemExit(".env topilmadi")
    return ENV_PATH.read_text(encoding="utf-8")


def _write_env(content: str) -> None:
    ENV_PATH.write_text(content, encoding="utf-8")


def _get_var(content: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}=(.*)$", content, re.MULTILINE)
    return m.group(1).strip() if m else None


def _set_var(content: str, key: str, value: str) -> str:
    line = f"{key}={value}"
    if re.search(rf"^{re.escape(key)}=", content, re.MULTILINE):
        return re.sub(rf"^{re.escape(key)}=.*$", line, content, flags=re.MULTILINE)
    return content.rstrip() + "\n" + line + "\n"


def cmd_backup_and_test() -> None:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    content = _read_env()
    dev = _get_var(content, "DEV_TELEGRAM_ID")
    admin = _get_var(content, "ADMIN_TELEGRAM_IDS")
    if not dev:
        raise SystemExit("DEV_TELEGRAM_ID .env da topilmadi")

    BACKUP_PATH.write_text(
        f"DEV_TELEGRAM_ID={dev}\nADMIN_TELEGRAM_IDS={admin or ''}\n",
        encoding="utf-8",
    )

    # Admin faqat Akbarali (eski dev) uchun qoladi; yangi test user admin emas
    content = _set_var(content, "DEV_TELEGRAM_ID", str(TEST_DEV_TELEGRAM_ID))
    if dev and (not admin or admin.strip() == ""):
        content = _set_var(content, "ADMIN_TELEGRAM_IDS", dev)
    _write_env(content)
    print("OK: Akbarali DEV profili backup qilindi (.local/dev_env_backup)")
    print("OK: DEV_TELEGRAM_ID yangi test foydalanuvchiga o‘rnatildi")
    print("Keyingi qadam: backendni qayta ishga tushiring va brauzerda sessionStorage tozalang yoki inkognito oching")


def cmd_restore_akbarali() -> None:
    if not BACKUP_PATH.is_file():
        raise SystemExit("Backup topilmadi. Avval backup-and-test bajaring.")
    lines = BACKUP_PATH.read_text(encoding="utf-8").splitlines()
    backup = {}
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            backup[k.strip()] = v.strip()
    content = _read_env()
    if "DEV_TELEGRAM_ID" in backup:
        content = _set_var(content, "DEV_TELEGRAM_ID", backup["DEV_TELEGRAM_ID"])
    if "ADMIN_TELEGRAM_IDS" in backup:
        content = _set_var(content, "ADMIN_TELEGRAM_IDS", backup["ADMIN_TELEGRAM_IDS"])
    _write_env(content)
    print("OK: DEV_TELEGRAM_ID va ADMIN_TELEGRAM_IDS backupdan tiklandi")
    print("Backendni qayta ishga tushiring")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/local_dev_profile.py backup-and-test | restore-akbarali")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "backup-and-test":
        cmd_backup_and_test()
    elif cmd == "restore-akbarali":
        cmd_restore_akbarali()
    else:
        raise SystemExit(f"Noma'lum buyruq: {cmd}")


if __name__ == "__main__":
    main()
