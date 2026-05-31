import requests
import schedule
import time
import json
from datetime import datetime

# ============================================================
BOT_TOKEN = "8742902326:AAGleHwcDM8N8eud3Uv4IBw_lmuV1bJe5SA"
CHAT_ID   = "6571435266"
CHECK_EVERY_MINUTES = 5
# ============================================================

VFS_URL = "https://lift-api.vfsvisaonline.com/api/AppointmentManagement/GetCurrentAppointmentSlotsByCategory"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.vfsvisaonline.com",
    "Referer": "https://www.vfsvisaonline.com/",
}

PAYLOAD = {
    "countryCode": "dza",
    "missionCode": "ita",
    "centerCode": "ALGIERS-ITA",
    "categoryCode": "TOURISM",
    "applicantCount": 1
}

last_status = None


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    # جرب بدون proxy أولاً
    try:
        response = requests.post(url, json=data, timeout=15)
        if response.status_code == 200:
            print(f"[{now()}] ✅ Telegram message sent")
            return True
    except Exception as e:
        print(f"[{now()}] ⚠️ Direct failed: {e}")

    # جرب مع proxy مجاني
    proxies_list = [
        "socks5://proxy.torproject.org:9050",
        "http://51.158.68.68:8811",
        "http://51.77.141.29:3128",
    ]
    for proxy in proxies_list:
        try:
            response = requests.post(
                url, json=data, timeout=15,
                proxies={"http": proxy, "https": proxy}
            )
            if response.status_code == 200:
                print(f"[{now()}] ✅ Sent via proxy: {proxy}")
                return True
        except Exception as e:
            print(f"[{now()}] ❌ Proxy {proxy} failed: {e}")
            continue

    print(f"[{now()}] ❌ All methods failed")
    return False


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def check_slots():
    global last_status
    print(f"[{now()}] 🔍 Checking VFS Italy slots...")

    try:
        response = requests.post(
            VFS_URL,
            headers=HEADERS,
            json=PAYLOAD,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            slots_available = False
            slot_info = ""

            if isinstance(data, list) and len(data) > 0:
                slots_available = True
                slot_info = f"عدد المواعيد المتاحة: <b>{len(data)}</b>\n"
                for slot in data[:5]:
                    date = slot.get("appointmentDate", "غير معروف")
                    slot_info += f"📅 {date}\n"

            elif isinstance(data, dict):
                available = data.get("availableSlots", data.get("slots", []))
                if available and len(available) > 0:
                    slots_available = True
                    slot_info = f"عدد المواعيد: <b>{len(available)}</b>"

            if slots_available and last_status != "available":
                last_status = "available"
                message = (
                    "🚨 <b>تنبيه VFS Italy!</b>\n\n"
                    "✅ <b>مواعيد متاحة الآن!</b>\n\n"
                    f"{slot_info}\n"
                    "🔗 احجز الآن:\n"
                    "https://www.vfsvisaonline.com/Italy-Algeria\n\n"
                    f"⏰ {now()}"
                )
                send_telegram(message)

            elif not slots_available and last_status != "none":
                last_status = "none"
                print(f"[{now()}] ❌ No slots available yet.")

        else:
            print(f"[{now()}] ⚠️ HTTP {response.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"[{now()}] ❌ Connection error - VFS blocked")
    except requests.exceptions.Timeout:
        print(f"[{now()}] ⏱️ Timeout")
    except json.JSONDecodeError:
        print(f"[{now()}] ⚠️ Invalid JSON")
    except Exception as e:
        print(f"[{now()}] ❌ Error: {e}")


def main():
    print("=" * 50)
    print("   VFS Italy Slot Checker — Dia")
    print(f"   يتحقق كل {CHECK_EVERY_MINUTES} دقائق")
    print("=" * 50)

    send_telegram(
        "✅ <b>البوت يعمل الآن!</b>\n\n"
        f"🔍 يتحقق كل <b>{CHECK_EVERY_MINUTES} دقائق</b>\n"
        "📍 VFS Italy - الجزائر - سياحة\n\n"
        "سأرسل لك إشعاراً فور ظهور موعد متاح 🎯"
    )

    check_slots()
    schedule.every(CHECK_EVERY_MINUTES).minutes.do(check_slots)

    print(f"\n[{now()}] ⏳ Running... Press Ctrl+C to stop\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
