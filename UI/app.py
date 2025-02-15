import streamlit as st
import json
import pandas as pd


# Open and load the JSON file
with open("../results/mini_results_batch.json", "r") as file:
    data = json.load(file)
    
# Streamlit UI
st.set_page_config(page_title="Healthcare Provider Dashboard", layout="wide")
st.title("🏥 Healthcare Provider Validation Dashboard")

# Sidebar
st.sidebar.header("Filters")
selected_provider = st.sidebar.selectbox("Select Provider", [item["provider"] for item in data])

# Get selected provider data
provider_data = next(item for item in data if item["provider"] == selected_provider)
st.subheader(f"📍 {provider_data['provider']}")

# Convert data to DataFrame for better display
records = []
for field, details in provider_data["results"].items():
    records.append([field, details["status"], details["message"], details["source"][0]])

df = pd.DataFrame(records, columns=["Field", "Status", "Message", "Source"])

# Color coding status
def highlight_status(row):
    color = "lightgreen" if row.Status == "Validated" else "salmon"
    return [f"background-color: {color}"] * len(row)

st.dataframe(df.style.apply(highlight_status, axis=1), use_container_width=True)

# Show details
for _, row in df.iterrows():
    with st.expander(f"🔹 {row['Field']}"):
        st.write(f"**Status:** {row['Status']}")
        st.write(f"**Message:** {row['Message']}")
        st.markdown(f"[🔗 Source]({row['Source']})")

st.success("✅ Data processing complete!")
