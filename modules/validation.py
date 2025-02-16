import os
import pandas as pd
import json
import logging
from modules import strategies
from utils.perplexity_client import PerplexityClient

logger = logging.getLogger(__name__)

def validate_dataset(csv_filepath, output_prefix, strategy="batch", api_key=None, api_url=None, model=None, fields_to_validate=None):
    """
    Reads a CSV file, validates each provider using the Perplexity API
    (with the chosen strategy), computes statistics, and saves the results
    as both JSON and CSV files in the 'results' folder.
    
    If `fields_to_validate` is provided (as a list of column names), only those fields are validated.
    
    Each provider's result includes:
      - "counts": Raw counts for each validation type.
      - "statistics": Percentage breakdown of validation statuses.
    """
    if not api_key or not api_url or not model:
        raise ValueError("Perplexity API credentials and settings must be provided.")
    
    client = PerplexityClient(api_key=api_key, api_url=api_url, model=model)
    
    df = pd.read_csv(csv_filepath)
    results_list = []
    
    for idx, row in df.iterrows():
        provider = row.get("Provider Name", "Unknown Provider")
        skip_fields = ["Provider Name", "Validated?", "Probability of validated", "Source"]
        # Only validate fields not in skip_fields and if fields_to_validate is set, only those fields.
        fields = {
            col: str(row[col]).strip() 
            for col in df.columns 
            if col not in skip_fields and (fields_to_validate is None or col in fields_to_validate)
        }
        
        logger.info("Validating provider: %s", provider)
        if strategy == "batch":
            try:
                result = strategies.validate_provider_batch(provider, fields, client)
            except Exception as e:
                logger.error("Error in batch validation for provider %s: %s", provider, e)
                result = {"provider": provider, "results": {}}
        else:
            try:
                result = strategies.validate_provider_threaded(provider, fields, client)
            except Exception as e:
                logger.error("Error in threaded validation for provider %s: %s", provider, e)
                result = {"provider": provider, "results": {}}
        
        provider_results = result.get("results", {})
        counts = {"Validated": 0, "Needs Work": 0, "Incorrect": 0}
        total_fields = 0
        for outcome in provider_results.values():
            status = outcome.get("status", "")
            if status in counts:
                counts[status] += 1
            total_fields += 1
        statistics = {k: round((v / total_fields) * 100, 2) if total_fields > 0 else 0 for k, v in counts.items()}
        
        result["counts"] = counts
        result["statistics"] = statistics
        results_list.append(result)
    
    # Global statistics (if needed)
    global_counts = {"Validated": 0, "Needs Work": 0, "Incorrect": 0}
    total_global = 0
    for entry in results_list:
        for outcome in entry.get("results", {}).values():
            status = outcome.get("status", "")
            if status in global_counts:
                global_counts[status] += 1
            total_global += 1
    global_statistics = {k: round((v / total_global) * 100, 2) if total_global > 0 else 0 for k, v in global_counts.items()}
    
    final_json = {"global_statistics": global_statistics, "results": results_list}
    
    os.makedirs("results", exist_ok=True)
    json_path = os.path.join("results", f"{output_prefix}_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=2)
    
    # Save a copy of the original CSV (for joining on the validation)
    csv_path = os.path.join("results", f"{output_prefix}_results.csv")
    df.to_csv(csv_path, index=False)
    
    return final_json
