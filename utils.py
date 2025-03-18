import pandas as pd
import requests
import numpy as np
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import folium
import polyline
import os
import json

# OpenWeatherMap API key from environment variable
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "686810d738e10e4b20cf4f81ae5e0705")

# State capital coordinates
STATE_CAPITAL_COORDS = {
    "Alabama": (32.3770, -86.3000),
    "Alaska": (58.3019, -134.4197),
    "Arizona": (33.4484, -112.0740),
    "Arkansas": (34.7465, -92.2896),
    "California": (38.5767, -121.4936),
    "Colorado": (39.7392, -104.9903),
    "Connecticut": (41.7658, -72.6734),
    "Delaware": (39.1582, -75.5244),
    "Florida": (30.4383, -84.2807),
    "Georgia": (33.7490, -84.3880),
    "Hawaii": (21.3070, -157.8584),
    "Idaho": (43.6150, -116.2023),
    "Illinois": (39.7980, -89.6440),
    "Indiana": (39.7684, -86.1581),
    "Iowa": (41.5868, -93.6250),
    "Kansas": (39.0473, -95.6752),
    "Kentucky": (38.1867, -84.8753),
    "Louisiana": (30.4571, -91.1874),
    "Maine": (44.3106, -69.7795),
    "Maryland": (38.9784, -76.4922),
    "Massachusetts": (42.3601, -71.0589),
    "Michigan": (42.7337, -84.5555),
    "Minnesota": (44.9537, -93.0900),
    "Mississippi": (32.2988, -90.1848),
    "Missouri": (38.5767, -92.1735),
    "Montana": (46.5891, -112.0391),
    "Nebraska": (40.8136, -96.7026),
    "Nevada": (39.1638, -119.7674),
    "New Hampshire": (43.1939, -71.5724),
    "New Jersey": (40.2206, -74.7597),
    "New Mexico": (35.6868, -105.9378),
    "New York": (42.6526, -73.7562),
    "North Carolina": (35.7796, -78.6382),
    "North Dakota": (46.8083, -100.7837),
    "Ohio": (39.9612, -82.9988),
    "Oklahoma": (35.4676, -97.5164),
    "Oregon": (44.9429, -123.0351),
    "Pennsylvania": (40.2732, -76.8867),
    "Rhode Island": (41.8309, -71.4146),
    "South Carolina": (34.0007, -81.0348),
    "South Dakota": (44.3670, -100.3364),
    "Tennessee": (36.1627, -86.7816),
    "Texas": (30.2672, -97.7431),
    "Utah": (40.7608, -111.8910),
    "Vermont": (44.2601, -72.5754),
    "Virginia": (37.5407, -77.4360),
    "Washington": (47.0379, -122.9007),
    "West Virginia": (38.3364, -81.6123),
    "Wisconsin": (43.0747, -89.3844),
    "Wyoming": (41.1400, -104.8202)
}

def get_temperature(lat, lon):
    """Get temperature using OpenWeatherMap API"""
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=imperial"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['main']['temp']
    except requests.exceptions.RequestException as e:
        return None

def calculate_avg_temp(states):
    """Calculate average temperature for states along the route"""
    state_temp = defaultdict(list)

    def fetch_temp(state):
        if state in STATE_CAPITAL_COORDS:
            lat, lon = STATE_CAPITAL_COORDS[state]
            temp = get_temperature(lat, lon)
            if temp is not None:
                state_temp[state].append(temp)

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(fetch_temp, states)

    return {state: np.mean(temps) for state, temps in state_temp.items() if temps}

def recommend_truck_type(avg_temp):
    """Recommend truck type based on temperature"""
    if 40 <= avg_temp <= 60:
        return "Dry Truck (40°F - 60°F)"
    else:
        return "Reefer Truck (Outside 40°F - 60°F)"

def create_route_map(polyline_str):
    """Create a Folium map with the route polyline"""
    try:
        # Debug print
        print(f"Received polyline string: {polyline_str[:50]}...")  # Print first 50 chars

        # Basic validation
        if not isinstance(polyline_str, str):
            raise ValueError(f"Expected string, got {type(polyline_str)}")

        if not polyline_str.strip():
            raise ValueError("Empty polyline string")

        # Decode polyline to get coordinates
        try:
            coords = polyline.decode(polyline_str)
        except Exception as e:
            raise ValueError(f"Failed to decode polyline: {str(e)}")

        if not coords:
            raise ValueError("No coordinates found after decoding polyline")

        # Print first few coordinates for debugging
        print(f"First few coordinates: {coords[:3]}")

        # Calculate center point for the map
        center_lat = sum(lat for lat, _ in coords) / len(coords)
        center_lng = sum(lng for _, lng in coords) / len(coords)

        # Create base map
        m = folium.Map(location=[center_lat, center_lng], zoom_start=5)

        # Add the route polyline
        folium.PolyLine(
            coords,
            weight=3,
            color='blue',
            opacity=0.8
        ).add_to(m)

        # Add markers for start and end points
        folium.Marker(
            coords[0],
            popup='Start (Portland, ME)',
            icon=folium.Icon(color='green')
        ).add_to(m)

        folium.Marker(
            coords[-1],
            popup='Destination',
            icon=folium.Icon(color='red')
        ).add_to(m)

        return m
    except Exception as e:
        print(f"Error in create_route_map: {str(e)}")  # Debug print
        raise Exception(f"Failed to create route map: {str(e)}")

def get_available_dates():
    """Get list of available dates (current date + 5 days)"""
    today = datetime.now()
    dates = [today + timedelta(days=x) for x in range(6)]
    return dates

def load_route_data():
    """Load and process route data from Excel"""
    try:
        # Try loading from root directory first
        file_paths = ['route_unique_data.xlsx', 'attached_assets/route_unique_data.xlsx']

        for file_path in file_paths:
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                print(f"Available columns: {df.columns.tolist()}")  # Debug info
                df['Pick Zip'] = df['Pick Zip'].astype(str).str.strip()
                df['Drop Zip'] = df['Drop Zip'].astype(str).str.strip()
                return df

        raise FileNotFoundError("Route data file not found in any expected location")
    except Exception as e:
        raise Exception(f"Failed to load route data: {str(e)}")

def load_polyline_from_json(city, state):
    """Load polyline data from JSON file for a given city and state"""
    try:
        json_paths = ['route_data.json', 'attached_assets/route_data.json']

        for path in json_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    route_data = json.loads(f.read())

                # Look for matching route
                for route in route_data:
                    if (route.get('drop_city', '').lower() == city.lower() and 
                        route.get('drop_state', '').lower() == state.lower()):
                        return route.get('polyline')

        return None
    except Exception as e:
        print(f"Error loading JSON polyline: {str(e)}")
        return None

def get_route_polyline(destination_row):
    """Get polyline data from either Excel or JSON source"""
    try:
        # First try Excel data
        if 'Encoded Polyline' in destination_row:
            polyline_data = destination_row['Encoded Polyline']
            if not pd.isna(polyline_data):
                return polyline_data

        # If Excel data not available, try JSON
        city = destination_row['Drop City']
        state = destination_row['Drop State']
        return load_polyline_from_json(city, state)

    except Exception as e:
        print(f"Error getting route polyline: {str(e)}")
        return None