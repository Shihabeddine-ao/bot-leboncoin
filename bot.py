import os
import time
import requests

# Configuration
# URL API interne Leboncoin (exemple avec recherche voitures d'occasion diesel en Auvergne-Rhône-Alpes)
LEBONCOIN_API_URL = "https://api.leboncoin.fr/finder/search"

# Paramètres de recherche (modifie selon besoin)
SEARCH_PAYLOAD = {
    "limit": 20,
    "filters": {
        "category": {"id": 2},  # voiture
        "price": {"min": 1000, "max": 5000},
        "fuel": {"value": "diesel"},
        "year": {"min": 2010},
        "mileage": {"max": 190000},
        "regions": ["auvergne-rhone-alpes"],
        "criterias": {"crit_air": {"min": 2}}
    },
    "search_id": "",  # facultatif
}

# Headers HTTP (User-Agent + Content-Type JSON)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
}

# Token et chat_id Telegram depuis variables d'environnement
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("❌ Erreur: variables TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID non définies.")
    exit(1)

# Stockage des annonces déjà envoyées (id)
seen_ads = set()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": True}
    try:
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            print("✅ Message Telegram envoyé.")
        else:
            print(f"⚠️ Erreur Telegram : {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"❌ Exception Telegram : {e}")

def fetch_leboncoin_ads():
    try:
        resp = requests.post(LEBONCOIN_API_URL, json=SEARCH_PAYLOAD, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ API Leboncoin erreur : {resp.status_code}")
            return []
        data = resp.json()
        ads = data.get("ads") or data.get("items") or []
        return ads
    except Exception as e:
        print(f"❌ Exception API Leboncoin : {e}")
        return []

def check_new_ads():
    print("🔎 Vérification des annonces en cours...")
    ads = fetch_leboncoin_ads()
    print(f"🔗 {len(ads)} annonces récupérées.")

    new_ads = []
    for ad in ads:
        ad_id = ad.get("id") or ad.get("advertisement_id")
        if ad_id and ad_id not in seen_ads:
            new_ads.append(ad)
            seen_ads.add(ad_id)

    if not new_ads:
        print("ℹ️ Pas de nouvelle annonce détectée.")
        return

    for ad in new_ads:
        title = ad.get("subject") or ad.get("title") or "Sans titre"
        price = ad.get("price") or "Prix non indiqué"
        url = f"https://www.leboncoin.fr/voitures/{ad.get('id')}.htm"
        message = f"🚗 Nouvelle annonce : {title}\nPrix : {price} €\n{url}"
        print(message)
        send_telegram_message(message)

if __name__ == "__main__":
    print("🔄 Bot Leboncoin Telegram lancé...")

    while True:
        check_new_ads()
        print("⏳ Pause 5 minutes...\n")
        time.sleep(300)  # 5 minutes
