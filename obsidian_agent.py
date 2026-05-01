# obsidian_agent.py - AGENTE DE ESCRITA AUTOMÁTICA (VERSÃO FINAL BLINDADA)
# Gera, atualiza e mantém notas do Obsidian sem intervenção manual.
# Thread-safe, Dataview-ready, YAML válido.
# FIX: Sintaxe corrigida + construção de strings em partes para evitar conflito """ + ```

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from config import OBSIDIAN_TRADES_PATH, DB_NAME

class ObsidianAgent:
    def __init__(self, vault_path: str = None, db_name: str = "jarvis_trades.db"):
        self.vault = Path(vault_path or OBSIDIAN_TRADES_PATH).resolve()
        self.vault.mkdir(parents=True, exist_ok=True)
        self.db_path = self.vault.parent / db_name
        self._lock = Lock()
        (self.vault / "trades").mkdir(exist_ok=True)
        (self.vault / "reports").mkdir(exist_ok=True)

    def _get_db_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def log_trade(self, trade_data: dict) -> Path:
        symbol = trade_data.get("symbol", "UNKNOWN")
        side = trade_data.get("side", "LONG")
        ts = trade_data.get("open_time", datetime.now())
        filename = "{:%Y-%m-%d_%H-%M}_{}_{}.md".format(ts, symbol, side)
        filepath = self.vault / "trades" / filename

        # YAML em string simples (sem backticks)
        yaml = (
            "---\n"
            "tipo: trade\n"
            "ativo: \"{}\"\n"
            "direcao: \"{}\"\n"
            "data_abertura: \"{}\"\n"
            "entry: {}\n"
            "stop: {}\n"
            "take: {}\n"
            "qty: {}\n"
            "score: {}\n"
            "status: \"{}\"\n"
            "pnl_usdt: {:.2f}\n"
            "tags: [trade, {}, {}]\n"
            "---\n"
        ).format(
            symbol, side,
            ts.strftime("%Y-%m-%d %H:%M:%S"),
            trade_data.get("entry", 0),
            trade_data.get("stop", 0),
            trade_data.get("take", 0),
            trade_data.get("qty", 0),
            trade_data.get("score", 0),
            trade_data.get("status", "OPEN"),
            trade_data.get("pnl_usdt", 0.0),
            symbol, side
        )

        # Corpo sem blocos de código (apenas texto)
        body = (
            "# 🟣 Trade — {} {}\n\n"
            "> [!INFO] Dados da Operação\n"
            "> - **Entry**: ${}\n"
            "> - **Stop**: ${}\n"
            "> - **Take**: ${}\n"
            "> - **Qty**: {}\n"
            "> - **Score**: {}\n"
            "> - **PnL**: ${:.2f}\n\n"
            "---\n\n"
            "## 🧠 Contexto do Setup\n"
            "- Filtros ativos: Trend HTF, Volume Confirmation, ATR Stop\n"
            "- Regime de mercado: {}\n"
            "- Gerado por: Sexta-Feira v6 em {}\n\n"
            "> [!NOTE] Atualização Automática\n"
            "> Esta nota será atualizada pela IA ao fechar a posição.\n"
        ).format(
            symbol, side,
            trade_data.get("entry", 0),
            trade_data.get("stop", 0),
            trade_data.get("take", 0),
            trade_data.get("qty", 0),
            trade_data.get("score", 0),
            trade_data.get("pnl_usdt", 0.0),
            trade_data.get("regime", "NEUTRO"),
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        content = yaml + body
        with self._lock:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        return filepath

    def update_trade_close(self, symbol: str, side: str, open_time: str, pnl: float, status: str = "CLOSED"):
        ts = open_time.replace(":", "-").replace(" ", "_")
        filename = "{}_{}_{}.md".format(ts, symbol, side)
        filepath = self.vault / "trades" / filename
        if not filepath.exists():
            return

        with self._lock:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                if line.startswith("pnl_usdt:"):
                    line = "pnl_usdt: {:.2f}\n".format(pnl)
                elif line.startswith("status:"):
                    line = 'status: "{}"\n'.format(status)
                elif line.startswith("data_fechamento:"):
                    line = 'data_fechamento: "{}"\n'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    new_lines.append(line)
            if "data_fechamento:" not in "".join(lines):
                new_lines.insert(5, 'data_fechamento: "{}"\n'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

    def generate_daily_report(self, date_str: str = None) -> Path:
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        filename = "{}_Relatorio_Diario.md".format(date_str)
        filepath = self.vault / "reports" / filename

        conn = self._get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN pnl_usdt > 0 THEN 1 ELSE 0 END) as wins,
                   SUM(pnl_usdt) as pnl
            FROM trades WHERE DATE(close_time) = ? OR DATE(open_time) = ?
        """, (date_str, date_str))
        row = cur.fetchone()
        total, wins, pnl = (row.total, row.wins, row.pnl) if row else (0, 0, 0.0)
        wr = (wins / total * 100) if total > 0 else 0
        conn.close()

        # Query Dataview em variável separada para evitar conflito de parsing
        dataview_query = (
            "```dataview\n"
            "TABLE ativo, direcao, entry, pnl_usdt, status\n"
            "FROM \"trades\"\n"
            "WHERE tipo = \"trade\" AND contains(data_abertura, \"{}\")\n"
            "SORT data_abertura ASC\n"
            "```"
        ).format(date_str)

        yaml_part = (
            "---\n"
            "tipo: relatorio_diario\n"
            "data: \"{}\"\n"
            "trades: {}\n"
            "wins: {}\n"
            "losses: {}\n"
            "pnl: {:.2f}\n"
            "win_rate: {:.1f}\n"
            "tags: [report, daily, {}]\n"
            "---\n\n"
        ).format(date_str, total, wins, total - wins, pnl, wr, date_str)

        header_part = (
            "# 📊 Relatório Diário — {}\n\n"
            "> [!SUMMARY] Resumo\n"
            "> - **Trades**: {} | **Wins**: {} | **Losses**: {}\n"
            "> - **Win Rate**: {:.1f}%\n"
            "> - **PnL**: ${:.2f}\n\n"
            "---\n\n"
            "## 📈 Trades do Dia\n"
        ).format(date_str, total, wins, total - wins, wr, pnl)

        content = yaml_part + header_part + dataview_query + "\n\n> [!TIP] Nota da Sexta-Feira\n> Se Win Rate < 40% ou PnL < -$2.00, revisar filtros de entrada e session_filter.\n"

        with self._lock:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        return filepath

    def generate_monthly_performance(self, year_month: str = None) -> Path:
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")
        filename = "{}_Performance.md".format(year_month)
        filepath = self.vault / "reports" / filename

        metrics_block = (
            "> [!SUMMARY] Métricas (Calculadas via Dataview)\n"
            "> - **Trades**: `=length(rows)`\n"
            "> - **PnL Total**: `$=round(sum(pnl_usdt), 2)`\n"
            "> - **Win Rate**: `$=round(sum(pnl_usdt > 0) / length(rows) * 100, 1)`%\n"
        )

        dataview_query = (
            "```dataview\n"
            "TABLE ativo, direcao, entry, pnl_usdt, score, status\n"
            "FROM \"trades\"\n"
            "WHERE tipo = \"trade\" AND startsWith(data_abertura, \"{}\")\n"
            "SORT data_abertura ASC\n"
            "```"
        ).format(year_month)

        yaml_part = (
            "---\n"
            "tipo: performance_mensal\n"
            "periodo: \"{}\"\n"
            "banca_inicial: 60.00\n"
            "banca_final: null\n"
            "pnl_total: null\n"
            "win_rate: null\n"
            "trades_total: null\n"
            "tags: [performance, monthly, {}]\n"
            "---\n\n"
        ).format(year_month, year_month)

        header_part = "# 📊 Performance — {}\n\n".format(year_month)

        footer_note = (
            "\n> [!NOTE] Atualização Manual\n"
            "> Preencha `banca_final` no frontmatter no dia 1º do próximo mês.\n"
            "> A Sexta-Feira atualiza pnl_total e win_rate automaticamente via Dataview.\n"
        )

        content = yaml_part + header_part + metrics_block + "\n---\n\n## 📋 Trades do Mês\n" + dataview_query + footer_note

        with self._lock:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        return filepath