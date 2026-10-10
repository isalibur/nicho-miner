import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Minerador de Nichos", layout="wide")

st.title("Minerador de Nichos para YouTube")

API_TOKEN = st.sidebar.text_input("API Token", type="password", value="dev-token-12345")

top_n = st.sidebar.slider("Quantidade de resultados", 5, 100, 20)

tab1, tab2, tab3 = st.tabs(["Keywords", "Anomalias", "Nichos"])

with tab1:
    st.header("Palavras-chave Extraídas")
    if st.button("Buscar Keywords"):
        try:
            headers = {"Authorization": f"Bearer {API_TOKEN}"}
            response = requests.get("http://localhost:8000/keywords", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                if not df.empty:
                    df = df.head(top_n)
                    st.dataframe(df, use_container_width=True)
                    st.download_button("Exportar CSV", df.to_csv(index=False), file_name="keywords.csv", mime="text/csv")
                else:
                    st.warning("Nenhuma keyword encontrada.")
            else:
                st.error(f"Erro na API: {response.status_code}")
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")

with tab2:
    st.header("Anomalias Detectadas")
    if st.button("Buscar Anomalias"):
        try:
            headers = {"Authorization": f"Bearer {API_TOKEN}"}
            response = requests.get("http://localhost:8000/anomalies", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    st.download_button("Exportar CSV", df.to_csv(index=False), file_name="anomalies.csv", mime="text/csv")
                else:
                    st.warning("Nenhuma anomalia encontrada.")
            else:
                st.error(f"Erro na API: {response.status_code}")
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")

with tab3:
    st.header("Nichos Identificados")
    if st.button("Buscar Nichos"):
        try:
            headers = {"Authorization": f"Bearer {API_TOKEN}"}
            response = requests.get("http://localhost:8000/niches", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    st.download_button("Exportar CSV", df.to_csv(index=False), file_name="niches.csv", mime="text/csv")
                else:
                    st.warning("Nenhum nicho encontrado.")
            else:
                st.error(f"Erro na API: {response.status_code}")
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")
