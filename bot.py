import os
import sys
import requests
from bs4 import BeautifulSoup
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://www.leboncoin.fr/recherche?category=2&price=1000-5000&fuel=diesel&kilometers=0-190000&year=2010-&critics=2"

app = Flask(__name__)

seen_links = set()

proxy_url = "http://51.158.123.35:8811"  # Proxy HTTP gratuit (attention à l'instabilité)

proxies = {
    "http": proxy_url,
    "https": proxy_url,
}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        r = requests.post(url, json=data)
        if r.status_code == 200:
            print("📩 Message envoyé à Telegram.", file=sys.stderr)
        else:
            print(f"⚠️ Erreur envoi Telegram : {r.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Exception Telegram : {e}", file=sys.stderr)

def check_leboncoin_once():
    global seen_links
    print("🚀 Début de la vérification Leboncoin", file=sys.stderr)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://www.leboncoin.fr/",
            "Connection": "keep-alive",
        }
        res = requests.get(URL, headers=headers, proxies=proxies, timeout=10)
        print(f"📡 Statut de la requête : {res.status_code}", file=sys.stderr)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            ads = soup.select("a[data-qa-id='aditem_container']")
            print(f"🔗 Nombre de liens trouvés : {len(ads)}", file=sys.stderr)

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
                print("ℹ️ Pas de nouvelle annonce cette fois.", file=sys.stderr)
        else:
            print(f"⚠️ Erreur requête Leboncoin : {res.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Erreur scraping : {e}", file=sys.stderr)

    print("✅ Fin de la vérification Leboncoin\n", file=sys.stderr)
    return "✅ Vérification terminée."

@app.route('/')
def home():
    return "🤖 Bot Leboncoin en ligne."

@app.route('/check')
def check():
    return check_leboncoin_once()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
