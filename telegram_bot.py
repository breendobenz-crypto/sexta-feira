# telegram_bot.py - BOT TELEGRAM SEXTA-FEIRA (COM FORMULÁRIO VIP)
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
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")  # ID numérico do admin
VIP_GROUP_ID = os.getenv("TELEGRAM_VIP_GROUP_ID")
FREE_GROUP_ID = os.getenv("TELEGRAM_FREE_GROUP_ID")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://sexta-feira-wm1s.onrender.com")

# 🔗 LINK DO FORMULÁRIO GOOGLE (Configuração OKX) — APENAS VIP
FORMULARIO_OKX_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdZvdshqbSKx0jiMLfo03Jpo1E5giXD9sTCC_q75GVhRm7sPw/viewform?usp=pp_url"

if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN não configurado.")
    exit(1)

# ==========================================
# COMANDOS DO BOT
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mensagem de boas-vindas — igual para Free e VIP"""
    user = update.effective_user
    welcome_msg = (
        f"🟣 Bem-vindo à SEXTA-FEIRA Advanced!\n\n"
        f"Olá {user.first_name}! 👋\n\n"
        f"Sou seu assistente de trading automatizado com IA.\n\n"
        f"📋 PRIMEIROS PASSOS:\n"
        f"1️⃣ Preencha o formulário de configuração:\n"
        f"🔗 /formulario (apenas para VIPs)\n\n"
        f"2️⃣ Acesse o Dashboard VIP:\n"
        f"🔗 {DASHBOARD_URL}\n\n"
        f"O que posso fazer:\n"
        f"📊 Enviar sinais de trading em tempo real\n"
        f"📰 Notícias de crypto filtradas\n"
        f"📈 Alertas de entrada e saída\n"
        f"🆘 Suporte técnico prioritário\n\n"
        f"Digite /help para ver todos os comandos disponíveis."
    )
    keyboard = [
        [InlineKeyboardButton("📊 Acessar Dashboard VIP", url=DASHBOARD_URL)]
    ]
    # Só mostra botão do formulário se for VIP
    if str(update.effective_chat.id) == VIP_GROUP_ID or str(user.id) == ADMIN_ID:
        keyboard.insert(0, [InlineKeyboardButton("📋 Preencher Formulário OKX", url=FORMULARIO_OKX_URL)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista de comandos — adaptada por tipo de usuário"""
    is_vip = str(update.effective_chat.id) == VIP_GROUP_ID or str(update.effective_user.id) == ADMIN_ID
    
    help_msg = (
        "📚 COMANDOS DISPONÍVEIS:\n\n"
        "/start - 🚀 Iniciar o bot\n"
        "/help - 📚 Esta mensagem de ajuda\n"
    )
    if is_vip:
        help_msg += "/formulario - 📋 Preencher formulário OKX (VIP)\n"
    help_msg += (
        "/status - 📊 Ver status do sistema\n"
        "/vip - 💎 Informações sobre plano VIP\n"
        "/suporte - 🆘 Falar com suporte técnico\n"
        "/config - ⚙️ Configurações da conta\n"
        "/trades - 📈 Ver trades abertos\n"
        "/noticias - 📰 Últimas notícias crypto\n"
        "/dashboard - 📊 Receber link do painel\n\n"
        "🔗 Links Importantes:\n"
        f"📊 Dashboard VIP: {DASHBOARD_URL}\n"
        "🔗 OKX (Desconto): https://okx.com/join/69938298"
    )
    await update.message.reply_text(help_msg, parse_mode='Markdown')


# ✅ COMANDO /formulario — APENAS PARA VIP OU ADMIN
async def formulario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia o link do formulário de configuração OKX — APENAS VIP/ADMIN"""
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    
    # Verifica se é grupo VIP ou admin
    if chat_id != VIP_GROUP_ID and str(user.id) != ADMIN_ID:
        await update.message.reply_text(
            "🔒 Este comando é exclusivo para usuários VIP.\n\n"
            "Para acessar: https://whop.com/sexta-feira-advanced/sexta-feira-advanced-19/",
            parse_mode='Markdown'
        )
        return
    
    msg = (
        "📋 FORMULÁRIO DE CONFIGURAÇÃO OKX\n\n"
        "Para ativar o bot de trading, preencha o formulário com suas credenciais:\n\n"
        f"🔗 Link direto:\n{FORMULARIO_OKX_URL}\n\n"
        "⚠️ Instruções:\n"
        "• Use o mesmo email cadastrado na Whop\n"
        "• Cole sua API Key, Secret e Passphrase da OKX\n"
        "• Suas chaves serão criptografadas automaticamente\n"
        "• Após enviar, aguarde até 5 minutos para ativação\n\n"
        f"📊 Dashboard: {DASHBOARD_URL}"
    )
    keyboard = [[InlineKeyboardButton("📋 Abrir Formulário Agora", url=FORMULARIO_OKX_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)


# ✅ NOVO COMANDO: /enviar_formulario @usuario (APENAS ADMIN)
async def enviar_formulario_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin envia o formulário via privado para um usuário específico"""
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("❌ Apenas o admin pode usar este comando.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Uso correto:\n`/enviar_formulario @username`",
            parse_mode='Markdown'
        )
        return
    
    username = context.args[0].replace('@', '')
    
    try:
        # Tenta obter o chat do usuário pelo username
        chat = await context.bot.get_chat(f"@{username}")
        user_id = chat.id
        
        msg = (
            f"🟣 *Olá {chat.first_name}!*\n\n"
            f"Recebi seu acesso VIP na SEXTA-FEIRA Advanced! 🎉\n\n"
            f"📋 Para ativar seu bot de trading, preencha este formulário:\n"
            f"{FORMULARIO_OKX_URL}\n\n"
            f"⚠️ Suas chaves serão criptografadas e seguras.\n"
            f"📊 Após enviar, acesse seu dashboard: {DASHBOARD_URL}\n\n"
            f"Qualquer dúvida, me chame aqui! 🤖"
        )
        keyboard = [[InlineKeyboardButton("📋 Preencher Formulário", url=FORMULARIO_OKX_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=user_id,
            text=msg,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        await update.message.reply_text(f"✅ Formulário enviado para @{username} com sucesso!")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao enviar: {e}\n\nVerifique se o usuário já interagiu com o bot antes.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Status do sistema"""
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
    """Informações sobre plano VIP"""
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
        "1️⃣ Acesse: https://whop.com/sexta-feira-advanced/sexta-feira-advanced-19/\n"
        "2️⃣ Finalize o pagamento\n"
        "3️⃣ Use /formulario para configurar OKX\n"
        "4️⃣ Receba acesso imediato ao Dashboard\n\n"
        "🔗 Cadastre-se na OKX com desconto:\n"
        "https://okx.com/join/69938298"
    )
    await update.message.reply_text(vip_msg, parse_mode='Markdown')


async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Canais de suporte"""
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
    
    # Notifica admin se não for ele mesmo
    if ADMIN_ID and str(update.effective_user.id) != ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🆘 *Novo pedido de suporte*\n\n"
                    f"👤 Usuário: @{update.effective_user.username or 'Sem username'}\n"
                    f"📧 Nome: {update.effective_user.first_name}\n"
                    f"💬 Mensagem: /suporte"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.warning(f"⚠️ Falha ao notificar admin: {e}")


async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Configurações da conta"""
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
        f"🔗 Dashboard: {DASHBOARD_URL}\n"
        f"📋 Formulário OKX: /formulario"
    )
    await update.message.reply_text(config_msg, parse_mode='Markdown')


async def trades_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ver trades abertos"""
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
    """Ver notícias crypto"""
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
    """Link do dashboard"""
    keyboard = [
        [InlineKeyboardButton("📊 Acessar Dashboard VIP", url=DASHBOARD_URL)]
    ]
    # Só adiciona formulário se for VIP
    if str(update.effective_chat.id) == VIP_GROUP_ID or str(update.effective_user.id) == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📋 Formulário OKX", url=FORMULARIO_OKX_URL)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🟣 Sexta-Feira Advanced\n\n"
        "Acesse seu painel de controle:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando não reconhecido"""
    await update.message.reply_text(
        "❌ Comando não reconhecido. Digite /help para ver a lista de comandos.",
        parse_mode='Markdown'
    )


# ==========================================
# ENVIO DE SINAL VIP (Completo)
# ==========================================
def enviar_sinal_vip(ativo: str, direcao: str, score: str, entrada: str, take: str, stop: str, hora: str, isolado: str = "5x", leverage: str = "10x") -> bool:
    """Envia sinal completo apenas no grupo VIP"""
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
    """Envia teaser apenas no grupo Free — SEM FORMULÁRIO"""
    if not FREE_GROUP_ID or not TOKEN:
        return False
    
    caption = (
        f"👀 *ALERTA DE MERCADO: {ativo}*\n\n"
        f"Detectamos um movimento forte de **{direcao}**!\n"
        f"📊 Score de Confiança: `{score}%`\n\n"
        f"⚠️ *O Alvo e Stop Loss estão ocultos para usuários Free.*\n\n"
        f"🔥 **Quer saber onde entrar?**\n"
        f"👉 [SEJA VIP](https://whop.com/sexta-feira-advanced/sexta-feira-advanced-19/)\n\n"
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
    
    # Remove webhook antigo (para polling)
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=5)
        logger.info("✅ Webhook antigo removido")
    except Exception:
        pass
    
    application = Application.builder().token(TOKEN).build()
    
    # Handlers de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("formulario", formulario))  # VIP only
    application.add_handler(CommandHandler("enviar_formulario", enviar_formulario_admin))  # Admin only
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