import pandas as pd
import requests
import numpy as np
from collections import defaultdict
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import folium
import polyline
import os
import json
import random
import streamlit as st

# OpenWeatherMap API key from environment variable
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "686810d738e10e4b20cf4f81ae5e0705")

# ✅ State capital coordinates (for fast lookup)
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


# Get available delivery dates (next 5 days)
def get_available_dates():
    today = datetime.now()
    dates = [today + timedelta(days=x) for x in range(6)]
    return dates


# ✅ Get temperature using OpenWeatherMap API (5-day forecast)
def get_temperature(lat, lon, target_date):
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=imperial"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()['list']
        target_date = datetime.strptime(target_date, '%Y-%m-%d')

        # Get all temperature readings for the target date
        temps = []
        for entry in data:
            forecast_time = datetime.fromtimestamp(entry['dt'])
            if forecast_time.date() == target_date.date():
                temp = entry['main'].get('temp')
                if temp is not None:
                    temps.append(temp)
        
        if temps:
            # Calculate min, max, and average temperatures
            min_temp = min(temps)
            max_temp = max(temps)
            avg_temp = sum(temps) / len(temps)
            
            return {
                'min_temp': round(min_temp, 2),
                'max_temp': round(max_temp, 2),
                'avg_temp': round(avg_temp, 2)
            }

    return None

# ✅ Get average temperature for states along the route
def calculate_avg_temp(states, date):
    """
    Calculate average temperature for a list of states on a given date.
    Returns a dictionary with temperature data for each state.
    """
    try:
        state_temps = {}
        
        # Use threading for faster execution
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_state = {
                executor.submit(get_temperature, STATE_CAPITAL_COORDS[state][0], 
                              STATE_CAPITAL_COORDS[state][1], date): state 
                for state in states if state in STATE_CAPITAL_COORDS
            }
            
            for future in future_to_state:
                state = future_to_state[future]
                try:
                    temp_data = future.result()
                    if temp_data is not None:
                        state_temps[state] = temp_data
                    else:
                        st.warning(f"Temperature data not available for {state}")
                        state_temps[state] = {
                            'min_temp': 0,
                            'max_temp': 0,
                            'avg_temp': 0
                        }
                except Exception as e:
                    st.warning(f"Error getting temperature for {state}: {str(e)}")
                    state_temps[state] = {
                        'min_temp': 0,
                        'max_temp': 0,
                        'avg_temp': 0
                    }
        
        # Preserve order based on the order in the `states` list
        ordered_temps = OrderedDict(
            (state, state_temps[state]) for state in states if state in state_temps
        )
        
        return ordered_temps
        
    except Exception as e:
        st.error(f"Error calculating temperatures: {str(e)}")
        return {}


# Recommend truck type based on temperature
def recommend_truck_type(avg_temp):
    if 40 <= avg_temp <= 60:
        return "Dry Truck (40°F - 60°F)"
    else:
        return "Reefer Truck (Outside 40°F - 60°F)"

# Load route data from Excel
def load_route_data():
    """Load route data from Excel file."""
    try:
        # Use absolute path for the dataset
        file_path = "/Users/bhaveshpatidar/Downloads/TruckRouteWeather/attached_assets/route_unique_data.xlsx"
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            print(f"Current directory contents:")
            print(os.listdir("/Users/bhaveshpatidar/Downloads/TruckRouteWeather/attached_assets"))
            return pd.DataFrame()
            
        print(f"Attempting to load file from: {file_path}")
        df = pd.read_excel(file_path)
        
        if df.empty:
            print("Warning: Loaded DataFrame is empty")
            return df
            
        print(f"Successfully loaded DataFrame with shape: {df.shape}")
        print("Available columns in the dataset:", df.columns.tolist())
        print("\nFirst few rows of the DataFrame:")
        print(df.head())
        return df
        
    except Exception as e:
        print(f"Error loading route data: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return pd.DataFrame()  # Return empty DataFrame if there's an error

