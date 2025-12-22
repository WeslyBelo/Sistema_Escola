import streamlit as st
import sqlite3
import pandas as pd
import os

st.set_page_config(page_title="Configurações", layout="wide")

# Proteção de segurança contra acesso direto via URL
if 'logado' not in st.session_state or not st.session_state.logado:
    st.error("⚠️ Acesso negado. Por favor, faça login.")
    st.stop()

# Verifica o cargo de forma segura usando .get() para evitar AttributeError
if st.session_state.get('cargo') != "Gestor":
    st.warning("⛔ Apenas utilizadores com perfil de **Gestor** podem aceder a esta página.")
    st.stop()

st.title("⚙️ Configurações do Sistema")

# --- SEÇÃO: PONTUAÇÃO ---
st.subheader("Configurações Disciplinares")
conn = sqlite3.connect('escola.db')
res = conn.execute("SELECT valor FROM config_geral WHERE chave='pontos_iniciais'").fetchone()
pontos_atuais = int(res[0]) if res else 100

novo_ponto = st.number_input("Pontuação Inicial de Conduta:", value=pontos_atuais)
if st.button("Salvar Pontuação"):
    conn.execute("INSERT OR REPLACE INTO config_geral (chave, valor) VALUES ('pontos_iniciais', ?)", (str(novo_ponto),))
    conn.commit()
    st.success("Pontuação atualizada!")

st.divider()

# --- SEÇÃO: RESET ---
st.subheader("🚨 Zona de Perigo")
st.write("Estas ações são permanentes e apagam todos os dados dos alunos.")

if st.button("Limpar Todos os Alunos e Notas"):
    if st.checkbox("Confirmo que desejo apagar tudo"):
        conn.execute("DELETE FROM alunos")
        conn.execute("DELETE FROM ocorrencias")
        conn.execute("DELETE FROM frequencia")
        conn.commit()
        st.success("Banco de dados limpo com sucesso!")

conn.close()