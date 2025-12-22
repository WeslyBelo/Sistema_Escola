import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Mural de Avisos", layout="wide")

# --- 1. SEGURANÇA ---
if 'logado' not in st.session_state or not st.session_state.logado:
    st.error("⚠️ Por favor, faça login na página inicial.")
    st.stop()

def conectar():
    return sqlite3.connect('escola.db')

# --- 2. GARANTIR QUE A TABELA EXISTE (EVITA O DATABASEERROR) ---
conn = conectar()
conn.execute('''CREATE TABLE IF NOT EXISTS avisos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  autor TEXT, titulo TEXT, mensagem TEXT, 
                  data TEXT, prioridade TEXT)''')
conn.commit()
conn.close()

# --- 3. CABEÇALHO PERSONALIZADO ---
st.markdown(f"""
    <div style="border-bottom: 2px solid #003366; padding-bottom: 10px; margin-bottom: 25px;">
        <h2 style='margin: 0; color: #003366;'>📢 Mural de Avisos Digital</h2>
        <p style='margin: 0; color: gray;'>Usuário: <b>{st.session_state.nome}</b></p>
    </div>
""", unsafe_allow_html=True)

# --- 4. FORMULÁRIO DE PUBLICAÇÃO ---
if st.session_state.cargo in ["Gestor", "Professor"]:
    with st.expander("📝 Publicar Novo Comunicado"):
        with st.form("form_novo_aviso", clear_on_submit=True):
            titulo = st.text_input("Título do Aviso")
            prioridade = st.select_slider("Nível de Urgência", options=["Baixa", "Média", "Alta"])
            mensagem = st.text_area("Conteúdo do Comunicado")
            
            # Botão obrigatório dentro do formulário
            if st.form_submit_button("🚀 Postar no Mural"):
                if titulo and mensagem:
                    conn = conectar()
                    conn.execute("INSERT INTO avisos (autor, titulo, mensagem, data, prioridade) VALUES (?,?,?,?,?)",
                                 (st.session_state.nome, titulo, mensagem, datetime.now().strftime('%d/%m/%Y %H:%M'), prioridade))
                    conn.commit()
                    conn.close()
                    st.success("Aviso publicado com sucesso!")
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos.")

st.write("##")

# --- 5. EXIBIÇÃO DOS AVISOS (APARÊNCIA MELHORADA) ---
conn = conectar()
# Agora o read_sql não falhará pois a tabela foi criada no passo 2
df_avisos = pd.read_sql("SELECT * FROM avisos ORDER BY id DESC", conn)
conn.close()

if not df_avisos.empty:
    for index, row in df_avisos.iterrows():
        # Define cores baseadas na prioridade
        cor_destaque = "#ff4b4b" if row['prioridade'] == "Alta" else "#003366"
        fundo_leve = "rgba(255, 75, 75, 0.1)" if row['prioridade'] == "Alta" else "rgba(0, 51, 102, 0.05)"
        
        # Card transparente com borda lateral
        st.markdown(f"""
            <div style="
                padding: 20px; 
                margin-bottom: 15px; 
                border-left: 6px solid {cor_destaque}; 
                background-color: {fundo_leve}; 
                border-radius: 5px;
                color: inherit;
            ">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 12px; color: gray;">📅 {row['data']}</span>
                    <span style="font-size: 11px; font-weight: bold; color: {cor_destaque};">● PRIORIDADE {row['prioridade'].upper()}</span>
                </div>
                <h3 style="margin: 10px 0; color: {cor_destaque};">{row['titulo']}</h3>
                <p style="font-size: 16px; line-height: 1.5;">{row['mensagem']}</p>
                <hr style="margin: 10px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
                <span style="font-size: 12px; color: gray;">Postado por: <b>{row['autor']}</b></span>
            </div>
        """, unsafe_allow_html=True)
        
        # Botão de exclusão (Apenas autor ou gestor)
        if st.session_state.cargo == "Gestor" or row['autor'] == st.session_state.nome:
            if st.button(f"🗑️ Remover Aviso #{row['id']}", key=f"del_{row['id']}"):
                conn = conectar()
                conn.execute("DELETE FROM avisos WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
else:
    st.info("📭 O mural está vazio no momento.")