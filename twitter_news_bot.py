# twitter_news_bot.py - Bot de Notícias Crypto do X (Twitter)
import os
import tweepy
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s"
)
logger = logging.getLogger(__name__)

# ================= CONFIGURAÇÃO =================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_FREE_GROUP_ID = os.getenv("TELEGRAM_FREE_GROUP_ID")

# Contas para monitorar (crypto influencers + projetos)
CRYPTO_ACCOUNTS = [
    "elonmusk",           # Elon Musk
    "VitalikButerin",     # Ethereum
    "cz_binance",         # Binance
    "APompliano",         # Anthony Pompliano
    "santimentfeed",      # Santiment
    "whale_alert",        # Whale Alert
    "glassnode",          # Glassnode
    "CoinDesk",           # CoinDesk
    "Cointelegraph",      # Cointelegraph
    "TheBlock__",         # The Block
]

# Palavras-chave para filtrar
KEYWORDS = ["BTC", "Bitcoin", "ETH", "Ethereum", "crypto", "altcoin", "trading"]

# Intervalo entre verificações (em minutos)
CHECK_INTERVAL = 15  # 15 minutos

# Cache de tweets já postados
posted_tweets = set()

# ================= CLIENTE X API =================
def create_client():
    """Cria cliente da API do X (Twitter) v2."""
    bearer_token = os.getenv("X_BEARER_TOKEN")
    
    if not bearer_token:
        logger.error("❌ X_BEARER_TOKEN não configurado no .env")
        return None
    
    return tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)

# ================= BUSCAR TWEETS =================
def fetch_latest_tweets(client, usernames, max_results=5):
    """Busca tweets recentes das contas especificadas."""
    all_tweets = []
    
    for username in usernames:
        try:
            # Pega user ID pelo username
            user = client.get_user(username=username)
            if not user.data:
                continue
            
            user_id = user.data.id
            
            # Busca tweets recentes
            tweets = client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=["created_at", "text", "public_metrics", "author_id"],
                exclude=["retweets", "replies"]
            )
            
            if tweets.data:
                for tweet in tweets.data:
                    # Filtra por palavras-chave
                    if any(keyword.lower() in tweet.text.lower() for keyword in KEYWORDS):
                        all_tweets.append({
                            "username": username,
                            "text": tweet.text,
                            "created_at": tweet.created_at,
                            "metrics": tweet.public_metrics,
                            "id": tweet.id
                        })
                        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar tweets de @{username}: {e}")
            time.sleep(2)  # Evita rate limit
    
    # Ordena por data (mais recente primeiro)
    all_tweets.sort(key=lambda x: x["created_at"], reverse=True)
    return all_tweets[:10]  # Retorna top 10

# ================= ENVIAR TELEGRAM =================
def send_telegram_message(message: str, parse_mode="HTML"):
    """Envia mensagem para o grupo Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_FREE_GROUP_ID:
        logger.warning("⚠️ Telegram não configurado. Mensagem:")
        logger.info(message)
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_FREE_GROUP_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("✅ Mensagem enviada no Telegram")
            return True
        else:
            logger.error(f"❌ Erro Telegram: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao enviar Telegram: {e}")
        return False

def format_tweet_message(tweet: dict) -> str:
    """Formata tweet para mensagem Telegram."""
    username = tweet["username"]
    text = tweet["text"]
    created = tweet["created_at"].strftime("%H:%M")
    likes = tweet["metrics"].get("like_count", 0)
    retweets = tweet["metrics"].get("retweet_count", 0)
    
    # Trunca texto se muito longo (Telegram tem limite de 4096 chars)
    if len(text) > 800:
        text = text[:800] + "..."
    
    # Substitui URLs longas por [...]
    import re
    text = re.sub(r'https?://\S+', '[link]', text)
    
    message = f"""
🐦 <b>@{username}</b> <i>({created})</i>

{text}

📊 <b>Engajamento:</b> {likes} 👍 | {retweets} 🔄
"""
    return message

# ================= LOOP PRINCIPAL =================
def run_news_bot():
    """Executa o bot de notícias."""
    logger.info("🟣 BOT DE NOTÍCIAS CRYPTO INICIADO")
    logger.info(f"📡 Monitorando {len(CRYPTO_ACCOUNTS)} contas")
    logger.info(f" Verificando a cada {CHECK_INTERVAL} minutos")
    
    client = create_client()
    if not client:
        logger.error("❌ Falha ao criar cliente X API. Verifique o X_BEARER_TOKEN.")
        return
    
    # Mensagem de boas-vindas
    send_telegram_message(
        "🚀 <b>Bot de Notícias Crypto Ativado!</b>\n\n"
        "📡 Monitorando influencers e fontes confiáveis...\n"
        "🔔 Você receberá notícias relevantes sobre BTC, ETH e mercado crypto."
    )
    
    try:
        while True:
            logger.info(f"🔄 Buscando tweets recentes... ({datetime.now().strftime('%H:%M:%S')})")
            
            tweets = fetch_latest_tweets(client, CRYPTO_ACCOUNTS)
            logger.info(f"📥 {len(tweets)} tweets relevantes encontrados")
            
            new_count = 0
            for tweet in tweets:
                tweet_id = tweet["id"]
                
                # Evita duplicatas
                if tweet_id in posted_tweets:
                    continue
                
                # Formata e envia
                message = format_tweet_message(tweet)
                if send_telegram_message(message):
                    posted_tweets.add(tweet_id)
                    new_count += 1
                    logger.info(f"✅ Tweet de @{tweet['username']} postado")
                
                time.sleep(1)  # Evita spam no Telegram
            
            logger.info(f"✨ {new_count} nova(s) notícia(s) enviada(s)")
            
            # Limpa cache antigo (mantém últimos 100)
            if len(posted_tweets) > 100:
                posted_tweets.clear()
            
            time.sleep(CHECK_INTERVAL * 60)  # Aguarda próximo ciclo
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.critical(f"💥 Erro fatal: {e}")
        logger.exception(e)

if __name__ == "__main__":
    run_news_bot()