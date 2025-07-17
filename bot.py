import requests
import json
import os
import time

# 📦 Variables d’environnement à configurer sur Fly.io
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SEEN_FILE = "seen_ads.json"

def load_seen_ads():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return []

def save_seen_ads(seen_ads):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen_ads, f)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print("Erreur envoi Telegram:", response.text)

def search_leboncoin():
    url = "https://api.leboncoin.fr/finder/search"
    payload = {
        "filters": {
            "category": {"id": "2"},  # Voitures
            "location": {"zipcode": "69000", "radius": 50},
            "price": {"min": 500, "max": 5000},
            "enums": {
                "regdate": ["2010"],
                "critair": ["1", "2"]
            },
            "mileage": {"max": 190000},
            "keywords": {"text": "voiture", "type": "all"}
        },
        "limit": 30,
        "limit_alu": 0,
        "offset": 0
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "LeboncoinBot/1.0"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("ads", [])
        else:
            print("Erreur API Leboncoin:", response.status_code)
    except Exception as e:
        print("⚠️ Erreur de requête:", e)
    return []

def main_loop():
    print("🚗 Démarrage du bot Leboncoin...")
    seen_ads = load_seen_ads()

    while True:
        try:
            ads = search_leboncoin()
            new_ads = [ad for ad in ads if ad["id"] not in seen_ads]

            for ad in new_ads:
                title = ad.get("subject", "Annonce")
                price = ad.get("price", 0)
                link = f"https://www.leboncoin.fr/vi/{ad['id']}.htm"
                message = f"🚘 {title} - {price} €\n{link}"
                send_telegram_message(message)
                print("🔔 Nouvelle annonce envoyée :", title)
                seen_ads.append(ad["id"])

            if new_ads:
                save_seen_ads(seen_ads)

            time.sleep(180)  # 3 minutes
        except Exception as e:
            print("❌ Erreur dans la boucle :", e)
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
