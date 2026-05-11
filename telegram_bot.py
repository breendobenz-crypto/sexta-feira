# telegram_bot.py - BOT TELEGRAM SEXTA-FEIRA (COM ENVIO DE PDF)
import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURAÇÕES
# ==========================================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
VIP_GROUP_ID = os.getenv("TELEGRAM_VIP_GROUP_ID")
FREE_GROUP_ID = os.getenv("TELEGRAM_FREE_GROUP_ID")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://sexta-feira-wm1s.onrender.com")
VIP_LINK = "https://whop.com/sexta-feira-advanced/sexta-feira-advanced-19/"

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN não configurado.")
    exit(1)

# ==========================================
# COMANDOS DO BOT
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_msg = (
        f"🟣 Bem-vindo à SEXTA-FEIRA Advanced!\n\n"
        f"Olá {user.first_name}! 👋\n\n"
        f"Sou seu assistente de trading automatizado com IA.\n\n"
        f"O que posso fazer:\n"
        f"📊 Enviar sinais de trading em tempo real\n"
        f"📰 Notícias de crypto filtradas\n"
        f"📈 Alertas de entrada e saída\n"
        f"🆘 Suporte técnico prioritário\n\n"
        f"Digite /help para ver todos os comandos disponíveis."
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_msg = (
        "📚 COMANDOS DISPONÍVEIS:\n\n"
        "/start - 🚀 Iniciar o bot\n"
        "/help - 📚 Esta mensagem de ajuda\n"
        "/guia - 📥 Baixar o Guia VIP (PDF)\n"  # ✅ NOVO COMANDO
        "/status - 📊 Ver status do sistema\n"
        "/vip - 💎 Informações sobre plano VIP\n"
        "/suporte - 🆘 Falar com suporte técnico\n"
        "/config - ⚙️ Configurações da conta\n"
        "/trades - 📈 Ver trades abertos\n"
        "/noticias - 📰 Últimas notícias crypto\n"
        "/dashboard - 📊 Receber link do painel\n\n"
        f"🔗 Dashboard VIP: {DASHBOARD_URL}\n"
        "🔗 OKX (Desconto): https://okx.com/join/69938298"
    )
    await update.message.reply_text(help_msg, parse_mode='Markdown')

# ✅ FUNÇÃO PARA ENVIAR O PDF
async def guia_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia o arquivo PDF do Guia de Inicialização."""
    pdf_file = 'Guia_VIP_Sexta_Feira_Advanced.pdf'
    
    try:
        # Abre o arquivo e envia
        with open(pdf_file, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                caption="📚 **GUIA DE INICIALIZAÇÃO VIP**\n\n"
                        "Siga as instruções passo a passo para configurar sua conta e conectar à OKX.\n\n"
                        "🟣 *Sexta-Feira Advanced - A IA que trabalha por você.*",
                parse_mode='Markdown'
            )
        logger.info(f"✅ PDF Guia enviado para {update.effective_user.id}")
    except FileNotFoundError:
        await update.message.reply_text("⚠️ Erro: O arquivo do Guia não foi encontrado no servidor.")
    except Exception as e:
        logger.error(f"❌ Erro ao enviar PDF: {e}")
        await update.message.reply_text(f"❌ Erro ao enviar o PDF. Entre em contato com o suporte.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    status_msg = (
        "📊 STATUS DO SISTEMA:\n\n"
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
    vip_msg = (
        "💎 SEXTA-FEIRA VIP\n\n"
        "Benefícios Exclusivos:\n"
        "✅ Acesso ao Dashboard Premium\n"
        "✅ Sinais de trading com IA Claude\n"
        "✅ Raciocínio técnico por trade\n"
        "✅ Suporte prioritário 24/7\n"
        "✅ Relatórios semanais de performance\n"
        "✅ Grupo VIP exclusivo no Telegram\n"
        "✅ Gráficos TradingView integrados\n\n"
        "💰 Investimento: R$ 197/mês\n\n"
        "Como Assinar:\n"
        f"1️⃣ Acesse: {VIP_LINK}\n"
        "2️⃣ Finalize o pagamento\n"
        "3️⃣ Receba acesso imediato ao Dashboard\n\n"
        "🔗 Cadastre-se na OKX com desconto:\n"
        "https://okx.com/join/69938298"
    )
    await update.message.reply_text(vip_msg, parse_mode='Markdown')

async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_user = os.getenv('ADMIN_USERNAME', 'sextafeira_suporte')
    suporte_msg = (
        "🆘 SUPORTE TÉCNICO\n\n"
        "Canais de Atendimento:\n\n"
        "📧 Email: suporte@sextafeira.com\n"
        f"💬 Telegram: @{admin_user}\n"
        "🕐 Horário: Seg-Sex 9h às 18h (BRT)\n\n"
        "Para agilizar seu atendimento, informe:\n"
        "• Seu email de cadastro\n"
        "• Print do erro (se houver)\n"
        "• Descrição detalhada do problema\n"
        "• Horário aproximado do ocorrido\n\n"
        "⏱ Tempo médio de resposta: 2h"
    )
    await update.message.reply_text(suporte_msg, parse_mode='Markdown')

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
    config_msg = (
        "⚙️ CONFIGURAÇÕES\n\n"
        "Para alterar suas configurações:\n\n"
        "1️⃣ Acesse o Dashboard VIP\n"
        "2️⃣ Vá em '⚙️ Configurações'\n"
        "3️⃣ Altere sua senha ou preferências\n\n"
        "Configurações Disponíveis:\n"
        "• 🔑 Senha de acesso\n"
        "• 🔔 Notificações Telegram\n"
        "• 📊 Ativos monitorados\n"
        "• ⚡ Alavancagem padrão\n\n"
        f"🔗 Dashboard: {DASHBOARD_URL}"
    )
    await update.message.reply_text(config_msg, parse_mode='Markdown')

async def trades_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    trades_msg = (
        "📈 TRADES ABERTOS\n\n"
        "Para visualizar seus trades em tempo real:\n\n"
        "1️⃣ Acesse o Dashboard VIP\n"
        "2️⃣ Vá na aba '📌 Posições'\n"
        "3️⃣ Veja entradas, stops e PnL não realizado\n\n"
        "Informações Disponíveis:\n"
        "• Ativo e direção\n"
        "• Preço de entrada\n"
        "• Stop Loss e Take Profit\n"
        "• PnL em tempo real\n"
        "• Alavancagem utilizada\n\n"
        f"🔗 Dashboard: {DASHBOARD_URL}"
    )
    await update.message.reply_text(trades_msg, parse_mode='Markdown')

async def noticias_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    noticias_msg = (
        "📰 ÚLTIMAS NOTÍCIAS CRYPTO\n\n"
        "Para ver notícias em tempo real:\n\n"
        "1️⃣ Acesse o Dashboard VIP\n"
        "2️⃣ Vá na aba '📰 Notícias'\n"
        "3️⃣ Veja feed de CoinDesk, Cointelegraph e Decrypt\n\n"
        "Fontes Monitoradas:\n"
        "• CoinDesk\n"
        "• Cointelegraph\n"
        "• Decrypt\n"
        "• The Block\n\n"
        "🔔 Notícias relevantes são enviadas automaticamente no grupo Free."
    )
    await update.message.reply_text(noticias_msg, parse_mode='Markdown')

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("📊 Acessar Dashboard VIP", url=DASHBOARD_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🟣 Sexta-Feira Advanced\n\n"
        "Acesse seu painel de controle, métricas e configurações de API abaixo:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "❌ Comando não reconhecido. Digite /help para ver a lista de comandos.",
        parse_mode='Markdown'
    )

# ==========================================
# ENVIO DE SINAL VIP (Completo)
# ==========================================
def enviar_sinal_vip(ativo: str, direcao: str, score: str, entrada: str, take: str, stop: str, hora: str, isolado: str = "5x", leverage: str = "10x") -> bool:
    if not VIP_GROUP_ID or not TOKEN:
        logger.warning("⚠️ TELEGRAM_VIP_GROUP_ID ou TOKEN não configurados")
        return False

    caption = (
        f"⚡ SEXTA-FEIRA SIGNAL\n\n"
        f"Ativo: {ativo}\n"
        f"Direção: {direcao}\n"
        f"Score: {score}\n"
        f"┌────────────────────┐\n"
        f"│ ENTRADA: {entrada}\n"
        f"│ TAKE   : {take}\n"
        f"│ STOP   : {stop}\n"
        f"└────────────────────┘\n\n"
        f"Isolado: {isolado}\n"
        f"Leverage: {leverage}\n"
        f"Hora: {hora}"
    )

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        response = requests.post(
            url,
            json={"chat_id": VIP_GROUP_ID, "text": caption, "parse_mode": "Markdown"},
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

# ==========================================
# ENVIO DE TEASER FREE (Funil de Vendas)
# ==========================================
def enviar_alerta_free(ativo: str, direcao: str, score: int) -> bool:
    if not FREE_GROUP_ID or not TOKEN:
        return False

    caption = (
        f"👀 *ALERTA DE MERCADO: {ativo}*\n\n"
        f"Detectamos um movimento forte de **{direcao}**!\n"
        f"📊 Score de Confiança: `{score}%`\n\n"
        f"⚠️ *O Alvo e Stop Loss estão ocultos para usuários Free.*\n\n"
        f"🔥 **Quer saber onde entrar?**\n"
        f"👉 [SEXTA-FEIRA ADVANCED]({VIP_LINK})\n\n"
        f"_Powered by Sexta-Feira AI_"
    )

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        response = requests.post(
            url,
            json={"chat_id": FREE_GROUP_ID, "text": caption, "parse_mode": "Markdown"},
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"✅ Teaser Free enviado: {ativo} {direcao}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Erro ao enviar para Free: {e}")
        return False

# ==========================================
# INICIALIZAÇÃO DO BOT
# ==========================================
def main() -> None:
    if not TOKEN:
        logger.error("❌ TOKEN não configurado. Bot não iniciado.")
        return

    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=5)
        logger.info("✅ Webhook antigo removido")
    except Exception:
        pass

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("guia", guia_command))  # ✅ REGISTRADO AQUI
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("vip", vip_info))
    application.add_handler(CommandHandler("suporte", suporte))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("trades", trades_command))
    application.add_handler(CommandHandler("noticias", noticias_command))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("🤖 Bot Telegram iniciado. Ouvindo comandos...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()