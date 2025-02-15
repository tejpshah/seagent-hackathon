import json
import logging
import threading
from models import FieldResult, ProviderValidation

logger = logging.getLogger(__name__)

def validate_provider_threaded(provider: str, fields: dict, client) -> dict:
    """
    Validate each field in its own thread.
    :param provider: Provider name.
    :param fields: Dictionary of field names to current values.
    :param client: Instance of PerplexityClient.
    :return: Structured JSON dictionary.
    """
    results = {}
    threads = []
    lock = threading.Lock()
    
    def validate_field(field, value):
        prompt = (
            f"Validate the following detail for provider '{provider}':\n"
            f"{field}: {value}\n\n"
            "Determine if the value is verified as 'yes', 'needs attention', or 'no', "
            "and provide a short supplementary message. "
            "Output a JSON object with the following format:\n"
            '{"status": "<yes|needs attention|no>", "message": "<supplementary guidance>"}\n'
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
            result = {"status": "needs attention", "message": "Error validating this field."}
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
