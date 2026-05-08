#!/bin/bash

# Inicializa o banco de dados
python -c "from saas_db import init_saas_db; init_saas_db(); print('✅ Banco inicializado')"

# Inicia o Streamlit
streamlit run dashboard_saas.py --server.port $PORT --server.address 0.0.0.0 --server.headless true