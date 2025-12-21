# weather.py
import requests
import streamlit as st
import random

# 1. Define Airports
AIRPORT_COORDS = {
    "OPSK": {"lat": 32.5353, "lon": 74.3636, "name": "Sialkot"},
    "OPKC": {"lat": 24.9060, "lon": 67.1600, "name": "Karachi"},
    "OPLA": {"lat": 31.5216, "lon": 74.4036, "name": "Lahore"},
    "OPIS": {"lat": 33.5490, "lon": 73.0169, "name": "Islamabad"},
    "OMDB": {"lat": 25.2532, "lon": 55.3657, "name": "Dubai"},
}

def get_weather_for_airport(icao_code):
    """
    Fetches real-time weather. Returns None if API fails.
    """
    airport = AIRPORT_COORDS.get(icao_code)
    if not airport: return None

    # Get API Key from Secrets
    api_key = st.secrets.get("OPENWEATHER_API_KEY") or st.secrets.get("WEATHER_API_KEY")
    
    if not api_key:
        print(f"⚠️ Weather: No API Key found for {icao_code}")
        return None

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={airport['lat']}&lon={airport['lon']}&units=metric&appid={api_key}"
    
    try:
        response = requests.get(url, timeout=2) # Short timeout to prevent lag
        if response.status_code == 200:
            data = response.json()
            icon_code = data['weather'][0]['icon'][:2]
            icon_map = {"01": "☀️", "02": "⛅", "03": "☁️", "04": "☁️", "09": "🌧️", "10": "🌦️", "11": "⛈️", "13": "❄️", "50": "🌫️"}
            
            return {
                "temp": round(data['main']['temp']),
                "condition": data['weather'][0]['main'],
                "wind": round(data['wind']['speed'] * 3.6),
                "icon": icon_map.get(icon_code, "🌤️"),
                "name": airport['name'],
                "source": "Live"
            }
        else:
            print(f"⚠️ Weather API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"⚠️ Weather Connection Error: {e}")
    
    return None

def get_mock_data(icao_code):
    """Fallback data so the UI never breaks"""
    airport = AIRPORT_COORDS.get(icao_code)
    return {
        "temp": random.randint(20, 35),
        "condition": "Demo Data",
        "wind": random.randint(5, 15),
        "icon": "📡",
        "name": airport['name'],
        "source": "Demo"
    }

def get_all_weather():
    """Returns weather data (Real or Fallback)"""
    priority_hubs = ["OPSK", "OPKC", "OPLA", "OPIS", "OMDB"]
    results = []
    
    for icao in priority_hubs:
        # 1. Try Real API
        data = get_weather_for_airport(icao)
        
        # 2. Use Mock Data if Real Failed
        if not data:
            data = get_mock_data(icao)
            
        results.append(data)
            
    return results
