import streamlit as st
import pandas as pd
import yaml
import subprocess
import os 

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
            "input_csv": os.path.join(UPLOAD_DIR, file_name),
            "output_csv_csv": os.path.join(RESULTS_DIR, f"{user_id}",f"{file_name}_results_batch.csv"),
            "output_csv_json": os.path.join(RESULTS_DIR, f"{user_id}",f"{file_name}_results_batch.json")
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

    return yaml_path


def main():

    st.title("🚀 Launch Page - CSV Uploader")
    st.write("Upload a CSV file to get started.")

     # Initialize session state if not set
    if "uploaded_data" not in st.session_state:
        st.session_state["uploaded_data"] = None
    if "selected_columns" not in st.session_state:
        st.session_state["selected_columns"] = []
    if "compute_mode" not in st.session_state:
        st.session_state["compute_mode"] = "Low Compute"  # Default to Low Compute

    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    # input user id 
    user_id = str(st.text_input("Enter your User ID:", key="user_id"))

    if uploaded_file is not None:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        #save file to user specific directory
        file_name = uploaded_file.name  # Get original file name

        # Create user-specific directory in uploaded_csv/
        user_upload_dir = os.path.join(UPLOAD_DIR, user_id)
        os.makedirs(user_upload_dir, exist_ok=True)  # Ensure directory exists

        # Save uploaded CSV to user-specific folder
        file_path = os.path.join(user_upload_dir, file_name)
        df.to_csv(file_path, index=False)


        # Display the data preview
        st.write("### Preview of Uploaded File:")
        st.dataframe(df.head())

       

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


            if st.session_state["compute_mode"] == "Low Compute":
                st.success("Proceeding with Low Compute mode.")
                # Load configuration from the specified config file
                yaml_path  = generate_yaml(uploaded_file.name, user_id, st.session_state["selected_columns"], "batch")
                command  = "python main.py --config " + yaml_path + " --strategy batch"
                 # Run batch workload using the batch config file
                run_command(command)
                print(yaml_path)
            else:
                st.warning("Proceeding with High Compute mode. This may take longer.")
                yaml_path = generate_yaml(uploaded_file.name, user_id, st.session_state["selected_columns"], "batch")
                print(yaml_path)
            st.success("Data uploaded successfully! Proceed to the next step.")

if __name__ == "__main__":
    main()
