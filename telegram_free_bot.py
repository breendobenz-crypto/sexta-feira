# telegram_free_bot.py - BOT PARA GRUPO FREE (NEWS, IA, DICAS, POLLS)
import os
import sys
import time
import logging
import requests
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import tweepy

load_dotenv()

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler("telegram_free_bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURAÇÕES
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_FREE_GROUP_ID = os.getenv("TELEGRAM_FREE_GROUP_ID")

# Twitter API (opcional - se tiver acesso)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# OKX API (pública para dados de mercado)
OKX_BASE_URL = "https://www.okx.com"

# Intervalos (em horas)
NEWS_INTERVAL = 4          # Notícias a cada 4h
DAILY_BRIEFING_HOUR = 9    # Resumo diário às 09:00
WEEKLY_TRADE_DAY = "friday" # Trade da semana na sexta
TIP_INTERVAL = 6           # Dicas a cada 6h

# Contas do Twitter para monitorar (Crypto influencers)
TWITTER_ACCOUNTS = [
    "elonmusk", "VitalikButerin", "cz_binance", "APompliano",
    "santimentfeed", "whale_alert", "glassnode"
]

# Banco de dicas educativas
EDUCATIONAL_TIPS = [
    {
        "category": "Risk Management",
        "tip": "Nunca arrisque mais de 1-2% do seu capital por trade. Sobreviver é mais importante que ganhar.",
        "hashtag": "#RiskManagement"
    },
    {
        "category": "Psychology",
        "tip": "FOMO (Fear Of Missing Out) é o maior inimigo do trader. Espere o setup, não corra atrás do preço.",
        "hashtag": "#TradingPsychology"
    },
    {
        "category": "Technical Analysis",
        "tip": "Médias móveis são suportes/resistências dinâmicas. EMA9, EMA21 e EMA50 são as mais usadas por institucionais.",
        "hashtag": "#TechnicalAnalysis"
    },
    {
        "category": "Strategy",
        "tip": "Tendência é sua amiga até que termine. Não tente adivinhar topos e fundos — opere a favor da tendência.",
        "hashtag": "#TrendFollowing"
    },
    {
        "category": "Money Management",
        "tip": "Sempre use Stop Loss. Não é sobre estar certo, é sobre proteger seu capital quando estiver errado.",
        "hashtag": "#StopLoss"
    },
    {
        "category": "Market Structure",
        "tip": "Suporte vira resistência e resistência vira suporte. Isso é básico mas 90% dos traders esquecem.",
        "hashtag": "#SupportResistance"
    },
    {
        "category": "Indicators",
        "tip": "RSI acima de 70 = sobrecomprado. RSI abaixo de 30 = sobrevendido. Mas em tendência forte, pode ficar sobrecomprado/vendido por muito tempo.",
        "hashtag": "#RSI"
    },
    {
        "category": "Volume",
        "tip": "Preço sem volume é armadilha. Sempre confirme rompimentos com aumento de volume.",
        "hashtag": "#VolumeAnalysis"
    },
    {
        "category": "Patience",
        "tip": "O melhor trade é aquele que você não faz. Paciência é a virtude mais lucrativa no trading.",
        "hashtag": "#TradingTips"
    },
    {
        "category": "Backtesting",
        "tip": "Nunca opere uma estratégia sem testar. Backtest é o laboratório do trader — teste antes de arriscar dinheiro real.",
        "hashtag": "#Backtesting"
    }
]

# ==========================================
# FUNÇÕES DE ENVIO TELEGRAM
# ==========================================
def send_telegram_message(text: str, parse_mode: str = "Markdown"):
    """Envia mensagem para o grupo free."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_FREE_GROUP_ID:
        logger.warning("⚠️ Telegram não configurado. Mensagem ignorada.")
        logger.debug(f"Mensagem: {text[:100]}...")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_FREE_GROUP_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("✅ Mensagem enviada no Telegram")
            return True
        else:
            logger.error(f"❌ Erro Telegram API: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Falha ao enviar mensagem: {e}")
        return False

def send_poll(question: str, options: list, is_anonymous: bool = False):
    """Envia enquete para o grupo."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_FREE_GROUP_ID:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": TELEGRAM_FREE_GROUP_ID,
        "question": question,
        "options": options,
        "is_anonymous": is_anonymous,
        "type": "regular"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("✅ Poll enviada no Telegram")
            return True
        else:
            logger.error(f"❌ Erro ao enviar poll: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Falha ao enviar poll: {e}")
        return False

# ==========================================
# NOTÍCIAS DO TWITTER/X
# ==========================================
def fetch_twitter_news():
    """Busca tweets recentes das contas monitoradas."""
    if not TWITTER_BEARER_TOKEN:
        logger.warning("⚠️ Twitter API não configurada. Pulando notícias.")
        return []
    
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
    all_tweets = []
    
    for account in TWITTER_ACCOUNTS[:3]:  # Limita a 3 contas para não spammar
        try:
            query = f"from:{account} -is:retweet -is:reply (crypto OR bitcoin OR BTC OR ethereum OR ETH OR trading)"
            tweets = client.search_recent_tweets(
                query=query,
                tweet_fields=["created_at", "text", "author_id", "public_metrics"],
                max_results=2
            )
            
            if tweets.data:
                all_tweets.extend(tweets.data)
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar tweets de {account}: {e}")
            continue
    
    # Ordena por data
    all_tweets.sort(key=lambda x: x.created_at, reverse=True)
    return all_tweets[:3]  # Retorna apenas os 3 mais recentes

def format_twitter_news(tweets):
    """Formata tweets para mensagem Telegram."""
    if not tweets:
        return None
    
    msg = "🐦 *CRYPTO NEWS — TWITTER*\n\n"
    
    for tweet in tweets:
        # Trunca texto se for muito longo
        text = tweet.text[:200] + "..." if len(tweet.text) > 200 else tweet.text
        # Remove URLs
        text = text.replace("https://t.co/", "")
        
        msg += f"📌 {text}\n"
        msg += f"🔗 [Ver tweet](https://twitter.com/i/web/status/{tweet.id})\n\n"
    
    msg += f"⏰ {datetime.now().strftime('%H:%M')}"
    
    return msg

# ==========================================
# RESUMO DIÁRIO DE MERCADO (OKX)
# ==========================================
def fetch_market_data():
    """Busca dados de mercado da OKX."""
    assets = ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP", "PAXG-USDT-SWAP"]
    market_data = {}
    
    for inst in assets:
        try:
            r = requests.get(f"{OKX_BASE_URL}/api/v5/market/ticker?instId={inst}", timeout=5)
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data:
                    d = data[0]
                    symbol = inst.split("-")[0]
                    market_data[symbol] = {
                        "price": float(d.get("last", 0)),
                        "change_24h": float(d.get("sodUtc8", 0)),
                        "high_24h": float(d.get("high24h", 0)),
                        "low_24h": float(d.get("low24h", 0)),
                        "volume_24h": float(d.get("vol24h", 0))
                    }
        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados de {inst}: {e}")
            continue
    
    return market_data

def generate_daily_briefing(market_data):
    """Gera resumo diário com análise de mercado."""
    if not market_data:
        return None
    
    msg = "🌅 *SEXTA-FEIRA MARKET BRIEFING*\n"
    msg += f"📅 {datetime.now().strftime('%d/%m/%Y')}\n\n"
    
    # Preços e variações
    msg += "*MERCADO SPOT:*\n"
    for symbol, data in market_data.items():
        change = data["change_24h"]
        change_str = f"{change:+.2f}%"
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        
        msg += f"{emoji} *{symbol}:* ${data['price']:,.2f} ({change_str})\n"
    
    # Análise simplificada de tendência
    btc_change = market_data.get("BTC", {}).get("change_24h", 0)
    eth_change = market_data.get("ETH", {}).get("change_24h", 0)
    
    msg += "\n*ANÁLISE DE TENDÊNCIA:*\n"
    if btc_change > 2 and eth_change > 2:
        msg += "🟢 *BULLISH* — Mercado em alta forte\n"
        msg += "💡 *Viés do Dia:* Long (compra)\n"
        risk = "Médio"
    elif btc_change < -2 and eth_change < -2:
        msg += "🔴 *BEARISH* — Mercado em baixa forte\n"
        msg += "💡 *Viés do Dia:* Short (venda)\n"
        risk = "Alto"
    else:
        msg += "🟡 *SIDEWAYS* — Mercado lateral/consolidação\n"
        msg += "💡 *Viés do Dia:* Aguardar rompimento\n"
        risk = "Baixo"
    
    msg += f"\n⚠️ *Nível de Risco:* {risk}\n"
    
    # Insight educacional aleatório
    tip = random.choice(EDUCATIONAL_TIPS)
    msg += f"\n💡 *DICA RÁPIDA:*\n{tip['tip']}\n"
    
    msg += f"\n🔗 *Quer operar assim automaticamente?*\n"
    msg += "👉 Seja VIP: https://whop.com/sexta-feira-advanced\n"
    
    msg += f"\n⏰ {datetime.now().strftime('%H:%M')}"
    
    return msg

# ==========================================
# TRADE OF THE WEEK
# ==========================================
def generate_weekly_trade(market_data):
    """Gera preview do trade da semana (simulado/educativo)."""
    if not market_data or "BTC" not in market_data:
        return None
    
    btc_price = market_data["BTC"]["price"]
    
    # Simula um setup educacional (NÃO É SINAL REAL)
    entry = btc_price
    stop = entry * 0.97  # 3% abaixo
    take = entry * 1.06  # 6% acima
    
    msg = "🏆 *TRADE DA SEMANA* (EDUCATIVO)\n\n"
    msg += f"📊 *Ativo:* BTC/USDT\n"
    msg += f" *Direção:* LONG (compra)\n\n"
    
    msg += "*SETUP:*\n"
    msg += f"🎯 *Entrada:* ${entry:,.2f}\n"
    msg += f"🛑 *Stop Loss:* ${stop:,.2f} (-3%)\n"
    msg += f"✅ *Take Profit:* ${take:,.2f} (+6%)\n"
    msg += f"📐 *Risco/Retorno:* 1:2\n\n"
    
    msg += "*RAZÃO TÉCNICA:*\n"
    msg += "🧠 'BTC testando suporte em $XX.XXX com volume crescente. RSI saindo de sobrevenda. Setup de reversão com bom R/R.'\n\n"
    
    msg += "⚠️ *Aviso:* Este é um exemplo educativo. Não é recomendação de investimento.\n\n"
    
    msg += "🔗 *Quer receber sinais em tempo real?*\n"
    msg += "👉 Seja VIP: https://whop.com/sexta-feira-advanced\n"
    
    msg += f"\n⏰ {datetime.now().strftime('%H:%M')}"
    
    return msg

# ==========================================
# DICAS EDUCATIVAS
# ==========================================
def send_educational_tip():
    """Envia dica educativa aleatória."""
    tip = random.choice(EDUCATIONAL_TIPS)
    
    msg = f"🧠 *DICA RÁPIDA #{random.randint(1, 999)}*\n\n"
    msg += f"📚 *{tip['category']}:*\n"
    msg += f"{tip['tip']}\n\n"
    msg += f"{tip['hashtag']}\n\n"
    
    msg += "💡 *Quer aprender mais?*\n"
    msg += "👉 Conheça o SEXTA-FEIRA ADVANCED\n"
    msg += "https://whop.com/sexta-feira-advanced"
    
    return send_telegram_message(msg)

# ==========================================
# POLLS DE ENGAJAMENTO
# ==========================================
def send_daily_poll():
    """Envia poll de engajamento diário."""
    polls = [
        {
            "question": "🗳️ Qual seu viés para BTC nas próximas 24h?",
            "options": ["🟢 Long (subida)", "🔴 Short (queda)", "🟡 Lateral (consolidação)"]
        },
        {
            "question": "📊 Qual ativo você está operando mais?",
            "options": ["BTC", "ETH", "SOL", "Outros"]
        },
        {
            "question": "💰 Qual seu % máximo de risco por trade?",
            "options": ["0.5-1%", "1-2%", "2-5%", "+5% (arriscado)"]
        },
        {
            "question": "📈 Você prefere operar:",
            "options": ["Scalping (minutos)", "Day Trade (horas)", "Swing Trade (dias)", "Position (semanas)"]
        }
    ]
    
    poll = random.choice(polls)
    return send_poll(poll["question"], poll["options"])

# ==========================================
# LOOP PRINCIPAL
# ==========================================
def main():
    logger.info("🤖 BOT GRUPO FREE — INICIADO")
    logger.info(f"📱 Grupo: {TELEGRAM_FREE_GROUP_ID}")
    logger.info(f"🐦 Twitter API: {'Configurada' if TWITTER_BEARER_TOKEN else 'Não configurada'}")
    
    last_news = None
    last_briefing = None
    last_tip = None
    last_poll = None
    
    try:
        while True:
            now = datetime.now()
            
            # 1. Notícias do Twitter (a cada 4h)
            if not last_news or (now - last_news).total_seconds() >= NEWS_INTERVAL * 3600:
                logger.info("📰 Buscando notícias do Twitter...")
                tweets = fetch_twitter_news()
                if tweets:
                    msg = format_twitter_news(tweets)
                    if msg:
                        send_telegram_message(msg)
                last_news = now
            
            # 2. Resumo Diário (09:00)
            if not last_briefing or (now.date() > last_briefing.date() and now.hour == DAILY_BRIEFING_HOUR):
                logger.info("🌅 Gerando resumo diário...")
                market_data = fetch_market_data()
                msg = generate_daily_briefing(market_data)
                if msg:
                    send_telegram_message(msg)
                last_briefing = now
            
            # 3. Trade da Semana (Sexta-feira)
            if now.strftime("%A").lower() == WEEKLY_TRADE_DAY and (not last_briefing or (now - last_briefing).total_seconds() > 86400):
                logger.info("🏆 Gerando trade da semana...")
                market_data = fetch_market_data()
                msg = generate_weekly_trade(market_data)
                if msg:
                    send_telegram_message(msg)
            
            # 4. Dicas Educativas (a cada 6h)
            if not last_tip or (now - last_tip).total_seconds() >= TIP_INTERVAL * 3600:
                logger.info("🧠 Enviando dica educativa...")
                send_educational_tip()
                last_tip = now
            
            # 5. Poll de Engajamento (uma vez por dia, horário aleatório)
            if not last_poll or (now.date() > last_poll.date()):
                if random.random() < 0.3:  # 30% de chance de enviar poll
                    logger.info("🗳️ Enviando poll...")
                    send_daily_poll()
                    last_poll = now
            
            # Aguarda 15 minutos antes da próxima verificação
            time.sleep(900)
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.critical(f"💥 Erro fatal no bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()