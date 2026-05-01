# ==========================================
# BRAIN ANALYST - CLAUDE (Anthropic)
# Análise profunda dos trades via Claude API (Sonnet 3.5)
# Substitui a análise local e gera insights semanais
# ==========================================
import os
import glob
import anthropic
from datetime import datetime, timedelta
from database import get_all_closed_trades

# Configuração de Diretórios
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Padrão: Pasta 'trades' na raiz do projeto (se não definir env var)
OBSIDIAN_PATH = os.getenv("OBSIDIAN_PATH", os.path.join(_SCRIPT_DIR, "trades"))

# ----------------------------------------
# Fonte 1: Notas Markdown do Obsidian (Segundo Cérebro)
# ----------------------------------------
def get_trade_notes(days: int = 7) -> str:
    """Lê notas recentes da pasta de trades (ou onde você configurou o Obsidian)."""
    if not os.path.exists(OBSIDIAN_PATH):
        print(f"[CLAUDE WARN] Pasta Obsidian não encontrada em {OBSIDIAN_PATH}")
        return ""
    
    cutoff  = datetime.now() - timedelta(days=days)
    content = []
    
    try:
        for f in glob.glob(os.path.join(OBSIDIAN_PATH, "*.md")):
            # Filtra por data de modificação
            file_mtime = datetime.fromtimestamp(os.path.getmtime(f))
            if file_mtime > cutoff:
                with open(f, encoding="utf-8") as fh:
                    # Lê apenas os primeiros 2000 chars para economizar tokens
                    content.append(fh.read()[:2000])
    except Exception as e:
        print(f"[CLAUDE ERROR] Erro ao ler notas: {e}")
        
    return "\n---\n".join(content)


# ----------------------------------------
# Fonte 2: Trades do banco de dados (SQLite)
# ----------------------------------------
def get_db_summary(limit: int = 50) -> str:
    """Extrai um resumo textual dos últimos trades para o prompt."""
    trades = get_all_closed_trades(limit=limit)
    if not trades:
        return "Nenhum trade fechado no banco."
    
    lines = ["symbol | side | entry | exit | pnl_usdt | pnl_pct | score | close_time"]
    for t in trades:
        # Usa chaves compatíveis com database.py (entry_price)
        lines.append(
            f"{t['symbol']} | {t['side']} | {t['entry_price']:.2f} | "
            f"{t.get('exit_price',0):.2f} | {t.get('pnl_usdt',0):.2f} | "
            f"{t.get('pnl_pct',0):.2f}% | {t.get('score',0)} | {t.get('close_time','')}"
        )
    return "\n".join(lines)


# ----------------------------------------
# Análise via Claude API
# ----------------------------------------
def analyze_with_claude(notes: str, db_summary: str) -> str:
    """Envia os dados para a API da Anthropic e retorna a análise."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "[ERRO] ANTHROPIC_API_KEY não configurada no .env. Adicione sua chave para ativar a análise."

    # Inicializa cliente
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Você é o 'Sexta-Feira', um Trader Profissional Sênior e Quant Developer.
Sua personalidade é fria, analítica e focada em dados (sem emoções).
Analise os dados abaixo do meu bot de trading automatizado e responda em Português do Brasil.

=== HISTÓRICO DO BANCO DE DADOS (últimos 50 trades) ===
{db_summary}

=== NOTAS DO DIÁRIO / CONTEXTO (últimos 7 dias) ===
{notes if notes else "Nenhuma nota contextual encontrada."}

Responda estritamente nestas 4 seções:

## 📊 Análise Técnica
Qual setup (padrão/score) gerou mais lucro? Qual gerou mais prejuízo? Existe correlação clara entre Score Alto (>80) e Win?

## 📈 Estatísticas Chave
Resumo de: Win Rate, Expectativa Matemática, Drawdown perceptível, Ativo mais lucrativo (Alpha) e Ativo problemático (Beta negativo).

## 🧠 Padrões Comportamentais
O bot está operando demais (overtrading)? Há entradas em horários de baixa liquidez? O filtro de spread está sendo ignorado?

## 💡 Ação Corretiva (Prompt)
Uma sugestão técnica e objetiva de código (ex: alterar filtro de ATR, reduzir alavancagem em SOL, aumentar Score mínimo) para melhorar o PnL da próxima semana.
"""

    try:
        # Modelo Sonnet 3.5 (Otimizado para raciocínio lógico e código)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022", 
            max_tokens=2048,
            temperature=0.3, # Temperatura baixa para respostas mais determinísticas
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"[ERRO CLAUDE API] {e}"


# ----------------------------------------
# Salvar análise como nota Markdown (Obsidian Ready)
# ----------------------------------------
def save_analysis(text: str):
    """Salva a resposta da IA como uma nota datada na pasta de trades."""
    os.makedirs(OBSIDIAN_PATH, exist_ok=True)
    ts       = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filepath = os.path.join(OBSIDIAN_PATH, f"Analise_Claude_{ts}.md")
    
    header = f"""---
tags: [analise, claude, ia, segundo-cerebro, weekly-review]
date: {datetime.now().strftime("%Y-%m-%d")}
model: claude-3-5-sonnet
---

# 🧠 Análise Semanal por Claude (Sexta-Feira Brain)

{text}

---
*Gerado automaticamente pelo Brain Analyst — Sexta-Feira Advanced*
"""

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(header)
        print(f"[CLAUDE BRAIN] ✅ Análise salva: {os.path.basename(filepath)}")
        return filepath
    except Exception as e:
        print(f"[CLAUDE ERROR] Falha ao salvar análise: {e}")
        return None


# ----------------------------------------
# Ponto de entrada (Teste Manual)
# ----------------------------------------
if __name__ == "__main__":
    print("🧠 Brain Analyst com Claude iniciando...")

    notes      = get_trade_notes(days=7)
    db_summary = get_db_summary(limit=50)

    if not notes and "Nenhum" in db_summary:
        print("[AVISO] Nenhum dado suficiente encontrado para análise.")
    else:
        print("📡 Enviando dados para Claude... (aguarde)")
        analysis = analyze_with_claude(notes, db_summary)
        
        if analysis and not analysis.startswith("[ERRO"):
            print("\n📜 --- ANÁLISE DO CLAUDE ---")
            print(analysis)
            print("-------------------------\n")
            save_analysis(analysis)
            print("✅ Concluído! Verifique sua pasta de trades.")
        else:
            print(analysis)