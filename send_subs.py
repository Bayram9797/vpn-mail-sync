import os
import base64
import urllib.request
from datetime import datetime, timezone, timedelta

# 👇 СПИСОК ВСЕХ ВАШИХ ПОДПИСОК 👇
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
    },
    {
        "name": "VlessForU Working Configs",
        "filename": "sub_vlessforu.txt",
        "url": "https://sub.vlessfo.ru/vlessforu/working_configs.txt"
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

def main():
    msk_tz = timezone(timedelta(hours=3))
    now_msk = datetime.now(msk_tz).strftime("%d.%m.%Y %H:%M")
    
    os.makedirs("subs", exist_ok=True)
    
    for sub in SUBSCRIPTIONS:
        print(f"Скачиваю {sub['name']}...")
        try:
            req = urllib.request.Request(sub["url"], headers={"User-Agent": "HappVPN-Sync/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw_data = resp.read().decode("utf-8", errors="replace")

            servers = decode_if_base64(raw_data)
            if not servers.strip():
                print(f"⚠️ Пропуск {sub['name']}: пустой список серверов")
                continue

            lines = [line for line in servers.splitlines() if not line.startswith(("#profile-title:", "#profile-update-interval:", "#announce:"))]
            clean_servers = "\n".join(lines).strip()

            header = (
                f"#profile-title: {sub['name']}\n"
                f"#profile-update-interval: 3\n"
                f"#announce: Синхронизировано: {now_msk} (МСК)\n\n"
            )
            final_content = header + clean_servers + "\n"

            filepath = os.path.join("subs", sub["filename"])
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(final_content)
            print(f"✅ Файл {sub['filename']} успешно сохранен.")
        except Exception as e:
            print(f"❌ Ошибка при скачивании {sub['name']}: {e}")

    with open("status.txt", "w", encoding="utf-8") as f:
        f.write(f"Last sync: {now_msk} MSK\n")

if __name__ == "__main__":
    main()
