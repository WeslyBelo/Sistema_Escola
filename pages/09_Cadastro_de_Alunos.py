import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import io

st.set_page_config(page_title="Cadastro de Alunos", layout="wide")

if 'logado' not in st.session_state or not st.session_state.logado:
    st.error("⚠️ Faça login para acessar.")
    st.stop()

def conectar():
    return sqlite3.connect('escola.db')

st.title("📝 Gestão de Cadastros: Alunos")

# --- 1. ABAS PARA ORGANIZAR OS MÉTODOS DE CADASTRO ---
tab1, tab2 = st.tabs(["👤 Cadastro Individual", "📊 Cadastro em Massa (Excel/CSV)"])

# --- ABA 1: CADASTRO INDIVIDUAL (COM FOTO) ---
with tab1:
    with st.form("form_individual", clear_on_submit=True):
        col_f, col_d = st.columns([1, 2])
        with col_f:
            foto = st.file_uploader("Foto de Perfil", type=["jpg", "png"])
        with col_d:
            nome = st.text_input("Nome Completo")
            mat = st.text_input("Matrícula")
            c1, c2, c3 = st.columns(3)
            with c1: ano = st.selectbox("Ano:", ["1º Ano", "2º Ano", "3º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "1º EM", "2º EM", "3º EM"], key="ind_ano")
            with c2: num = st.selectbox("ID Turma:", ["1", "2", "3", "4", "5"], key="ind_num")
            with c3: let = st.selectbox("Letra:", ["A", "B", "C", "D"], key="ind_let")
        
        if st.form_submit_button("✅ Salvar Individual"):
            if nome and mat:
                div = f"{num}{let}"
                conn = conectar()
                conn.execute("INSERT INTO alunos (matricula, nome, turma, divisao) VALUES (?,?,?,?)", (mat, nome, ano, div))
                conn.commit()
                conn.close()
                st.success(f"{nome} cadastrado!")

# --- ABA 2: CADASTRO EM MASSA ---
with tab2:
    st.subheader("Importar Planilha de Alunos")
    st.info("""
        A sua planilha deve conter as colunas exatamente com estes nomes: 
        **nome**, **matricula**, **turma**, **divisao** (Ex: 4A, 1B).
    """)
    
    arquivo_upload = st.file_uploader("Subir arquivo Excel ou CSV", type=["xlsx", "csv"])

    if arquivo_upload:
        try:
            if arquivo_upload.name.endswith('.csv'):
                df_massa = pd.read_csv(arquivo_upload)
            else:
                df_massa = pd.read_excel(arquivo_upload)
            
            st.write("### Prévia dos dados a serem importados:")
            st.dataframe(df_massa.head(), use_container_width=True)
            
            if st.button("🚀 Confirmar Importação de todos os alunos"):
                conn = conectar()
                sucesso = 0
                erros = 0
                
                for _, row in df_massa.iterrows():
                    try:
                        conn.execute("""
                            INSERT INTO alunos (nome, matricula, turma, divisao) 
                            VALUES (?, ?, ?, ?)
                        """, (str(row['nome']), str(row['matricula']), str(row['turma']), str(row['divisao'])))
                        sucesso += 1
                    except Exception as e:
                        erros += 1
                
                conn.commit()
                conn.close()
                st.success(f"✅ Importação concluída! {sucesso} alunos adicionados.")
                if erros > 0:
                    st.warning(f"⚠️ {erros} registros falharam (possível matrícula duplicada).")
                    
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# --- 3. LISTAGEM PARA CONFERÊNCIA ---
st.divider()
st.subheader("📋 Lista de Alunos no Sistema")
conn = conectar()
df_total = pd.read_sql("SELECT matricula, nome, turma, divisao FROM alunos ORDER BY id DESC", conn)
conn.close()
st.dataframe(df_total, use_container_width=True)