# admin_panel.py - PAINEL DE CONTROLE SEXTA-FEIRA (APENAS PARA VOCÊ)
import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

# --- CONFIGURAÇÃO ---
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123") # Mude no .env!

st.set_page_config(page_title="🛡️ SEXTA-FEIRA ADMIN", layout="wide")

# --- CSS ADMIN ---
st.markdown("""
<style>
    .stAlert { border: 1px solid #ff4b4b; background-color: #2a0000; }
    .metric-card { background-color: #111; padding: 20px; border-radius: 10px; border: 1px solid #333; }
    .user-badge-active { color: #00ff88; font-weight: bold; }
    .user-badge-banned { color: #ff4444; font-weight: bold; }
    button[kind="primary"] { background-color: #ff4b4b; color: white; }
</style>
""", unsafe_allow_html=True)

# --- TELA DE LOGIN ---
def check_login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if not st.session_state["authenticated"]:
        st.title("🔒 Acesso Restrito")
        password = st.text_input("Senha de Administrador", type="password")
        if st.button("Entrar"):
            if password == ADMIN_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        return False
    return True

# --- PAINEL PRINCIPAL ---
def render_dashboard():
    from saas_db import get_all_users, update_user_status, register_user
    
    st.title("🛡️ Painel de Controle — SEXTA-FEIRA ADVANCED")
    
    # Botão Sair
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

    # Importar dados
    all_users = get_all_users()
    df_users = pd.DataFrame(all_users)
    
    # Métricas
    total_users = len(df_users)
    active_users = len(df_users[df_users["status"] == "ACTIVE"])
    banned_users = len(df_users[df_users["status"] == "BANNED"])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de VIPs", total_users)
    col2.metric("Ativos", active_users, delta_color="normal")
    col3.metric("Banidos", banned_users, delta_color="inverse")

    st.divider()

    # TABS: Lista de Usuários vs Adicionar Novo
    tab_list, tab_add = st.tabs(["👥 Gerenciar Usuários", "➕ Adicionar VIP Manualmente"])

    # --- ABA 1: LISTA DE USUÁRIOS ---
    with tab_list:
        st.subheader("Base de Usuários")
        
        if df_users.empty:
            st.info("Nenhum usuário cadastrado ainda.")
        else:
            # Formatar tabela
            df_display = df_users[["email", "display_name", "plan", "status", "joined_at"]].copy()
            
            # Estilizar status
            def color_status(val):
                return 'color: #00ff88' if val == 'ACTIVE' else 'color: #ff4444'
            
            st.dataframe(df_display.style.applymap(color_status, subset=["status"]), use_container_width=True)
            
            # Ações
            st.write("### ⚙️ Ações")
            cols = st.columns([4, 1])
            with cols[0]:
                user_to_manage = st.selectbox("Selecione um usuário para gerenciar:", df_users["email"].tolist(), key="manage_select")
            
            with cols[1]:
                st.write("") # Spacer
                current_status = df_users[df_users["email"] == user_to_manage]["status"].values[0]
                current_uid = df_users[df_users["email"] == user_to_manage]["user_id"].values[0]
                
                new_status = "BANNED" if current_status == "ACTIVE" else "ACTIVE"
                action_label = "Banir 🚫" if new_status == "BANNED" else "Ativar ✅"
                action_type = "primary" if new_status == "BANNED" else "secondary"
                
                if st.button(action_label, type=action_type, use_container_width=True):
                    update_user_status(current_uid, new_status)
                    st.success(f"Usuário {user_to_manage} alterado para {new_status}!")
                    st.rerun()

    # --- ABA 2: ADICIONAR USUÁRIO ---
    with tab_add:
        st.subheader("Cadastrar Novo VIP")
        with st.form("add_user_form"):
            u_name = st.text_input("Nome / Display Name")
            u_email = st.text_input("Email")
            u_id = st.text_input("User ID (ex: whop_xxxxx ou manual)")
            
            st.markdown("---")
            st.write("Chaves OKX (Criptografadas automaticamente)")
            k1 = st.text_input("API Key", type="password")
            k2 = st.text_input("API Secret", type="password")
            k3 = st.text_input("Passphrase", type="password")
            
            submitted = st.form_submit_button("💾 Cadastrar Usuário")
            
            if submitted:
                if register_user(u_id, u_name, u_email, k1, k2, k3):
                    st.success(f"✅ VIP {u_name} cadastrado com sucesso!")
                else:
                    st.error("❌ Erro ao cadastrar. Verifique o terminal.")

# --- ROTEAMENTO ---
if check_login():
    render_dashboard()