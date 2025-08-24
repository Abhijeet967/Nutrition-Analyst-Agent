import os
from typing import Any
from dotenv import load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP

load_dotenv()
# Create a FastMCP server instance
mcp = FastMCP("usda-food-data-central")

# API Configuration
FDC_API_BASE = "https://api.nal.usda.gov/fdc/v1"
USER_AGENT = "usda-fdc-mcp/1.0"

# Global API key storage
API_KEY = os.getenv("API_KEY")


async def make_fdc_request(endpoint: str, method: str = "GET", params: dict[str, Any] | None = None, data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Make HTTP request to the USDA Food Data Central API."""
    if not API_KEY:
        return {"error": "API key not set. Use set_api_key tool first."}
    
    url = f"{FDC_API_BASE}/{endpoint.lstrip('/')}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Add API key to parameters
    if params is None:
        params = {}
    params['api_key'] = API_KEY
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, params=params, json=data, timeout=30.0)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}


def format_food_summary(food: dict) -> str:
    """Format food item for display."""
    return f"""Food: {food.get('description', 'Unknown')}
FDC ID: {food.get('fdcId', 'N/A')}
Data Type: {food.get('dataType', 'Unknown')}
Brand: {food.get('brandOwner', 'N/A') if food.get('brandOwner') else 'Generic'}
Published: {food.get('publishedDate', 'N/A')}"""


def format_food_details(food: dict) -> str:
    """Format detailed food information."""
    details = f"""Food: {food.get('description', 'Unknown')}
FDC ID: {food.get('fdcId', 'N/A')}
Data Type: {food.get('dataType', 'Unknown')}
Category: {food.get('foodCategory', {}).get('description', 'N/A')}
"""
    
    if food.get('brandOwner'):
        details += f"Brand: {food['brandOwner']}\n"
    
    if food.get('ingredients'):
        details += f"Ingredients: {food['ingredients']}\n"
    
    # Add nutritional information
    if food.get('foodNutrients'):
        details += "\nNutritional Information (per 100g):\n"
        for nutrient in food['foodNutrients'][:10]:  # Show top 10 nutrients
            name = nutrient.get('nutrient', {}).get('name', 'Unknown')
            amount = nutrient.get('amount', 0)
            unit = nutrient.get('nutrient', {}).get('unitName', '')
            if amount and amount > 0:
                details += f"  {name}: {amount} {unit}\n"
    
    return details


@mcp.tool()
async def search_foods(query: str, data_type: str | None = None, page_size: int = 25) -> str:
    """Search for foods in the USDA Food Data Central database."""
    search_data = {
        "query": query,
        "pageSize": min(page_size, 50),  # Limit to reasonable size
        "pageNumber": 1
    }
    
    if data_type:
        valid_types = ["Foundation", "Branded", "Survey (FNDDS)", "Legacy", "Experimental"]
        if data_type in valid_types:
            search_data["dataType"] = [data_type]
        else:
            return f"Invalid data type. Valid options: {', '.join(valid_types)}"
    
    result = await make_fdc_request("foods/search", method="POST", data=search_data)
    
    if not result or "error" in result:
        return f"Search failed: {result.get('error', 'Unknown error')}"
    
    if not result.get("foods"):
        return "No foods found for your search query."
    
    foods = result["foods"]
    total = result.get("totalHits", len(foods))
    
    search_results = [format_food_summary(food) for food in foods[:10]]  # Show top 10
    
    summary = f"Found {total} foods. Showing top {len(search_results)} results:\n\n"
    summary += "\n---\n".join(search_results)
    
    if total > len(search_results):
        summary += f"\n\n... and {total - len(search_results)} more results."
    
    return summary


@mcp.tool()
async def get_food_details(fdc_id: int) -> str:
    """Get detailed nutritional information for a specific food item."""
    result = await make_fdc_request(f"food/{fdc_id}")
    
    if not result or "error" in result:
        return f"Failed to get food details: {result.get('error', 'Unknown error')}"
    
    return format_food_details(result)


@mcp.tool()
async def get_food_nutrients(fdc_id: int, nutrient_ids: str | None = None) -> str:
    """Get specific nutrient information for a food item."""
    params = {}
    if nutrient_ids:
        # Parse comma-separated nutrient IDs
        try:
            ids = [int(id.strip()) for id in nutrient_ids.split(",")]
            params["nutrients"] = ",".join(map(str, ids))
        except ValueError:
            return "Invalid nutrient IDs. Provide comma-separated numbers (e.g., '203,204,208')"
    
    result = await make_fdc_request(f"food/{fdc_id}", params=params)
    
    if not result or "error" in result:
        return f"Failed to get nutrient data: {result.get('error', 'Unknown error')}"
    
    food_name = result.get('description', 'Unknown Food')
    nutrients_info = f"Nutrient information for {food_name} (FDC ID: {fdc_id}):\n\n"
    
    if result.get('foodNutrients'):
        for nutrient in result['foodNutrients']:
            name = nutrient.get('nutrient', {}).get('name', 'Unknown')
            amount = nutrient.get('amount', 0)
            unit = nutrient.get('nutrient', {}).get('unitName', '')
            if amount and amount > 0:
                nutrients_info += f"{name}: {amount} {unit}\n"
    else:
        nutrients_info += "No nutrient data available."
    
    return nutrients_info


@mcp.tool()
async def compare_foods(fdc_ids: str, nutrient_ids: str | None = None) -> str:
    """Compare nutritional information between multiple foods."""
    try:
        ids = [int(id.strip()) for id in fdc_ids.split(",")]
        if len(ids) > 5:
            return "Maximum 5 foods can be compared at once."
    except ValueError:
        return "Invalid FDC IDs. Provide comma-separated numbers (e.g., '123456,789012')"
    
    # Prepare request data
    request_data = {"fdcIds": ids}
    if nutrient_ids:
        try:
            nutrients = [int(id.strip()) for id in nutrient_ids.split(",")]
            request_data["nutrients"] = nutrients
        except ValueError:
            return "Invalid nutrient IDs. Provide comma-separated numbers."
    
    result = await make_fdc_request("foods", method="POST", data=request_data)
    
    if not result or "error" in result:
        return f"Failed to compare foods: {result.get('error', 'Unknown error')}"
    
    foods = result if isinstance(result, list) else []
    if not foods:
        return "No food data found for the provided IDs."
    
    comparison = "Food Comparison:\n\n"
    
    for food in foods:
        comparison += f"=== {food.get('description', 'Unknown')} (ID: {food.get('fdcId')}) ===\n"
        
        if food.get('foodNutrients'):
            for nutrient in food['foodNutrients'][:8]:  # Top 8 nutrients
                name = nutrient.get('nutrient', {}).get('name', 'Unknown')
                amount = nutrient.get('amount', 0)
                unit = nutrient.get('nutrient', {}).get('unitName', '')
                if amount and amount > 0:
                    comparison += f"  {name}: {amount} {unit}\n"
        
        comparison += "\n"
    
    return comparison


@mcp.tool()
async def get_nutrient_reference() -> str:
    """Get reference information for common nutrient IDs."""
    nutrients = {
        "203": "Protein",
        "204": "Total lipid (fat)",
        "205": "Carbohydrate, by difference", 
        "208": "Energy (kcal)",
        "269": "Sugars, total including NLEA",
        "291": "Fiber, total dietary",
        "301": "Calcium, Ca",
        "303": "Iron, Fe",
        "304": "Magnesium, Mg",
        "305": "Phosphorus, P",
        "306": "Potassium, K",
        "307": "Sodium, Na",
        "309": "Zinc, Zn",
        "401": "Vitamin C, total ascorbic acid",
        "404": "Thiamin (Vitamin B1)",
        "405": "Riboflavin (Vitamin B2)",
        "406": "Niacin (Vitamin B3)",
        "415": "Vitamin B-6",
        "417": "Folate, total",
        "418": "Vitamin B-12",
        "320": "Vitamin A, RAE",
        "324": "Vitamin D (D2 + D3)",
        "323": "Vitamin E (alpha-tocopherol)",
        "430": "Vitamin K (phylloquinone)"
    }
    
    reference = "Common Nutrient IDs for filtering:\n\n"
    for nutrient_id, name in nutrients.items():
        reference += f"{nutrient_id}: {name}\n"
    
    reference += "\nUsage: Use these IDs with get_food_nutrients() or compare_foods()"
    reference += "\nExample: get_food_nutrients(fdc_id=123456, nutrient_ids='203,204,208')"
    
    return reference


@mcp.tool()
async def get_data_types() -> str:
    """Get information about available food data types."""
    data_types = {
        "Foundation": "Comprehensive nutrient data on a diverse set of foods that provide the foundation for other food composition data",
        "Branded": "Label data from branded/packaged foods available in the marketplace",
        "Survey (FNDDS)": "Foods from the Food and Nutrient Database for Dietary Studies, used in dietary surveys",
        "Legacy": "Historical data from the Standard Reference database",
        "Experimental": "Foods from research studies and experimental data"
    }
    
    info = "Available Food Data Types:\n\n"
    for data_type, description in data_types.items():
        info += f"{data_type}:\n  {description}\n\n"
    
    info += "Usage: Use these data type names with search_foods()"
    info += "\nExample: search_foods(query='apple', data_type='Foundation')"
    
    return info


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')