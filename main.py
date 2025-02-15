import os
import logging
import yaml
import argparse
import json
import csv
from dotenv import load_dotenv
from utils.perplexity_client import PerplexityClient
from strategies import strategy_batch, strategy_threaded

def setup_logging(level):
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    # Load environment variables from .env
    load_dotenv()
    
    # Parse command line arguments (including config file and strategy)
    parser = argparse.ArgumentParser(description="Healthcare Provider Validation")
    parser.add_argument(
        "--config",
        type=str,
        default="config_batch.yaml",
        help="Path to the YAML configuration file."
    )
    parser.add_argument(
        "--strategy",
        choices=["batch", "threaded"],
        help="Validation strategy: 'batch' (one API call for all fields) or 'threaded' (one call per field)."
    )
    args = parser.parse_args()
    
    # Load configuration from the specified config file
    config = load_config(args.config)
    
    # Set up logging based on config
    log_level = config.get("logging", {}).get("level", "INFO")
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    # Get Perplexity API key from environment
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        logger.error("PERPLEXITY_API_KEY not found in environment variables.")
        return
    
    # Create a PerplexityClient instance
    api_url = config.get("perplexity_api_url")
    model = config.get("perplexity_model")
    client = PerplexityClient(api_key, api_url, model)
    
    # Determine the validation strategy:
    strategy = args.strategy if args.strategy else config.get("default_strategy", "batch")
    
    # Get data file paths from config
    input_csv = config.get("data", {}).get("input_csv", "data/seagent_healthcare_data.csv")
    output_csv = config.get("data", {}).get("output_csv_csv", "results/results.csv")
    output_json = config.get("data", {}).get("output_csv_json", "results/results.json")
    
    # Optionally, get a list of fields to skip (like the "Provider Name")
    fields_to_skip = config.get("validation", {}).get("fields_to_skip", ["Provider Name"])
    
    # Ensure the results folder exists.
    results_folder = os.path.dirname(output_csv)
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    
    # Prepare to accumulate results for CSV and JSON output.
    results_rows = []
    all_results = []
    status_counts = {"Validated": 0, "Needs Work": 0, "Incorrect": 0}
    total_fields = 0
    
    # Check if the input CSV file exists
    if not os.path.exists(input_csv):
        logger.error("Data file '%s' not found.", input_csv)
        return
    
    with open(input_csv, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Use the "Provider Name" as the key (if present)
            provider = row.get("Provider Name", "Unknown Provider").strip()
            # Validate every field except the ones to skip.
            fields = { key: value.strip() for key, value in row.items() if key not in fields_to_skip }
            
            logger.info("Validating provider: %s", provider)
            
            # Choose the strategy
            if strategy == "batch":
                result = strategy_batch.validate_provider_batch(provider, fields, client)
            else:
                result = strategy_threaded.validate_provider_threaded(provider, fields, client)
            
            # Print the structured JSON output for the provider.
            print(json.dumps(result, indent=2))
            
            all_results.append(result)
            
            # Process each field's result and count statuses.
            provider_name = result.get("provider", provider)
            for field, outcome in result.get("results", {}).items():
                results_rows.append({
                    "Provider Name": provider_name,
                    "Field": field,
                    "Status": outcome.get("status", ""),
                    "Message": outcome.get("message", ""),
                    "Source": "; ".join(outcome.get("source", []))
                })
                total_fields += 1
                status = outcome.get("status", "")
                if status in status_counts:
                    status_counts[status] += 1
    
    # Compute statistics (percentages)
    statistics = {}
    if total_fields > 0:
        for key, count in status_counts.items():
            statistics[key] = round((count / total_fields) * 100, 2)
    
    # Prepare final JSON object including statistics.
    final_json = {
        "statistics": statistics,
        "results": all_results
    }
    
    # Write the aggregated results to the output CSV file.
    with open(output_csv, "w", newline="", encoding="utf-8") as outfile:
        fieldnames = ["Provider Name", "Field", "Status", "Message", "Source"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_rows)
    
    # Write the full JSON results including statistics.
    with open(output_json, "w", encoding="utf-8") as jfile:
        json.dump(final_json, jfile, indent=2)
    
    logger.info("Validation complete. Results saved to %s and %s", output_csv, output_json)

if __name__ == "__main__":
    main()
