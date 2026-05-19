import requests
import json
from datetime import datetime, timedelta

API_KEY = "105154551947396:efe6c9bf23a381fcd3a46d40006cf4fd"
BASE_URL = "https://api.manychat.com"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# כמה ימים ללא פעילות = לא פעיל
INACTIVE_DAYS = 180


def get_page_info():
    r = requests.get(f"{BASE_URL}/fb/page/getInfo", headers=HEADERS)
    return r.json()


def get_subscribers(limit=100, page=1):
    r = requests.get(
        f"{BASE_URL}/fb/subscriber/findByName",
        headers=HEADERS,
        params={"name": "", "page": page, "limit": limit}
    )
    return r.json()


def get_all_subscribers():
    all_subs = []
    page = 1
    while True:
        data = get_subscribers(limit=100, page=page)
        if data.get("status") != "success":
            break
        subs = data.get("data", [])
        if not subs:
            break
        all_subs.extend(subs)
        print(f"נטענו {len(all_subs)} אנשי קשר עד כה...")
        if len(subs) < 100:
            break
        page += 1
    return all_subs


def is_inactive(subscriber):
    last_interaction = subscriber.get("last_interaction")
    if not last_interaction:
        return True
    last_dt = datetime.fromisoformat(last_interaction.replace("Z", "+00:00"))
    cutoff = datetime.now(last_dt.tzinfo) - timedelta(days=INACTIVE_DAYS)
    return last_dt < cutoff


def delete_subscriber(subscriber_id):
    r = requests.post(
        f"{BASE_URL}/fb/subscriber/deleteContact",
        headers=HEADERS,
        json={"id": subscriber_id}
    )
    return r.json()


def main():
    print("=== ManyChat Cleanup Tool ===\n")

    # בדיקת חיבור
    print("מתחבר לחשבון...")
    info = get_page_info()
    if info.get("status") != "success":
        print(f"שגיאה: {info}")
        return
    print(f"חשבון: {info['data'].get('name', 'לא ידוע')}\n")

    # שליפת כל אנשי הקשר
    print("שולף אנשי קשר...")
    subscribers = get_all_subscribers()
    print(f"\nסה\"כ נמצאו: {len(subscribers)} אנשי קשר\n")

    # סינון לא פעילים
    inactive = [s for s in subscribers if is_inactive(s)]
    print(f"לא פעילים (מעל {INACTIVE_DAYS} יום): {len(inactive)}\n")

    if not inactive:
        print("אין אנשי קשר למחיקה!")
        return

    # הצגת הרשימה
    print("=== אנשי קשר שיימחקו ===")
    for s in inactive[:20]:  # מציג עד 20 ראשונים
        name = f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or "ללא שם"
        last = s.get("last_interaction", "אף פעם")
        print(f"  - {name} | אחרון: {last}")

    if len(inactive) > 20:
        print(f"  ... ועוד {len(inactive) - 20}")

    print(f"\nסה\"כ {len(inactive)} אנשי קשר יימחקו.")
    confirm = input("\nהאם למחוק? הקלד 'כן' לאישור: ").strip()

    if confirm != "כן":
        print("בוטל.")
        return

    # מחיקה
    print("\nמוחק...")
    deleted = 0
    errors = 0
    for s in inactive:
        result = delete_subscriber(s["id"])
        if result.get("status") == "success":
            deleted += 1
        else:
            errors += 1
        if deleted % 10 == 0:
            print(f"  נמחקו {deleted}...")

    print(f"\nהושלם! נמחקו: {deleted} | שגיאות: {errors}")


if __name__ == "__main__":
    main()
