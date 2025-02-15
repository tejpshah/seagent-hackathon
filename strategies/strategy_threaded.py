import json
import logging
import threading
from models import FieldResult, ProviderValidation

logger = logging.getLogger(__name__)

def validate_provider_threaded(provider: str, fields: dict, client) -> dict:
    """
    Validate each field in its own thread.
    Returns a JSON object with each field having:
      - status: "Validated", "Needs Work", or "Incorrect"
      - message: supplementary guidance
      - source: list of URL strings from Perplexity response
    """
    results = {}
    threads = []
    lock = threading.Lock()
    
    def validate_field(field, value):
        prompt = (
            f"Validate the following detail for provider '{provider}':\n"
            f"{field}: {value}\n\n"
            "Determine if the provided value is:\n"
            "  - Validated (if it is correct),\n"
            "  - Needs Work (if it appears outdated or partially correct), or\n"
            "  - Incorrect (if it is wrong).\n\n"
            "Also, provide a short supplementary message and include the relevant source URL(s) from which the information was obtained.\n\n"
            "Output a JSON object with the following format:\n"
            '{"status": "<Validated|Needs Work|Incorrect>", "message": "<supplementary guidance>", "source": ["<url1>", "<url2>", ...]}\n'
            "Only output the JSON object."
        )
        # Use the FieldResult model JSON schema.
        json_schema = FieldResult.model_json_schema()
        response_format = {
            "type": "json_schema",
            "json_schema": {"schema": json_schema}
        }
        logger.info("Threaded validation: Validating field '%s' for provider '%s'", field, provider)
        try:
            response_content = client.get_response(prompt, response_format)
            result = json.loads(response_content)
        except Exception as e:
            logger.error("Error validating field '%s': %s", field, e, exc_info=True)
            result = {"status": "Needs Work", "message": "Error validating this field.", "source": []}
        with lock:
            results[field] = result
    
    # Start a thread for each field.
    for field, value in fields.items():
        thread = threading.Thread(target=validate_field, args=(field, value))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to finish.
    for thread in threads:
        thread.join()
    
    provider_validation = {
        "provider": provider,
        "results": results
    }
    
    return provider_validation
