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

    for entry in data["results"]:
        provider_name = entry["provider"]
        row = {"Provider": provider_name}

        for field, details in entry["results"].items():
            row[field] = details["message"]  # Extract the message
            row[f"{field}_status"] = details["status"]  # Extract the status for coloring

        provider_data.append(row)

    return pd.DataFrame(provider_data)

# Load Data
json_file = "../results/mini_results_batch.json"  # Update path if needed
data = load_json(json_file)
df = json_to_dataframe(data)

# Function to Apply Cell Colors
def apply_cell_color(val):
    if isinstance(val, str):
        if "Validated" in val:
            return "background-color: #d4edda;"  # Green
        elif "Needs Work" in val:
            return "background-color: #fff3cd;"  # Yellow
        elif "Incorrect" in val:
            return "background-color: #f8d7da;"  # Red
    return ""

# Streamlit App
st.set_page_config(page_title="Healthcare Data Dashboard", layout="wide")
st.title("🏥 Healthcare Data Dashboard")
st.write("This table displays provider data with validation messages. Cells are color-coded based on status.")

# Apply cell coloring
styled_df = df.style.applymap(apply_cell_color, subset=[col for col in df.columns if "_status" in col])

# Display Styled DataFrame
st.dataframe(styled_df)
