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
        # Search input for destination city
        available_cities = sorted(df['Dropoff Location'].str.split(',').str[0].unique())
        search_city = st.text_input(
            "Search Drop City",
            help="Type to search for your delivery city"
        )

        # Filter cities based on search input
        filtered_cities = [city for city in available_cities if search_city.lower() in city.lower()] if search_city else available_cities

        # Show filtered cities in a selectbox
        selected_city = st.selectbox(
            "Select from available cities",
            options=filtered_cities,
            help="Choose your delivery city from the filtered list"
        )

        # Get full location (city, state) based on selected city
        selected_destination = df[df['Dropoff Location'].str.contains(selected_city, case=False)]['Dropoff Location'].iloc[0]

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

    if st.button("Calculate Route", type="primary"):
        with st.spinner("Processing route information..."):
            # Get route information
            route_info = df[df['Dropoff Location'] == selected_destination].iloc[0]
            states = route_info['States Along Route'].split(', ')

            # Calculate temperatures
            state_temps = calculate_avg_temp(states)
            avg_temp = np.mean(list(state_temps.values()))

            # Create columns for results
            result_col1, result_col2 = st.columns([1, 1])

            with result_col1:
                # Route Information in a styled container
                with st.container():
                    st.markdown("### 📍 Route Details")
                    st.markdown("""
                    <style>
                    .route-info {
                        padding: 20px;
                        border-radius: 10px;
                        background-color: #f0f2f6;
                        margin: 10px 0;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="route-info">', unsafe_allow_html=True)
                    st.markdown(f"""
                    🏁 **Origin:** Portland, Maine  
                    🎯 **Destination:** {selected_destination}  
                    📅 **Delivery Date:** {selected_date.strftime('%B %d, %Y')}
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)

                # Temperature Analysis
                st.markdown("### 🌡️ Temperature Analysis")
                with st.container():
                    for state, temp in state_temps.items():
                        st.markdown(f"**{state}:** {temp:.1f}°F")
                    st.markdown(f"**Overall Average:** {avg_temp:.1f}°F")

                # Truck Recommendation
                truck_type = recommend_truck_type(avg_temp)
                st.markdown("### 🚚 Recommendation")

                recommendation_color = "#28a745" if "Dry Truck" in truck_type else "#dc3545"
                st.markdown(
                    f"""
                    <div style='padding: 15px; border-radius: 5px; background-color: {recommendation_color}; color: white;'>
                        <strong>Recommended Truck Type:</strong><br>{truck_type}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with result_col2:
                st.markdown("### 🗺️ Route Visualization")
                # Create and display map
                if route_info['Polyline']:
                    try:
                        route_map = create_route_map(route_info['Polyline'])
                        folium_static(route_map, width=600)
                    except Exception as e:
                        st.error("Unable to display route map. Please try again.")
                else:
                    st.error("Route visualization not available for this destination")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.error("Please try again later or contact support if the problem persists.")

# Footer
st.markdown("---")
st.markdown("🚚 Logistics Route Planner - Helping you choose the right truck for your delivery")