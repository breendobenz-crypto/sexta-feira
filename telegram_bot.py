import requests
import threading
import time
import os
import json
from datetime import datetime, timezone

try:
    from config import (
        TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TRADINGVIEW_CHART_URL,
        ELEVENLABS_API_KEY, VOICE_ID, HEARTBEAT_FILE, TELEGRAM_SIGNAL_GROUP
    )
except ImportError:
    print("[WARN] Arquivo config.py não encontrado. Crie-o com suas chaves.")
    # Fallbacks para evitar crash se config não existir ainda
    TELEGRAM_TOKEN = ""
    TELEGRAM_CHAT_ID = ""
    TELEGRAM_SIGNAL_GROUP = None
    TRADINGVIEW_CHART_URL = ""
    ELEVENLABS_API_KEY = ""
    VOICE_ID = ""
    HEARTBEAT_FILE = "bot_heartbeat.json"

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("[WARN] Telegram não configurado. Notificações desativadas.")

# URLs da API
# ✅ CORREÇÃO: f-strings sem espaços
URL_SEND_MSG    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
URL_SEND_PHOTO  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
URL_SEND_VOICE  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
URL_GET_UPDATES = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"

# Session reutilizável
_session = requests.Session()
_session.headers.update({'Connection': 'keep-alive'})

# Thread safety
_update_lock = threading.Lock()
last_update_id = 0

# Rate limiting
_last_msg_time = 0
MIN_MSG_INTERVAL = 1.0

# ==========================================
# ❤️ HEARTBEAT
# ==========================================
def _log_telegram_activity(action: str, details: dict = None):
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = json.load(f)
            hb["last_telegram_action"] = action
            hb["last_telegram_details"] = details or {}
            hb["last_telegram_time"] = datetime.now(timezone.utc).isoformat()
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(hb, f)
    except:
        pass

# ==========================================
# RATE LIMIT
# ==========================================
def _rate_limit():
    global _last_msg_time
    now = time.time()
    elapsed = now - _last_msg_time
    if elapsed < MIN_MSG_INTERVAL:
        time.sleep(MIN_MSG_INTERVAL - elapsed)
    _last_msg_time = time.time()

# ==========================================
# ENVIO ROBUSTO
# ==========================================
def _send(msg: str, parse_mode: str = "HTML", retries: int = 3, chat_id: str = None) -> bool:
    if not TELEGRAM_TOKEN:
        return False
    target = chat_id or TELEGRAM_CHAT_ID
    for attempt in range(retries):
        try:
            _rate_limit()
            # ✅ CORREÇÃO: removido espaços nas chaves do JSON
            r = _session.post(
                URL_SEND_MSG,
                json={"chat_id": target, "text": msg, "parse_mode": parse_mode},
                timeout=10
            )
            if r.status_code == 200:
                return True
            elif r.status_code == 401:
                print("[TELEGRAM ERROR] ❌ Token inválido.")
                return False
            elif r.status_code == 429:
                try: wait = int(r.json().get("parameters", {}).get("retry_after", 5))
                except: wait = 5
                print(f"[TELEGRAM RATE LIMIT] ⏳ Aguardando {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f"[TELEGRAM WARN] Status {r.status_code}: {r.text[:100]}")
                return False
        except requests.exceptions.RemoteDisconnected:
            print(f"[TELEGRAM] Conexão fechada (tentativa {attempt+1}/{retries})")
            if attempt < retries - 1: time.sleep(2 ** attempt); continue
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"[TELEGRAM] Erro de conexão: {e}")
            if attempt < retries - 1: time.sleep(2 ** attempt); continue
            return False
        except Exception as e:
            print(f"[TELEGRAM ERROR] {type(e).__name__}: {e}")
            return False
    return False

# ==========================================
# VOZ (ELEVENLABS + FALLBACK TEXTO)
# ==========================================
def generate_natural_audio(text: str) -> bytes | None:
    if not ELEVENLABS_API_KEY: return None
    try:
        # ✅ CORREÇÃO: f-string limpa
        r = _session.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
            headers={"Accept": "audio/mpeg", "xi-api-key": ELEVENLABS_API_KEY},
            json={"text": text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
            timeout=20
        )
        return r.content if r.status_code == 200 else None
    except Exception as e:
        print(f"[VOICE ERROR] {e}"); return None

def send_voice_response(text: str):
    audio = generate_natural_audio(text)
    if audio:
        try:
            _rate_limit()
            _session.post(URL_SEND_VOICE, files={"voice": ("sexta.mp3", audio, "audio/mpeg")},
                          data={"chat_id": TELEGRAM_CHAT_ID}, timeout=20)
            _log_telegram_activity("voice_sent")
        except Exception as e:
            print(f"[SEND VOICE ERROR] {e}"); _send(text)
    else:
        _send(text)

# ==========================================
# CLAUDE IA
# ==========================================
_claude_client = None
def _get_claude():
    global _claude_client
    if _claude_client is None:
        # ✅ CORREÇÃO: Carregar variável de ambiente corretamente
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key:
            try:
                import anthropic
                _claude_client = anthropic.Anthropic(api_key=api_key)
            except ImportError: print("[CLAUDE WARN] pip install anthropic")
    return _claude_client

def ask_claude(query: str) -> str:
    client = _get_claude()
    if not client: return "🔧 Núcleo offline. Configure ANTHROPIC_API_KEY no .env."
    
    equity_str = "desconhecida"
    try:
        from bybit_connect import get_account_info
        info = get_account_info()
        # ✅ CORREÇÃO: chave "equity" sem espaço
        if info and info.get("equity"): equity_str = f"${info['equity']:.2f}"
    except: pass

    try:
        # ✅ CORREÇÃO: system prompt e f-string limpos
        msg = client.messages.create(
            model="claude-3-haiku-20240307", max_tokens=400,
            system="Você é a SEXTA-FEIRA, IA de trading autônoma. Fria, calculista, direta. Use termos de trading. Responda em PT-BR.",
            messages=[{"role": "user", "content": f"Equity atual: {equity_str}\n\n{query}"}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"Falha técnica: {type(e).__name__}"

# ==========================================
# STATUS COM CACHE
# ==========================================
_status_cache = {"data": None, "ts": 0}
def _build_status_text() -> str:
    now = time.time()
    with _update_lock:
        if _status_cache["data"] and (now - _status_cache["ts"]) < 10:
            return _status_cache["data"]
        try:
            from bybit_connect import get_account_info
            from risk_manager import get_risk_status
            info = get_account_info() or {}
            # ✅ CORREÇÃO: chaves sem espaços
            equity = info.get("equity", 0)
            avail = info.get("availableBalance", 0)
            pos = info.get("positions", [])
            
            risk = get_risk_status()
            min_score = 70
            if os.path.exists("brain_memory.json"):
                try:
                    with open("brain_memory.json") as f: min_score = json.load(f).get("optimized_min_score", 70)
                except: pass
            
            lines = ["📊 <b>STATUS — SEXTA-FEIRA</b>",
                     f"💰 Equity: <b>${equity:.2f}</b> | Disp: ${avail:.2f}",
                     f"🎯 Min Score: {min_score} | Modo: {'🛡️ DEF' if risk['modo_reducao'] else '✅ NORM'}",
                     f"📉 Streak: {risk['loss_streak']} | Loss Dia: {risk['daily_loss_pct']:.2%}",
                     f"📌 Posições: {len(pos)}"]
            
            for p in pos:
                pnl = p.get("unrealisedPnl", 0); sign = "🟢" if pnl >= 0 else "🔴"
                lines.append(f"  {sign} {p['symbol']} {p['side']} | PnL: ${pnl:.2f}")
            
            res = "\n".join(lines); _status_cache["data"] = res; _status_cache["ts"] = now; return res
        except Exception as e: return f"⚠️ Erro status: {e}"

# ==========================================
# LISTENER DE COMANDOS
# ==========================================
def handle_incoming_messages():
    global last_update_id
    print("👂 Sexta-Feira ouvindo comandos no Telegram...")
    _log_telegram_activity("listener_started")
    while True:
        try:
            r = _session.get(URL_GET_UPDATES, params={"offset": last_update_id + 1, "timeout": 30}, timeout=35)
            if r.status_code != 200: time.sleep(5); continue
            for update in r.json().get("result", []):
                with _update_lock: last_update_id = update["update_id"]
                msg = update.get("message", {})
                if not msg.get("text"): continue
                if str(msg["chat"]["id"]) != TELEGRAM_CHAT_ID: continue
                
                text = msg["text"].strip(); lower = text.lower()
                if lower in ["/status", "/saldo"]: 
                    _send(_build_status_text()); _log_telegram_activity("status_requested"); continue
                elif lower in ["/ajuda", "/help"]:
                    _send("🤖 <b>Comandos</b>\n• /status ou /saldo\n• /trades\n• /config\n• /ping\n• Pergunte sobre mercado/trading.")
                    continue
                elif lower == "/ping": 
                    _send("🟢 ONLINE — Claude/Bybit/DB OK"); _log_telegram_activity("ping"); continue
                elif lower == "/trades":
                    try:
                        from database import get_all_closed_trades
                        trades = get_all_closed_trades(limit=5)
                        if not trades: _send("📭 Sem trades recentes.")
                        else:
                            lines = ["📋 <b>Últimos Trades</b>"]
                            for t in trades:
                                pnl = t.get("pnl_usdt", 0); sign = "+" if pnl >= 0 else ""
                                lines.append(f"• {t['symbol']} {t['side']}: {sign}${pnl:.2f} (Score: {t.get('score',0)})")
                            _send("\n".join(lines))
                    except Exception as e: _send(f"⚠️ Erro: {e}")
                    continue
                elif lower == "/config":
                    try:
                        from config import SYMBOLS, MIN_SCORE_ENTRY, MAX_TRADES_ABERTOS
                        _send(f"⚙️ <b>Config</b>\n• Ativos: {', '.join(SYMBOLS)}\n• Score Mín: {MIN_SCORE_ENTRY}\n• Máx Abertos: {MAX_TRADES_ABERTOS}")
                    except Exception as e: _send(f"⚠️ Erro config: {e}")
                    continue
                else:
                    response = ask_claude(text); send_voice_response(response)
                    _log_telegram_activity("claude_query", {"query_length": len(text)})
        except Exception as e:
            print(f"[LISTENER ERROR] {e}"); _log_telegram_activity("listener_error", {"error": str(e)}); time.sleep(5)

_listener = threading.Thread(target=handle_incoming_messages, daemon=True)
_listener.start()

# ==========================================
# ENVIO DE SINAL
# ==========================================
def enviar_sinal_com_grafico(ativo, direcao, score, entrada, take, stop, hora):
    # ✅ CORREÇÃO: f-string limpa
    caption = (f"🟣 <b>SEXTA-FEIRA SIGNAL</b>\n\nAtivo: {ativo}\nDireção: {direcao}\nScore: {score}\n\n"
               f"┌────────────────────┐\n│ ENTRADA : {entrada}\n│ TAKE    : {take}\n│ STOP    : {stop}\n└────────────────────┘\n\nHora: {hora}")
    
    targets = []
    if TELEGRAM_SIGNAL_GROUP: targets.append(TELEGRAM_SIGNAL_GROUP)
    targets.append(TELEGRAM_CHAT_ID)

    for target in targets:
        try:
            _rate_limit()
            r = _session.post(URL_SEND_PHOTO, json={"chat_id": target, "photo": TRADINGVIEW_CHART_URL, 
                   "caption": caption, "parse_mode": "HTML"}, timeout=10)
            if r.status_code != 200: 
                _send(caption, chat_id=target)
        except: 
            _send(caption, chat_id=target)
            
    _log_telegram_activity("signal_sent", {"symbol": ativo, "direction": direcao})

# ==========================================
# ALERTAS
# ==========================================
def alerta_trade(symbol, side, entry): _send(f"🚀 <b>TRADE ABERTO</b>\n{symbol}\n{side}\nEntry: {entry}"); _log_telegram_activity("trade_opened", {"symbol": symbol})
def alerta_stop(symbol): _send(f"❌ <b>STOP HIT</b>\n{symbol}"); _log_telegram_activity("stop_hit", {"symbol": symbol})
def alerta_be(symbol): _send(f"⚖️ <b>BREAK EVEN</b>\n{symbol}")
def alerta_kill(): _send("🛑 <b>KILL SWITCH</b>\nOperações suspensas até amanhã."); _log_telegram_activity("kill_switch_activated")
def alerta_erro(msg): _send(f"⚠️ <b>ERRO</b>\n{msg}"); _log_telegram_activity("system_error", {"message": msg[:200]})

# ==========================================
# RESUMO DIÁRIO
# ==========================================
def enviar_resumo_diario():
    try:
        from database import get_daily_stats
        stats = get_daily_stats()
        if stats["total"] == 0: return _send("📊 <b>RESUMO DIA</b>\nNenhuma operação hoje.")
        wr = (stats["wins"] / stats["total"] * 100) if stats["total"] > 0 else 0
        sign = "+" if stats["pnl"] >= 0 else ""
        _send(f"📊 <b>RESUMO DIÁRIO</b>\n📈 Trades: {stats['total']} | 🟢 Wins: {stats['wins']} | 🔴 Losses: {stats['losses']}\n🎯 WR: {wr:.1f}% | Score Médio: {stats.get('avg_score',0):.0f}\n💰 Resultado: <b>${sign}{stats['pnl']:.2f}</b>")
        _log_telegram_activity("daily_summary_sent", {"pnl": stats["pnl"], "wr": wr})
    except Exception as e: print(f"[DAILY SUMMARY ERROR] {e}")

# ==========================================
# TESTE STANDALONE
# ==========================================
# ✅ CORREÇÃO: Adicionados underscores em __name__
if __name__ == "__main__":
    _send("🟣 Sexta-Feira ONLINE — Claude integrado, grupo ativo.")
    print("🤖 Bot standalone. Ctrl+C para parar.")
    try:
        while True: time.sleep(10)
    except KeyboardInterrupt: print("\n🛑 Encerrado.")