import os
import requests
from django.http import Http404, HttpResponse
from django.shortcuts import render

TILE_LAYERS = {"precipitation_new", "clouds_new", "wind_new", "temp_new", "pressure_new"}


def get_theme(main, icon):
    """Pick a background theme from OpenWeather's condition and day/night icon."""
    night = icon.endswith("n")
    if main == "Clear":
        return "clear-night" if night else "clear-day", night
    mapping = {
        "Clouds": "clouds",
        "Rain": "rain",
        "Drizzle": "rain",
        "Thunderstorm": "storm",
        "Snow": "snow",
    }
    theme = mapping.get(main, "mist" if main in {"Mist", "Fog", "Haze", "Smoke", "Dust", "Sand", "Ash"} else "default")
    return theme, night


def weather_view(request):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    city = request.GET.get("city", "Puerto Princesa")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        theme, night = get_theme(data["weather"][0]["main"], data["weather"][0]["icon"])
        weather_data = {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_kmh": round(data["wind"]["speed"] * 3.6),
            "description": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"],
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"],
            "theme": theme,
            "night": night,
        }
    except requests.exceptions.RequestException as e:
        weather_data = {
            "error": "Failed to fetch weather data",
            "details": str(e),
        }
    except KeyError:
        weather_data = {
            "error": f"Could not find weather information for '{city}'."
        }

    return render(request, "weather.html", {"weather": weather_data, "city": city})


def storm_map(request):
    try:
        lat = float(request.GET["lat"])
        lon = float(request.GET["lon"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError
        config = {"lat": lat, "lon": lon, "zoom": 7, "marker": True}
    except (KeyError, ValueError):
        config = {"lat": 12.5, "lon": 122.0, "zoom": 5, "marker": False}
    return render(request, "storms.html", {"map_config": config})


def weather_tile(request, layer, z, x, y):
    """Fetch a map tile from OpenWeather so the API key stays on the server."""
    if layer not in TILE_LAYERS:
        raise Http404
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png"
    try:
        r = requests.get(url, params={"appid": api_key}, timeout=10)
    except requests.exceptions.RequestException:
        return HttpResponse(status=502)
    if r.status_code != 200:
        return HttpResponse(status=r.status_code)
    resp = HttpResponse(r.content, content_type="image/png")
    resp["Cache-Control"] = "public, max-age=600"
    return resp