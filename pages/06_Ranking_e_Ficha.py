import streamlit as st
import sqlite3
import pandas as pd
import os

st.set_page_config(page_title="Ranking e Histórico", layout="wide")

if 'logado' not in st.session_state or not st.session_state.logado:
    st.error("⚠️ Por favor, realize o login.")
    st.stop()

st.title("🏆 Ranking e Histórico Disciplinar")

def conectar():
    return sqlite3.connect('escola.db')

# --- 1. CONFIGURAÇÕES DE PONTOS ---
conn = conectar()
res_base = conn.execute("SELECT valor FROM config_geral WHERE chave='pontos_iniciais'").fetchone()
BASE_PTS = int(res_base[0]) if res_base else 100
conn.close()

tab_ranking, tab_ficha = st.tabs(["📊 Ranking por Turma", "📄 Ficha Individual"])

# --- ABA: RANKING ---
with tab_ranking:
    st.subheader("Classificação Geral das Turmas")
    
    conn = conectar()
    # INNER JOIN garante que apenas alunos ATIVOS (que existem na tabela alunos) contem pontos
    query_rank = """
        SELECT a.turma, a.divisao, SUM(o.pontos) as saldo_pontos, COUNT(DISTINCT a.id) as total_alunos
        FROM alunos a
        INNER JOIN ocorrencias o ON a.id = o.aluno_id
        GROUP BY a.turma, a.divisao
    """
    df_rank = pd.read_sql(query_rank, conn)
    conn.close()

    if not df_rank.empty:
        df_rank['Média de Conduta'] = BASE_PTS + (df_rank['saldo_pontos'] / df_rank['total_alunos'])
        df_rank['Classe'] = df_rank['turma'] + " " + df_rank['divisao']
        
        df_final = df_rank[['Classe', 'total_alunos', 'Média de Conduta']].sort_values('Média de Conduta', ascending=False)
        
        st.dataframe(
            df_final,
            column_config={
                "Média de Conduta": st.column_config.NumberColumn(format="%.1f pts"),
                "total_alunos": "Alunos Ativos"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("💡 O ranking aparecerá assim que houver alunos ativos com ocorrências registradas.")

# --- ABA: FICHA INDIVIDUAL (COM TRAVA DE PESQUISA) ---
with tab_ficha:
    st.subheader("Consulta de Ficha Individual")
    
    conn = conectar()
    # Busca apenas alunos que não foram excluídos
    df_vivos = pd.read_sql("SELECT * FROM alunos ORDER BY nome", conn)
    conn.close()

    if not df_vivos.empty:
        # Lógica de "Em Branco": Adicionamos uma opção neutra no início
        lista_nomes = ["Digite ou selecione um aluno..."] + [f"{r['nome']} ({r['turma']} {r['divisao']})" for _, r in df_vivos.iterrows()]
        aluno_input = st.selectbox("Pesquise o Aluno:", lista_nomes)

        if aluno_input != "Digite ou selecione um aluno...":
            # Extrai o nome para buscar o ID (considerando o formato da string)
            nome_extraido = aluno_input.split(" (")[0]
            aluno_info = df_vivos[df_vivos['nome'] == nome_extraido]

            if not aluno_info.empty:
                aluno_info = aluno_info.iloc[0]
                id_aluno = aluno_info['id']
                
                c1, c2 = st.columns([1, 3])
                with c1:
                    if aluno_info['foto_perfil'] and os.path.exists(aluno_info['foto_perfil']):
                        st.image(aluno_info['foto_perfil'], width=150)
                    else:
                        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
                
                with c2:
                    st.markdown(f"### {aluno_info['nome']}")
                    st.write(f"**Matrícula:** {aluno_info['matricula']} | **Classe:** {aluno_info['turma']} {aluno_info['divisao']}")
                    
                    conn = conectar()
                    df_hist = pd.read_sql(f"SELECT data, tipo, pontos, descricao, monitor FROM ocorrencias WHERE aluno_id = {id_aluno} ORDER BY id DESC", conn)
                    conn.close()
                    
                    saldo_atual = BASE_PTS + df_hist['pontos'].sum()
                    st.metric("Saldo Atual de Conduta", f"{saldo_atual} pts")
                    
                    st.write("**Histórico Detalhado:**")
                    st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else:
                st.error("Erro ao localizar dados do aluno.")
        else:
            st.divider()
            st.info("🔍 Utilize o campo acima para pesquisar a ficha de um aluno específico.")
    else:
        st.warning("⚠️ Não há alunos ativos no cadastro.")