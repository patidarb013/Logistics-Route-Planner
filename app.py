import time
import json
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
from utils import (
    load_route_data, get_available_dates, calculate_avg_temp,
    recommend_truck_type
)

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Logistics Route Planner",
    page_icon="🚛",
    layout="wide"
) 


# Load environment variables
load_dotenv()

# Google Maps API Key from environment variable
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Validate API key
if not GOOGLE_MAPS_API_KEY:
    st.error("⚠️ Google Maps API key is not set. Please add your API key to the .env file.")
    st.info("To get a Google Maps API key:\n1. Go to https://console.cloud.google.com/\n2. Create a project\n3. Enable Maps JavaScript API, Directions API, and Geocoding API\n4. Create credentials (API key)\n5. Add the key to your .env file")

# Title and description
st.title("🚛 Logistics Route Planner")
st.markdown("Plan your route from Portland, Maine and get truck recommendations based on temperature.")

# Initialize session state for tracking savings
if 'total_savings' not in st.session_state:
    st.session_state.total_savings = 0
if 'savings_history' not in st.session_state:
    st.session_state.savings_history = []

try:
    # Load route data
    df = load_route_data()

    # Add a sidebar section for savings overview
    with st.sidebar:
        st.markdown("### 💰 Savings Overview")
        st.markdown(f"**Total Savings:** ${st.session_state.total_savings:,.2f}")
        if st.session_state.savings_history:
            st.markdown("#### Recent Savings")
            for entry in st.session_state.savings_history[-5:]:  # Show last 5 entries
                st.markdown(f"- {entry['city']}: ${entry['savings']:,.2f}")

    # Debug info
    st.sidebar.write("Debug Info:")
    st.sidebar.write("Available columns:", df.columns.tolist())
    
    # Show available cities
    st.sidebar.write("Available Cities:")
    available_cities = sorted(df['Drop City'].unique().tolist())
    for city in available_cities:
        st.sidebar.write(f"- {city}")

    # Create two columns for input
    col1, col2 = st.columns(2)

    with col1:
        # Simple text input for DROP CITY
        search_city = st.text_input(
            "Enter DROP CITY",
            help="Type your delivery city name"
        )

        if search_city:
            # Filter destinations based on the entered city
            matches = df[df['Drop City'].str.contains(search_city, case=False)]
            if matches.empty:
                st.error("No matching cities found. Please try a different city name.")
                selected_destination = None
            else:
                selected_destination = matches.iloc[0]
                st.success(f"Found destination: {selected_destination['Drop City']}, {selected_destination['Drop State']}")
        else:
            selected_destination = None

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

    # Move the calculate route button here, right after the input fields
    if selected_destination is not None and st.button("Calculate Route", type="primary"):
        with st.spinner("Processing route information..."):
            # Get route information
            states = selected_destination['States Along Route'].split(', ')

            # ✅ Calculate temperatures (in order)
            state_temps = calculate_avg_temp(states, selected_date.strftime('%Y-%m-%d'))
            avg_temp = np.mean([data['avg_temp'] for data in state_temps.values()])

            # ✅ Create columns for results
            result_col1, result_col2 = st.columns([1, 1])

            with result_col1:
                # ✅ Route Information
                with st.container():
                    st.markdown(f"""
                        ### 📍 Route Details
                        - 🏁 **Origin:** Portland, Maine  
                        - 🎯 **Destination:** {selected_destination['Drop City']}, {selected_destination['Drop State']}  
                        - 📅 **Delivery Date:** {selected_date.strftime('%B %d, %Y')}
                        """)

                # ✅ Truck Recommendation
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

                # ✅ Temperature Analysis Heading
                st.markdown("## 🌡️ Temperature Analysis")

                # ✅ State Temperatures Heading
                st.markdown("### State Temperatures:")
                
                # ✅ Create a DataFrame for temperatures
                temp_data = {
                    'State': list(state_temps.keys()),
                    'Min Temp (°F)': [data['min_temp'] for data in state_temps.values()],
                    'Max Temp (°F)': [data['max_temp'] for data in state_temps.values()],
                    'Avg Temp (°F)': [data['avg_temp'] for data in state_temps.values()],
                }
                temp_df = pd.DataFrame(temp_data)

                # ✅ Display table
                st.dataframe(temp_df, hide_index=True)

                # ✅ Overall Average Temperature Heading
                st.markdown("### Overall Average Temperature:")
                st.write(f"**Overall average temperature across all states on the route:** {avg_temp:.1f}°F")

                # Add Route Analysis Section
                st.markdown("### 📊 Route Analysis")
                
                # Calculate route statistics
                route_length = len(states)
                temp_variation = max([data['max_temp'] for data in state_temps.values()]) - min([data['min_temp'] for data in state_temps.values()])
                
                # Create route analysis box
                st.markdown(
                    f"""
                    <div style='padding: 15px; border-radius: 5px; background-color: #6c757d; color: white;'>
                        <strong>Route Statistics:</strong><br>
                        - Number of States: {route_length}<br>
                        - Temperature Range: {temp_variation:.1f}°F<br>
                        - Temperature Stability: {'High' if temp_variation < 20 else 'Medium' if temp_variation < 40 else 'Low'}<br>
                        - Route Complexity: {'Simple' if route_length <= 3 else 'Moderate' if route_length <= 5 else 'Complex'}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Add Route Recommendations
                st.markdown("### 💡 Route Recommendations")
                recommendations = []
                
                if temp_variation > 40:
                    recommendations.append("⚠️ High temperature variation detected. Consider additional cargo protection measures.")
                if route_length > 5:
                    recommendations.append("⚠️ Complex route with multiple states. Plan for additional fuel stops.")
                if avg_temp < 32:
                    recommendations.append("⚠️ Freezing temperatures possible. Ensure cargo is properly insulated.")
                if avg_temp > 85:
                    recommendations.append("⚠️ High temperatures expected. Monitor cargo temperature closely.")
                
                if recommendations:
                    for rec in recommendations:
                        st.markdown(f"- {rec}")
                else:
                    st.markdown("✅ No special recommendations needed for this route.")

            with result_col2:
                st.markdown("### 🗺️ Route Visualization")

                # ✅ Generate Google Maps URL using Pickup and Drop City
                def generate_google_maps_url(pickup_city, drop_city):
                    if not GOOGLE_MAPS_API_KEY:
                        return None
                    # URL encode the cities
                    pickup_city = pickup_city.replace(" ", "+")
                    drop_city = drop_city.replace(" ", "+")
                    return f"""
                    <iframe
                        width="100%"
                        height="500"
                        frameborder="0"
                        style="border:0"
                        src="https://www.google.com/maps/embed/v1/directions?key={GOOGLE_MAPS_API_KEY}&origin={pickup_city}&destination={drop_city}&mode=driving"
                        allowfullscreen>
                    </iframe>
                    """

                pickup_city = "Portland, Maine"
                drop_city = f"{selected_destination['Drop City']}, {selected_destination['Drop State']}"

                try:
                    if not GOOGLE_MAPS_API_KEY:
                        st.warning("Google Maps visualization is disabled. Please add your API key to the .env file.")
                    else:
                        google_maps_html = generate_google_maps_url(pickup_city, drop_city)
                        if google_maps_html:
                            components.html(google_maps_html, height=500)
                        else:
                            st.error("Unable to generate map URL. Please check your API key.")
                except Exception as e:
                    st.error(f"Unable to display route map: {str(e)}")
                    st.write("Please try a different destination or contact support if the issue persists.")

                # Calculate and display cost savings
                if 'Linehaul/ Shipment' in selected_destination:
                    total_cost = float(selected_destination['Linehaul/ Shipment'])
                    # Assuming Reefer truck costs 40% more than Dry truck
                    reefer_cost = total_cost * 1.40
                    dry_cost = total_cost
                    
                    # Calculate savings based on recommended truck type
                    if "Dry Truck" in truck_type:
                        savings = reefer_cost - dry_cost
                        savings_percentage = (savings / reefer_cost) * 100
                        
                        # Update session state with new savings
                        st.session_state.total_savings += savings
                        st.session_state.savings_history.append({
                            'city': selected_destination['Drop City'],
                            'savings': savings,
                            'date': selected_date.strftime('%Y-%m-%d')
                        })
                    else:
                        savings = 0
                        savings_percentage = 0
                    
                    st.markdown("### 💰 Cost Savings Analysis")
                    st.markdown(
                        f"""
                        <div style='padding: 15px; border-radius: 5px; background-color: #007bff; color: white;'>
                            <strong>Cost Analysis:</strong><br>
                            <strong>Reefer Truck Cost:</strong> ${reefer_cost:,.2f}<br>
                            <strong>Dry Truck Cost:</strong> ${dry_cost:,.2f}<br>
                            <strong>Recommended Truck:</strong> {truck_type}<br>
                            <strong>Cost Savings:</strong> ${savings:,.2f} ({savings_percentage:.1f}% savings)
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Add explanation of savings
                    if "Dry Truck" in truck_type:
                        st.markdown(
                            f"""
                            <div style='padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
                                <strong>Smart Route Planning Savings:</strong><br>
                                By using our temperature-based model, we recommend a Dry Truck instead of a Reefer Truck 
                                for this route. This saves you ${savings:,.2f} on this shipment while maintaining cargo safety.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    # Move date comparison here, after the calculate route button
    if selected_destination is not None:
        st.markdown("### 📅 Date Comparison")
        comparison_dates = [selected_date + timedelta(days=x) for x in range(1, 4)]
        comparison_data = []
        
        try:
            # Convert available_dates[-1] to date object for comparison
            max_date = available_dates[-1].date() if isinstance(available_dates[-1], datetime) else available_dates[-1]
            
            for date in comparison_dates:
                if date <= max_date:
                    states = selected_destination['States Along Route'].split(', ')
                    temps = calculate_avg_temp(states, date.strftime('%Y-%m-%d'))
                    avg_temp = np.mean([data['avg_temp'] for data in temps.values()])
                    comparison_data.append({
                        'date': date.strftime('%B %d, %Y'),  # Convert to string format
                        'avg_temp': avg_temp,
                        'truck_type': recommend_truck_type(avg_temp)
                    })
            
            if comparison_data:
                comparison_df = pd.DataFrame(comparison_data)
                st.markdown("**Temperature and Truck Type by Date:**")
                st.dataframe(comparison_df, hide_index=True)
                
                # Find optimal date (closest to 50°F)
                optimal_date = min(comparison_data, key=lambda x: abs(x['avg_temp'] - 50))
                st.markdown(
                    f"""
                    <div style='padding: 10px; border-radius: 5px; background-color: #28a745; color: white;'>
                        <strong>Optimal Delivery Date:</strong><br>
                        {optimal_date['date']} - {optimal_date['avg_temp']:.1f}°F
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.warning("No valid dates available for comparison. Please select a different date range.")
        except Exception as e:
            st.warning("Unable to generate date comparison. Please try a different date.")
            st.write("Debug info:", str(e))

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.error("Please try again later or contact support if the problem persists.")

# Footer
st.markdown("---")
st.markdown("🚚 Logistics Route Planner - Helping you choose the right truck for your delivery")
 