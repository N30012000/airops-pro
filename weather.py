# weather.py
import requests
import streamlit as st

# 1. Define Airports (ICAO codes and Coordinates)
AIRPORT_COORDS = {
    "OPSK": {"lat": 32.5353, "lon": 74.3636, "name": "Sialkot"},
    "OPKC": {"lat": 24.9060, "lon": 67.1600, "name": "Karachi"},
    "OPLA": {"lat": 31.5216, "lon": 74.4036, "name": "Lahore"},
    "OPIS": {"lat": 33.5490, "lon": 73.0169, "name": "Islamabad"},
    "OMDB": {"lat": 25.2532, "lon": 55.3657, "name": "Dubai"},
    "OEJN": {"lat": 21.6796, "lon": 39.1560, "name": "Jeddah"},
    "OPPS": {"lat": 33.9930, "lon": 71.4731, "name": "Peshawar"},
    "OPQT": {"lat": 30.1798, "lon": 66.9905, "name": "Quetta"},
}

def get_weather_for_airport(icao_code):
    """
    Fetches real-time weather from OpenWeatherMap.
    """
    # Get coordinates
    airport = AIRPORT_COORDS.get(icao_code)
    if not airport:
        return None

    # Get API Key (Checks secrets.toml)
    api_key = st.secrets.get("OPENWEATHER_API_KEY") or st.secrets.get("WEATHER_API_KEY")
    
    if not api_key:
        # Fallback if no key is set (Visual Placeholder)
        return {
            "temp": "--", 
            "condition": "No API Key", 
            "wind": "--", 
            "icon": "⚠️", 
            "name": airport['name']
        }

    # Make Request
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={airport['lat']}&lon={airport['lon']}&units=metric&appid={api_key}"
    
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            
            # Map Icon Codes to Emojis
            icon_code = data['weather'][0]['icon'][:2]
            icon_map = {
                "01": "☀️", "02": "⛅", "03": "☁️", "04": "☁️", 
                "09": "🌧️", "10": "🌦️", "11": "⛈️", "13": "❄️", "50": "🌫️"
            }
            
            return {
                "temp": round(data['main']['temp']),
                "condition": data['weather'][0]['main'],
                "wind": round(data['wind']['speed'] * 3.6), # Convert m/s to km/h
                "icon": icon_map.get(icon_code, "🌤️"),
                "name": airport['name']
            }
    except Exception as e:
        print(f"Weather Fetch Error: {e}")
    
    return None

def get_all_weather():
    """Returns a list of weather data for dashboard display"""
    # Prioritize main hubs
    priority_hubs = ["OPSK", "OPKC", "OPLA", "OPIS", "OMDB"]
    results = []
    
    for icao in priority_hubs:
        data = get_weather_for_airport(icao)
        if data:
            results.append(data)
            
    return results
