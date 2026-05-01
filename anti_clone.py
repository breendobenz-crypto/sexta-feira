# =====================================
# ANTI CLONE - STABLE LOCK VERSION
# =====================================

import os
import atexit

LOCK_FILE = "jarvis.lock"


def verificar_instancia(nome_script):

    if os.path.exists(LOCK_FILE):

        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())

            # verifica se o processo ainda existe
            if os.path.exists(f"/proc/{pid}") or _process_running(pid):
                print("Outra instância já está rodando.")
                return False

        except Exception:
            pass

        # lock velho → remove
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass

    # cria novo lock
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    atexit.register(liberar_instancia)

    return True


def liberar_instancia():

    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass


def _process_running(pid):

    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False