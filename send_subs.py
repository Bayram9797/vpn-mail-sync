import os
import sys
import base64
import smtplib
import urllib.request
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage

SUBSCRIPTIONS = [
    {
        "name": "Mifa White-List (Diman331)",
        "filename": "sub_diman331.txt",
        "url": "https://gist.githubusercontent.com/Diman331/8c868070c0b5a5ec0c7d94507717b67b/raw/subscription.txt"
    },
    {
        "name": "Mobile Whitelist 1 (mmaksim9191)",
        "filename": "sub_mmaksim.txt",
        "url": "https://raw.githubusercontent.com/mmaksim9191/my-vpn-configs/refs/heads/main/configs/mobile-whitelist-1.txt"
    }
]

def decode_if_base64(raw_text: str) -> str:
    clean = raw_text.strip()
    if any(proto in clean for proto in ("vless://", "vmess://", "trojan://", "ss://", "hysteria2://", "#profile-title")):
        return clean
    try:
        padded = clean + "=" * (-len(clean) % 4)
        decoded = base64.b64decode(padded).decode("utf-8")
        if any(proto in decoded for proto in ("vless://", "vmess://", "trojan://", "ss://", "hysteria2://")):
            return decoded.strip()
    except Exception:
        pass
    return clean

def fetch_and_format(sub: dict, now_msk: str) -> str:
    req = urllib.request.Request(sub["url"], headers={"User-Agent": "HappVPN-Sync/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw_data = resp.read().decode("utf-8", errors="replace")

    servers = decode_if_base64(raw_data)
    if not servers.strip():
        raise ValueError(f"Получен пустой список серверов для {sub['name']}")

    lines = [line for line in servers.splitlines() if not line.startswith(("#profile-title:", "#profile-update-interval:", "#announce:"))]
    clean_servers = "\n".join(lines).strip()

    header = (
        f"#profile-title: {sub['name']}\n"
        f"#profile-update-interval: 3\n"
        f"#announce: Синхронизировано: {now_msk} (МСК)\n\n"
    )
    return header + clean_servers + "\n"

def send_email(sub: dict, content: str, now_msk: str):
    gmail_user = os.environ["GMAIL_USER"]
    gmail_pass = os.environ["GMAIL_PASS"]

    msg = EmailMessage()
    msg["Subject"] = f"VPN Подписка: {sub['name']} [{now_msk}]"
    msg["From"] = gmail_user
    msg["To"] = gmail_user
    msg.set_content(
        f"Актуальная подписка: {sub['name']}\n"
        f"Время синхронизации: {now_msk} (МСК)\n\n"
        f"Скачайте прикрепленный файл {sub['filename']} и импортируйте его в приложение Happ VPN."
    )

    msg.add_attachment(
        content.encode("utf-8"),
        maintype="text",
        subtype="plain",
        filename=sub["filename"]
    )

    # Подключение через безопасный порт 587 с TLS
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(gmail_user, gmail_pass)
        smtp.send_message(msg)

def main():
    msk_tz = timezone(timedelta(hours=3))
    now_msk = datetime.now(msk_tz).strftime("%d.%m.%Y %H:%M")
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "queue":
        current_hour = datetime.now(timezone.utc).hour
        slot = current_hour // 3
        target_subs = [SUBSCRIPTIONS[slot % len(SUBSCRIPTIONS)]]
    else:
        target_subs = SUBSCRIPTIONS

    for sub in target_subs:
        print(f"Скачиваю {sub['name']}...")
        content = fetch_and_format(sub, now_msk)
        print(f"Отправляю письмо для {sub['name']}...")
        send_email(sub, content, now_msk)
        print(f"Успешно отправлено: {sub['name']}")

    with open("status.txt", "w", encoding="utf-8") as f:
        f.write(f"Last sync: {now_msk} MSK\n")

if __name__ == "__main__":
    main()
