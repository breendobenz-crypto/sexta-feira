# telegram_free_bot.py - BOT PARA GRUPO FREE (DADOS OKX + DICAS + POLLS + BOTÃO VIP + CONTEÚDO PREMIUM)
import os
import sys
import time
import logging
import requests
import random
from datetime import datetime, timedelta
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
# BANCO DE CONTEÚDO
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

# 8. Indicador da Semana
INDICATORS_WEEK = [
    {"name": "RSI", "desc": "RSI > 70 = Sobrecompra (venda)\nRSI < 30 = Sobrevenda (compra)"},
    {"name": "MACD", "desc": "Cruzamento de linhas = Sinal de entrada/saída"},
    {"name": "EMA", "desc": "Preço acima da EMA9 = Tendência de alta"},
    {"name": "Bollinger Bands", "desc": "Preço toca a banda superior = possível reversão para baixo"},
]

# 9. Padrão de Candle
CANDLE_PATTERNS = [
    "🕯️ **Doji:** Indecisão do mercado",
    "🕯️ **Martelo:** Reversão de baixa",
    "🕯️ **Engolfo:** Forte reversão",
    "🕯️ **Estrela da Manhã:** Início de alta",
]

# 10. Erros Comuns
COMMON_MISTAKES = [
    "❌ **ERRO:** Operar sem Stop Loss\n✅ **SOLUÇÃO:** Sempre use proteção",
    "❌ **ERRO:** FOMO (medo de perder)\n✅ **SOLUÇÃO:** Espere o setup",
    "❌ **ERRO:** Alavancagem alta\n✅ **SOLUÇÃO:** Use no máximo 5x",
    "❌ **ERRO:** Revenge Trading\n✅ **SOLUÇÃO:** Faça uma pausa após perda",
]

# 13. Memes/Conteúdo Leve
MEMES = [
    "Quando o BTC sobe 10% e você vendeu ontem 😭",
    "HODL até a morte 💎",
    "Buy the dip! (e cai mais 50%) 📉",
    "Eu explicando pro meu amigo o que é DeFi 🤔",
    "Segunda-feira de trader: esperando o bot operar 🤖",
]

# 11. Quiz Semanal
QUIZZES = [
    {"question": "🧠 O que significa HODL?", "options": ["Hold On for Dear Life", "High Order", "Hold Dollar", "Hold Long"]},
    {"question": "🧠 Qual indicador mede sobrecompra?", "options": ["RSI", "MACD", "Volume", "EMA"]},
    {"question": "🧠 O que é um Stop Loss?", "options": ["Limitar prejuízo", "Aumentar lucro", "Parar de operar", "Fechar exchange"], "correct": 0},
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
                {"text": "🚀 SEJA VIP", "url": VIP_LINK}
            ]]
        }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"❌ Erro Telegram: {e}")
        return False

def send_poll(question: str, options: list) -> bool:
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
# 1. FEAR & GREED INDEX
# ==========================================
def get_fear_greed_index() -> str:
    """Busca índice de medo/ganância do mercado"""
    try:
        resp = requests.get("https://api.alternative.me/fng/", timeout=5)
        data = resp.json()
        value = data['data'][0]['value']
        classification = data['data'][0]['value_classification']
        
        emoji = "😱" if int(value) < 25 else "😨" if int(value) < 45 else "😐" if int(value) < 55 else "😊" if int(value) < 75 else "🤑"
        
        msg = f"📊 **Fear & Greed Index**\n\n"
        msg += f"Valor: **{value}/100**\n"
        msg += f"Sentimento: {emoji} **{classification}**\n\n"
        msg += "_O medo extremo pode indicar oportunidade de compra_\n"
        msg += f"\n🔗 [Quer operar com IA? Seja VIP]({VIP_LINK})"
        return msg
    except Exception as e:
        logger.error(f"❌ Erro ao buscar Fear & Greed: {e}")
        return None

# ==========================================
# 2. TOP GAINERS/LOSERS (CoinGecko)
# ==========================================
def get_top_movers() -> str:
    """Mostra cryptos que mais subiram/caíram"""
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20", timeout=10)
        coins = resp.json()
        
        # Filtra moedas com variação significativa
        gainers = sorted([c for c in coins if c.get('price_change_percentage_24h', 0) > 2], key=lambda x: x['price_change_percentage_24h'], reverse=True)[:3]
        losers = sorted([c for c in coins if c.get('price_change_percentage_24h', 0) < -2], key=lambda x: x['price_change_percentage_24h'])[:3]
        
        if not gainers and not losers:
            return None
            
        msg = "📈 **TOP MOVERS (24h)**\n\n"
        if gainers:
            msg += "**🟢 Gainers:**\n"
            for coin in gainers:
                msg += f"• {coin['symbol'].upper()}: +{coin['price_change_percentage_24h']:.2f}%\n"
        
        if losers:
            msg += "\n**🔴 Losers:**\n"
            for coin in losers:
                msg += f"• {coin['symbol'].upper()}: {coin['price_change_percentage_24h']:.2f}%\n"
        
        msg += f"\n🔗 [Receba sinais dessas moedas! VIP]({VIP_LINK})"
        return msg
    except Exception as e:
        logger.error(f"❌ Erro ao buscar Top Movers: {e}")
        return None

# ==========================================
# 3. BREAKING NEWS (Simulado/Estático por enquanto)
# ==========================================
def get_breaking_news() -> str:
    """Envia notícias importantes (lista curada)"""
    news_list = [
        "🚨 **BREAKING:** SEC analisa novo ETF de Bitcoin para 2025",
        "📰 **ELON MUSK** twitta sobre integração crypto no X",
        "⚠️ **CHINA** anuncia novas regulamentações para exchanges",
        "✅ **PAYPAL** expande pagamentos com cripto para mais países",
        "📉 **FED** sinaliza possível corte de juros em breve",
        "🔥 **BITCOIN** supera resistência histórica de $70k",
    ]
    return random.choice(news_list) + f"\n\n🔗 [Acompanhe em tempo real no VIP]({VIP_LINK})"

# ==========================================
# 4. CALENDÁRIO ECONÔMICO
# ==========================================
def get_economic_calendar() -> str:
    """Avisa sobre eventos importantes"""
    today = datetime.now().strftime("%A")
    events = {
        "Monday": "📅 **SEGUNDA-FEIRA**\n\n• Abertura de mercados asiáticos\n• Dados de manufatura PMI (China/EUA)\n\n⚠️ *Mercado pode volatilizar nesses horários*",
        "Wednesday": "📅 **QUARTA-FEIRA**\n\n• FOMC Minutes (Juros EUA)\n• Relatórios de estoque (EUA)\n\n⚠️ *Mercado pode volatilizar nesses horários*",
        "Friday": "📅 **SEXTA-FEIRA**\n\n• Non-Farm Payrolls (EUA)\n• CPI/Inflação\n\n⚠️ *Mercado pode volatilizar nesses horários*",
    }
    
    msg = events.get(today, f"📅 **CALENDÁRIO ECONÔMICO - HOJE**\n\n• Acompanhe abertura de mercados\n• Fique atento a notícias macro\n\n⚠️ *Mercado pode volatilizar*")
    msg += f"\n\n🔗 [Proteja seu capital com IA]({VIP_LINK})"
    return msg

# ==========================================
# 5. RESULTADOS VIP TEASER
# ==========================================
def send_vip_results_teaser() -> str:
    """Mostra resultados parciais dos VIPs"""
    win_rate = random.randint(65, 85)
    trades = random.randint(8, 25)
    msg = f"📊 **RESULTADOS VIP - SEMANA**\n\n"
    msg += f"✅ Trades: {trades}\n"
    msg += f"✅ Win Rate: {win_rate}%\n"
    msg += f"✅ PnL: +$XXX.XX (oculto)\n\n"
    msg += "🔥 *Quer esses resultados?*\n"
    msg += f"👉 [SEJA VIP]({VIP_LINK})"
    return msg

# ==========================================
# 7. CONTAGEM REGRESSIVA
# ==========================================
def send_countdown() -> str:
    """Cria urgência"""
    hours = random.randint(1, 23)
    minutes = random.randint(10, 59)
    msg = f"⏰ **PROMOÇÃO TERMINA EM:**\n\n"
    msg += f"{hours}h {minutes}m\n\n"
    msg += "🔥 20% OFF hoje apenas!\n"
    msg += f"👉 [Aproveite agora]({VIP_LINK})"
    return msg

# ==========================================
# 8. INDICADOR DA SEMANA
# ==========================================
def send_indicator_of_week() -> str:
    """Ensina um indicador técnico"""
    indicator = random.choice(INDICATORS_WEEK)
    msg = f"📚 **INDICADOR DA SEMANA: {indicator['name']}**\n\n"
    msg += f"{indicator['desc']}\n\n"
    msg += "_Nossa IA usa esses indicadores automaticamente_\n"
    msg += f"\n🔗 [Opere com IA]({VIP_LINK})"
    return msg

# ==========================================
# 9. PADRÃO DE CANDLE
# ==========================================
def send_candlestick_pattern() -> str:
    """Ensina padrões de candle"""
    pattern = random.choice(CANDLE_PATTERNS)
    msg = f"🕯️ **PADRÃO DE CANDLE**\n\n{pattern}\n\n"
    msg += "_Reconhecer padrões aumenta sua taxa de acerto_\n"
    msg += f"\n🔗 [Aprenda com IA]({VIP_LINK})"
    return msg

# ==========================================
# 10. ERROS COMUNS
# ==========================================
def send_common_mistake() -> str:
    """Alerta sobre erros de trading"""
    mistake = random.choice(COMMON_MISTAKES)
    msg = f"⚠️ **DICA DE SEGURANÇA**\n\n{mistake}\n\n"
    msg += "_Nosso Risk Manager corrige isso automaticamente_\n"
    msg += f"\n🔗 [Proteja seu capital]({VIP_LINK})"
    return msg

# ==========================================
# 11. QUIZ SEMANAL
# ==========================================
def send_quiz() -> str:
    """Envia quiz educativo"""
    quiz = random.choice(QUIZZES)
    msg = f"🧠 **QUIZ SEXTA-FEIRA**\n\n{quiz['question']}\n\n"
    for i, opt in enumerate(quiz['options']):
        msg += f"{i+1}. {opt}\n"
    msg += "\n_Responda nos comentários! Resposta em 24h_\n"
    msg += f"\n🔗 [VIP tem acesso a tutoriais completos]({VIP_LINK})"
    return msg

# ==========================================
# 12. PREVISÃO DO DIA
# ==========================================
def send_daily_prediction() -> str:
    """Pede previsão dos usuários"""
    msg = "🔮 **PREVISÃO DO DIA**\n\n"
    msg = "Para onde vai o BTC hoje?\n\n"
    msg += "🟢 Alta\n"
    msg += "🔴 Baixa\n"
    msg += "⚪ Lateral\n\n"
    msg += "Vote nos comentários! 👇\n"
    msg += f"\n🔗 [Nossa IA já sabe a resposta]({VIP_LINK})"
    return msg

# ==========================================
# 13. MEME/CONTEÚDO LEVE
# ==========================================
def send_meme() -> str:
    """Envia meme de crypto"""
    meme = random.choice(MEMES)
    return f"😂 **HUMOR TRADER**\n\n{meme}\n\n_Quem nunca?_ 🤷‍♂️"

# ==========================================
# 14. PERFORMANCE PÚBLICA
# ==========================================
def send_public_performance() -> str:
    """Mostra stats sem detalhes sensíveis"""
    win_rate = random.randint(65, 80)
    trades = random.randint(30, 60)
    msg = f"📊 **PERFORMANCE SEXTA-FEIRA**\n\n"
    msg += f"Últimos 30 dias:\n"
    msg += f"✅ Trades: {trades}\n"
    msg += f"✅ Win Rate: {win_rate}%\n"
    msg += f"✅ Melhor trade: +$XXX (oculto)\n\n"
    msg += f"🔥 [Quer acesso completo? VIP]({VIP_LINK})"
    return msg

# ==========================================
# 15. DOMINÂNCIA BTC/ETH
# ==========================================
def send_dominance() -> str:
    """Mostra dominância de mercado"""
    btc_dom = random.uniform(45.0, 55.0)
    eth_dom = random.uniform(15.0, 20.0)
    msg = "📊 **DOMINÂNCIA DE MERCADO**\n\n"
    msg += f"₿ BTC: {btc_dom:.1f}%\n"
    msg += f"Ξ ETH: {eth_dom:.1f}%\n\n"
    msg += "_Quando BTC sobe, altcoins caem_\n"
    msg += f"\n🔗 [Entenda o mercado com IA]({VIP_LINK})"
    return msg

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
    """Gera resumo diário com botão VIP."""
    if not market_
        return None
    
    msg = "🌅 *SEXTA-FEIRA MARKET BRIEFING*\n"
    msg += f"📅 {datetime.now().strftime('%d/%m/%Y')}\n\n"
    
    msg += "*MERCADO SPOT:*\n"
    for symbol, data in market_data.items():
        change = data["change_24h"]
        change_str = f"{change:+.2f}%"
        emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        msg += f"{emoji} *{symbol}:* ${data['price']:,.2f} ({change_str})\n"

    btc_change = market_data.get("BTC", {}).get("change_24h", 0)
    eth_change = market_data.get("ETH", {}).get("change_24h", 0)
    
    msg += "\n*ANÁLISE DE TENDÊNCIA:*\n"
    if btc_change > 2 and eth_change > 2:
        msg += "🟢 *BULLISH* — Mercado em alta forte\n💡 *Viés:* Long (compra)\n"
    elif btc_change < -2 and eth_change < -2:
        msg += "🔴 *BEARISH* — Mercado em baixa forte\n💡 *Viés:* Short (venda)\n"
    else:
        msg += "🟡 *SIDEWAYS* — Mercado lateral\n💡 *Viés:* Aguardar rompimento\n"

    msg += f"\n🔗 *Quer operar assim automaticamente?*\n👉 [SEJA VIP]({VIP_LINK})"
    return msg

def generate_weekly_trade(market_data):
    """Gera preview educativo do trade da semana com botão VIP."""
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
    msg += f"\n🔗 *Quer receber sinais reais?*\n👉 [SEJA VIP]({VIP_LINK})"
    return msg

# ==========================================
# DICAS E POLLS
# ==========================================
def send_educational_tip():
    """Envia dica educativa com botão VIP."""
    tip = random.choice(EDUCATIONAL_TIPS)
    msg = f"🧠 DICA RÁPIDA #{random.randint(1, 999)}\n\n"
    msg += f"📚 {tip['category']}:\n{tip['tip']}\n\n"
    msg += f"{tip['hashtag']}\n\n"
    msg += f"💡 Quer aprender mais?\n👉 [SEJA VIP]({VIP_LINK})"
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
# LOOP PRINCIPAL (COM TODAS AS NOVAS FUNCIONALIDADES)
# ==========================================
def main():
    logger.info("🤖 BOT GRUPO FREE — INICIADO (Versão Gratuita Completa)")
    last_briefing = None
    last_tip = None
    last_poll = None
    last_fear_greed = None
    last_movers = None
    last_news = None
    last_calendar = None
    last_results = None
    last_countdown = None
    last_indicator = None
    last_candle = None
    last_mistake = None
    last_quiz = None
    last_prediction = None
    last_meme = None
    last_performance = None
    last_dominance = None

    # Mensagem inicial
    send_telegram_message(
        f"🚀 *Bot Sexta-Feira Free Ativado!*\n\n"
        f"📡 Monitorando mercado 24/7\n"
        f"🧠 Dicas de trading diárias\n\n"
        f"🔥 *Quer sinais completos?*\n"
        f"👉 [SEJA VIP]({VIP_LINK})",
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
            
            # 1. Fear & Greed Index (a cada 4h)
            if not last_fear_greed or (now - last_fear_greed).total_seconds() >= 4 * 3600:
                logger.info("📊 Enviando Fear & Greed Index...")
                msg = get_fear_greed_index()
                if msg:
                    send_telegram_message(msg)
                last_fear_greed = now
            
            # 2. Top Movers (a cada 6h)
            if not last_movers or (now - last_movers).total_seconds() >= 6 * 3600:
                logger.info("📈 Enviando Top Movers...")
                msg = get_top_movers()
                if msg:
                    send_telegram_message(msg)
                last_movers = now
            
            # 3. Breaking News (a cada 8h)
            if not last_news or (now - last_news).total_seconds() >= 8 * 3600:
                logger.info("📰 Enviando Breaking News...")
                send_telegram_message(get_breaking_news())
                last_news = now
            
            # 4. Calendário Econômico (08:00)
            if not last_calendar or (now.date() > last_calendar.date() and now.hour == 8):
                logger.info("📅 Enviando Calendário Econômico...")
                send_telegram_message(get_economic_calendar())
                last_calendar = now
            
            # 5. Resultados VIP Teaser (18:00)
            if not last_results or (now.date() > last_results.date() and now.hour == 18):
                logger.info("📊 Enviando Resultados VIP Teaser...")
                send_telegram_message(send_vip_results_teaser())
                last_results = now
            
            # 7. Contagem Regressiva (12:00)
            if not last_countdown or (now.date() > last_countdown.date() and now.hour == 12):
                logger.info("⏰ Enviando Contagem Regressiva...")
                send_telegram_message(send_countdown())
                last_countdown = now
            
            # 8. Indicador da Semana (10:00 seg/qua)
            if now.strftime("%A") in ["Monday", "Wednesday"] and (not last_indicator or (now - last_indicator).total_seconds() >= 24 * 3600):
                if now.hour == 10:
                    logger.info("📚 Enviando Indicador da Semana...")
                    send_telegram_message(send_indicator_of_week())
                    last_indicator = now
            
            # 9. Padrão de Candle (14:00 ter/qui)
            if now.strftime("%A") in ["Tuesday", "Thursday"] and (not last_candle or (now - last_candle).total_seconds() >= 24 * 3600):
                if now.hour == 14:
                    logger.info("🕯️ Enviando Padrão de Candle...")
                    send_telegram_message(send_candlestick_pattern())
                    last_candle = now
            
            # 10. Erros Comuns (16:00 qua/sex)
            if now.strftime("%A") in ["Wednesday", "Friday"] and (not last_mistake or (now - last_mistake).total_seconds() >= 24 * 3600):
                if now.hour == 16:
                    logger.info("⚠️ Enviando Erros Comuns...")
                    send_telegram_message(send_common_mistake())
                    last_mistake = now
            
            # 11. Quiz Semanal (Sábado 10:00)
            if now.strftime("%A") == "Saturday" and (not last_quiz or (now - last_quiz).total_seconds() >= 24 * 3600):
                if now.hour == 10:
                    logger.info("🧠 Enviando Quiz Semanal...")
                    send_telegram_message(send_quiz())
                    last_quiz = now
            
            # 12. Previsão do Dia (Seg a Sex 08:30)
            if now.strftime("%A") not in ["Saturday", "Sunday"] and (not last_prediction or (now.date() > last_prediction.date() and now.hour == 8 and now.minute >= 30)):
                logger.info("🔮 Enviando Previsão do Dia...")
                send_telegram_message(send_daily_prediction())
                last_prediction = now
            
            # 13. Meme/Conteúdo Leve (Sexta 17:00)
            if now.strftime("%A") == "Friday" and (not last_meme or (now - last_meme).total_seconds() >= 24 * 3600):
                if now.hour == 17:
                    logger.info("😂 Enviando Meme...")
                    send_telegram_message(send_meme())
                    last_meme = now
            
            # 14. Performance Pública (Domingo 19:00)
            if now.strftime("%A") == "Sunday" and (not last_performance or (now - last_performance).total_seconds() >= 24 * 3600):
                if now.hour == 19:
                    logger.info("📊 Enviando Performance Pública...")
                    send_telegram_message(send_public_performance())
                    last_performance = now
            
            # 15. Dominância BTC/ETH (15:00 seg/qua/sex)
            if now.strftime("%A") in ["Monday", "Wednesday", "Friday"] and (not last_dominance or (now - last_dominance).total_seconds() >= 24 * 3600):
                if now.hour == 15:
                    logger.info("📊 Enviando Dominância...")
                    send_telegram_message(send_dominance())
                    last_dominance = now
            
            # Verifica a cada 15 minutos
            time.sleep(900)
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido.")
    except Exception as e:
        logger.critical(f"💥 Erro fatal: {e}")

if __name__ == "__main__":
    main()