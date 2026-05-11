# telegram_free_bot.py - BOT PARA GRUPO FREE (DADOS OKX + DICAS + POLLS)
import os
import sys
import time
import logging
import requests
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler("telegram_free_bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)  # ✅ Corrigido: __name__

# ==========================================
# CONFIGURAÇÕES
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_FREE_GROUP_ID = os.getenv("TELEGRAM_FREE_GROUP_ID")

# OKX API (pública para dados de mercado - GRÁTIS)
OKX_BASE_URL = "https://www.okx.com"

# Link VIP (Whop)
VIP_LINK = "https://whop.com/sexta-feira-advanced/sexta-feira-advanced-19/"

# Intervalos (em horas)
MARKET_BRIEFING_HOUR = 9       # Resumo diário às 09:00
TIP_INTERVAL = 6               # Dicas a cada 6h
WEEKLY_TRADE_DAY = "friday"    # Trade da semana na sexta

# Banco de dicas educativas
EDUCATIONAL_TIPS = [
    {"category": "Risk Management", "tip": "Nunca arrisque mais de 1-2% do seu capital por trade. Sobreviver é mais importante que ganhar.", "hashtag": "#RiskManagement"},
    {"category": "Psychology", "tip": "FOMO (Fear Of Missing Out) é o maior inimigo do trader. Espere o setup, não corra atrás do preço.", "hashtag": "#TradingPsychology"},
    {"category": "Technical Analysis", "tip": "Médias móveis são suportes/resistências dinâmicos. EMA9, EMA21 e EMA50 são as mais usadas.", "hashtag": "#TechnicalAnalysis"},
    {"category": "Strategy", "tip": "Tendência é sua amiga até que termine. Não tente adivinhar topos e fundos — opere a favor da tendência.", "hashtag": "#TrendFollowing"},
    {"category": "Money Management", "tip": "Sempre use Stop Loss. Não é sobre estar certo, é sobre proteger seu capital quando estiver errado.", "hashtag": "#StopLoss"},
    {"category": "Market Structure", "tip": "Suporte vira resistência e resistência vira suporte. Isso é básico mas 90% dos traders esquecem.", "hashtag": "#SupportResistance"},
    {"category": "Volume", "tip": "Preço sem volume é armadilha. Sempre confirme rompimentos com aumento de volume.", "hashtag": "#VolumeAnalysis"},
    {"category": "Patience", "tip": "O melhor trade é aquele que você não faz. Paciência é a virtude mais lucrativa no trading.", "hashtag": "#TradingTips"},
]

# ==========================================
# FUNÇÕES DE ENVIO TELEGRAM
# ==========================================
def send_telegram_message(text: str, parse_mode: str = "Markdown", with_button: bool = False) -> bool:
    """Envia mensagem para o Grupo Free (com opção de botão ADVANCED)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_FREE_GROUP_ID:
        logger.warning("⚠️ Telegram não configurado.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_FREE_GROUP_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    # Adiciona botão ADVANCED se solicitado
    if with_button:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "🚀 SEXTA-FEIRA ADVANCED", "url": VIP_LINK}  # ✅ Alterado para ADVANCED
            ]]
        }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"❌ Erro Telegram: {e}")
        return False

def send_poll(question: str, options: list):
    """Envia poll para o Grupo Free."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_FREE_GROUP_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": TELEGRAM_FREE_GROUP_ID,
        "question": question,
        "options": options,
        "type": "regular"
    }
    try:
        return requests.post(url, json=payload, timeout=10).status_code == 200
    except Exception as e:
        logger.error(f"❌ Erro Poll: {e}")
        return False

# ==========================================
# DADOS DE MERCADO (OKX - GRÁTIS)
# ==========================================
def fetch_market_data():
    """Busca dados de mercado da OKX (Spot)."""
    assets = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "PAXG-USDT"]
    market_data = {}
    for inst in assets:
        try:
            r = requests.get(f"{OKX_BASE_URL}/api/v5/market/ticker?instId={inst}", timeout=5)
            if r.status_code == 200:
                data = r.json().get("data", [])
                if 
                    d = data[0]
                    symbol = inst.split("-")[0]
                    # OKX retorna preço e variação em strings
                    market_data[symbol] = {
                        "price": float(d.get("last", 0)),
                        "change_24h": float(d.get("sodUtc8", 0)), # Variação
                        "high_24h": float(d.get("high24h", 0)),
                        "low_24h": float(d.get("low24h", 0))
                    }
        except Exception as e:
            logger.error(f"❌ Erro OKX {inst}: {e}")
    return market_data

def generate_daily_briefing(market_data):
    """Gera resumo diário com link Advanced."""
    if not market_
        return None
    
    msg = "🌅 SEXTA-FEIRA ADVANCED - MARKET BRIEFING\n"
    msg += f"📅 {datetime.now().strftime('%d/%m/%Y')}\n\n"
    
    msg += "*MERCADO SPOT:*\n"
    for symbol, data in market_data.items():
        change = data["change_24h"]
        change_str = f"{change:+.2f}%"
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        msg += f"{emoji} *{symbol}:* ${data['price']:,.2f} ({change_str})\n"

    # Análise de sentimento simples
    btc_change = market_data.get("BTC", {}).get("change_24h", 0)
    eth_change = market_data.get("ETH", {}).get("change_24h", 0)
    
    msg += "\n*ANÁLISE DE TENDÊNCIA:*\n"
    if btc_change > 2 and eth_change > 2:
        msg += "🟢 *BULLISH* — Mercado em alta forte\n"
        msg += "💡 *Viés:* Long (compra)\n"
    elif btc_change < -2 and eth_change < -2:
        msg += "🔴 *BEARISH* — Mercado em baixa forte\n"
        msg += "💡 *Viés:* Short (venda)\n"
    else:
        msg += "🟡 *SIDEWAYS* — Mercado lateral\n"
        msg += "💡 *Viés:* Aguardar rompimento\n"

    msg += f"\n🔗 *Quer operar assim automaticamente?*\n👉 [SEXTA-FEIRA ADVANCED]({VIP_LINK})"
    return msg

def generate_weekly_trade(market_data):
    """Gera preview educativo do trade da semana com link Advanced."""
    if not market_data or "BTC" not in market_
        return None
    
    btc_price = market_data["BTC"]["price"]
    stop = btc_price * 0.97
    take = btc_price * 1.06
    
    msg = "🏆 *TRADE DA SEMANA* (EDUCATIVO)\n\n"
    msg += f"📊 *Ativo:* BTC/USDT\n*Direção:* LONG (compra)\n\n"
    msg += "*SETUP:*\n"
    msg += f"🎯 *Entrada:* ${btc_price:,.2f}\n"
    msg += f"🛑 *Stop Loss:* ${stop:,.2f} (-3%)\n"
    msg += f"✅ *Take Profit:* ${take:,.2f} (+6%)\n"
    msg += "\n⚠️ *Aviso:* Este é um exemplo educativo. Não é recomendação.\n"
    msg += f"\n🔗 *Quer receber sinais reais?*\n👉 [SEXTA-FEIRA ADVANCED]({VIP_LINK})"
    return msg

# ==========================================
# DICAS E POLLS
# ==========================================
def send_educational_tip():
    """Envia dica educativa com botão ADVANCED."""
    tip = random.choice(EDUCATIONAL_TIPS)
    msg = f"🧠 DICA RÁPIDA #{random.randint(1, 999)}\n\n"
    msg += f"📚 {tip['category']}:\n{tip['tip']}\n\n"
    msg += f"{tip['hashtag']}\n\n"
    msg += f"💡 Quer aprender mais?\n👉 Conheça o SEXTA-FEIRA ADVANCED\n{VIP_LINK}"
    return send_telegram_message(msg, with_button=True)

def send_daily_poll():
    """Envia poll de engajamento."""
    polls = [
        {"question": "🗳️ Qual seu viés para BTC nas próximas 24h?", "options": ["🟢 Long (subida)", "🔴 Short (queda)", "🟡 Lateral"]},
        {"question": "📊 Qual ativo você está operando mais?", "options": ["BTC", "ETH", "SOL", "Outros"]},
        {"question": "💰 Qual seu % máximo de risco por trade?", "options": ["0.5-1%", "1-2%", "2-5%", "+5% (arriscado)"]}
    ]
    poll = random.choice(polls)
    return send_poll(poll["question"], poll["options"])

# ==========================================
# LOOP PRINCIPAL
# ==========================================
def main():
    logger.info("🤖 BOT GRUPO FREE — INICIADO (SEXTA-FEIRA ADVANCED)")
    last_briefing = None
    last_tip = None
    last_poll = None

    # Mensagem inicial
    send_telegram_message(
        f"🚀 *Sexta-Feira Advanced Free Ativado!*\n\n"
        f"📡 Monitorando mercado 24/7\n"
        f"🧠 Dicas de trading diárias\n\n"
        f"🔥 *Quer operar automaticamente?*\n"
        f"👉 Use o botão abaixo!",
        with_button=True
    )

    try:
        while True:
            now = datetime.now()
            
            # 1. Resumo Diário (09:00)
            if not last_briefing or (now.date() > last_briefing.date() and now.hour == MARKET_BRIEFING_HOUR):
                logger.info("🌅 Gerando resumo diário...")
                market_data = fetch_market_data()
                msg = generate_daily_briefing(market_data)
                if msg:
                    send_telegram_message(msg, with_button=True)
                last_briefing = now
            
            # 2. Trade da Semana (Sexta-feira)
            if now.strftime("%A").lower() == WEEKLY_TRADE_DAY and (not last_briefing or (now - last_briefing).total_seconds() > 86400):
                logger.info("🏆 Gerando trade da semana...")
                market_data = fetch_market_data()
                msg = generate_weekly_trade(market_data)
                if msg:
                    send_telegram_message(msg, with_button=True)
            
            # 3. Dicas Educativas (a cada 6h)
            if not last_tip or (now - last_tip).total_seconds() >= TIP_INTERVAL * 3600:
                logger.info("🧠 Enviando dica educativa...")
                send_educational_tip()
                last_tip = now
            
            # 4. Poll de Engajamento (uma vez por dia)
            if not last_poll or (now.date() > last_poll.date()):
                if random.random() < 0.3:
                    logger.info("🗳️ Enviando poll...")
                    send_daily_poll()
                    last_poll = now
            
            # Verifica a cada 15 minutos
            time.sleep(900)
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido.")
    except Exception as e:
        logger.critical(f"💥 Erro fatal: {e}")

if __name__ == "__main__":
    main()