import streamlit as st
from utils import (
    load_route_data, get_available_dates, calculate_avg_temp,
    recommend_truck_type, create_route_map
)
import numpy as np
from datetime import datetime
import folium
from streamlit_folium import folium_static

# Page configuration
st.set_page_config(
    page_title="Logistics Route Planner",
    page_icon="🚛",
    layout="wide"
)

# Title and description
st.title("🚛 Logistics Route Planner")
st.markdown("Plan your route from Portland, Maine and get truck recommendations based on temperature.")

try:
    # Load route data
    df = load_route_data()
    
    # Create two columns for input
    col1, col2 = st.columns(2)
    
    with col1:
        # Dropdown for destination selection
        destinations = sorted(df['Dropoff Location'].unique())
        selected_destination = st.selectbox(
            "Select Drop-off Location",
            options=destinations,
            help="Choose your delivery destination"
        )
    
    with col2:
        # Date selection
        available_dates = get_available_dates()
        selected_date = st.date_input(
            "Select Delivery Date",
            min_value=available_dates[0],
            max_value=available_dates[-1],
            value=available_dates[0],
            help="Choose a delivery date (up to 5 days from today)"
        )

    if st.button("Calculate Route"):
        with st.spinner("Processing route information..."):
            # Get route information
            route_info = df[df['Dropoff Location'] == selected_destination].iloc[0]
            states = route_info['States Along Route'].split(', ')
            
            # Calculate temperatures
            state_temps = calculate_avg_temp(states)
            avg_temp = np.mean(list(state_temps.values()))
            
            # Create columns for results
            result_col1, result_col2 = st.columns(2)
            
            with result_col1:
                st.subheader("Route Information")
                st.write("**From:** Portland, Maine")
                st.write(f"**To:** {selected_destination}")
                st.write(f"**Delivery Date:** {selected_date.strftime('%B %d, %Y')}")
                
                # Temperature information
                st.subheader("Temperature Analysis")
                for state, temp in state_temps.items():
                    st.write(f"**{state}:** {temp:.1f}°F")
                st.write(f"**Average Route Temperature:** {avg_temp:.1f}°F")
                
                # Truck recommendation
                truck_type = recommend_truck_type(avg_temp)
                st.subheader("Recommendation")
                st.info(f"**Recommended Truck Type:** {truck_type}")
            
            with result_col2:
                st.subheader("Route Visualization")
                # Create and display map
                if 'Polyline' in route_info:
                    route_map = create_route_map(route_info['Polyline'])
                    folium_static(route_map)
                else:
                    st.error("Route visualization not available")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.error("Please try again later or contact support if the problem persists.")

# Footer
st.markdown("---")
st.markdown("🚚 Logistics Route Planner - Helping you choose the right truck for your delivery")
