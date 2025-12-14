from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initilaize FastMCP instance
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_news_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API and return the JSON response."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
    }
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
        
def format_alert(feature: dict) -> str:
    """Format a weather alert feature into a readabale string."""
    props = feature["properties"]
    return f"""
        Event: {props.get('event', 'N/A')}
        Area: {props.get('areaDesc', 'N/A')}
        Effective: {props.get('severity', 'N/A')}
        Description: {props.get('description', 'N/A')}
        Instructions: {props.get('instruction', 'N/A')}
        """   
        
@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.
    
    Args:
        state (str): The two-letter state code (e.g., 'CA' for California).
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
    data = await make_news_request(url)
    
    if not data or "features" not in data:
        return "No alerts found or an error occurred."
    
    if not data["features"]:
        return "No active alerts for this state."
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude:float) -> str:
    """Get weather forecast for given latitude and longitude.
    
    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
    """
    
    # First, get the forecast grid endpoint from the points API
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_news_request(points_url)
    
    if not points_data:
        return "Error retrieving forecast data."
    
    # Get the forecast URL
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_news_request(forecast_url)
    
    if not forecast_data:
        return "Error retrieving forecast data."
    
    # Format the forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods:
        forecast = f"""
        {period['name']}:
        Temperature: {period['temperature']} {period['temperatureUnit']}
        Wind: {period['windSpeed']} {period['windDirection']}
        Detailed Forecast: {period['detailedForecast']}
        """  
        forecasts.append(forecast)
    
    return "\n---\n".join(forecasts)

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()