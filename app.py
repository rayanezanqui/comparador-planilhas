import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Validador & PROCV Automático", page_icon="📊", layout="wide")

st.title("📊 Validador e Comparador de Planilhas (PROCV)")
st.write("Conecte a planilha base e envie o arquivo CSV para comparar e validar os dados automaticamente.")

st.sidebar.header("1. Configuração das Fontes")

# Input do Google Sheets e CSV
sheets_url = st.sidebar.text_input("Cole o Link Público do Google Sheets:")
uploaded_csv = st.sidebar.file_uploader("Envie seu arquivo CSV", type=["csv"])

def limpar_id(texto):
    """Remove caracteres especiais como #, espaços e transforma em texto limpo"""
    if pd.isna(texto):
        return ""
    texto_limpo = re.sub(r'[#\s]', '', str(texto))
    return texto_limpo.strip()

if sheets_url and uploaded_csv:
    try:
        if "edit" in sheets_url:
            base_url = sheets_url.split("/edit")[0] + "/export?format=csv"
        else:
            base_url = sheets_url

        # Tenta ler a planilha ignorando a linha de título se existir
        df_temp = pd.read_csv(base_url, nrows=5)
        if any("Solicitação" in str(col) for col in df_temp.columns):
            df_base = pd.read_csv(base_url, skiprows=1)
        else:
            df_base = pd.read_csv(base_url)

        df_csv = pd.read_csv(uploaded_csv)

        st.success("✅ Arquivos carregados com sucesso!")

        st.subheader("2. Mapeamento para o PROCV")
        col1, col2 = st.columns(2)

        with col1:
            key_base = st.selectbox("Coluna Chave no Google Sheets (Selecione 'ID'):", df_base.columns)
        with col2:
            key_csv = st.selectbox("Coluna Chave no CSV:", df_csv.columns)

        if st.button("🚀 Processar Comparação e Validação", type="primary"):
            # Cria colunas de comparação limpas (sem # e sem espaços)
            df_base['_key_clean'] = df_base[key_base].apply(limpar_id)
            df_csv['_key_clean'] = df_csv[key_csv].apply(limpar_id)

            # Executa o PROCV
            resultado = pd.merge(
                df_csv, 
                df_base, 
                on='_key_clean', 
                how="left", 
                suffixes=('_CSV', '_SHEETS')
            )

            # Define status
            resultado["Status_Validacao"] = resultado['_key_clean'].apply(
                lambda x: "🟢 Encontrado" if x in df_base['_key_clean'].values else "🔴 Não Encontrado"
            )

            # Remove a coluna temporária de limpeza da exibição final
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
