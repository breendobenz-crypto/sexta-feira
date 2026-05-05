\# 🟣 SEXTA-FEIRA ADVANCED — SaaS de Trading Automatizado



> \*\*Bot de trading algorítmico para OKX com arquitetura multi-tenant, IA adaptativa e dashboard em tempo real.\*\*



!\[Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)

!\[OKX](https://img.shields.io/badge/Exchange-OKX-black)

!\[License](https://img.shields.io/badge/License-Private-red)



\---



\## ✨ Funcionalidades



\### 🤖 Para o Trader (VIP)

\- ✅ \*\*Operação 100% automatizada\*\* na OKX (Long/Short)

\- ✅ \*\*Gestão de risco inteligente\*\*: Stop Loss, Take Profit, trailing stop

\- ✅ \*\*Dashboard em tempo real\*\*: equity, PnL, histórico, métricas

\- ✅ \*\*Isolamento total\*\*: suas chaves são criptografadas e nunca compartilhadas

\- ✅ \*\*IA adaptativa\*\*: o bot aprende com o regime de mercado



\### 🛡️ Para o Administrador

\- ✅ \*\*Arquitetura SaaS multi-tenant\*\*: centenas de VIPs no mesmo sistema

\- ✅ \*\*Cadastro automático via Whop + Google Forms\*\*

\- ✅ \*\*Webhook seguro\*\* com assinatura HMAC

\- ✅ \*\*Logs centralizados\*\* e alertas por Telegram

\- ✅ \*\*Kill Switch automático\*\* por perda diária



\### 📊 Tecnologia

\- \*\*Backend\*\*: Python 3.10+, FastAPI, SQLite

\- \*\*Frontend\*\*: Streamlit (dashboard responsivo)

\- \*\*Criptografia\*\*: `cryptography.fernet` para chaves de API

\- \*\*IA\*\*: Integração com Claude/OpenAI para análise de contexto

\- \*\*Deploy\*\*: Render.com (webhook) + VPS local (bot principal)



\---



\## 🚀 Começando



\### Pré-requisitos

```bash

Python 3.10+

pip install -r requirements.txt





**EVEN.**



\# OKX

OKX\_API\_KEY=sua\_key

OKX\_API\_SECRET=seu\_secret

OKX\_PASSPHRASE=sua\_senha

OKX\_SIMULATED=false  # true para teste, false para real



\# SaaS

SAAS\_MASTER\_KEY=JarvisSaaS2026!

WHOP\_WEBHOOK\_SECRET=whsec\_...



\# Google Sheets (cadastro automático)

GOOGLE\_SHEET\_ID=seu\_id\_aqui

GOOGLE\_CREDS\_FILE=google\_creds.json



\# Telegram (alertas)

TELEGRAM\_BOT\_TOKEN=seu\_token

TELEGRAM\_ADMIN\_ID=seu\_id\_numerico



**Rodando Localmente**

**bash**



\# 1. Bot principal (orquestrador)

python -B main\_saaS.py



\# 2. Dashboard VIP (outro terminal)

streamlit run dashboard\_saas.py



\# 3. Processador de formulários (opcional, para cadastro automático)

python process\_whop\_form.py



Acessando o Dashboard

URL: http://localhost:8501

Login: email cadastrado na Whop





&#x20;                📦 Estrutura do Projeto



sf\_v4\_fixed/

├── main\_saaS.py          # Orquestrador principal

├── dashboard\_saas.py     # Dashboard Streamlit para VIPs

├── saas\_db.py            # Gestão de usuários e trades (criptografado)

├── execution\_engine.py   # Execução de ordens na OKX

├── strategy\_engine.py    # Lógica de entrada/saída

├── risk\_manager.py       # Gestão de risco e kill switch

├── crypto\_vault.py       # Criptografia/descriptografia

├── webhook\_whop.py       # Endpoint para Whop (FastAPI)

├── process\_whop\_form.py  # Leitor de Google Forms → cadastro VIP

├── telegram\_bot.py       # Bot de alertas e comandos

├── config.py             # Configurações globais

├── requirements.txt      # Dependências Python

├── .env                  # Variáveis sensíveis (NÃO COMMITAR)

├── google\_creds.json     # Credenciais Google (NÃO COMMITAR)

└── README.md             # Este arquivo



&#x20;

🤝 Contribuindo

Este é um projeto privado. Para acesso ou parcerias, entre em contato via Telegram: @seu\_usuario.

📄 Licença

Proprietário. Todos os direitos reservados.

Desenvolvido com 🟣 por Breendo

"Sexta-Feira: Sua vantagem algorítmica no mercado crypto."

