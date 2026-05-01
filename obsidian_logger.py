# ==========================================
# OBSIDIAN LOGGER - JARVIS PRO (V2 - THREAD-SAFE + CONFIG-ALIGNED)
# Integração: Segundo Cérebro, escrita segura, frontmatter rico para Dataview
# ==========================================
import os
import threading
from datetime import datetime

# Tenta ler do config centralizado, fallback para env ou pasta local
try:
    from config import OBSIDIAN_TRADES_PATH
except ImportError:
    OBSIDIAN_TRADES_PATH = os.getenv("OBSIDIAN_TRADES_PATH", "trades")

# Lock para evitar race condition em escritas simultâneas
_write_lock = threading.Lock()

def ensure_dir():
    os.makedirs(OBSIDIAN_TRADES_PATH, exist_ok=True)

def log_trade_to_obsidian(
    symbol: str,
    side: str,
    entry: float,
    exit_price: float,
    pnl_usdt: float,
    pnl_pct: float,
    status: str,
    score: int = 0,
    regime: str = "UNKNOWN",
    leverage: int = 5,
    notes: str = ""
):
    """
    Registra trade como nota Markdown no Obsidian.
    Compatível com chamada original + parâmetros extras opcionais.
    """
    ensure_dir()

    # Normalização de direção
    side_norm = side.upper()
    is_long = side_norm in ("BUY", "LONG")
    side_tag = "long" if is_long else "short"
    side_label = "Buy" if is_long else "Sell"
    result_tag = "win" if pnl_usdt > 0 else "loss"

    # Sanitização do nome do arquivo
    safe_symbol = symbol.replace("/", "-").replace(":", "-")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = os.path.join(OBSIDIAN_TRADES_PATH, f"{timestamp}_{safe_symbol}.md")

    # Template otimizado para Dataview & Canvas
    content = f"""---
tags: [trade, {symbol.lower()}, {side_tag}, {result_tag}, score-{score}, regime-{regime.lower()}]
date: {datetime.now().strftime("%Y-%m-%d")}
time: {datetime.now().strftime("%H:%M:%S")}
symbol: "{symbol}"
direction: {side_label}
entry: {entry}
exit: {exit_price}
pnl_usdt: {pnl_usdt:.2f}
pnl_pct: {pnl_pct:.2f}
status: {result_tag.upper()}
score: {score}
leverage: {leverage}
---

# 📊 Trade Report: [[{symbol}]]

## 📈 Detalhes da Operação
| Campo | Valor |
|-------|-------|
| **Direção** | {side_label} (`#{side_tag}`) |
| **Entrada** | `${entry:.4f}` |
| **Saída** | `${exit_price:.4f}` |
| **Resultado** | `${pnl_usdt:.2f}` (`{pnl_pct:.2f}%`) |
| **Score IA** | `{score}` |
| **Alavancagem** | `{leverage}x` |
| **Regime** | `{regime}` |

## 🧠 Reflexão Pós-Trade
> {notes.strip() if notes else "Preencha: O setup foi válido? O mercado seguiu a previsão? O que a IA acertou/errou?"}

### ✅ Checklist de Execução
- [ ] Entrada no nível planejado?
- [ ] Stop Loss respeitado ou movido para Breakeven?
- [ ] Take Profit atingido ou parcial realizada?
- [ ] Gerenciamento de risco aplicado?

## 🔗 Conexões & Contexto
- **Horário:** `{datetime.now().strftime("%H:%M")}`
- **Referências:** `[[Padrões de Mercado]]`, `[[Risk Management]]`, `[[AI Insights]]`
- **Setup:** `[[{regime} Setup]]`

---
*Gerado automaticamente pela Sexta-Feira Advanced*
"""
    try:
        with _write_lock:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        print(f"[OBSIDIAN] ✅ Nota criada: {os.path.basename(filepath)}")
        return filepath
    except Exception as e:
        print(f"[OBSIDIAN ERROR] Falha ao salvar nota: {e}")
        return None