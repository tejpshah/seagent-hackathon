import json
import logging
from models import ProviderValidation

logger = logging.getLogger(__name__)

def validate_provider_batch(provider: str, fields: dict, client) -> dict:
    """
    Validate all fields in one go via a single API call.
    Returns a JSON object with each field having:
      - status: "Validated", "Needs Work", or "Incorrect"
      - message: supplementary guidance
      - source: list of URL strings from Perplexity response
    """
    # Build a prompt listing all fields to validate.
    field_lines = "\n".join([f"{field}: {value}" for field, value in fields.items()])
    prompt = (
        f"Validate the following details for provider '{provider}':\n"
        f"{field_lines}\n\n"
        "For each field, determine if the provided value is:\n"
        "  - Validated (if it is correct),\n"
        "  - Needs Work (if it appears outdated or partially correct), or\n"
        "  - Incorrect (if it is wrong).\n\n"
        "Also, provide a short supplementary message and include the relevant source URL(s) from which the information was obtained.\n\n"
        "Output a JSON object with the following format:\n"
        "{\n"
        '  "provider": "<provider name>",\n'
        '  "results": {\n'
        '    "<field>": {"status": "<Validated|Needs Work|Incorrect>", "message": "<supplementary guidance>", "source": ["<url1>", "<url2>", ...]},\n'
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
