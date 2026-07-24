import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Validador & PROCV Automático", page_icon="📊", layout="wide")

st.title("📊 Validador e Comparador de Planilhas (PROCV)")
st.write("Conecte a planilha base e envie o arquivo CSV para comparar e validar os dados automaticamente.")

# --- SEÇÃO DE ENTRADA DE DADOS ---
st.sidebar.header("1. Configuração das Fontes")

# 1. Google Sheets (ou Excel)
st.sidebar.subheader("Planilha Base (Google Sheets)")
sheets_url = st.sidebar.text_input("Cole o Link Público do Google Sheets:")

# 2. Upload do CSV
st.sidebar.subheader("Planilha para Comparar (CSV)")
uploaded_csv = st.sidebar.file_uploader("Envie seu arquivo CSV", type=["csv"])

# --- PROCESSAMENTO ---
if sheets_url and uploaded_csv:
    try:
        # Converter URL do Google Sheets para exportação direta em CSV
        if "edit" in sheets_url:
            base_url = sheets_url.split("/edit")[0] + "/export?format=csv"
        else:
            base_url = sheets_url

        # Carregar os dados
        df_base = pd.read_csv(base_url)
        df_csv = pd.read_csv(uploaded_csv)

        st.success("✅ Arquivos carregados com sucesso!")

        # --- SELEÇÃO DE COLUNAS ---
        st.subheader("2. Mapeamento para o PROCV")
        col1, col2 = st.columns(2)

        with col1:
            key_base = st.selectbox("Coluna Chave no Google Sheets (ex: ID, CPF):", df_base.columns)
        with col2:
            key_csv = st.selectbox("Coluna Chave no CSV:", df_csv.columns)

        if st.button("🚀 Processar Comparação e Validação", type="primary"):
            # Garantir que as chaves sejam tratadas como texto para evitar erros
            df_base[key_base] = df_base[key_base].astype(str).str.strip()
            df_csv[key_csv] = df_csv[key_csv].astype(str).str.strip()

            # Executar o PROCV (Left Join)
            resultado = pd.merge(
                df_csv, 
                df_base, 
                left_on=key_csv, 
                right_on=key_base, 
                how="left", 
                suffixes=('_CSV', '_SHEETS')
            )

            # Adicionar Validador
            resultado["Status_Validacao"] = resultado[key_base].apply(
                lambda x: "🟢 Encontrado" if pd.notnull(x) else "🔴 Não Encontrado"
            )

            # --- RESULTADOS ---
            st.divider()
            st.subheader("3. Resultado da Comparação")

            # Métrica rápida
            total = len(resultado)
            encontrados = (resultado["Status_Validacao"] == "🟢 Encontrado").sum()
            nao_encontrados = total - encontrados

            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Registros (CSV)", total)
            m2.metric("🟢 Encontrados na Base", encontrados)
            m3.metric("🔴 Não Encontrados", nao_encontrados)

            # Tabela de resultados
            st.dataframe(resultado, use_container_width=True)

            # Botão para Baixar
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
    st.info("👈 Por favor, insira o link do Google Sheets e faça o upload do CSV na barra lateral para começar.")