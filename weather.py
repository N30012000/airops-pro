# weather.py
# Simple OpenWeatherMap wrapper for airport weather
import requests
from datetime import datetime
from typing import List
from config_loader import WEATHER_API_KEY

AIRPORT_COORDS = {
    "OPSK": {"lat":32.5353,"lon":74.3636},
    "OPKC": {"lat":24.9060,"lon":67.1600},
    "OPLA": {"lat":31.5216,"lon":74.4036},
    "OPIS": {"lat":33.5490,"lon":73.0169},
    "OPPS": {"lat":33.9930,"lon":71.4731},
    "OPQT": {"lat":30.1798,"lon":66.9905},
    "OPFA": {"lat":31.4180,"lon":73.0790},
    "OPMT": {"lat":30.1575,"lon":71.5249},
    "OMDB": {"lat":25.2532,"lon":55.3657},
    "OMSJ": {"lat":25.3285,"lon":55.5179},
    "OMAA": {"lat":24.4332,"lon":54.6510},
    "OERK": {"lat":24.9576,"lon":46.6986},
    "OEJN": {"lat":21.6796,"lon":39.1560},
    "OEDF": {"lat":26.4713,"lon":50.1036},
    "OTHH": {"lat":25.2736,"lon":51.6086},
    "OBBI": {"lat":26.2708,"lon":50.6339},
    "OOMS": {"lat":23.5933,"lon":58.2844},
    "OKBK": {"lat":29.2266,"lon":47.9681},
}

class WeatherClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or WEATHER_API_KEY

    def fetch_for_airport(self, icao):
        coords = AIRPORT_COORDS.get(icao)
        if not coords:
            return {"icao": icao, "error": "unknown airport"}
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&units=metric&appid={self.api_key}"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            return {
                "icao": icao,
                "temp_c": data["main"]["temp"],
                "weather": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "icon": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
                "timestamp": datetime.utcfromtimestamp(data["dt"]).isoformat()
            }
        except Exception as e:
            return {"icao": icao, "error": str(e)}

    def fetch_all(self, icaos: List[str]=None):
        icaos = icaos or list(AIRPORT_COORDS.keys())
        results = []
        for icao in icaos:
            results.append(self.fetch_for_airport(icao))
        return results
