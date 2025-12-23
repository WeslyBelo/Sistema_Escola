import streamlit as st
import sqlite3
import hashlib
import pandas as pd

st.set_page_config(page_title="Gestão de Usuários", layout="wide")

# --- 1. TRAVA DE SEGURANÇA ---
if st.session_state.get('cargo') != "Gestor":
    st.error("⛔ Acesso Restrito: Apenas Gestores podem gerenciar usuários.")
    st.stop()

def conectar():
    return sqlite3.connect('escola.db')

st.title("👥 Gerenciamento de Usuários")

# --- 2. FORMULÁRIO DE CADASTRO (NOVO USUÁRIO) ---
with st.expander("➕ Cadastrar Novo Usuário"):
    with st.form("form_novo_usuario", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            novo_nome = st.text_input("Nome Completo")
            novo_user = st.text_input("Login (Usuário)")
        with col2:
            nova_senha = st.text_input("Senha", type="password")
            novo_cargo = st.selectbox("Cargo", ["Monitor", "Professor", "Gestor"])
        
        if st.form_submit_button("Salvar Novo Usuário"):
            if novo_user and nova_senha:
                senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                conn = conectar()
                try:
                    conn.execute("INSERT INTO usuarios (username, senha, nome, cargo) VALUES (?,?,?,?)",
                                 (novo_user.strip().lower(), senha_hash, novo_nome, novo_cargo))
                    conn.commit()
                    st.success("Usuário criado!")
                    st.rerun()
                except:
                    st.error("Usuário já existe.")
                finally:
                    conn.close()

st.divider()

# --- 3. LISTAGEM, EDIÇÃO E EXCLUSÃO ---
st.subheader("Usuários Cadastrados")
conn = conectar()
df_users = pd.read_sql("SELECT id, username, nome, cargo FROM usuarios", conn)
conn.close()

# Exibe a tabela de usuários
st.dataframe(df_users, use_container_width=True, hide_index=True)

# Seleção para Editar ou Deletar
user_selecionado = st.selectbox("Selecione um usuário para Editar ou Deletar:", [""] + df_users['username'].tolist())

if user_selecionado:
    dados_user = df_users[df_users['username'] == user_selecionado].iloc[0]
    
    col_ed1, col_ed2 = st.columns(2)
    
    with col_ed1:
        st.markdown(f"### Editar: {user_selecionado}")
        with st.form("form_editar"):
            edit_nome = st.text_input("Nome Completo", value=dados_user['nome'])
            edit_cargo = st.selectbox("Cargo", ["Monitor", "Professor", "Gestor"], 
                                      index=["Monitor", "Professor", "Gestor"].index(dados_user['cargo']))
            nova_senha_edit = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password")
            
            if st.form_submit_button("Atualizar Dados"):
                conn = conectar()
                if nova_senha_edit:
                    s_hash = hashlib.sha256(nova_senha_edit.encode()).hexdigest()
                    conn.execute("UPDATE usuarios SET nome=?, cargo=?, senha=? WHERE username=?", 
                                 (edit_nome, edit_cargo, s_hash, user_selecionado))
                else:
                    conn.execute("UPDATE usuarios SET nome=?, cargo=? WHERE username=?", 
                                 (edit_nome, edit_cargo, user_selecionado))
                conn.commit()
                conn.close()
                st.success("Usuário atualizado!")
                st.rerun()

    with col_ed2:
        st.markdown("### Excluir")
        st.warning(f"Tem certeza que deseja apagar {user_selecionado}?")
        if st.button(f"🗑️ Confirmar Exclusão de {user_selecionado}"):
            if user_selecionado == "admin":
                st.error("O usuário 'admin' principal não pode ser deletado.")
            else:
                conn = conectar()
                conn.execute("DELETE FROM usuarios WHERE username=?", (user_selecionado,))
                conn.commit()
                conn.close()
                st.success("Usuário removido!")
                st.rerun()
