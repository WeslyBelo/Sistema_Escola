import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Disciplina Militar", layout="wide")

# --- 1. SEGURANÇA ---
if 'logado' not in st.session_state or not st.session_state.logado:
    st.error("⚠️ Faça login na página inicial para aceder à Disciplina.")
    st.stop()

def conectar():
    return sqlite3.connect('escola.db')

# --- 2. INICIALIZAÇÃO E MIGRAÇÃO DO BANCO ---
conn = conectar()
# Garante que todas as tabelas e colunas necessárias existem
conn.execute('''CREATE TABLE IF NOT EXISTS regras_indisciplina 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, pontos INTEGER)''')
conn.execute('''CREATE TABLE IF NOT EXISTS ocorrencias 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, tipo TEXT, 
              pontos INTEGER, descricao TEXT, data TEXT, monitor TEXT, status TEXT DEFAULT 'Pendente')''')
conn.execute('''CREATE TABLE IF NOT EXISTS frequencia 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, data TEXT, presenca INTEGER)''')

# Tenta adicionar a coluna status caso a tabela ocorrencias já existisse sem ela
try:
    conn.execute("ALTER TABLE ocorrencias ADD COLUMN status TEXT DEFAULT 'Pendente'")
except:
    pass
conn.commit()
conn.close()

st.title("🎖️ Departamento de Disciplina Militar")

# --- 3. GATILHO FICAI (ALERTA DE EVASÃO ESCOLAR) ---
st.subheader("🚨 Alerta FICAI - Risco de Evasão")

def verificar_ficai():
    conn = conectar()
    # Busca alunos com 3 ou mais faltas registradas no sistema
    query = """
        SELECT a.nome, a.turma, a.divisao, COUNT(f.id) as total_faltas
        FROM alunos a
        JOIN frequencia f ON a.id = f.aluno_id
        WHERE f.presenca = 0
        GROUP BY a.id
        HAVING total_faltas >= 3
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df_ficai = verificar_ficai()

if not df_ficai.empty:
    for _, row in df_ficai.iterrows():
        st.error(f"⚠️ **FICAI ATIVO:** {row['nome']} ({row['turma']} {row['divisao']}) atingiu {row['total_faltas']} faltas!")
else:
    st.success("✅ Nenhuma irregularidade crítica de frequência detectada.")

st.divider()

# --- 4. RELATOS PENDENTES (VINDOS DO DIÁRIO DE CLASSE) ---
st.subheader("⏳ Relatos de Sala de Aula para Validação")

conn = conectar()
query_pendentes = """
    SELECT o.id, a.nome as aluno, a.turma, a.divisao, o.tipo, o.pontos, o.descricao, o.data, o.monitor 
    FROM ocorrencias o
    JOIN alunos a ON o.aluno_id = a.id
    WHERE o.status = 'Pendente'
    ORDER BY o.id DESC
"""
df_pendentes = pd.read_sql(query_pendentes, conn)
conn.close()

if not df_pendentes.empty:
    for index, row in df_pendentes.iterrows():
        with st.expander(f"🔴 NOVO RELATO: {row['aluno']} ({row['turma']} {row['divisao']})"):
            c_info, c_txt = st.columns([1, 2])
            with c_info:
                st.write(f"**Data:** {row['data']}")
                st.write(f"**Professor:** {row['monitor']}")
                st.write(f"**Sugerido:** {row['pontos']} pts")
            with c_txt:
                st.info(f"**Descrição:** {row['descricao']}")
            
            b1, b2, _ = st.columns([1, 1, 2])
            if b1.button("✅ Confirmar Punição", key=f"conf_{row['id']}"):
                conn = conectar()
                conn.execute("UPDATE ocorrencias SET status = 'Aprovado' WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
            if b2.button("🗑️ Ignorar", key=f"ign_{row['id']}"):
                conn = conectar()
                conn.execute("DELETE FROM ocorrencias WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
else:
    st.info("Nenhum relato de professor aguardando revisão.")

st.divider()

# --- 5. GESTÃO DE REGRAS (CONFIGURAÇÃO DE PONTOS) ---
if st.session_state.cargo == "Gestor":
    with st.expander("⚙️ Configurar Tabela de Pontos e Regras"):
        with st.form("form_regras_militar", clear_on_submit=True):
            col_n, col_p = st.columns(2)
            nome_regra = col_n.text_input("Nome da Regra (Ex: Atraso, Fardamento)")
            valor_ponto = col_p.number_input("Pontuação (Negativo para faltas)", value=-5)
            if st.form_submit_button("💾 Salvar Nova Regra"):
                if nome_regra:
                    conn = conectar()
                    conn.execute("INSERT OR REPLACE INTO regras_indisciplina (nome, pontos) VALUES (?,?)", 
                                 (nome_regra.strip(), valor_ponto))
                    conn.commit()
                    conn.close()
                    st.success("Regra atualizada com sucesso!")
                    st.rerun()

# --- 6. HISTÓRICO GERAL DE OCORRÊNCIAS EFETIVADAS ---
st.subheader("📚 Histórico Disciplinar Consolidado")
conn = conectar()
df_hist = pd.read_sql("""
    SELECT a.nome as Aluno, a.turma as Ano, a.divisao as Turma, o.tipo as Falta, 
           o.pontos as Pts, o.data as Data, o.monitor as Aplicado_Por
    FROM ocorrencias o
    JOIN alunos a ON o.aluno_id = a.id
    WHERE o.status = 'Aprovado'
    ORDER BY o.id DESC
""", conn)
conn.close()

if not df_hist.empty:
    st.dataframe(df_hist, use_container_width=True, hide_index=True)
else:
    st.write("O histórico está limpo.")