import requests
from bs4 import BeautifulSoup
import time

# CONFIGURATION
URL = "https://www.leboncoin.fr/recherche?category=2&regions=22&fuel=1&price=0-2000&year=2010-&mileage=0-190000"
TELEGRAM_BOT_TOKEN = "7673698272:AAHr2EPeTX7t24ZEAVhaoqYTS4y6gzRAgr4"
TELEGRAM_CHAT_ID = "6768525534"
seen_ads = set()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

def check_new_ads():
    headers = {"User-Agent": "Mozilla/5.0"}
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

# BOUCLE PRINCIPALE (toutes les 5 minutes)
while True:
    try:
        check_new_ads()
        time.sleep(300)  # 5 minutes
    except Exception as e:
        print("Erreur :", e)
        time.sleep(60)
