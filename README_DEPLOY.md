# SEXTA-FEIRA v3 — GUIA DE DEPLOY

## ANTES DE TUDO: SEGURANÇA
1. Renomeie `_env` → `.env` na sua máquina
2. Gire TODAS as chaves em Bybit, Telegram, Anthropic, ElevenLabs
3. Confirme que `.gitignore` contém `.env` e `_env`

## INSTALAÇÃO
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## INICIAR (ordem correta)
```bash
python watchdog.py
# NÃO rode main.py diretamente — o watchdog gerencia o processo
```

## DASHBOARD (terminal separado)
```bash
streamlit run dashboard.py
```

## VERIFICAÇÃO PÓS-DEPLOY (checklist)
- [ ] bot_heartbeat.json atualizado a cada 30s
- [ ] /status no Telegram retorna equity real
- [ ] brain_memory.json com risk_level != FROZEN
- [ ] watchdog.log sem crashes em 30min
- [ ] Nenhum trade em PAXGUSDT (desativado)

## O QUE FOI CORRIGIDO (v3)
1. **brain_optimizer**: win_rate=0 agora TRAVA score em 82 (antes BAIXAVA para 65)
2. **market_regime**: `import os` faltando causava NameError silencioso
3. **main.py**: SIGTERM handler — shutdown limpo, sem crash 0xC000013A
4. **telegram_bot**: listener NÃO mais auto-inicia no import
5. **strategy_engine**: slippage_guard, trade_limiter e exposure_control integrados
6. **execution_engine**: race condition em _partial_done/_last_stop corrigida com lock
7. **config.py**: PAXG desativado (93% das perdas), max_leverage=3, allow_counter_trend=False
8. **HEARTBEAT_FILE**: adicionado ao config.py (estava causando ImportError)
9. **.gitignore**: protege _env além de .env

## REATIVAR PAXG
Quando resolver o sinal, descomente `"PAXGUSDT"` em `SYMBOLS` no config.py.
