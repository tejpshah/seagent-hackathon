import os

def save_uploaded_file(uploaded_file):
    """
    Save the uploaded CSV file to the data/uploads folder.
    """
    uploads_dir = os.path.join("data", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def get_available_results():
    """
    List all processed result files (prefixes) in the results directory.
    Files should be named in the pattern <prefix>_results.json.
    """
    results_dir = "results"
    files = []
    if not os.path.exists(results_dir):
        return files
    for file in os.listdir(results_dir):
        if file.endswith("_results.json"):
            prefix = file.replace("_results.json", "")
            files.append(prefix)
    return sorted(files)
