# Logistics Route Planner

A Streamlit application that helps plan logistics routes and recommend truck types based on weather conditions along the route.

## Features

- Route planning from Portland, Maine to various destinations
- Weather-based truck type recommendations
- Interactive Google Maps visualization
- Temperature analysis across states
- 5-day weather forecast integration

## Prerequisites

- Python 3.8 or higher
- Google Maps API key
- OpenWeatherMap API key

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd TruckRouteWeather
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your API keys:
     ```
     GOOGLE_MAPS_API_KEY=your_google_maps_api_key
     WEATHER_API_KEY=your_openweathermap_api_key
     ```

## Running the Application

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

## Usage

1. Enter the destination city in the "Enter DROP CITY" field
2. Select a delivery date (up to 5 days from today)
3. Click "Calculate Route" to see:
   - Route details
   - Temperature analysis across states
   - Recommended truck type
   - Interactive route map

## Data Files

The application expects a route data file (`route_unique_data.xlsx`) in one of these locations:
- Project root directory
- `data/` directory
- `attached_assets/` directory

## Notes

- The application uses OpenWeatherMap API for weather data
- Google Maps integration requires a valid API key
- Temperature recommendations are based on the average temperature across the route 