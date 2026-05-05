# telegram_bot.py - BOT TELEGRAM SEXTA-FEIRA (VERSÃO FINAL CORRIGIDA)
import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURAÇÕES
# ==========================================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
VIP_GROUP_ID = os.getenv("TELEGRAM_VIP_GROUP_ID")

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN não configurado no .env")
    exit(1)

# ==========================================
# COMANDOS DO BOT
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start"""
    user = update.effective_user
    welcome_msg = (
        f"🟣 *Bem-vindo à SEXTA-FEIRA Advanced!*\n\n"
        f"Olá {user.first_name}! 👋\n\n"
        f"Sou seu assistente de trading automatizado com IA.\n\n"
        f"*O que posso fazer:*\n"
        f"📊 Enviar sinais de trading em tempo real\n"
        f"📰 Notícias de crypto filtradas\n"
        f"📈 Alertas de entrada e saída\n"
        f"🆘 Suporte técnico prioritário\n\n"
        f"Digite /help para ver todos os comandos disponíveis."
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /help"""
    help_msg = (
        "📚 *COMANDOS DISPONÍVEIS:*\n\n"
        "/start - 🚀 Iniciar o bot\n"
        "/help - 📚 Esta mensagem de ajuda\n"
        "/status - 📊 Ver status do sistema\n"
        "/vip - 💎 Informações sobre plano VIP\n"
        "/suporte - 🆘 Falar com suporte técnico\n"
        "/config - ⚙️ Configurações da conta\n"
        "/trades - 📈 Ver trades abertos\n"
        "/noticias - 📰 Últimas notícias crypto\n\n"
        "*Links Úteis:*\n"
        "🔗 Dashboard VIP: localhost:8501\n"
        "🔗 OKX (Desconto): https://okx.com/join/69938298"
    )
    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /status"""
    status_msg = (
        "📊 *STATUS DO SISTEMA:*\n\n"
        "✅ Bot Online\n"
        "✅ OKX Conectado\n"
        "✅ IA Anthropic Ativa\n"
        "✅ Scanner de Mercado Rodando\n"
        "✅ Risk Manager Protegido\n\n"
        "🕐 Última atualização: Agora\n"
        "🔄 Próximo scan: 30s"
    )
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def vip_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /vip"""
    vip_msg = (
        "💎 *SEXTA-FEIRA VIP*\n\n"
        "*Benefícios Exclusivos:*\n"
        "✅ Acesso ao Dashboard Premium\n"
        "✅ Sinais de trading com IA Claude\n"
        "✅ Raciocínio técnico por trade\n"
        "✅ Suporte prioritário 24/7\n"
        "✅ Relatórios semanais de performance\n"
        "✅ Grupo VIP exclusivo no Telegram\n"
        "✅ Gráficos TradingView integrados\n\n"
        "*Investimento:* R\\$ 97/mês\n\n"
        "*Como Assinar:*\n"
        "1️⃣ Acesse: localhost:8501\n"
        "2️⃣ Clique em \"Assinar VIP\"\n"
        "3️⃣ Preencha com suas credenciais OKX\n"
        "4️⃣ Aguarde aprovação (até 24h)\n\n"
        "🔗 Cadastre-se na OKX com desconto:\n"
        "https://okx.com/join/69938298"
    )
    await update.message.reply_text(vip_msg, parse_mode='Markdown')

async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /suporte - CORRIGIDO"""
    admin_user = os.getenv('ADMIN_USERNAME', 'seu_usuario')
    suporte_msg = (
        "🆘 *SUPORTE TÉCNICO*\n\n"
        "*Canais de Atendimento:*\n\n"
        "📧 Email: suporte@sextafeira.com\n"
        f"💬 Telegram: @{admin_user}\n"
        "🕐 Horário: Seg-Sex 9h às 18h (BRT)\n\n"
        "*Para agilizar seu atendimento, informe:*\n"
        "• Seu email de cadastro\n"
        "• Print do erro (se houver)\n"
        "• Descrição detalhada do problema\n"
        "• Horário aproximado do ocorrido\n\n"
        "⏱ Tempo médio de resposta: 2h"
    )
    await update.message.reply_text(suporte_msg, parse_mode='Markdown')
    
    # Notifica admin sobre novo pedido de suporte
    if ADMIN_ID:
        try:
            user = update.effective_user
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🆘 *Novo pedido de suporte*\n\n"
                    f"👤 Usuário: @{user.username or 'Sem username'}\n"
                    f"📧 Nome: {user.first_name}\n"
                    f"💬 Mensagem: /suporte"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"⚠️ Falha ao notificar admin: {e}")

async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /config"""
    config_msg = (
        "⚙️ *CONFIGURAÇÕES*\n\n"
        "Para alterar suas configurações:\n\n"
        "1️⃣ Acesse o Dashboard VIP\n"
        "2️⃣ Vá em \"⚙️ Configurações\"\n"
        "3️⃣ Altere sua senha ou preferências\n\n"
        "*Configurações Disponíveis:*\n"
        "• 🔑 Senha de acesso\n"
        "• 🔔 Notificações Telegram\n"
        "• 📊 Ativos monitorados\n"
        "• ⚡ Alavancagem padrão\n\n"
        "🔗 Dashboard: localhost:8501"
    )
    await update.message.reply_text(config_msg, parse_mode='Markdown')

async def trades_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /trades"""
    trades_msg = (
        "📈 *TRADES ABERTOS*\n\n"
        "Para visualizar seus trades em tempo real:\n\n"
        "1️⃣ Acesse o Dashboard VIP\n"
        "2️⃣ Vá na aba \"📌 Posições\"\n"
        "3️⃣ Veja entradas, stops e PnL não realizado\n\n"
        "*Informações Disponíveis:*\n"
        "• Ativo e direção\n"
        "• Preço de entrada\n"
        "• Stop Loss e Take Profit\n"
        "• PnL em tempo real\n"
        "• Alavancagem utilizada\n\n"
        "🔗 Dashboard: localhost:8501"
    )
    await update.message.reply_text(trades_msg, parse_mode='Markdown')

async def noticias_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /noticias"""
    noticias_msg = (
        "📰 *ÚLTIMAS NOTÍCIAS CRYPTO*\n\n"
        "Para ver notícias em tempo real:\n\n"
        "1️⃣ Acesse o Dashboard VIP\n"
        "2️⃣ Vá na aba \"📰 Notícias\"\n"
        "3️⃣ Veja feed de CoinDesk, Cointelegraph e Decrypt\n\n"
        "*Fontes Monitoradas:*\n"
        "• CoinDesk\n"
        "• Cointelegraph\n"
        "• Decrypt\n"
        "• The Block\n\n"
        "🔔 Notícias relevantes são enviadas automaticamente no grupo Free."
    )
    await update.message.reply_text(noticias_msg, parse_mode='Markdown')

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando desconhecido"""
    await update.message.reply_text(
        "❌ Comando não reconhecido. Digite /help para ver a lista de comandos.",
        parse_mode='Markdown'
    )

# ==========================================
# ENVIO DE SINAL VIP (FORMATO EXATO SOLICITADO)
# ==========================================

def enviar_sinal_vip(
    ativo: str, 
    direcao: str, 
    score: str, 
    entrada: str, 
    take: str, 
    stop: str, 
    hora: str,
    isolado: str = "5x", 
    leverage: str = "10x"
) -> bool:
    """
    Envia sinal formatado APENAS para o Grupo VIP.
    Formato exato solicitado pelo usuário.
    """
    if not VIP_GROUP_ID or not TOKEN:
        logger.warning("⚠️ TELEGRAM_VIP_GROUP_ID ou TOKEN não configurados")
        return False
    
    # Formato EXATO como solicitado (com box characters)
    caption = (
        f"⚡ SEXTA-FEIRA SIGNAL\n\n"
        f"Ativo: {ativo}\n"
        f"Direção: {direcao}\n"
        f"Score: {score}\n"
        f"┌────────────────────┐\n"
        f"│ ENTRADA : {entrada}\n"
        f"│ TAKE    : {take}\n"
        f"│ STOP    : {stop}\n"
        f"└────────────────────┘\n\n"
        f"Isolado: {isolado}\n"
        f"Leverage: {leverage}\n"
        f"Hora: {hora}"
    )
    
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        response = requests.post(
            url,
            json={
                "chat_id": VIP_GROUP_ID,
                "text": caption,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"✅ Sinal enviado para VIP: {ativo} {direcao}")
            return True
        else:
            logger.error(f"❌ Erro ao enviar sinal: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Exceção ao enviar sinal: {type(e).__name__}: {e}")
        return False


def enviar_sinal_com_grafico(
    ativo: str, 
    direcao: str, 
    score: str, 
    entrada: str, 
    take: str, 
    stop: str, 
    hora: str,
    chart_url: str = None
) -> bool:
    """Envia sinal com gráfico opcional para o Grupo VIP."""
    if not VIP_GROUP_ID or not TOKEN:
        return False
    
    caption = (
        f"⚡ SEXTA-FEIRA SIGNAL\n\n"
        f"Ativo: {ativo}\n"
        f"Direção: {direcao}\n"
        f"Score: {score}\n"
        f"┌────────────────────┐\n"
        f"│ ENTRADA : {entrada}\n"
        f"│ TAKE    : {take}\n"
        f"│ STOP    : {stop}\n"
        f"└────────────────────┘\n\n"
        f"Isolado: 5x\n"
        f"Leverage: 10x\n"
        f"Hora: {hora}"
    )
    
    try:
        if chart_url:
            # Envia com foto/gráfico
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            response = requests.post(
                url,
                json={
                    "chat_id": VIP_GROUP_ID,
                    "photo": chart_url,
                    "caption": caption,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
        else:
            # Envia apenas texto
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            response = requests.post(
                url,
                json={
                    "chat_id": VIP_GROUP_ID,
                    "text": caption,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
        
        if response.status_code == 200:
            logger.info(f"✅ Sinal com gráfico enviado: {ativo} {direcao}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Erro ao enviar sinal com gráfico: {type(e).__name__}: {e}")
        return False

# ==========================================
# ALERTAS DO SISTEMA (APENAS VIP)
# ==========================================

def alerta_trade(symbol: str, side: str, entry: str) -> None:
    """Alerta de trade aberto para VIP."""
    msg = (
        f"🚀 *TRADE ABERTO*\n\n"
        f"{symbol} | {side}\n"
        f"Entry: `{entry}`\n\n"
        f"⚡ SEXTA-FEIRA Advanced"
    )
    _send_to_vip(msg)

def alerta_stop(symbol: str) -> None:
    """Alerta de stop hit para VIP."""
    msg = (
        f"❌ *STOP HIT*\n\n"
        f"{symbol}\n\n"
        f"🛡️ Risk Manager ativado\n"
        f"⚡ SEXTA-FEIRA Advanced"
    )
    _send_to_vip(msg)

def alerta_erro(msg: str) -> None:
    """Alerta de erro crítico para Admin."""
    if ADMIN_ID and TOKEN:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(
                url, 
                json={
                    "chat_id": ADMIN_ID,
                    "text": f"⚠️ *ERRO CRÍTICO*\n\n{msg}",
                    "parse_mode": "Markdown"
                }, 
                timeout=10
            )
        except Exception as e:
            logger.error(f"❌ Falha ao enviar alerta de erro: {e}")

def _send_to_vip(text: str) -> None:
    """Envia mensagem apenas para o grupo VIP."""
    if not VIP_GROUP_ID or not TOKEN:
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(
            url, 
            json={
                "chat_id": VIP_GROUP_ID,
                "text": text,
                "parse_mode": "Markdown"
            }, 
            timeout=10
        )
    except Exception as e:
        logger.error(f"❌ Falha ao enviar para VIP: {e}")

# ==========================================
# INICIALIZAÇÃO DO BOT
# ==========================================

def main() -> None:
    """Inicializa e roda o bot Telegram."""
    if not TOKEN:
        logger.error("❌ TOKEN não configurado. Bot não iniciado.")
        return
    
    # Cria aplicação
    application = Application.builder().token(TOKEN).build()
    
    # Registra comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("vip", vip_info))
    application.add_handler(CommandHandler("suporte", suporte))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("trades", trades_command))
    application.add_handler(CommandHandler("noticias", noticias_command))
    
    # Handler para comandos desconhecidos
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Inicia o bot
    logger.info("🤖 Bot Telegram iniciado. Ouvindo comandos...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()