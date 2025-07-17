import requests
import time
import threading
from flask import Flask
import os

print("🔄 Bot lancé...")

# Variables d'environnement (à définir sur Render)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
seen_ads = set()

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Token ou Chat ID manquant.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("❌ Erreur envoi Telegram :", e)

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

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("ads", [])
        else:
            print(f"⚠️ Erreur lors de la requête : {response.status_code}")
            return []
    except Exception as e:
        print("❌ Erreur lors de l'appel API Leboncoin :", e)
        return []

def check_new_ads():
    print("🔎 Vérification des annonces en cours...")
    ads = fetch_ads()
    print(f"🔗 Annonces récupérées : {len(ads)}")

    new_found = False
    for ad in ads:
        ad_id = ad.get("id")
        url = f"https://www.leboncoin.fr/voitures/{ad_id}.htm"
        if ad_id and ad_id not in seen_ads:
            seen_ads.add(ad_id)
            message = f"🚗 Nouvelle annonce détectée !\n{url}"
            send_telegram_message(message)
            print("✅ Nouvelle annonce :", url)
            new_found = True

    if not new_found:
        print("ℹ️ Pas de nouvelle annonce cette fois.")

def start_bot_loop():
    count = 0
    while True:
        try:
            count += 1
            print(f"\n⏰ Début vérification #{count}")
            check_new_ads()
            print(f"✔️ Vérification #{count} terminée.")
        except Exception as e:
            print("❌ Erreur dans la boucle :", e)
        print("⏳ Pause de 5 minutes...\n")
        time.sleep(300)

# Lancer la vérification en thread
threading.Thread(target=start_bot_loop).start()

# Flask pour l'hébergement web sur Render
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot Leboncoin avec API en ligne et opérationnel."

app.run(host='0.0.0.0', port=10000)
