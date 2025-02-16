import json
import logging
import threading
import aiohttp
import asyncio
from modules.models import FieldResult, ProviderValidation

logger = logging.getLogger(__name__)

def validate_provider_batch(provider: str, fields: dict, client) -> dict:
    """
    Validate all fields in one API call via the Perplexity API.
    """
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
    
    json_schema = ProviderValidation.model_json_schema()
    response_format = {
        "type": "json_schema",
        "json_schema": {"schema": json_schema}
    }
    
    logger.info("Batch validation for provider '%s'", provider)
    response_content = client.get_response(prompt, response_format)
    
    try:
        result = json.loads(response_content)
    except Exception as e:
        logger.error("Failed to parse JSON response: %s", e, exc_info=True)
        raise
    return result


async def validate_provider_async(session, client, provider: str, fields: dict):
    """
    Async function to validate provider using PerplexityClient.
    """
    field_lines = "\n".join([f"{field}: {value}" for field, value in fields.items()])
    prompt = (
        f"Validate the following details for provider '{provider}':\n"
        f"{field_lines}\n\n"
        "For each field, determine if the provided value is:\n"
        "  - Validated (if it is correct),\n"
        "  - Needs Work (if it appears outdated or partially correct), or\n"
        "  - Incorrect (if it is wrong).\n\n"
        "Provide a short supplementary message and include the relevant source URL(s).\n\n"
        "Output JSON:\n"
        "{\n"
        '  "provider": "<provider name>",\n'
        '  "results": {\n'
        '    "<field>": {"status": "<Validated|Needs Work|Incorrect>", "message": "<guidance>", "source": ["<url1>", "<url2>", ...]},\n'
        "  }\n"
        "}"
    )
    
    json_schema = ProviderValidation.model_json_schema()
    response_format = {"type": "json_schema", "json_schema": {"schema": json_schema}}

    logger.info(f"Sending async request for provider: {provider}")
    
    response_content = await client.get_response(session, prompt, response_format)
    
    if response_content:
        try:
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {provider}: {e}")
            return {"provider": provider, "results": {}, "error": "Invalid JSON response"}
    
    return {"provider": provider, "results": {}, "error": "No response from API"}

async def batch_validate_providers(providers_list, client):
    """
    Run async validation for all providers in parallel.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [validate_provider_async(session, client, provider["provider"], provider["fields"]) for provider in providers_list]
        results = await asyncio.gather(*tasks)
    # Debug: Show all running tasks
        for task in asyncio.all_tasks():
            print(f"📌 Running task: {task}")

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"❌ Error validating provider {providers_list[i]['provider']}: {result}")
            results[i] = {"provider": providers_list[i]["provider"], "results": {}, "error": str(result)}
    return results

def validate_provider_threaded(provider: str, fields: dict, client) -> dict:
    """
    Validate each field in its own thread via the Perplexity API.
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
        json_schema = FieldResult.model_json_schema()
        response_format = {
            "type": "json_schema",
            "json_schema": {"schema": json_schema}
        }
        logger.info("Threaded validation for field '%s' of provider '%s'", field, provider)
        try:
            response_content = client.get_response(prompt, response_format)
            print(response_content)
            result = json.loads(response_content)
        except Exception as e:
            logger.error("Error validating field '%s': %s", field, e, exc_info=True)
            result = {"status": "Needs Work", "message": "Error validating this field.", "source": []}
        with lock:
            results[field] = result

    for field, value in fields.items():
        thread = threading.Thread(target=validate_field, args=(field, value))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    
    provider_validation = {
        "provider": provider,
        "results": results
    }
    
    return provider_validation
