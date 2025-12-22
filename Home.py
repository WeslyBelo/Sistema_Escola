import streamlit as st
import sqlite3
import hashlib
import os

st.set_page_config(page_title="Gestão Escolar Militar", layout="wide")

# Inicialização de segurança
if 'logado' not in st.session_state:
    st.session_state.logado = False
if 'cargo' not in st.session_state:
    st.session_state.cargo = None

def inicializar_e_corrigir_banco():
    conn = sqlite3.connect('escola.db')
    c = conn.cursor()
    
    # 1. Garante que a tabela existe
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, 
                  senha TEXT, nome TEXT, cargo TEXT)''')
    
    # 2. Garante que a coluna cargo existe (Migração)
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN cargo TEXT")
    except:
        pass

    # 3. FORÇAR O ADMIN A SER GESTOR (Correção do seu problema)
    senha_hash = hashlib.sha256("admin123".encode()).hexdigest()
    # Verifica se o admin existe
    admin_exists = c.execute("SELECT id FROM usuarios WHERE username='admin'").fetchone()
    
    if not admin_exists:
        c.execute("INSERT INTO usuarios (username, senha, nome, cargo) VALUES (?,?,?,?)",
                  ("admin", senha_hash, "Comandante Geral", "Gestor"))
    else:
        # Se ele já existe, forçamos o cargo para 'Gestor'
        c.execute("UPDATE usuarios SET cargo='Gestor' WHERE username='admin'")
    
    # 4. Outras tabelas necessárias
    c.execute('''CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, matricula TEXT UNIQUE, nome TEXT, turma TEXT, divisao TEXT, foto_perfil TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS regras_indisciplina (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, pontos INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_geral (chave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute("INSERT OR IGNORE INTO config_geral (chave, valor) VALUES ('pontos_iniciais', '100')")

    conn.commit()
    conn.close()

# Executa a correção
inicializar_e_corrigir_banco()

# --- INTERFACE DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login de Administração")
    with st.form("login"):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            phash = hashlib.sha256(p.encode()).hexdigest()
            conn = sqlite3.connect('escola.db')
            user = conn.execute("SELECT nome, cargo FROM usuarios WHERE username=? AND senha=?", (u, phash)).fetchone()
            conn.close()
            
            if user:
                st.session_state.logado = True
                st.session_state.nome = user[0]
                st.session_state.cargo = user[1] # Agora será 'Gestor'
                st.rerun()
            else:
                st.error("Credenciais incorretas.")
else:
    st.title("🛡️ Painel Principal")
    st.success(f"Logado como: {st.session_state.nome} | Perfil: {st.session_state.cargo}")
    
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()
    
    if st.button("🚨 Reset Total (Apagar Banco)"):
        if os.path.exists("escola.db"):
            os.remove("escola.db")
            st.session_state.logado = False
            st.rerun()