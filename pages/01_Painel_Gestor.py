import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Painel do Gestor", layout="wide")

# Verificação de Segurança (Login)
if 'logado' not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Por favor, realize o login na página inicial para aceder aos indicadores.")
    st.stop()

st.title("📊 Painel de Indicadores Disciplinares")

def carregar_dados_gestor():
    conn = sqlite3.connect('escola.db')
    try:
        # 1. Tenta buscar a pontuação base configurada
        res = conn.execute("SELECT valor FROM config_geral WHERE chave='pontos_iniciais'").fetchone()
        base = int(res[0]) if res else 100
        
        # 2. Consulta com INNER JOIN: Garante que ALUNOS EXCLUÍDOS NÃO APAREÇAM
        # Só soma pontos de ocorrências cujos alunos ainda existem na tabela 'alunos'
        query = """
            SELECT a.turma, a.divisao, SUM(o.pontos) as pts, COUNT(DISTINCT a.id) as total_alunos
            FROM alunos a
            INNER JOIN ocorrencias o ON a.id = o.aluno_id
            GROUP BY a.turma, a.divisao
        """
        df = pd.read_sql(query, conn)
        
        # 3. Estatísticas rápidas para os cards
        total_alunos_cadastrados = conn.execute("SELECT COUNT(*) FROM alunos").fetchone()[0]
        total_ocorrencias = conn.execute("SELECT COUNT(*) FROM ocorrencias").fetchone()[0]
        
        conn.close()
        return df, base, total_alunos_cadastrados, total_ocorrencias
    except Exception as e:
        conn.close()
        return pd.DataFrame(), 100, 0, 0

# Execução do carregamento
df_ranking, pontos_base, total_alunos, total_ops = carregar_dados_gestor()

# --- INTERFACE DO GESTOR ---

# 1. Cards de Resumo
c1, c2, c3 = st.columns(3)
c1.metric("Alunos Ativos", total_alunos)
c2.metric("Ocorrências Totais", total_ops)

if not df_ranking.empty:
    # Cálculos de Média
    df_ranking['Média'] = pontos_base + (df_ranking['pts'] / df_ranking['total_alunos'])
    df_ranking['Turma'] = df_ranking['turma'] + " " + df_ranking['divisao']
    
    media_escola = df_ranking['Média'].mean()
    c3.metric("Média Geral da Escola", f"{media_escola:.1f} pts")

    st.divider()

    # 2. Gráficos
    col_graf1, col_graf2 = st.columns([2, 1])

    with col_graf1:
        st.subheader("🏆 Ranking de Médias por Turma")
        # Gráfico dinâmico que muda de cor (Vermelho -> Verde) conforme a nota
        fig = px.bar(
            df_ranking, 
            x='Turma', 
            y='Média', 
            color='Média',
            color_continuous_scale='RdYlGn', 
            text_auto='.1f',
            range_y=[0, pontos_base + 10]
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_graf2:
        st.subheader("📋 Top Turmas (Ativas)")
        df_display = df_ranking[['Turma', 'Média']].sort_values('Média', ascending=False)
        st.dataframe(
            df_display, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Média": st.column_config.NumberColumn(format="%.1f pts")
            }
        )

    # 3. Análise de Ocorrências Críticas
    st.divider()
    st.subheader("🚨 Tipos de Infrações mais Comuns")
    
    conn = sqlite3.connect('escola.db')
    # INNER JOIN aqui também para limpar dados de alunos excluídos
    df_tipos = pd.read_sql("""
        SELECT o.tipo, COUNT(*) as quantidade
        FROM ocorrencias o
        INNER JOIN alunos a ON o.aluno_id = a.id
        GROUP BY o.tipo
        ORDER BY quantidade DESC
    """, conn)
    conn.close()

    if not df_tipos.empty:
        fig_pizza = px.pie(df_tipos, values='quantidade', names='tipo', hole=0.4)
        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.info("Sem dados de infrações para exibir no gráfico circular.")

else:
    c3.metric("Média Geral", "0.0")
    st.divider()
    st.info("💡 O painel está em branco porque ainda não existem ocorrências lançadas para os alunos ativos.")
    st.write("Para ver os gráficos, vá até a página **05_Disciplina_Militar** e registe uma ocorrência.")