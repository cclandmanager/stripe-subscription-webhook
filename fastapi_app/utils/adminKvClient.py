import os
import httpx
import asyncio
from typing import Tuple, Dict, Any, Optional, List, Union
from fastapi_app.logging_setup import logger

async def kv_request(endpoint: str, method: str, body: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
    """
    Make a request to the Admin KV Storage API.
    """
    base_url = os.getenv("ADMIN_KV_API_URL")
    if not base_url:
        raise ValueError("ADMIN_KV_API_URL not configured")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    timeout = httpx.Timeout(float(os.getenv("HTTP_TIMEOUT_S", "10.0")), connect=5.0)
    retries = int(os.getenv("HTTP_RETRIES", "2"))

    async with httpx.AsyncClient(timeout=timeout) as client:
        last_exc = None
        for attempt in range(retries + 1):
            try:
                # response = await client.request(...)
                logger.debug(f"KV API Request: {method} {endpoint} - Body: {body}")
                response = await client.request(
                    method,
                    f"{base_url.rstrip('/')}{endpoint}",
                    json=body,
                    headers=headers
                )
                
                if response.status_code >= 500:
                    # Retry on server errors
                    if attempt < retries:
                        await asyncio.sleep(0.5 * (2 ** attempt))
                        continue
                
                json_data = response.json()
                
                if not response.is_success:
                    message = json_data.get("error", response.reason_phrase)
                    raise Exception(f"Admin KV API error: {message}")
                
                return json_data
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exc = e
                if attempt < retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                else:
                    logger.error(f"Admin KV API request failed after {retries} retries: {str(e)}")
                    raise last_exc
            except Exception as e:
                logger.error(f"Unexpected error during Admin KV API request: {str(e)}")
                raise e

async def get_objects_by_type(variables: Dict[str, Any], token: str) -> Dict[str, Any]:
    """
    Get objects by type (e.g., all subscriptions).
    """
    obj_type = variables.get("type")
    result = await kv_request("/query", "POST", {"type": obj_type}, token)
    return {"objectsByType": result.get("records", [])}

async def get_objects_by_owner(variables: Dict[str, Any], token: str) -> Dict[str, Any]:
    """
    Get objects by owner (e.g., specific user's records).
    """
    owner = variables.get("owner")
    result = await kv_request("/query", "POST", {"owner": owner}, token)
    return {"objectsByOwner": result.get("records", [])}

async def upsert_object(variables: Dict[str, Any], token: str) -> Dict[str, Any]:
    """
    Upsert (create or update) an object.
    """
    # Map variables to KV API format
    # Use 'id' if present, otherwise fallback to 'key'
    obj_id = variables.get("id") or variables.get("key")
    
    record = {
        "id": obj_id,
        "owner": variables.get("owner"),
        "type": variables.get("type"),
        "authorizedUsers": variables.get("authorizedUsers", []),
        "object": variables.get("object")
    }
    
    # Add optional fields if present
    if "name" in variables: record["name"] = variables["name"]
    if "startDate" in variables: record["startDate"] = variables["startDate"]
    if "endDate" in variables: record["endDate"] = variables["endDate"]
    
    # Filter out None values to match JS behavior where undefined is omitted in JSON.stringify
    record = {k: v for k, v in record.items() if v is not None}
    
    result = await kv_request("/upsert", "POST", record, token)
    return {"upsertObject": result.get("record")}

async def query_object_stor(props: Dict[str, Any], token: str, client: Optional[httpx.AsyncClient] = None) -> Tuple[Any, int]:
    """
    Compatibility wrapper: Queries the object store.
    Matches the signature used in the codebase.
    Returns: [records, status_code]
    """
    try:
        query_body = {}
        # Support both 'id' and 'key' as identifiers
        obj_id = props.get("id") or props.get("key")
        if obj_id: query_body["id"] = obj_id
        
        if "owner" in props: query_body["owner"] = props["owner"]
        if "type" in props: query_body["type"] = props["type"]
        if "objPropKey" in props: query_body["objPropKey"] = props["objPropKey"]
        if "objPropValue" in props: query_body["objPropValue"] = props["objPropValue"]

        # Filter out None values to match JS behavior
        query_body = {k: v for k, v in query_body.items() if v is not None}

        result = await kv_request("/query", "POST", query_body, token)
        return result.get("records", []), 200
    except Exception as e:
        logger.error(f"query_object_stor failed: {str(e)}")
        return None, 500

async def update_object_stor(props: Dict[str, Any], token: str, client: Optional[httpx.AsyncClient] = None) -> Tuple[Any, int]:
    """
    Compatibility wrapper: Updates or deletes an object in the store.
    Matches the signature used in the codebase.
    Returns: [result, status_code]
    """
    try:
        if props.get("deleteNodeId"):
            # Handle Delete operation
            result = await kv_request("/delete", "POST", {"id": props["deleteNodeId"], "owner": props.get("owner")}, token)
            return result.get("record") or result, 200
        else:
            # Handle Upsert
            result = await upsert_object(props, token)
            return result.get("upsertObject"), 200
    except Exception as e:
        logger.error(f"update_object_stor failed: {str(e)}")
        return None, 500
