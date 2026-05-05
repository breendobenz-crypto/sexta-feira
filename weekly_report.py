# weekly_report.py - Relatório Semanal Automático SEXTA-FEIRA
import os
import sys
import logging
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger(__name__)

try:
    from saas_db import get_active_users, get_user_stats
except ImportError as e:
    logger.error(f"❌ Erro ao importar saas_db: {e}")
    sys.exit(1)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_VIP_GROUP_ID = os.getenv("TELEGRAM_VIP_GROUP_ID")

def send_report():
    logger.info("🟣 Iniciando Relatório Semanal SEXTA-FEIRA")
    report = f"📊 **RELATÓRIO SEMANAL SEXTA-FEIRA** 📊\n📅 Semana: {datetime.now().strftime('%d/%m/%Y')}\n\n"
    
    users = get_active_users()
    if not users:
        report += "😴 Nenhum VIP ativo esta semana."
    else:
        total_trades, total_pnl, total_wins, total_losses = 0, 0.0, 0, 0
        user_stats = []
        for uid in users:
            stats = get_user_stats(uid)
            t, p, w, l = stats.get('total_trades', 0), stats.get('total_pnl', 0), stats.get('wins', 0), stats.get('losses', 0)
            total_trades += t; total_pnl += p; total_wins += w; total_losses += l
            user_stats.append({'uid': uid, 'trades': t, 'pnl': p, 'wr': (w/t*100) if t > 0 else 0})
        
        overall_wr = (total_wins/total_trades*100) if total_trades > 0 else 0
        report += f"👥 **VIPs Ativos:** {len(users)}\n🔄 **Total de Trades:** {total_trades}\n🏆 **Win Rate Geral:** {overall_wr:.1f}%\n💰 **PnL Agregado:** ${total_pnl:.2f}\n\n"
        
        if user_stats:
            report += "🏅 **TOP PERFORMERS:**\n"
            for i, u in enumerate(sorted(user_stats, key=lambda x: x['pnl'], reverse=True)[:3], 1):
                report += f"{'🥇' if i==1 else '🥈' if i==2 else '🥉'} #{i}: ${u['pnl']:.2f} ({u['wr']:.1f}% WR)\n"
    
    report += "\n---\n🟣 **SEXTA-FEIRA ADVANCED**\n_Relatório gerado automaticamente_"
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_VIP_GROUP_ID:
        logger.error("❌ Telegram não configurado. Report gerado no console:")
        print(report)
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={"chat_id": TELEGRAM_VIP_GROUP_ID, "text": report, "parse_mode": "Markdown"}, timeout=10)
        if resp.status_code == 200: logger.info("✅ Relatório enviado com sucesso!")
        else: logger.error(f"❌ Erro ao enviar: {resp.text}")
    except Exception as e: logger.error(f"❌ Erro de rede: {e}")

if __name__ == "__main__":
    send_report()