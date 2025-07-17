import os
import time
import requests
from flask import Flask
from threading import Thread

app = Flask(__name__)

# === CONFIG ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INTERVAL = 300  # 5 minutes
SEEN_ADS = set()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

def fetch_ads():
    url = "https://api.leboncoin.fr/finder/search"
    payload = {
        "filters": {
            "category": {"id": 2},
            "enums": {
                "fuel": ["essence"],
                "critair": ["0", "1", "2"]
            },
            "ranges": {
                "price": {"min": 2000},
                "mileage": {"max": 190000},
                "regdate": {"min": 2010}
            },
            "location": {"zipcode": "69000", "radius": 50}
        },
        "limit": 20,
        "limit_alu": 3,
        "offset": 0,
        "owner_type": "all",
        "sort_by": "time"
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "LeboncoinBot/1.0"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("ads", [])
    else:
        print(f"⚠️ Erreur lors de la requête : {response.status_code}")
        return []

def check_new_ads():
    print("🔎 Vérification des annonces en cours... début")
    ads = fetch_ads()
    print(f"🔗 Annonces récupérées : {len(ads)}")
    new_count = 0
    for ad in ads:
        ad_id = ad.get("list_id")
        if ad_id not in SEEN_ADS:
            SEEN_ADS.add(ad_id)
            title = ad.get("subject")
            price = ad.get("price")
            url = f"https://www.leboncoin.fr/vi/{ad_id}.htm"
            city = ad.get("location", {}).get("city", "N/A")
            message = f"🚗 Nouvelle annonce : {title}\n📍 {city}\n💰 {price} €\n🔗 {url}"
            send_telegram(message)
            print(f"✅ Nouvelle annonce envoyée : {title}")
            new_count += 1
    if new_count == 0:
        print("ℹ️ Pas de nouvelle annonce cette fois.")
    print("🔎 Vérification des annonces en cours... fin\n")

def start_bot():
    print("🔄 Bot lancé...")
    while True:
        check_new_ads()
        print(f"⏳ Pause de {INTERVAL // 60} minutes...\n")
        time.sleep(INTERVAL)

@app.route("/")
def home():
    return "Bot Leboncoin actif."

# Lancer le bot dans un thread pour ne pas bloquer Flask
if __name__ == "__main__":
    Thread(target=start_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
