# run_local.py - Para testar LOCALMENTE no seu PC
import os
import sys

# Define variáveis para teste local
os.environ["DATABASE_URL"] = ""  # Deixe vazio para usar SQLite local
os.environ["VIP_PASSWORD"] = "SextaFeira2026!"
os.environ["OKX_SIMULATED"] = "true"

# Roda o Streamlit com porta fixa
os.system("streamlit run dashboard_saas.py --server.port 8501 --server.address localhost")