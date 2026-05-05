# rss_news_bot.py - Bot de Notícias Crypto via RSS (Com Cache VIP)
import os
import json
import feedparser
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_FREE_GROUP_ID = os.getenv("TELEGRAM_FREE_GROUP_ID")

# Configuração de Cache
NEWS_CACHE_FILE = "news_cache.json"

RSS_FEEDS = [
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
    {"name": "Decrypt", "url": "https://decrypt.co/feed"},
]

CHECK_INTERVAL = 10 * 60  # 10 minutos
posted_links = set()

def save_news_to_cache(news_list):
    """Salva as últimas 10 notícias para o Dashboard VIP ler."""
    try:
        with open(NEWS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(news_list[:10], f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Cache de notícias salvo ({len(news_list)} itens)")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar cache: {e}")

def send_telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_FREE_GROUP_ID:
        logger.warning("⚠️ Telegram não configurado")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_FREE_GROUP_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=10)
    except Exception as e:
        logger.error(f"❌ Telegram: {e}")

def fetch_latest_news():
    news = []
    for feed in RSS_FEEDS:
        try:
            d = feedparser.parse(feed["url"])
            for entry in d.entries[:3]:
                if entry.link not in posted_links:
                    title = entry.get("title", "Sem título")
                    if any(kw in title.upper() for kw in ["BTC", "ETH", "CRYPTO", "BITCOIN", "ETHEREUM", "TRADING"]):
                        news.append({"source": feed["name"], "title": title, "link": entry.link, "date": entry.get("published", "")})
                        posted_links.add(entry.link)
        except Exception as e:
            logger.error(f"❌ Erro RSS {feed['name']}: {e}")
    return news

def run():
    logger.info("🟣 BOT DE NOTÍCIAS CRYPTO (RSS) INICIADO")
    send_telegram("🚀 <b>Bot de Notícias Crypto Ativado!</b>\n📡 Monitorando CoinDesk, Cointelegraph e Decrypt...\n🔔 Você receberá as principais notícias do mercado.")
    
    try:
        while True:
            items = fetch_latest_news()
            if items:
                for item in items:
                    msg = f"📰 <b>{item['source']}</b>\n\n{item['title']}\n\n🔗 {item['link']}"
                    send_telegram(msg)
                    time.sleep(2)
                logger.info(f"✨ {len(items)} notícia(s) enviada(s)")
                
                # ✅ SALVA CACHE PARA O DASHBOARD VIP
                save_news_to_cache(items)
            else:
                logger.info("💤 Nenhuma notícia nova no momento")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("🛑 Bot parado pelo usuário")

if __name__ == "__main__":
    run()