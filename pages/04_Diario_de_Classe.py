import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Diário de Classe", layout="wide")

# --- 1. SEGURANÇA ---
if 'logado' not in st.session_state or not st.session_state.logado:
    st.error("⚠️ Faça login na página inicial para aceder ao Diário.")
    st.stop()

def conectar():
    return sqlite3.connect('escola.db')

st.title("📓 Diário de Classe Digital")

# --- 2. NOVA ESTRUTURA DE SELECÇÃO DE TURMA (PADRÃO ESCOLA) ---
st.markdown("### 🏫 Identificação da Turma")
col_ano, col_num, col_letra = st.columns(3)

with col_ano:
    serie_base = st.selectbox("Ano:", ["3º Ano", "1º Ano", "2º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "1º EM", "2º EM", "3º EM"])

with col_num:
    # O número que vem antes da letra (Ex: 4, 1)
    num_turma = st.selectbox("Identificador:", ["1", "2", "3", "4", "5"])

with col_letra:
    # A letra da turma (Ex: A, B)
    letra_turma = st.selectbox("Letra:", ["A", "B", "C", "D"])

# Monta o nome completo conforme o seu exemplo: "3º Ano 4A"
divisao_completa = f"{num_turma}{letra_turma}"
st.info(f"📍 Turma Selecionada: **{serie_base} {divisao_completa}**")

# --- 3. CARREGAR DADOS ---
conn = conectar()
# Filtramos pela série (turma) e pela nova divisão composta (divisao)
df_alunos = pd.read_sql(f"""
    SELECT id, nome, matricula FROM alunos 
    WHERE turma = '{serie_base}' AND divisao = '{divisao_completa}' 
    ORDER BY nome
""", conn)

df_regras = pd.read_sql("SELECT * FROM regras_indisciplina ORDER BY nome", conn)
conn.close()

if df_alunos.empty:
    st.warning(f"Nenhum aluno cadastrado no {serie_base} {divisao_completa}. Verifique o Cadastro de Alunos.")
else:
    # --- 4. INTERFACE ---
    tab_chamada, tab_indisciplina = st.tabs(["📋 Chamada Escolar", "🚨 Relato de Indisciplina"])

    with tab_chamada:
        st.subheader(f"Lista de Presença - {serie_base} {divisao_completa}")
        with st.form("form_chamada"):
            for _, aluno in df_alunos.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"👤 {aluno['nome']}")
                c2.checkbox("Presente", value=True, key=f"check_{aluno['id']}")
            
            if st.form_submit_button("💾 Salvar Frequência"):
                st.success("Chamada realizada!")

    with tab_indisciplina:
        st.subheader("⚠️ Relatar Incidente")
        with st.form("form_indisciplina_diario"):
            aluno_opcoes = {a['nome']: a['id'] for _, a in df_alunos.iterrows()}
            aluno_sel = st.selectbox("Aluno:", list(aluno_opcoes.keys()))
            
            if not df_regras.empty:
                regras_dict = {f"{r['nome']} ({r['pontos']} pts)": (r['nome'], r['pontos']) for _, r in df_regras.iterrows()}
                falta_sel = st.selectbox("Tipo de Falta:", list(regras_dict.keys()))
                nome_falta, pontos_falta = regras_dict[falta_sel]
            else:
                nome_falta, pontos_falta = "Indisciplina", -5

            relato = st.text_area("Descrição do ocorrido:")
            
            # BOTÃO DE SUBMIT OBRIGATÓRIO
            if st.form_submit_button("🚨 Enviar para Disciplina Militar"):
                if relato:
                    conn = conectar()
                    conn.execute("""
                        INSERT INTO ocorrencias (aluno_id, tipo, pontos, descricao, data, monitor) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (aluno_opcoes[aluno_sel], "Sala de Aula", pontos_falta, relato, 
                          datetime.now().strftime('%d/%m/%Y'), st.session_state.nome))
                    conn.commit()
                    conn.close()
                    st.success(f"Relato de {aluno_sel} enviado com sucesso!")
                else:
                    st.error("Descreva o ocorrido.")