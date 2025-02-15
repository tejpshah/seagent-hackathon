import streamlit as st
import json
import pandas as pd

# Load JSON Data
def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

# Convert JSON to DataFrame with Status Columns
def json_to_dataframe(data):
    provider_data = []
    val_data = []
    for entry in data["results"]:
        provider_name = entry["provider"]
        row = {"Provider": provider_name}
        row_val = {"Provider": provider_name}

        for field, details in entry["results"].items():
            row[field] = details["message"]  # Extract the message
            row_val[field] = details["status"]  # Extract the status for coloring

        provider_data.append(row)
        val_data.append(row_val)

    return pd.DataFrame(provider_data), pd.DataFrame(val_data)
    
# Load Res Data
json_file = "../results/mini_results_batch.json"  # Update path if needed
data_res = load_json(json_file)

#Load source data
json_source_file = "../data/seagent_data_mini.csv"  # Update path if needed
data_source = pd.read_csv(json_source_file)

df, df_val = json_to_dataframe(data_res)

# Function to Apply Cell Colors Based on Validation
def apply_cell_colors(data, validation):
    styles = pd.DataFrame("", index=data.index, columns=data.columns)
    for col in data.columns:
        if col in validation.columns:
            styles[col] = validation[col].map(lambda status: 
                #"background-color: #d4edda;" if status == "Validated" else
                "background-color: #fff3cd;" if status == "Needs Work" else
                "background-color: #f8d7da;" if status == "Incorrect" else ""
            )
    return styles

# Streamlit App
st.set_page_config(page_title="Healthcare Data Dashboard", layout="wide")
st.title("🏥 Healthcare Data Dashboard")

# Display Source Data with Validation Coloring
st.write("### Source Data (with validation coloring)")
styled_df = data_source.style.apply(apply_cell_colors, validation=df_val, axis=None)
st.dataframe(styled_df)

# Display External Validation Results (Res)
st.write("### External Validation Results")
st.dataframe(df)