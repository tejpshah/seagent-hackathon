import json
import logging
from models import ProviderValidation

logger = logging.getLogger(__name__)

def validate_provider_batch(provider: str, fields: dict, client) -> dict:
    """
    Validate all fields in one go via a single API call.
    :param provider: Provider name.
    :param fields: Dictionary of field names to current values.
    :param client: Instance of PerplexityClient.
    :return: Structured JSON dictionary.
    """
    # Build a prompt listing all fields to validate.
    field_lines = "\n".join([f"{field}: {value}" for field, value in fields.items()])
    prompt = (
        f"Validate the following details for provider '{provider}':\n"
        f"{field_lines}\n\n"
        "For each field, determine if the value is verified as 'yes', 'needs attention', or 'no', "
        "and provide a short supplementary message. "
        "Output a JSON object with the following format:\n"
        "{\n"
        '  "provider": "<provider name>",\n'
        '  "results": {\n'
        '    "<field>": {"status": "<yes|needs attention|no>", "message": "<supplementary guidance>"},\n'
        "    ...\n"
        "  }\n"
        "}\n"
        "Only output the JSON object."
    )
    
    # Generate the JSON schema using our ProviderValidation model.
    json_schema = ProviderValidation.model_json_schema()
    response_format = {
        "type": "json_schema",
        "json_schema": {"schema": json_schema}
    }
    
    logger.info("Batch validation: Sending request to Perplexity API for provider '%s'", provider)
    response_content = client.get_response(prompt, response_format)
    
    try:
        result = json.loads(response_content)
    except Exception as e:
        logger.error("Failed to parse JSON response: %s", e, exc_info=True)
        raise
    return result
