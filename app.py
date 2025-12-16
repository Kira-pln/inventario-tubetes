import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# ===============================
# CONFIGURAÇÃO
# ===============================
st.set_page_config(
    page_title="Inventário de Tubetes",
    page_icon="📦",
    layout="wide"
)

# ===============================
# ARQUIVOS
# ===============================
ARQ_INV = "inventario.csv"
ARQ_TIPOS = "tipos_tubetes.csv"

# ===============================
# FUNÇÕES
# ===============================
def carregar_tipos():
    if os.path.exists(ARQ_TIPOS):
        return pd.read_csv(ARQ_TIPOS)
    return pd.DataFrame(columns=["Tipo", "Descricao", "Tempo Estufa (h)"])

def carregar_inv():
    if os.path.exists(ARQ_INV):
        return pd.read_csv(
            ARQ_INV,
            parse_dates=["Entrada", "Retirada Prevista", "Saida"]
        )
    return pd.DataFrame(columns=[
        "Tipo",
        "Descricao",
        "Quantidade",
        "Entrada",
        "Retirada Prevista",
        "Saida",
        "Quantidade Saida",
        "Umidade Saida"
    ])

def salvar_tipos(df):
    df.to_csv(ARQ_TIPOS, index=False)

def salvar_inv(df):
    df.to_csv(ARQ_INV, index=False)

# ===============================
# SESSION STATE
# ===============================
if "tipos" not in st.session_state:
    st.session_state.tipos = carregar_tipos()

if "inventario" not in st.session_state:
    st.session_state.inventario = carregar_inv()

# ===============================
# CABEÇALHO
# ===============================
st.title("📦 Sistema de Inventário de Tubetes")
st.caption("Controle de estufa • entrada • saída • rastreabilidade")

# ===============================
# MENU SUPERIOR (ABAS)
# ===============================
abas = st.tabs([
    "🧾 Cadastro de Tubetes",
    "📥 Entrada",
    "📤 Saída",
    " Relatórios"
])

# ======================================================
#  CADASTRO DE TUBETES
# ======================================================
with abas[0]:
    st.subheader("Cadastro de Tipos de Tubetes")

    col1, col2 = st.columns(2)

    with col1:
        tipo = st.text_input("Tipo do Tubete (ex: 76,5x10x162)")
        tempo = st.number_input(
            "Tempo máximo na estufa (horas)",
            min_value=1,
            step=1
        )

    with col2:
        descricao = st.text_area("Descrição do Tubete")

    if st.button("💾 Salvar Tipo", use_container_width=True):
        if tipo.strip() == "":
            st.error("Informe o tipo do tubete.")
        else:
            novo = pd.DataFrame([{
                "Tipo": tipo,
                "Descricao": descricao,
                "Tempo Estufa (h)": tempo
            }])

            st.session_state.tipos = pd.concat(
                [st.session_state.tipos, novo],
                ignore_index=True
            )
            salvar_tipos(st.session_state.tipos)
            st.success("Tipo cadastrado com sucesso!")

    st.divider()
    st.subheader("Tipos Cadastrados")
    st.dataframe(st.session_state.tipos, use_container_width=True)

# ======================================================
# 📥 ENTRADA
# ======================================================
with abas[1]:
    st.subheader("Entrada de Tubetes na Estufa")

    if st.session_state.tipos.empty:
        st.warning("Cadastre um tipo de tubete primeiro.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            tipo_sel = st.selectbox(
                "Tipo de Tubete",
                st.session_state.tipos["Tipo"]
            )

        tipo_info = st.session_state.tipos[
            st.session_state.tipos["Tipo"] == tipo_sel
        ].iloc[0]

        with col2:
            data_entrada = st.datetime_input(
                "Data e Hora de Entrada",
                datetime.now()
            )

        with col3:
            qtd = st.number_input(
                "Quantidade",
                min_value=1,
                step=1
            )

        retirada_prev = data_entrada + timedelta(
            hours=int(tipo_info["Tempo Estufa (h)"])
        )

        st.info(
            f"📄 {tipo_info['Descricao']} | "
            f"⏱ Retirada após {tipo_info['Tempo Estufa (h)']}h "
            f"({retirada_prev.strftime('%d/%m/%Y %H:%M')})"
        )

        if st.button("📥 Registrar Entrada", use_container_width=True):
            novo = pd.DataFrame([{
                "Tipo": tipo_sel,
                "Descricao": tipo_info["Descricao"],
                "Quantidade": qtd,
                "Entrada": data_entrada,
                "Retirada Prevista": retirada_prev,
                "Saida": None,
                "Quantidade Saida": None,
                "Umidade Saida": None
            }])

            st.session_state.inventario = pd.concat(
                [st.session_state.inventario, novo],
                ignore_index=True
            )
            salvar_inv(st.session_state.inventario)
            st.success("Entrada registrada com sucesso!")

# ======================================================
# 📤 SAÍDA
# ======================================================
with abas[2]:
    st.subheader("Saída de Tubetes")

    estoque = st.session_state.inventario[
        st.session_state.inventario["Saida"].isna()
    ]

    if estoque.empty:
        st.warning("Não há tubetes disponíveis no estoque.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            tipo_sel = st.selectbox(
                "Tipo de Tubete",
                estoque["Tipo"].unique()
            )

        estoque_tipo = estoque[estoque["Tipo"] == tipo_sel]

        with col2:
            idx = st.selectbox(
                "Lote (Entrada)",
                estoque_tipo.index,
                format_func=lambda x: (
                    f"{estoque_tipo.loc[x,'Entrada'].strftime('%d/%m/%Y %H:%M')} "
                    f"| Qtd: {estoque_tipo.loc[x,'Quantidade']}"
                )
            )

        col3, col4, col5 = st.columns(3)

        with col3:
            data_saida = st.datetime_input(
                "Data e Hora da Retirada",
                datetime.now()
            )

        with col4:
            qtd_saida = st.number_input(
                "Quantidade de Saída",
                min_value=1,
                max_value=int(estoque_tipo.loc[idx, "Quantidade"]),
                step=1
            )

        with col5:
            umidade = st.number_input(
                "Umidade de Saída (%)",
                min_value=0,
                max_value=100,
                step=1
            )

        liberacao = estoque_tipo.loc[idx, "Retirada Prevista"]

        if datetime.now() < liberacao:
            st.error(
                f"⚠️ Retirada permitida somente após "
                f"{liberacao.strftime('%d/%m/%Y %H:%M')}"
            )
        else:
            if st.button("📤 Registrar Saída", use_container_width=True):
                st.session_state.inventario.at[idx, "Quantidade"] -= qtd_saida
                st.session_state.inventario.at[idx, "Saida"] = data_saida
                st.session_state.inventario.at[idx, "Quantidade Saida"] = qtd_saida
                st.session_state.inventario.at[idx, "Umidade Saida"] = umidade
                salvar_inv(st.session_state.inventario)
                st.success("Saída registrada com sucesso!")

# ======================================================
# 📊 RELATÓRIOS
# ======================================================
with abas[3]:
    st.subheader("Relatórios de Inventário")

    df = st.session_state.inventario.copy()
    estoque = df[df["Saida"].isna()]

    estoque["Pode Retirar?"] = estoque["Retirada Prevista"].apply(
        lambda x: "Sim" if datetime.now() >= x else "Não"
    )

    st.markdown("### 📦 Inventário Atual")
    st.dataframe(
        estoque[[
            "Tipo", "Descricao", "Quantidade",
            "Entrada", "Retirada Prevista", "Pode Retirar?"
        ]],
        use_container_width=True
    )

    st.markdown("### 🚚 Histórico de Saídas")
    saidas = df[df["Saida"].notna()]
    st.dataframe(
        saidas[[
            "Tipo", "Descricao",
            "Entrada", "Saida",
            "Quantidade Saida", "Umidade Saida"
        ]],
        use_container_width=True
    )
