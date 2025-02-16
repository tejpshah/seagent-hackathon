import streamlit as st
import pandas as pd
import yaml
import subprocess
import os 
import json

UPLOAD_DIR = "uploaded_csv"
RESULTS_DIR = "results"
YAML_DIR = "yaml_configs"


# Directory settings
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure upload directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)  # Ensure results directory exists
os.makedirs(YAML_DIR, exist_ok=True)  # Ensure directory exists

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

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


def run_command(command):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
    else:
        print("Command completed successfully.\n")

def generate_yaml(file_name, user_id, validation_cols_to_skip, compute_mode):
    """Generate a YAML configuration file based on user selections."""
    # Create user-specific results directory
    user_results_dir = os.path.join(YAML_DIR, user_id)
    os.makedirs(user_results_dir, exist_ok=True)  # Ensure the user directory exist
    
    config = {
        "default_strategy": compute_mode,  # Default validation strategy
        "perplexity_api_url": "https://api.perplexity.ai/chat/completions",
        "perplexity_model": "sonar-pro",
        "data": {
            "input_csv": os.path.join(UPLOAD_DIR, f"{user_id}",file_name),
            "output_csv_csv": os.path.join(RESULTS_DIR, f"{user_id}",f"{file_name}_results_{compute_mode}.csv"),
            "output_csv_json": os.path.join(RESULTS_DIR, f"{user_id}",f"{file_name}_results_{compute_mode}.json")
        },
        "validation": {
            "fields_to_skip": validation_cols_to_skip
        },
        "logging": {
            "level": "DEBUG" if compute_mode == "High Compute" else "INFO"
        }
    }

    # Save YAML file
    yaml_path = os.path.join(user_results_dir, f"{file_name}.yaml")

    with open(yaml_path, "w") as file:
        yaml.dump(config, file, default_flow_style=False)

    return yaml_path, config

def initialize_session_state():
    """Initialize session state variables if they are not set."""
    if "uploaded_data" not in st.session_state:
        st.session_state["uploaded_data"] = None
    if "selected_columns" not in st.session_state:
        st.session_state["selected_columns"] = []
    if "compute_mode" not in st.session_state:
        st.session_state["compute_mode"] = "Low Compute"
    if "file_uploaded" not in st.session_state:
        st.session_state["file_uploaded"] = False

def save_uploaded_file(df, file_name, user_id):
    """Save uploaded CSV file to user-specific directory."""

    # Create user-specific directory in uploaded_csv/
    user_upload_dir = os.path.join(UPLOAD_DIR, user_id)
    os.makedirs(user_upload_dir, exist_ok=True)  # Ensure directory exists

    # Save uploaded CSV to user-specific folder
    file_path = os.path.join(user_upload_dir, file_name)
    df.to_csv(file_path, index=False)

    return file_path


# Load JSON Data
def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

def main():

    st.title("🚀 Launch Page - CSV Uploader")
    st.write("Upload a CSV file to get started.")

    initialize_session_state()

    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    # input user id 
    user_id = str(st.text_input("Enter your User ID:", key="user_id"))

    if uploaded_file is not None:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        # Display the data preview
        st.write("### Preview of Uploaded File:")
        st.dataframe(df.head())

       # Upload File Button
        if st.button("Upload File"):
            file_path  = save_uploaded_file(df, uploaded_file.name, user_id)
            st.session_state["file_path"] = file_path
            st.session_state["file_uploaded"] = True
            st.success(f"File saved at `{file_path}`")

        # Show additional options only after file is uploaded
    if st.session_state["file_uploaded"]:
        # Column selection
        st.write("### Select columns to skip validation:")
        selected_columns = st.multiselect(
            "Choose columns",
            options=df.columns.tolist(),
            help="Select the columns you want to skip validation"
        )

        
        # Store selected columns in session state
        if selected_columns:
            st.session_state["selected_columns"] = selected_columns

            # Display selected columns
            st.write(f"**You selected:** {', '.join(selected_columns)}")

        print(st.session_state["selected_columns"])
        
        # Compute Mode Selection
        st.write("### Select Compute Mode:")
        compute_mode = st.radio(
            "Choose compute mode",
            options=["Low Compute", "High Compute"],
            index=0 if st.session_state["compute_mode"] == "Low Compute" else 1,
            help="Low Compute is optimized for speed, High Compute runs more intensive operations."
        )

        # Store compute mode in session state
        st.session_state["compute_mode"] = compute_mode
        st.write(f"**Selected Compute Mode:** {compute_mode}")

        # need to define configuration for the payload function call

        # Proceed button
        if st.button("Run Check"):
            st.session_state["uploaded_data"] = df
            compute_mode = st.session_state["compute_mode"]

            # Determine strategy and YAML configuration based on compute mode
            strategy = "batch" if compute_mode == "Low Compute" else "threaded"
            yaml_path, config = generate_yaml(uploaded_file.name, user_id, st.session_state["selected_columns"], strategy)

            print(yaml_path)
            print(config)

            # Display status messages
            st.success(f"Proceeding with {compute_mode} mode. This may take longer." if compute_mode == "High Compute"
                    else "Proceeding with Low Compute mode.")

             # Construct and execute the command
            command = f"python main.py --config {yaml_path} --strategy {strategy}"
            run_command(command)
            
            # Load JSON results if available
            if os.path.exists(config["data"]["output_csv_json"]):
                st.session_state["json_results"] = config["data"]["output_csv_json"]


    
         # JSON Validation Section
    if st.session_state.get("json_results"):
        json_path = st.session_state["json_results"]
        data_res = load_json(json_path)
        df, df_val = json_to_dataframe(data_res)

        data_source = pd.read_csv(config["data"]["input_csv"])

        # Display Validation Results
        st.write("### External Validation Results")

        # Apply validation coloring
        # Display Source Data with Validation Coloring
        st.write("### Source Data (with validation coloring)")
        styled_df = data_source.style.apply(apply_cell_colors, validation=df_val, axis=None)
        st.dataframe(styled_df)


        # Display External Validation Results (Res)
        st.write("### External Validation Results")
        st.dataframe(df)

if __name__ == "__main__":
    main()
