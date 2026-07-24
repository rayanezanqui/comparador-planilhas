import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Validador & PROCV Automático", page_icon="📊", layout="wide")

st.title("📊 Validador e Comparador de Planilhas (PROCV)")
st.write("Conecte a planilha base e envie o arquivo CSV para comparar e validar os dados automaticamente.")

st.sidebar.header("1. Configuração das Fontes")

sheets_url = st.sidebar.text_input("Cole o Link Público do Google Sheets:")
uploaded_csv = st.sidebar.file_uploader("Envie seu arquivo CSV", type=["csv"])

def limpar_id(texto):
    """Remove caracteres especiais como #, espaços e transforma em texto limpo"""
    if pd.isna(texto):
        return ""
    texto_limpo = re.sub(r'[#\s]', '', str(texto))
    return texto_limpo.strip()

def carregar_base_sheets(url):
    """Lê o Google Sheets buscando automaticamente a linha que contém os cabeçalhos reais"""
    if "edit" in url:
        base_url = url.split("/edit")[0] + "/export?format=csv"
    else:
        base_url = url

    # Tenta encontrar em qual linha estão as colunas (procurando por 'ID' ou 'Status')
    for i in range(10):
        try:
            df = pd.read_csv(base_url, skiprows=i)
            cols = [str(c).upper() for c in df.columns]
            if any('ID' in c for c in cols) or any('STATUS' in c for c in cols):
                return df
        except:
            continue
    return pd.read_csv(base_url)

if sheets_url and uploaded_csv:
    try:
        df_base = carregar_base_sheets(sheets_url)
        df_csv = pd.read_csv(uploaded_csv)

        st.success("✅ Arquivos carregados com sucesso!")

        st.subheader("2. Mapeamento para o PROCV")
        col1, col2 = st.columns(2)

        with col1:
            key_base = st.selectbox("Coluna Chave no Google Sheets:", df_base.columns)
        with col2:
            key_csv = st.selectbox("Coluna Chave no CSV:", df_csv.columns)

        if st.button("🚀 Processar Comparação e Validação", type="primary"):
            df_base['_key_clean'] = df_base[key_base].apply(limpar_id)
            df_csv['_key_clean'] = df_csv[key_csv].apply(limpar_id)

            resultado = pd.merge(
                df_csv, 
                df_base, 
                on='_key_clean', 
                how="left", 
                suffixes=('_CSV', '_SHEETS')
            )

            resultado["Status_Validacao"] = resultado['_key_clean'].apply(
                lambda x: "🟢 Encontrado" if x in df_base['_key_clean'].values else "🔴 Não Encontrado"
            )

            resultado = resultado.drop(columns=['_key_clean'])

            st.divider()
            st.subheader("3. Resultado da Comparação")

            total = len(resultado)
            encontrados = (resultado["Status_Validacao"] == "🟢 Encontrado").sum()
            nao_encontrados = total - encontrados

            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Registros (CSV)", total)
            m2.metric("🟢 Encontrados na Base", encontrados)
            m3.metric("🔴 Não Encontrados", nao_encontrados)

            st.dataframe(resultado, use_container_width=True)

            csv_export = resultado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Resultado Completo (CSV)",
                data=csv_export,
                file_name="resultado_procv_validado.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os arquivos: {e}")
else:
    st.info("👈 Insira o link do Google Sheets e faça o upload do CSV na barra lateral para começar.")
