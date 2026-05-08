#!/bin/bash
echo "🚀 Iniciando Sexta-Feira Advanced Cloud..."

# 1. Inicializa o banco
python -c "from saas_db import init_saas_db; init_saas_db(); print('✅ Banco inicializado')"

# 2. Roda o Bot Telegram em background
echo "🤖 Iniciando Bot Telegram..."
python telegram_bot.py &

# 3. Roda o Orquestrador em background
echo "🧠 Iniciando Orquestrador..."
python main_saaS.py &

# 4. Streamlit em primeiro plano (mantém container vivo)
echo "📊 Iniciando Dashboard..."
streamlit run dashboard_saas.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false