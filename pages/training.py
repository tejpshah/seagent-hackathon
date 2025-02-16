from dotenv import load_dotenv
load_dotenv()  # Load environment variables

import os
import streamlit as st
import pandas as pd
from modules import validation, data_utils

st.title("Training / Running Mode")
st.write("Configure your training run below. By default, all fields are validated; you can restrict this to specific fields.")

# Upload CSV for training
uploaded_file = st.file_uploader("Upload CSV for Training", type=["csv"])

if uploaded_file is not None:
    # Save the uploaded file
    saved_file = data_utils.save_uploaded_file(uploaded_file)
    st.success(f"Training CSV saved: {saved_file}")
    
    # Read CSV headers to allow field selection
    try:
        df_train = pd.read_csv(saved_file)
        # Exclude unwanted columns
        all_fields = [col for col in df_train.columns if col not in ["Provider Name", "Validated?", "Probability of validated", "Source"]]
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        all_fields = []
    
    st.markdown("### Configure Fields for Training")
    # Multiselect with drag-and-drop (if available) – default all fields.
    fields_to_train = st.multiselect("Select fields to validate:", options=all_fields, default=all_fields)
    
    st.markdown("### Compute Mode")
    compute_mode = st.radio("Select compute mode:", options=["Low Compute (Batch)", "High Compute (Threaded)"], index=0)
    selected_strategy = "batch" if "Low" in compute_mode else "threaded"
    
    if st.button("Start Training Run"):
        # Get API settings solely from environment variables.
        api_key = os.getenv("PERPLEXITY_API_KEY")
        api_url = os.getenv("PERPLEXITY_API_URL")
        model = os.getenv("PERPLEXITY_MODEL")
        if not api_key or not api_url or not model:
            st.error("Perplexity API credentials and settings must be provided.")
        else:
            progress_text = st.empty()
            progress_bar = st.progress(0)
            try:
                progress_text.text("Step 1: Reading CSV...")
                df = pd.read_csv(saved_file)
                progress_bar.progress(20)
                
                progress_text.text("Step 2: Configuring training parameters...")
                # (Fields to validate have already been chosen by the user.)
                progress_bar.progress(40)
                
                progress_text.text(f"Step 3: Running validation using '{selected_strategy}' strategy...")
                # Run the training/validation run.
                output_prefix = "training_run"
                validation.validate_dataset(
                    csv_filepath=saved_file,
                    output_prefix=output_prefix,
                    strategy=selected_strategy,
                    api_key=api_key,
                    api_url=api_url,
                    model=model,
                    fields_to_validate=fields_to_train,
                )
                progress_bar.progress(80)
                
                progress_text.text("Step 4: Finalizing training run...")
                # (Optional: any post-run processing can be added here.)
                progress_bar.progress(100)
                
                st.success("Training run completed and results saved.")
                progress_text.text("Training run completed.")
            except Exception as e:
                st.error(f"Error during training run: {e}")
                progress_text.text("Training run failed.")
