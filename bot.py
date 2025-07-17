import os
import time
import threading
import requests
from flask import Flask
import sys

app = Flask(__name__)

LEBONCOIN_API_URL = "https://api.leboncoin.fr/finder/search"

SEARCH_PAYLOAD = {
    "limit": 20,
    "filters": {
        "category": {"id": 2},
        "price": {"min": 1000, "max": 5000},
        "fuel": {"value": "diesel"},
        "year": {"min": 2010},
        "mileage": {"max": 190000},
        "regions": ["auvergne-rhone-alpes"],
        "criterias": {"crit_air": {"min": 2}}
    }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://www.leboncoin.fr",
    "Referer": "https://www.leboncoin.fr/",
}


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Erreur: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID non définis.")
    sys.stdout.flush()
    exit(1)

seen_ads = set()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": True}
    try:
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            print("✅ Message Telegram envoyé.")
        else:
            print(f"⚠️ Erreur Telegram: {resp.status_code} {resp.text}")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ Exception lors de l'envoi Telegram: {e}")
        sys.stdout.flush()

def fetch_leboncoin_ads():
    try:
        resp = requests.post(LEBONCOIN_API_URL, json=SEARCH_PAYLOAD, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ Erreur API Leboncoin: {resp.status_code}")
            sys.stdout.flush()
            return []
        data = resp.json()
        ads = data.get("ads") or data.get("items") or []
        return ads
    except Exception as e:
        print(f"❌ Exception API Leboncoin: {e}")
        sys.stdout.flush()
        return []

def check_new_ads():
    print("🔎 Vérification des annonces en cours... début")
    print("📡 Envoi requête POST sur l’API Leboncoin...")
    sys.stdout.flush()

    ads = fetch_leboncoin_ads()
    print(f"✅ Requête OK, annonces récupérées : {len(ads)}")
    sys.stdout.flush()

    new_ads = []
    for ad in ads:
        ad_id = ad.get("id") or ad.get("advertisement_id")
        if ad_id and ad_id not in seen_ads:
            new_ads.append(ad)
            seen_ads.add(ad_id)

    if not new_ads:
        print("ℹ️ Pas de nouvelle annonce cette fois.")
    else:
        for ad in new_ads:
            title = ad.get("subject") or ad.get("title") or "Sans titre"
            price = ad.get("price") or "Prix non indiqué"
            url = f"https://www.leboncoin.fr/voitures/{ad.get('id')}.htm"
            print(f"🚗 Nouvelle annonce : {title} - Prix : {price} €\n{url}")
            send_telegram_message(f"🚗 Nouvelle annonce : {title}\nPrix : {price} €\n{url}")
    print("🔎 Vérification des annonces en cours... fin\n")
    sys.stdout.flush()

def background_task():
    # Petite attente pour éviter de démarrer la vérification trop vite au lancement
    time.sleep(5)
    while True:
        check_new_ads()
        print("⏳ Pause de 5 minutes avant la prochaine vérification...\n")
        sys.stdout.flush()
        time.sleep(300)  # 5 minutes

@app.route("/")
def home():
    return "Bot Leboncoin Telegram est en ligne !"

if __name__ == "__main__":
    thread = threading.Thread(target=background_task)
    thread.daemon = True
    thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
