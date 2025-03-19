# Logistics Route Planner 🚛

A Streamlit application that helps logistics companies optimize their truck routes based on temperature conditions. The app recommends whether to use a Reefer or Dry truck based on the temperature conditions along the route.

## Features

- Route planning from Portland, Maine to various destinations
- Temperature-based truck type recommendations (Reefer vs Dry)
- Cost savings analysis
- Route visualization using Google Maps
- Date comparison for optimal delivery timing
- Real-time weather data integration

## Setup

1. Clone the repository:
```bash
git clone https://github.com/patidarb013/Logistics-Route-Planner.git
cd Logistics-Route-Planner
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

5. Run the application:
```bash
streamlit run app.py
```

## Environment Variables

- `GOOGLE_MAPS_API_KEY`: Your Google Maps API key for route visualization

## Usage

1. Enter your destination city
2. Select a delivery date
3. Click "Calculate Route" to get:
   - Route details
   - Truck type recommendation
   - Temperature analysis
   - Cost savings analysis
   - Route visualization

## Deployment

This app is deployed on Streamlit Cloud. Visit [share.streamlit.io](https://share.streamlit.io) to deploy your own copy.

## Data Files

The application expects a route data file (`route_unique_data.xlsx`) in one of these locations:
- Project root directory
- `data/` directory
- `attached_assets/` directory

## Notes

- The application uses OpenWeatherMap API for weather data
- Google Maps integration requires a valid API key
- Temperature recommendations are based on the average temperature across the route 