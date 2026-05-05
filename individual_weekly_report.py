# individual_weekly_report.py
import os, sys, logging, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger(__name__)

try:
    from saas_db import get_active_users, get_user_stats, get_user_by_email
except ImportError as e:
    logger.error(f"❌ Erro ao importar saas_db: {e}")
    sys.exit(1)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_individual_reports():
    logger.info("🟣 Iniciando Relatórios Individuais Semanais...")
    users = get_active_users()
    if not users:
        logger.info("💤 Nenhum VIP ativo.")
        return

    for user_id in users:
        try:
            stats = get_user_stats(user_id)
            # Busca telegram_chat_id (ajuste conforme sua estrutura real)
            # Aqui assumimos que get_user_by_email retorna o chat_id
            user = get_user_by_email(f"{user_id}@example.com")  # Ajuste conforme necessário
            chat_id = user.get("telegram_chat_id") if user else None
            
            if not chat_id:
                logger.warning(f"💤 {user_id} sem telegram_chat_id. Pulando.")
                continue

            wr = stats.get("win_rate", 0) * 100
            pnl = stats.get("total_pnl", 0)
            trades = stats.get("total_trades", 0)

            report = f"""📊 **SEXTA-FEIRA — SEU RELATÓRIO SEMANAL**
👤 **Usuário:** {user_id}
📅 Período: {datetime.now().strftime('%d/%m/%Y')}

📈 **SEU DESEMPENHO:**
• 🔄 Trades: `{trades}`
• 🎯 Win Rate: `{wr:.1f}%`
• 💰 PnL Total: `${pnl:+.2f}`

🧠 *Dica da IA:* Mantenha a gestão de risco. O bot se adapta ao mercado.

🟣 **SEXTA-FEIRA ADVANCED**"""

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            resp = requests.post(url, json={"chat_id": chat_id, "text": report, "parse_mode": "Markdown"}, timeout=10)
            if resp.status_code == 200:
                logger.info(f"✅ Relatório enviado para {user_id}")
            else:
                logger.error(f"❌ Falha para {user_id}: {resp.text}")
        except Exception as e:
            logger.error(f"💥 Erro ao processar {user_id}: {e}")

if __name__ == "__main__":
    send_individual_reports()