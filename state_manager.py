# =====================================
# STATE MANAGER - JARVIS PRO
# Memória persistente das operações
# =====================================

import json
import os
from datetime import datetime
from threading import Lock

STATE_FILE = "state.json"
_lock = Lock()

# -------------------------------------
# GARANTE ARQUIVO
# -------------------------------------
def _garantir_arquivo():
    if not os.path.exists(STATE_FILE):
        estrutura_base = {
            "positions": {},
            "risk": {},
            "market": {},
            "system": {
                "last_update": None
            }
        }
        with open(STATE_FILE, "w") as f:
            json.dump(estrutura_base, f, indent=4)

# -------------------------------------
# CARREGAR ESTADO
# -------------------------------------
def carregar_estado():
    _garantir_arquivo()
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

# -------------------------------------
# SALVAR ESTADO COMPLETO
# -------------------------------------
def salvar_estado(estado):
    with _lock:
        # FIX: garante que chave "system" existe antes de acessar
        estado.setdefault("system", {})["last_update"] = datetime.utcnow().isoformat()
        with open(STATE_FILE, "w") as f:
            json.dump(estado, f, indent=4)

# -------------------------------------
# SALVAR POSIÇÃO
# -------------------------------------
def salvar_posicao(symbol, dados):
    with _lock:
        estado = carregar_estado()

        estado["positions"][symbol] = {
            **dados,
            "updated_at": datetime.utcnow().isoformat()
        }

        salvar_estado(estado)

# -------------------------------------
# REMOVER POSIÇÃO
# -------------------------------------
def remover_posicao(symbol):
    with _lock:
        estado = carregar_estado()

        if symbol in estado["positions"]:
            del estado["positions"][symbol]

        salvar_estado(estado)

# -------------------------------------
# OBTER POSIÇÃO
# -------------------------------------
def obter_posicao(symbol):
    estado = carregar_estado()
    return estado["positions"].get(symbol)

# -------------------------------------
# ATUALIZAR MERCADO (regime etc)
# -------------------------------------
def atualizar_market(symbol, regime):
    with _lock:
        estado = carregar_estado()
        estado["market"][symbol] = regime
        salvar_estado(estado)

# -------------------------------------
# ATUALIZAR RISCO
# -------------------------------------
def atualizar_risco(chave, valor):
    with _lock:
        estado = carregar_estado()
        estado["risk"][chave] = valor
        salvar_estado(estado)

# -------------------------------------
# GET VALOR DO ESTADO
# -------------------------------------
def get(key, default=None):
    estado = carregar_estado()
    return estado.get(key, default)


# -------------------------------------
# UPDATE VALOR DO ESTADO
# -------------------------------------
def update(key, value):
    estado = carregar_estado()
    estado[key] = value
    salvar_estado(estado)
