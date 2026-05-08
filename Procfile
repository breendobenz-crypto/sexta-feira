web: streamlit run dashboard_saas.py --server.port $PORT --server.address 0.0.0.0
web: streamlit run dashboard_saas.py --server.port $PORT --server.address 0.0.0.0
worker: uvicorn webhook_whop:app --host 0.0.0.0 --port $PORT
web: python bot_runner.py
worker: python telegram_bot.py
web: streamlit run dashboard_saas.py --server.port $PORT --server.address 0.0.0.0 --server.headless true