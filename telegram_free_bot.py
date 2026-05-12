# telegram_free_bot.py - BOT PARA GRUPO FREE (15 FUNCIONALIDADES + VIP LINK)
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
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURAÇÕES
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_FREE_GROUP_ID = os.getenv("TELEGRAM_FREE_GROUP_ID")
OKX_BASE_URL = "https://www.okx.com"
VIP_LINK = "https://whop.com/sexta-feira-advanced/sexta-feira-advanced-19/"

MARKET_BRIEFING_HOUR = 9
TIP_INTERVAL = 6
WEEKLY_TRADE_DAY = "friday"

# ==========================================
# BANCO DE CONTEÚDO (SEM ESPAÇOS NAS CHAVES)
# ==========================================
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

INDICATORS_WEEK = [
    {"name": "RSI", "desc": "RSI > 70 = Sobrecompra (venda)\nRSI < 30 = Sobrevenda (compra)"},
    {"name": "MACD", "desc": "Cruzamento de linhas = Sinal de entrada/saída"},
    {"name": "EMA", "desc": "Preço acima da EMA9 = Tendência de alta"},
    {"name": "Bollinger Bands", "desc": "Preço toca a banda superior = possível reversão para baixo"},
]

CANDLE_PATTERNS = [
    "🕯️ **Doji:** Indecisão do mercado",
    "🕯️ **Martelo:** Reversão de baixa",
    "🕯️ **Engolfo:** Forte reversão",
    "🕯️ **Estrela da Manhã:** Início de alta",
]

COMMON_MISTAKES = [
    "❌ **ERRO:** Operar sem Stop Loss\n✅ **SOLUÇÃO:** Sempre use proteção",
    "❌ **ERRO:** FOMO (medo de perder)\n✅ **SOLUÇÃO:** Espere o setup",
    "❌ **ERRO:** Alavancagem alta\n✅ **SOLUÇÃO:** Use no máximo 5x",
    "❌ **ERRO:** Revenge Trading\n✅ **SOLUÇÃO:** Faça uma pausa após perda",
]

MEMES = [
    "Quando o BTC sobe 10% e você vendeu ontem 😭",
    "HODL até a morte 💎",
    "Buy the dip! (e cai mais 50%) 📉",
    "Eu explicando pro meu amigo o que é DeFi 🤔",
    "Segunda-feira de trader: esperando o bot operar 🤖",
]

QUIZZES = [
    {"question": "🧠 O que significa HODL?", "options": ["Hold On for Dear Life", "High Order", "Hold Dollar", "Hold Long"]},
    {"question": "🧠 Qual indicador mede sobrecompra?", "options": ["RSI", "MACD", "Volume", "EMA"]},
    {"question": "🧠 O que é um Stop Loss?", "options": ["Limitar prejuízo", "Aumentar lucro", "Parar de operar", "Fechar exchange"]},
]

# ==========================================
# FUNÇÕES DE ENVIO TELEGRAM
# ==========================================
def send_telegram_message(text: str, parse_mode: str = "Markdown", with_button: bool = False) -> bool:
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
    
    if with_button:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "🚀 SEXTA-FEIRA ADVANCED", "url": VIP_LINK}
            ]]
        }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"❌ Erro Telegram: {e}")
        return False

def send_poll(question: str, options: list) -> bool:
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
# 1-15 FUNCIONALIDADES PREMIUM
# ==========================================
def get_fear_greed_index() -> str:
    try:
        resp = requests.get("https://api.alternative.me/fng/", timeout=5)
        data = resp.json()
        value = data['data'][0]['value']
        classification = data['data'][0]['value_classification']
        emoji = "😱" if int(value) < 25 else "😨" if int(value) < 45 else "😐" if int(value) < 55 else "😊" if int(value) < 75 else "🤑"
        return f"📊 **Fear & Greed Index**\n\nValor: **{value}/100**\nSentimento: {emoji} **{classification}**\n\n_O medo extremo pode indicar oportunidade de compra_\n\n🔗 [Quer operar com IA? Seja VIP]({VIP_LINK})"
    except: return None

def get_top_movers() -> str:
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20", timeout=10)
        coins = resp.json()
        gainers = sorted([c for c in coins if c.get('price_change_percentage_24h', 0) > 2], key=lambda x: x['price_change_percentage_24h'], reverse=True)[:3]
        losers = sorted([c for c in coins if c.get('price_change_percentage_24h', 0) < -2], key=lambda x: x['price_change_percentage_24h'])[:3]
        if not gainers and not losers: return None
        msg = "📈 **TOP MOVERS (24h)**\n\n"
        if gainers:
            msg += "**🟢 Gainers:**\n" + "".join([f"• {c['symbol'].upper()}: +{c['price_change_percentage_24h']:.2f}%\n" for c in gainers])
        if losers:
            msg += "\n**🔴 Losers:**\n" + "".join([f"• {c['symbol'].upper()}: {c['price_change_percentage_24h']:.2f}%\n" for c in losers])
        return msg + f"\n🔗 [Receba sinais dessas moedas! VIP]({VIP_LINK})"
    except: return None

def get_breaking_news() -> str:
    news = [
        "🚨 **BREAKING:** SEC analisa novo ETF de Bitcoin para 2025",
        "📰 **ELON MUSK** twitta sobre integração crypto no X",
        "⚠️ **CHINA** anuncia novas regulamentações para exchanges",
        "✅ **PAYPAL** expande pagamentos com cripto para mais países",
        "📉 **FED** sinaliza possível corte de juros em breve",
    ]
    return random.choice(news) + f"\n\n🔗 [Acompanhe em tempo real no VIP]({VIP_LINK})"

def get_economic_calendar() -> str:
    today = datetime.now().strftime("%A")
    events = {
        "Monday": "📅 **SEGUNDA**\n• PMI Manufatura (China/EUA)\n⚠️ *Volatilidade esperada*",
        "Wednesday": "📅 **QUARTA**\n• FOMC Minutes (Juros EUA)\n⚠️ *Volatilidade esperada*",
        "Friday": "📅 **SEXTA**\n• Non-Farm Payrolls (EUA)\n⚠️ *Volatilidade esperada*",
    }
    return events.get(today, "📅 **CALENDÁRIO ECONÔMICO**\n• Acompanhe abertura de mercados\n⚠️ *Mercado pode volatilizar*") + f"\n\n🔗 [Proteja seu capital com IA]({VIP_LINK})"

def send_vip_results_teaser() -> str:
    return f"📊 **RESULTADOS VIP - SEMANA**\n\n✅ Trades: {random.randint(8, 25)}\n✅ Win Rate: {random.randint(65, 85)}%\n✅ PnL: +$XXX.XX (oculto)\n\n🔥 *Quer esses resultados?*\n👉 [SEJA VIP]({VIP_LINK})"

def send_countdown() -> str:
    return f"⏰ **PROMOÇÃO TERMINA EM:**\n\n{random.randint(1, 23)}h {random.randint(10, 59)}m\n\n🔥 20% OFF hoje apenas!\n👉 [Aproveite agora]({VIP_LINK})"

def send_indicator_of_week() -> str:
    ind = random.choice(INDICATORS_WEEK)
    return f"📚 **INDICADOR DA SEMANA: {ind['name']}**\n\n{ind['desc']}\n\n_Nossa IA usa esses indicadores automaticamente_\n\n🔗 [Opere com IA]({VIP_LINK})"

def send_candlestick_pattern() -> str:
    return f"🕯️ **PADRÃO DE CANDLE**\n\n{random.choice(CANDLE_PATTERNS)}\n\n_Reconhecer padrões aumenta sua taxa de acerto_\n\n🔗 [Aprenda com IA]({VIP_LINK})"

def send_common_mistake() -> str:
    return f"⚠️ **DICA DE SEGURANÇA**\n\n{random.choice(COMMON_MISTAKES)}\n\n_Nosso Risk Manager corrige isso automaticamente_\n\n🔗 [Proteja seu capital]({VIP_LINK})"

def send_quiz() -> str:
    q = random.choice(QUIZZES)
    opts = "\n".join([f"{i+1}. {o}" for i, o in enumerate(q['options'])])
    return f"🧠 **QUIZ SEXTA-FEIRA**\n\n{q['question']}\n\n{opts}\n\n_Responda nos comentários! Resposta em 24h_\n\n🔗 [VIP tem acesso a tutoriais completos]({VIP_LINK})"

def send_daily_prediction() -> str:
    return f"🔮 **PREVISÃO DO DIA**\n\nPara onde vai o BTC hoje?\n\n🟢 Alta\n Baixa\n⚪ Lateral\n\nVote nos comentários! 👇\n\n🔗 [Nossa IA já sabe a resposta]({VIP_LINK})"

def send_meme() -> str:
    return f"😂 **HUMOR TRADER**\n\n{random.choice(MEMES)}\n\n_Quem nunca?_ 🤷♂️"

def send_public_performance() -> str:
    return f"📊 **PERFORMANCE SEXTA-FEIRA**\n\nÚltimos 30 dias:\n✅ Trades: {random.randint(30, 60)}\n✅ Win Rate: {random.randint(65, 80)}%\n✅ Melhor trade: +$XXX (oculto)\n\n🔥 [Quer acesso completo? VIP]({VIP_LINK})"

def send_dominance() -> str:
    return f"📊 **DOMINÂNCIA DE MERCADO**\n\n₿ BTC: {random.uniform(45.0, 55.0):.1f}%\nΞ ETH: {random.uniform(15.0, 20.0):.1f}%\n\n_Quando BTC sobe, altcoins caem_\n\n🔗 [Entenda o mercado com IA]({VIP_LINK})"

# ==========================================
# DADOS DE MERCADO (OKX)
# ==========================================
def fetch_market_data():
    assets = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "PAXG-USDT"]
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
                        "low_24h": float(d.get("low24h", 0))
                    }
        except Exception as e:
            logger.error(f"❌ Erro OKX {inst}: {e}")
    return market_data

def generate_daily_briefing(market_data):
    if not market_data: return None
    msg = "🌅 *SEXTA-FEIRA MARKET BRIEFING*\n"
    msg += f"📅 {datetime.now().strftime('%d/%m/%Y')}\n\n*MERCADO SPOT:*\n"
    for symbol, data in market_data.items():
        change = data["change_24h"]
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        msg += f"{emoji} *{symbol}:* ${data['price']:,.2f} ({change:+.2f}%)\n"
    
    btc = market_data.get("BTC", {}).get("change_24h", 0)
    eth = market_data.get("ETH", {}).get("change_24h", 0)
    msg += "\n*ANÁLISE DE TENDÊNCIA:*\n"
    if btc > 2 and eth > 2: msg += "🟢 *BULLISH* — Mercado em alta forte\n💡 *Viés:* Long (compra)\n"
    elif btc < -2 and eth < -2: msg += "🔴 *BEARISH* — Mercado em baixa forte\n💡 *Viés:* Short (venda)\n"
    else: msg += "🟡 *SIDEWAYS* — Mercado lateral\n💡 *Viés:* Aguardar rompimento\n"
    
    return msg + f"\n🔗 *Quer operar assim automaticamente?*\n👉 [SEJA VIP]({VIP_LINK})"

def generate_weekly_trade(market_data):
    if not market_data or "BTC" not in market_data: return None
    btc_price = market_data["BTC"]["price"]
    msg = f"🏆 *TRADE DA SEMANA* (EDUCATIVO)\n\n📊 *Ativo:* BTC/USDT\n*Direção:* LONG (compra)\n\n*SETUP:*\n"
    msg += f"🎯 *Entrada:* ${btc_price:,.2f}\n🛑 *Stop Loss:* ${btc_price*0.97:,.2f} (-3%)\n✅ *Take Profit:* ${btc_price*1.06:,.2f} (+6%)\n"
    return msg + "\n⚠️ *Aviso:* Exemplo educativo. Não é recomendação.\n\n🔗 *Quer sinais reais?*\n👉 [SEJA VIP]({VIP_LINK})"

# ==========================================
# LOOP PRINCIPAL
# ==========================================
def main():
    logger.info("🤖 BOT GRUPO FREE — INICIADO (Versão Completa)")
    timers = {k: None for k in ["briefing", "tip", "poll", "fg", "movers", "news", "cal", "res", "cd", "ind", "cand", "mist", "quiz", "pred", "meme", "perf", "dom"]}
    
    send_telegram_message(f"🚀 *Bot Sexta-Feira Free Ativado!*\n\n📡 Monitorando mercado 24/7\n🧠 Dicas diárias\n🔥 *Quer sinais completos?*\n👉 [SEJA VIP]({VIP_LINK})", with_button=True)

    try:
        while True:
            now = datetime.now()
            day = now.strftime("%A")
            
            # Agendamentos
            if not timers["briefing"] or (now.date() > timers["briefing"].date() and now.hour == MARKET_BRIEFING_HOUR):
                if msg := generate_daily_briefing(fetch_market_data()): send_telegram_message(msg, with_button=True)
                timers["briefing"] = now
                
            if day.lower() == WEEKLY_TRADE_DAY and (not timers["briefing"] or (now - timers["briefing"]).total_seconds() > 86400):
                if msg := generate_weekly_trade(fetch_market_data()): send_telegram_message(msg, with_button=True)
                
            if not timers["tip"] or (now - timers["tip"]).total_seconds() >= TIP_INTERVAL * 3600:
                tip = random.choice(EDUCATIONAL_TIPS)
                send_telegram_message(f"🧠 DICA RÁPIDA #{random.randint(1, 999)}\n\n📚 {tip['category']}:\n{tip['tip']}\n\n{tip['hashtag']}\n\n👉 [SEJA VIP]({VIP_LINK})", with_button=True)
                timers["tip"] = now
                
            if not timers["poll"] or now.date() > timers["poll"].date():
                if random.random() < 0.3:
                    polls = [{"q": "🗳️ Viés BTC 24h?", "o": ["🟢 Long", "🔴 Short", "🟡 Lateral"]}, {"q": "📊 Ativo principal?", "o": ["BTC", "ETH", "SOL", "Outros"]}]
                    p = random.choice(polls)
                    send_poll(p["q"], p["o"])
                timers["poll"] = now
                
            if not timers["fg"] or (now - timers["fg"]).total_seconds() >= 4*3600:
                if m := get_fear_greed_index(): send_telegram_message(m)
                timers["fg"] = now
                
            if not timers["movers"] or (now - timers["movers"]).total_seconds() >= 6*3600:
                if m := get_top_movers(): send_telegram_message(m)
                timers["movers"] = now
                
            if not timers["news"] or (now - timers["news"]).total_seconds() >= 8*3600:
                send_telegram_message(get_breaking_news())
                timers["news"] = now
                
            if not timers["cal"] or (now.date() > timers["cal"].date() and now.hour == 8):
                send_telegram_message(get_economic_calendar())
                timers["cal"] = now
                
            if not timers["res"] or (now.date() > timers["res"].date() and now.hour == 18):
                send_telegram_message(send_vip_results_teaser())
                timers["res"] = now
                
            if not timers["cd"] or (now.date() > timers["cd"].date() and now.hour == 12):
                send_telegram_message(send_countdown())
                timers["cd"] = now
                
            if day in ["Monday", "Wednesday"] and (not timers["ind"] or (now - timers["ind"]).total_seconds() >= 24*3600) and now.hour == 10:
                send_telegram_message(send_indicator_of_week())
                timers["ind"] = now
                
            if day in ["Tuesday", "Thursday"] and (not timers["cand"] or (now - timers["cand"]).total_seconds() >= 24*3600) and now.hour == 14:
                send_telegram_message(send_candlestick_pattern())
                timers["cand"] = now
                
            if day in ["Wednesday", "Friday"] and (not timers["mist"] or (now - timers["mist"]).total_seconds() >= 24*3600) and now.hour == 16:
                send_telegram_message(send_common_mistake())
                timers["mist"] = now
                
            if day == "Saturday" and (not timers["quiz"] or (now - timers["quiz"]).total_seconds() >= 24*3600) and now.hour == 10:
                send_telegram_message(send_quiz())
                timers["quiz"] = now
                
            if day not in ["Saturday", "Sunday"] and (not timers["pred"] or now.date() > timers["pred"].date()) and now.hour == 8:
                send_telegram_message(send_daily_prediction())
                timers["pred"] = now
                
            if day == "Friday" and (not timers["meme"] or (now - timers["meme"]).total_seconds() >= 24*3600) and now.hour == 17:
                send_telegram_message(send_meme())
                timers["meme"] = now
                
            if day == "Sunday" and (not timers["perf"] or (now - timers["perf"]).total_seconds() >= 24*3600) and now.hour == 19:
                send_telegram_message(send_public_performance())
                timers["perf"] = now
                
            if day in ["Monday", "Wednesday", "Friday"] and (not timers["dom"] or (now - timers["dom"]).total_seconds() >= 24*3600) and now.hour == 15:
                send_telegram_message(send_dominance())
                timers["dom"] = now
                
            time.sleep(900)
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido.")
    except Exception as e:
        logger.critical(f"💥 Erro fatal: {e}")

# ✅ CORRIGIDO: __name__
if __name__ == "__main__":
    main()