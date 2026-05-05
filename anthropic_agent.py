# anthropic_agent.py - Integração com IA Claude (Anthropic)
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Tenta inicializar o cliente
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if API_KEY:
    client = anthropic.Anthropic(api_key=API_KEY)
else:
    client = None
    print("⚠️ ANTHROPIC_API_KEY não encontrada. IA desativada.")

def generate_reasoning(symbol, side, score, entry):
    """Gera uma explicação técnica curta para o trade."""
    if not client:
        return "Setup técnico padrão (IA Offline)."

    prompt = f"""
    Atue como um analista técnico profissional de criptomoedas.
    Um bot acabou de abrir uma operação. Gere uma explicação curta e profissional (máx 20 palavras) do porquê.
    
    Dados:
    - Ativo: {symbol}
    - Direção: {side}
    - Score: {score}/100
    - Entrada: {entry}

    Retorne APENAS o texto do raciocínio.
    """

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",  # Modelo rápido e barato
            max_tokens=100,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        return f"Erro na IA: {str(e)}"