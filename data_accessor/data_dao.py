

import pandas as pd

import os

# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory where the script is located
file_path = os.path.join(script_dir, "../data/seagent_healthcare_data.csv")

df = pd.read_csv("/Users/jayko/Documents/SeaAiHack/seagent-hackathon/data/seagent_healtchare_data.csv")

# Function to get all column names
def get_all_columns(df):
    if df is None or df.empty:
        return "DataFrame is empty or does not exist"
    return df.columns.to_list()

# Writing DataFrame to a new CSV file
def write_to_new_file(df, filename="output.csv"):
    df.to_csv(filename, index=False)
    print(f"Data written to {filename}")

# Adding a new column to DataFrame
def add_new_column(df, column_name, default_value=None):
    df[column_name] = default_value
    print(f"Column '{column_name}' added with default value: {default_value}")


# Example usage
print("Columns:", get_all_columns(df))