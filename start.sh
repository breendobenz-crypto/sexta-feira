#!/bin/bash
echo "🚀 Iniciando Sexta-Feira Advanced Cloud..."

# 1. Inicializa o banco
python -c "from saas_db import init_saas_db; init_saas_db(); print('✅ Banco inicializado')"

# 2. ✅ FIX CONFLITO 409: telegram_bot.py NÃO sobe como processo separado
# O main_saaS.py importa enviar_sinal_vip e enviar_alerta_free diretamente
# Subir telegram_bot.py aqui causaria dois getUpdates simultâneos → 409 Conflict

# 3. Bot Grupo FREE (Background)
python telegram_free_bot.py &
echo "📢 Bot Free Group iniciado..."

# 4. Processador de Formulário VIP (Background)
python form_processor.py &
echo "📊 Processador de Formulário iniciado..."

# 5. Orquestrador de Trades SaaS (Background)
python main_saaS.py &
echo "🧠 Orquestrador iniciado..."

# 6. Streamlit Dashboard (mantém container vivo)
echo "📊 Iniciando Dashboard..."
streamlit run dashboard_saas.py --server.port $PORT --server.address 0.0.0.0 --server.headless true