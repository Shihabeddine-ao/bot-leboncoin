import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

# Infos Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# URL Leboncoin (ex. filtrée avec tes critères)
URL = "https://www.leboncoin.fr/recherche?category=2&price=1000-5000&fuel=diesel&kilometers=0-190000&year=2010-&critics=2"

# Pour garder en mémoire les annonces déjà vues
seen_links = set()

# Flask pour Render
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot Leboncoin en ligne."

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        r = requests.post(url, json=data)
        if r.status_code == 200:
            print("📩 Message envoyé à Telegram.")
        else:
            print(f"⚠️ Erreur envoi Telegram : {r.status_code}")
    except Exception as e:
        print(f"⚠️ Exception Telegram : {e}")

def check_leboncoin():
    global seen_links
    while True:
        print("🔎 Vérification des annonces en cours... début")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            res = requests.get(URL, headers=headers)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                ads = soup.select("a[data-qa-id='aditem_container']")
                print(f"🔗 Nombre de liens trouvés : {len(ads)}")

                new_ads = []
                for ad in ads:
                    link = "https://www.leboncoin.fr" + ad["href"]
                    if link not in seen_links:
                        seen_links.add(link)
                        new_ads.append(link)

                if new_ads:
                    for link in new_ads:
                        send_telegram(f"🚗 Nouvelle annonce : {link}")
                else:
                    print("ℹ️ Pas de nouvelle annonce cette fois.")
            else:
                print(f"⚠️ Erreur requête Leboncoin : {res.status_code}")
        except Exception as e:
            print(f"⚠️ Erreur scraping : {e}")

        print("🔎 Vérification des annonces en cours... fin\n")
        print("⏳ Pause de 5 minutes avant la prochaine vérification...\n")
        time.sleep(300)

def start_thread():
    t = threading.Thread(target=check_leboncoin)
    t.daemon = True
    t.start()

# Important : tout doit être dans ce bloc
if __name__ == '__main__':
    start_thread()
    app.run(host="0.0.0.0", port=10000)
