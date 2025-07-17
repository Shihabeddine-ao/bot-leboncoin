import requests
from bs4 import BeautifulSoup
import time
from flask import Flask
import threading
import os

print("🔄 Bot lancé...")  # Affichage au démarrage

# CONFIGURATION (valeurs à lire depuis les variables d’environnement)
URL = "https://www.leboncoin.fr/recherche?category=2&regions=22&fuel=1&price=0-2000&year=2010-&mileage=0-190000"
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
        print("Erreur envoi Telegram :", e)

def check_new_ads():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(URL, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)

        for link in links:
            href = link['href']
            if "/voitures/" in href and href not in seen_ads:
                seen_ads.add(href)
                full_link = "https://www.leboncoin.fr" + href
                send_telegram_message(f"🚗 Nouvelle annonce repérée :\n{full_link}")
                print("✅ Nouvelle annonce :", full_link)
    except Exception as e:
        print("Erreur analyse page :", e)

# Boucle dans un thread
def start_bot_loop():
    while True:
        check_new_ads()
        time.sleep(300)  # 5 minutes

threading.Thread(target=start_bot_loop).start()

# Serveur Flask factice pour Render
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot Leboncoin actif !"

app.run(host='0.0.0.0', port=10000)
