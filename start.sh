
#!/bin/bash
echo "🚀 Iniciando Sexta-Feira Advanced Cloud..."

# 1. Inicializa o banco
python -c "from saas_db import init_saas_db; init_saas_db(); print('✅ Banco inicializado')"

# 2. Bot Telegram VIP (Background)
python telegram_bot.py &
echo "🤖 Bot VIP iniciado..."

# 3. Bot Grupo FREE (Background) - Dicas, Polls, Resumo de Mercado
python telegram_free_bot.py &
echo "📢 Bot Free Group iniciado..."

# 4. Processador de Planilha VIP (Background) - Opcional, falha gracefully se sem creds
python form_processor.py &
echo "📊 Processador de Planilha iniciado..."

# 5. Orquestrador de Trades SaaS (Background)
python main_saaS.py &
echo "🧠 Orquestrador iniciado..."

# 6. Streamlit Dashboard (Frente - mantém container vivo)
echo "📊 Iniciando Dashboard..."
streamlit run dashboard_saas.py --server.port $PORT --server.address 0.0.0.0 --server.headless true