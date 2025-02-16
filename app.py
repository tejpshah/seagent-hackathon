from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

import os
import json
import pandas as pd
import streamlit as st
from modules import data_utils, validation

# ------------------- Enterprise Dashboard Styling -------------------
st.set_page_config(page_title="Seagent Healthcare Validation Dashboard", layout="wide")
st.markdown(
    """
    <style>
    .header {
        background-color: #0e2f44;
        padding: 15px;
        border-radius: 5px;
        color: white;
        text-align: center;
    }
    .section-title {
        font-size: 1.5em;
        margin-top: 25px;
        margin-bottom: 10px;
        border-bottom: 2px solid #0e2f44;
        padding-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
st.markdown("<div class='header'><h1>Seagent Healthcare Provider Validation Dashboard</h1></div>", unsafe_allow_html=True)

# ------------------- Ensure Directories -------------------
for folder in ["data/uploads", "results"]:
    os.makedirs(folder, exist_ok=True)

# ------------------- Sidebar Inputs -------------------
st.sidebar.header("Configuration")

# Perplexity API Settings
perplexity_api_url = os.getenv("PERPLEXITY_API_URL")
perplexity_model = os.getenv("PERPLEXITY_MODEL")
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
if not perplexity_api_key:
    st.sidebar.error("PERPLEXITY_API_KEY not found in environment variables.")

# Strategy Selection
strategy = st.sidebar.radio("Validation Strategy", options=["batch", "threaded"], index=0)

# Input Source Selection
input_source = st.sidebar.radio("Input Source", options=["Preloaded CSV", "Upload CSV"], index=0)

if input_source == "Preloaded CSV":
    # List CSV files in the data folder (ignoring subdirectories)
    data_files = [f for f in os.listdir("data") if f.endswith(".csv") and os.path.isfile(os.path.join("data", f))]
    selected_input_file = st.sidebar.selectbox("Select Preloaded CSV", options=data_files)
    if st.sidebar.button("Process Selected CSV"):
        saved_filename = os.path.join("data", selected_input_file)
        st.sidebar.info(f"Processing file: {saved_filename}")
        output_prefix = os.path.splitext(os.path.basename(saved_filename))[0]
        try:
            validation.validate_dataset(
                csv_filepath=saved_filename,
                output_prefix=output_prefix,
                strategy=strategy,
                api_key=perplexity_api_key,
                api_url=perplexity_api_url,
                model=perplexity_model,
            )
            st.sidebar.success("Dataset processed and results saved.")
        except Exception as e:
            st.sidebar.error(f"Error processing dataset: {e}")
elif input_source == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        saved_filename = data_utils.save_uploaded_file(uploaded_file)
        st.sidebar.success(f"File saved: {saved_filename}")
        with st.spinner("Processing dataset..."):
            output_prefix = os.path.splitext(os.path.basename(saved_filename))[0]
            try:
                validation.validate_dataset(
                    csv_filepath=saved_filename,
                    output_prefix=output_prefix,
                    strategy=strategy,
                    api_key=perplexity_api_key,
                    api_url=perplexity_api_url,
                    model=perplexity_model,
                )
                st.sidebar.success("Dataset processed and results saved.")
            except Exception as e:
                st.sidebar.error(f"Error processing dataset: {e}")

# Dataset Selection
st.sidebar.header("Select Processed Dataset")
available_datasets = data_utils.get_available_results()
selected_dataset = st.sidebar.selectbox("Select dataset", options=available_datasets)

# ------------------- Helper Functions -------------------
def compute_counts(results):
    counts = {"Validated": 0, "Needs Work": 0, "Incorrect": 0}
    for field, details in results.items():
        status = details.get("status", "")
        if status in counts:
            counts[status] += 1
    return counts

def compute_global_stats(dataset_json):
    global_counts = {"Validated": 0, "Needs Work": 0, "Incorrect": 0}
    total = 0
    for entry in dataset_json.get("results", []):
        for details in entry.get("results", {}).values():
            status = details.get("status", "")
            if status in global_counts:
                global_counts[status] += 1
            total += 1
    percentages = {k: round((v / total) * 100, 2) if total > 0 else 0 for k, v in global_counts.items()}
    return global_counts, percentages

# Exclude unwanted columns by default.
columns_to_exclude = {"Probability of validated", "Source", "Validated?"}

# ------------------- Main Dashboard -------------------
if selected_dataset:
    json_path = os.path.join("results", f"{selected_dataset}_results.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            dataset_json = json.load(f)
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        dataset_json = None

    if dataset_json:
        # ================= Global Statistics =================
        st.markdown("<div class='section-title'>Global Statistics</div>", unsafe_allow_html=True)
        global_counts, global_percentages = compute_global_stats(dataset_json)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Validated", f"{global_counts['Validated']} ({global_percentages['Validated']}%)")
        col2.metric("Total Needs Work", f"{global_counts['Needs Work']} ({global_percentages['Needs Work']}%)")
        col3.metric("Total Incorrect", f"{global_counts['Incorrect']} ({global_percentages['Incorrect']}%)")
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # ================= Data Tables: Original CSV & Detailed Validation =================
        st.markdown("<div class='section-title'>Data Tables</div>", unsafe_allow_html=True)
        
        # Load processed CSV from results; if not found, generate CSV from JSON "original" fields (in memory)
        csv_path = os.path.join("results", f"{selected_dataset}_results.csv")
        if os.path.exists(csv_path):
            try:
                df_original = pd.read_csv(csv_path)
            except Exception as e:
                st.error(f"Error loading original CSV: {e}")
                df_original = pd.DataFrame()
        else:
            # Generate from JSON "original" fields.
            rows = [entry.get("original") for entry in dataset_json.get("results", []) if entry.get("original")]
            if rows:
                df_original = pd.DataFrame(rows)
            else:
                fallback_path = os.path.join("data", "seagent_healthcare_data.csv")
                if os.path.exists(fallback_path):
                    df_original = pd.read_csv(fallback_path)
                else:
                    df_original = pd.DataFrame()
        
        # Build union of columns from CSV and JSON details, excluding unwanted columns.
        orig_cols = set(df_original.columns) if not df_original.empty else set()
        detail_cols = set()
        for entry in dataset_json.get("results", []):
            detail_cols.update(entry.get("results", {}).keys())
        common_cols = sorted((orig_cols.union(detail_cols)) - columns_to_exclude)
        selected_columns = st.multiselect("Select columns for display", options=common_cols, default=list(common_cols))
        
        # (a) Original CSV (Color-Coded)
        st.markdown("**Original CSV (Color-Coded)**")
        validation_mapping = {entry["provider"]: entry.get("results", {}) for entry in dataset_json.get("results", [])}
        def style_row(row):
            provider = row.get("Provider Name", "")
            styles = []
            for col in row.index:
                if provider in validation_mapping and col in validation_mapping[provider]:
                    status = validation_mapping[provider][col].get("status", "")
                    if status == "Validated":
                        styles.append("background-color: #d4edda")
                    elif status == "Needs Work":
                        styles.append("background-color: #fff3cd")
                    elif status == "Incorrect":
                        styles.append("background-color: #f8d7da")
                    else:
                        styles.append("")
                else:
                    styles.append("")
            return styles
        if not df_original.empty:
            styled_df = df_original[list(selected_columns)].style.apply(style_row, axis=1)
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.write("No original CSV data available.")
        
        # (b) Detailed Validation Table
        st.markdown("**Detailed Validation Table**")
        detailed_rows = []
        for entry in dataset_json.get("results", []):
            row = {"Provider": entry.get("provider", "Unknown Provider")}
            for field, details in entry.get("results", {}).items():
                if field in selected_columns:
                    status = details.get("status", "")
                    if status == "Validated":
                        display = "✅ Validated"
                    elif status == "Needs Work":
                        display = "⚠️ Needs Work"
                    elif status == "Incorrect":
                        display = "❌ Incorrect"
                    else:
                        display = status
                    row[field] = f"{display}\n{details.get('message', '')}"
            detailed_rows.append(row)
        if detailed_rows:
            df_details = pd.DataFrame(detailed_rows)
            common_detail_cols = [col for col in selected_columns if col in df_details.columns]
            st.dataframe(df_details[common_detail_cols], use_container_width=True)
        else:
            st.write("No detailed validation data available.")
        
        # ================= Provider Summary (with Duplicate Info) =================
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Provider Summary</div>", unsafe_allow_html=True)
        summary_data = []
        for entry in dataset_json.get("results", []):
            provider = entry.get("provider", "Unknown Provider")
            results = entry.get("results", {})
            counts = entry.get("counts")
            if not counts:
                counts = compute_counts(results)
            if counts.get("Incorrect", 0) == 0:
                overall = "✅ Fully Correct"
            elif counts.get("Incorrect", 0) < 3:
                overall = "⚠️ Some Issues"
            else:
                overall = "❌ Multiple Issues"
            summary_data.append({
                "Provider": provider,
                "Overall": overall,
                "Validated": counts.get("Validated", 0),
                "Needs Work": counts.get("Needs Work", 0),
                "Incorrect": counts.get("Incorrect", 0)
            })
        if summary_data:
            df_summary = pd.DataFrame(summary_data)
            def style_summary(row):
                overall = row["Overall"]
                if "✅" in overall:
                    color = "#d4edda"
                elif "⚠️" in overall:
                    color = "#fff3cd"
                else:
                    color = "#f8d7da"
                return ["background-color: " + color] * len(row)
            styled_summary = df_summary.style.apply(style_summary, axis=1)
            st.dataframe(styled_summary, use_container_width=True)
            
            # Show duplicate provider names in a 3-column grid, below summary.
            if "Provider" in df_summary.columns:
                dupes = df_original[df_original.duplicated(subset=["Provider Name"], keep=False)]
                if not dupes.empty:
                    dup_names = list(dupes["Provider Name"].unique())
                    st.markdown("**Duplicate Provider Names:**")
                    for i in range(0, len(dup_names), 3):
                        cols = st.columns(3)
                        for j, col in enumerate(cols):
                            if i + j < len(dup_names):
                                col.write(dup_names[i + j])
        else:
            st.write("No summary statistics available.")
        
    # ================= Per-Firm Detailed Report (Single Column Expanders) =================
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Per-Firm Detailed Report</div>", unsafe_allow_html=True)
    provider_entries = dataset_json.get("results", [])
    for idx, entry in enumerate(provider_entries):
        provider = entry.get("provider", "Unknown Provider")
        results = entry.get("results", {})
        counts = entry.get("counts")
        if not counts:
            counts = compute_counts(results)
        incorrect_count = counts.get("Incorrect", 0)
        if incorrect_count == 0:
            overall_color = "#d4edda"
            overall_rating = "Fully Correct"
        elif incorrect_count < 3:
            overall_color = "#fff3cd"
            overall_rating = "Some Issues"
        else:
            overall_color = "#f8d7da"
            overall_rating = "Multiple Issues"
        # Each firm is shown in an expander with a header that includes the firm name and rating.
        with st.expander(f"Firm: {provider}  [{overall_rating}]", expanded=False):
            st.markdown(
                f"<div style='background-color:{overall_color}; padding:10px; border-radius:5px;'>"
                f"<h3 style='margin:0; color:#333;'>{provider}</h3></div>",
                unsafe_allow_html=True
            )
            # Show each field's details in a styled block.
            for field, details in results.items():
                block_md = "<div style='border:1px solid #ddd; padding:8px; margin:4px 0; border-radius:5px;'>"
                block_md += f"<strong>Field:</strong> {field}<br>"
                block_md += f"<strong>Status:</strong> {details.get('status', '')}<br>"
                block_md += f"<strong>Message:</strong> {details.get('message', '')}<br>"
                sources = details.get("source", [])
                if sources:
                    block_md += "<strong>Sources:</strong><br>"
                    for src in sources:
                        block_md += f"- <a href='{src}' target='_blank'>{src}</a><br>"
                block_md += "</div>"
                st.markdown(block_md, unsafe_allow_html=True)
            # Build the report content for download.
            report_content = f"Report for {provider}\n\nOverall Rating: {overall_rating}\n\n"
            for field, details in results.items():
                report_content += f"Field: {field}\n"
                report_content += f"Status: {details.get('status', '')}\n"
                report_content += f"Message: {details.get('message', '')}\n"
                if details.get("source"):
                    report_content += "Sources:\n"
                    for src in details["source"]:
                        report_content += f" - {src}\n"
                report_content += "\n"
            st.download_button(
                label="Download Report",
                data=report_content,
                file_name=f"{provider}_report.txt",
                mime="text/plain",
                key=f"download_{provider}_{idx}"
            )
