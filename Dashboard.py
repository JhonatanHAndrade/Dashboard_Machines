import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Análise de Máquinas")

# --- CARREGAR DADOS ---
@st.cache_data
def carregar_dados():
    df = pd.read_csv('smart_manufacturing_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['machine_status'] = df['machine_status'].str.lower().str.strip()
    return df

df = carregar_dados()

# --- BARRA LATERAL DE FILTROS GERAIS ---
st.sidebar.header("Filtros")
maquinas = st.sidebar.multiselect("Máquinas", df['machine'].unique(), default=df['machine'].unique())
status = st.sidebar.multiselect("Status da Máquina", df['machine_status'].unique(), default=df['machine_status'].unique())

# --- Filtro de ano com segurança ---
anos_disponiveis = sorted(df['timestamp'].dropna().dt.year.unique())
if len(anos_disponiveis) == 0:
    st.error("Nenhum dado com ano disponível.")
    st.stop()

min_ano = int(min(anos_disponiveis))
max_ano = int(max(anos_disponiveis))

if min_ano == max_ano:
    intervalo_ano = (min_ano, max_ano)
    st.sidebar.markdown(f"**Ano disponível:** {min_ano}")
else:
    intervalo_ano = st.sidebar.slider("Ano (intervalo)", min_ano, max_ano, (min_ano, max_ano), step=1)

# --- APLICAR FILTROS GERAIS ---
df_filtrado = df[
    (df['machine'].isin(maquinas)) &
    (df['machine_status'].isin(status)) &
    (df['timestamp'].dt.year.between(intervalo_ano[0], intervalo_ano[1]))
]

# --- DICIONÁRIO MÊS NUMERO -> NOME ---
meses_dict = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# --- CRIAR ABAS ---
abas = st.tabs(["📊 Visão Geral", "⚙️ Eficiência", "📁 Relatório"])

# ----------------------
# ABA 1 - VISÃO GERAL 
# ----------------------
with abas[0]:
    st.header("Visão Geral das Máquinas")

    st.subheader("Distribuição de Status das Máquinas")
    st.plotly_chart(px.histogram(df_filtrado, x='machine_status'), use_container_width=True)

    st.subheader("Temperatura por Status")
    st.plotly_chart(px.box(df_filtrado, x='machine_status', y='temperature'), use_container_width=True)

    st.subheader("Temperatura vs Vibração")
    st.plotly_chart(px.scatter(df_filtrado, x='temperature', y='vibration', color='machine_status'), use_container_width=True)

    st.subheader("Umidade vs Temperatura")
    st.plotly_chart(px.scatter(df_filtrado, x='humidity', y='temperature', color='machine_status'), use_container_width=True)

    st.subheader("Vibração por Máquina")
    st.plotly_chart(px.box(df_filtrado, x='machine', y='vibration'), use_container_width=True)

    st.subheader("Temperatura Média por Máquina")
    temp_media = df_filtrado.groupby('machine')['temperature'].mean().reset_index()
    st.plotly_chart(px.bar(temp_media, x='machine', y='temperature', title='Temperatura Média'), use_container_width=True)

    st.subheader("Energia Média por Máquina")
    energia_media = df_filtrado.groupby('machine')['energy_consumption'].mean().reset_index()
    st.plotly_chart(px.bar(energia_media, x='machine', y='energy_consumption', title='Energia Média'), use_container_width=True)

    st.subheader("Consumo Médio de Energia (Filtro por mês e dia)")

    df_data = df_filtrado.copy()
    df_data['mes'] = df_data['timestamp'].dt.month
    df_data['dia'] = df_data['timestamp'].dt.day

    meses_disponiveis = sorted(df_data['mes'].unique())
    nomes_meses_disponiveis = [meses_dict[m] for m in meses_disponiveis]

    mes_selecionado_nome = st.selectbox("Selecione o mês", nomes_meses_disponiveis)


    mes_selecionado = {v: k for k, v in meses_dict.items()}[mes_selecionado_nome]


    dias_disponiveis = sorted(df_data[df_data['mes'] == mes_selecionado]['dia'].unique())
    dia_selecionado = st.selectbox("Selecione o dia", dias_disponiveis, format_func=lambda x: f"{x:02d}")

    df_energia = df_data[
        (df_data['mes'] == mes_selecionado) &
        (df_data['dia'] == dia_selecionado)
    ]

    energia_serie = df_energia.groupby('timestamp')['energy_consumption'].mean().reset_index()
    st.plotly_chart(px.line(energia_serie, x='timestamp', y='energy_consumption', title='Energia Média por Hora'), use_container_width=True)

# ----------------------
# ABA 2 - EFICIÊNCIA 
# ----------------------
with abas[1]:
    st.header("Eficiência das Máquinas")

    status_counts = df_filtrado.groupby(['machine', 'machine_status']).size().unstack(fill_value=0)
    for col in ['running', 'idle', 'failure']:
        if col not in status_counts:
            status_counts[col] = 0

    status_counts['total'] = status_counts[['running', 'idle', 'failure']].sum(axis=1)
    status_counts['efficiency_percent'] = (status_counts['running'] / status_counts['total']) * 100
    status_counts = status_counts.reset_index()

    top10 = status_counts.sort_values(by='efficiency_percent', ascending=False).head(10)
    low10 = status_counts.sort_values(by='efficiency_percent').head(10)

    st.subheader("Mais Eficientes")
    st.plotly_chart(px.bar(top10, x='machine', y='efficiency_percent', title='Eficiência (%)'), use_container_width=True)

    st.subheader("Menos Eficientes")
    st.plotly_chart(px.bar(low10, x='machine', y='efficiency_percent', title='Eficiência (%)'), use_container_width=True)

# ----------------------
# ABA 3 - RELATÓRIO
# ----------------------
with abas[2]:
    st.header("Visualização de Dados e Download")
    st.dataframe(df_filtrado)

    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Baixar CSV Filtrado", data=csv, file_name="dados_filtrados.csv", mime='text/csv')






