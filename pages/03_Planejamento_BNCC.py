import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Planejamento BNCC", layout="wide")

# --- 1. VERIFICAÇÃO DE SEGURANÇA ---
if 'logado' not in st.session_state or not st.session_state.logado:
    st.error("⚠️ Por favor, faça login na página inicial para acessar o planejamento.")
    st.stop()

# --- 2. CABEÇALHO (CORREÇÃO DO ERRO AQUI) ---
st.markdown(f"""
    <div style="background-color: #003366; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style='color: white; margin: 0;'>📝 Planejamento de Aula (BNCC)</h1>
        <p style='color: #ddd; margin: 5px 0 0 0;'>Professor: <b style='color: white;'>{st.session_state.nome}</b> | Perfil: <b style='color: white;'>{st.session_state.cargo}</b></p>
    </div>
""", unsafe_allow_html=True) # <-- Corrigido de unsafe_allow_value para unsafe_allow_html

# --- 3. CONEXÃO COM BANCO ---
def conectar():
    return sqlite3.connect('escola.db')

conn = conectar()
conn.execute('''CREATE TABLE IF NOT EXISTS planos_aula 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  professor TEXT, turma TEXT, data TEXT, 
                  objetivos TEXT, conteudo TEXT, habilidades_bncc TEXT)''')
conn.close()

# --- 4. FORMULÁRIO DE PLANEJAMENTO ---
with st.form("form_bncc"):
    col1, col2 = st.columns(2)
    
    with col1:
        turma = st.selectbox("Turma:", ["6º Ano", "7º Ano", "8º Ano", "9º Ano", "1º EM", "2º EM", "3º EM"])
        data_aula = st.date_input("Data da Aula:", datetime.now())
    
    with col2:
        # Exemplo de habilidades BNCC comuns
        habilidades = st.multiselect("Habilidades BNCC:", 
                                     ["EF06HI01", "EF07HI02", "EM13CHS101", "EM13CHS603", "EF09LP01"],
                                     help="Selecione os códigos das habilidades trabalhadas nesta aula.")

    objetivos = st.text_area("Objetivos de Aprendizagem (O que o aluno vai aprender?)")
    conteudo = st.text_area("Metodologia e Conteúdo (Como será a aula?)")
    
    submit = st.form_submit_button("💾 Salvar Planejamento")

    if submit:
        if objetivos and conteudo:
            conn = conectar()
            conn.execute("""INSERT INTO planos_aula (professor, turma, data, objetivos, conteudo, habilidades_bncc) 
                         VALUES (?, ?, ?, ?, ?, ?)""", 
                         (st.session_state.nome, turma, data_aula.strftime('%d/%m/%Y'), 
                          objetivos, conteudo, ", ".join(habilidades)))
            conn.commit()
            conn.close()
            st.success("✅ Plano de aula guardado!")
            st.balloons()
        else:
            st.warning("Preencha os campos obrigatórios.")

st.divider()

# --- 5. VISUALIZAÇÃO ---
st.subheader("📚 Histórico de Planejamentos")
conn = conectar()
df_planos = pd.read_sql(f"SELECT data, turma, habilidades_bncc, objetivos FROM planos_aula WHERE professor = '{st.session_state.nome}' ORDER BY id DESC", conn)
conn.close()

if not df_planos.empty:
    st.dataframe(df_planos, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum plano encontrado para este professor.")