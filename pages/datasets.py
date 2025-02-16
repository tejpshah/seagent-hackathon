import os
import json
import streamlit as st

st.title("Datasets Browser")

results_dir = "results"
if not os.path.exists(results_dir):
    st.write("No results available yet.")
else:
    files = [f for f in os.listdir(results_dir) if f.endswith("_results.json")]
    if not files:
        st.write("No processed datasets found.")
    else:
        selected_file = st.selectbox("Select a results file", files)
        file_path = os.path.join(results_dir, selected_file)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        st.json(data)
