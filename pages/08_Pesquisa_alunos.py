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

# --- 1. GARANTIR ESTRUTURA DO BANCO (FORÇAR TELEFONE) ---
conn = conectar()
cursor = conn.cursor()
# Cria a tabela do zero se não existir
cursor.execute('''CREATE TABLE IF NOT EXISTS alunos 
               (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                matricula TEXT UNIQUE, nome TEXT, turma TEXT, 
                divisao TEXT, telefone TEXT, foto_perfil BLOB)''')

# Tenta adicionar a coluna telefone especificamente caso a tabela já exista
try:
    cursor.execute("ALTER TABLE alunos ADD COLUMN telefone TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass # A coluna já existe, ignorar erro
conn.close()

st.title("📝 Cadastro de Alunos")

tab1, tab2 = st.tabs(["👤 Cadastro Individual", "📊 Importação em Massa"])

# --- ABA 1: CADASTRO INDIVIDUAL ---
with tab1:
    with st.form("form_novo_aluno", clear_on_submit=True):
        col_img, col_info = st.columns([1, 2])
        
        with col_img:
            st.subheader("Foto do Aluno")
            foto_upload = st.file_uploader("Upload da Foto", type=["jpg", "png", "jpeg"])
            if foto_upload:
                st.image(foto_upload, width=150)

        with col_info:
            st.subheader("Informações Cadastrais")
            nome = st.text_input("Nome Completo")
            mat = st.text_input("Número de Matrícula (ID)")
            
            # --- CAMPO DE TELEFONE ADICIONADO AQUI ---
            telefone = st.text_input("📞 Telefone do Responsável", placeholder="Ex: (00) 99999-9999")
            
            c1, c2, c3 = st.columns(3)
            with c1: serie = st.selectbox("Série/Ano:", ["1º Ano", "2º Ano", "3º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "1º EM", "2º EM", "3º EM"])
            with c2: id_turma = st.selectbox("Identificador:", ["1", "2", "3", "4", "5"])
            with c3: letra_turma = st.selectbox("Letra:", ["A", "B", "C", "D"])

        divisao_final = f"{id_turma}{letra_turma}"
        
        btn_salvar = st.form_submit_button("✅ Cadastrar Aluno")

        if btn_salvar:
            if nome and mat:
                foto_bytes = None
                if foto_upload:
                    img = Image.open(foto_upload).convert("RGB")
                    img = img.resize((300, 300))
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG")
                    foto_bytes = buffer.getvalue()

                conn = conectar()
                try:
                    conn.execute("""
                        INSERT INTO alunos (matricula, nome, turma, divisao, telefone, foto_perfil) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (mat.strip(), nome.strip(), serie, divisao_final, telefone, foto_bytes))
                    conn.commit()
                    st.success(f"Aluno {nome} registrado com telefone {telefone}!")
                except sqlite3.IntegrityError:
                    st.error("ERRO: Esta matrícula já está cadastrada.")
                finally:
                    conn.close()
            else:
                st.warning("Preencha o Nome e a Matrícula.")

# --- ABA 2: IMPORTAÇÃO EM MASSA ---
with tab2:
    st.info("Sua planilha Excel deve ter as colunas: **nome**, **matricula**, **turma**, **divisao**, **telefone**")
    arquivo = st.file_uploader("Selecione a planilha", type=["xlsx", "csv"])
    
    if arquivo:
        df = pd.read_csv(arquivo) if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
        st.dataframe(df.head())
        
        if st.button("🚀 Confirmar Importação"):
            conn = conectar()
            for _, r in df.iterrows():
                try:
                    # Garante que as colunas existem no DF antes de salvar
                    tel_planilha = r['telefone'] if 'telefone' in df.columns else ""
                    conn.execute("""
                        INSERT INTO alunos (nome, matricula, turma, divisao, telefone) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (str(r['nome']), str(r['matricula']), str(r['turma']), str(r['divisao']), str(tel_planilha)))
                except: pass
            conn.commit()
            conn.close()
            st.success("Importação concluída!")

# --- VISUALIZAÇÃO ---
st.divider()
st.subheader("📋 Lista de Alunos (Conferência de Telefone)")
conn = conectar()
df_lista = pd.read_sql("SELECT matricula, nome, turma, divisao, telefone FROM alunos ORDER BY id DESC", conn)
conn.close()
st.dataframe(df_lista, use_container_width=True)