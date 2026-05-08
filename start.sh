#!/bin/bash
echo "🚀 Iniciando Sexta-Feira Advanced Cloud..."

# 1. Inicializa o banco de dados
python -c "from saas_db import init_saas_db; init_saas_db(); print('✅ Banco inicializado')"

# 2. Roda o Bot Telegram em segundo plano
python telegram_bot.py &
echo "🤖 Bot Telegram iniciado em background"

# 3. Roda o Orquestrador de Trades em segundo plano
python main_saaS.py &
echo "🧠 Orquestrador (main_saaS) iniciado em background"

# 4. Roda o Webhook Whop em segundo plano (se existir no seu repo)
if [ -f "webhook_whop.py" ]; then
    python webhook_whop.py &
    echo "🔗 Webhook Whop iniciado em background"
fi

# 5. Mantém o container vivo rodando o Streamlit em primeiro plano
echo "📊 Iniciando Dashboard Streamlit..."
streamlit run dashboard_saas.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false