# At the top of your app.py file, add:
import streamlit as st
import requests
import os
from streamlit_folium import folium_static

# Import your modules with the updated name
from modules.pv_calculator_api import get_weather_data, get_solar_position, calculate_pv_production
from modules.financial import financial_analysis, estimate_consumption_and_capacity, project_electricity_price
from modules.mapping import create_town_map, town_list

# Check weather data availability
def check_weather_data_connection():
    """Test if the weather data in Azure is accessible"""
    try:
        # Get the URL from secrets or use default if testing locally
        WEATHER_DATA_URL = st.secrets.get("WEATHER_DATA_URL", 
            "https://ethiopiasolardata2025.blob.core.windows.net/weatherdata/Ethiopia_Annual_2023.nc?sv=2024-11-04&ss=bfqt&srt=co&sp=rtfx&se=2026-03-28T01:25:46Z&st=2025-03-27T17:25:46Z&spr=https&sig=YQCX4s9gQHpXXCJYV3jT02OV8xBmAxjg%2F7x5SO96bLQ%3D")
        
        # Simple HEAD request to check if file exists
        response = requests.head(WEATHER_DATA_URL)
        return response.status_code == 200 or response.status_code == 302
    except Exception as e:
        return False

# In your main function, add:
def main():
    st.set_page_config(
        page_title="Ethiopia Solar PV Assessment Tool",
        page_icon="☀️",
        layout="wide",
    )
    
    # Check weather data connection
    weather_data_available = check_weather_data_connection()
    
    # Add CSS styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .subheader {
        font-size: 1.5rem;
        color: #424242;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-header">Ethiopia Solar PV Assessment Tool</p>', unsafe_allow_html=True)
    
    # Display weather data connection status
    if weather_data_available:
        st.success("✅ Connected to weather data service")
    else:
        st.error("❌ Weather data service not available. Some features may not work correctly.")
    
    # Rest of your app code continues...
    # Introductory information
    with st.expander("ℹ️ About this tool"):
        st.write("""
        This tool helps you assess the solar photovoltaic (PV) potential in Ethiopia. 
        It provides technical and financial analysis to help you make informed decisions about installing solar panels.
        
        ### How to use:
        1. Select a town from the dropdown menu
        2. Enter your financial information in the Financial Inputs section
        3. Calculate your recommended system size based on your electricity consumption
        4. Adjust roof parameters if needed (values will be pre-filled based on your system size)
        5. Click "Calculate PV Potential" to see detailed performance and financial results
        
        ### Data sources:
        - Weather data: ERA5 reanalysis dataset (2023)
        - Geographic data: Ethiopia administrative boundaries from CSA
        - Maps: OpenStreetMap,ESRI satelite,Google-earth satelite, Humanitarian OpenStreetMap, and Sentinel.
        - Electricity tariffs: Ethiopian Electric Utility (2024-2028)
        """)
    
    # Create tabs for different workflow stages
    tab1, tab2, tab3 = st.tabs(["📍 Location Selection", "🏠 financial and roof parameter Configuration", "💰 Results"])
    
    # Initialize session state to store variables between interactions
    if 'selected_town' not in st.session_state:
        st.session_state.selected_town = None
    if 'lat' not in st.session_state:
        st.session_state.lat = None
    if 'lon' not in st.session_state:
        st.session_state.lon = None
    if 'pv_results' not in st.session_state:
        st.session_state.pv_results = None
    if 'financial_results' not in st.session_state:
        st.session_state.financial_results = None
    if 'recommended_roof_area' not in st.session_state:
        st.session_state.recommended_roof_area = None
    if 'consumption_estimate' not in st.session_state:
        st.session_state.consumption_estimate = None
    # Add this line to initialize recommended_size
    if 'recommended_size' not in st.session_state:
        st.session_state.recommended_size = None
    # Tab 1: Location Selection
    # Tab 1: Location Selection and Information
    with tab1:
        st.markdown('<p class="subheader">Select Location</p>', unsafe_allow_html=True)
        
        # Town selection dropdown - no default selection
        selected_town = st.selectbox("Select Town", [""] + town_list, 
                                    index=0,  # No default selection (empty string is first option)
                                    help="Choose a town from the dropdown list")
        
        if selected_town:
            # Store in session state
            st.session_state.selected_town = selected_town
            
            # Generate map
            with st.spinner("Generating map..."):
                result = create_town_map(selected_town)
            
            if not result:
                st.error(f"Failed to process town: {selected_town}")
            else:
                m, lat, lon, buildings = result
                
                # Store coordinates in session state
                st.session_state.lat = lat
                st.session_state.lon = lon
                
                # Display map
                st.write(f"Map for {selected_town} (Lat: {lat:.4f}, Lon: {lon:.4f})")
                folium_static(m, width=800, height=500)
                
                # Create a point geometry for the selected location
                geometry = Point(lon, lat)
                
                # Display location information
                render_location_info(selected_town, lat, lon, geometry)
                
                st.success(f"Location set to {selected_town}")
                st.info("Now proceed to the 'Financial Inputs' tab to enter your electricity details")
        else:
            # Clear session state if no town is selected
            st.session_state.selected_town = None
            st.session_state.lat = None
            st.session_state.lon = None
            
            # Show a placeholder message
            st.info("Please select a town from the dropdown menu to see location information")
    # Tab 2: Roof Configuration
    # Tab 2: Roof Configuration
    with tab2:
        st.markdown('<p class="subheader">Roof Configuration</p>', unsafe_allow_html=True)
        
        if not st.session_state.selected_town:
            st.warning("Please select a town in the 'Location Selection' tab first")
        else:
            st.write(f"Setting up configuration for {st.session_state.selected_town}")
            
            # Create columns for financial inputs and system recommendation
            col1, col2 = st.columns(2)
            
            with col1:
                # Financial inputs section in left column
                st.subheader("Financial Inputs")
                
                # Customer type selection
                customer_type = st.selectbox(
                    "Customer Type",
                    options=["Residential", "Commercial", "Industrial (Low Voltage)", 
                             "Industrial (Medium Voltage)",  "Street Light"],
                    index=0,
                    help="Select your electricity customer category"
                )
                
                # Map selection to internal categories
                customer_type_map = {
                    "Residential": "residential",
                    "Commercial": "commercial", 
                    "Industrial (Low Voltage)": "industrial_lv",
                    "Industrial (Medium Voltage)": "industrial_mv",
                    "Industrial (High Voltage)": "industrial_hv",
                    "Street Light": "street_light"
                }
                customer_type_code = customer_type_map[customer_type]
                
                # For industrial customers, ask about demand charges
                peak_demand_kw = None
                if "Industrial" in customer_type:
                    st.info("Industrial tariffs include both energy charges and demand charges.")
                    
                    # Allow entering the monthly peak demand
                    peak_demand_kw = st.number_input(
                        "Monthly Peak Demand (kW)",
                        min_value=0.0,
                        max_value=10000.0,
                        value=100.0,
                        help="Your monthly peak power demand in kW (from your bill)"
                    )
                
                # Allow user to adjust cost per watt
                cost_per_watt = st.number_input(
                    "Installation Cost (ETB/watt)",
                    min_value=0.01,
                    max_value=500.0,
                    value=1.5,
                    step=0.1,
                    help="Total cost per watt including equipment and installation"
                )
                
                # Add monthly electricity bill input
                monthly_bill = st.number_input(
                    "Average Monthly Electricity Bill (ETB)",
                    min_value=0,
                    max_value=100000,
                    value=500,
                    help="Your current average monthly electricity bill in Ethiopian Birr"
                )
                
                # Option to enter electricity rate directly
                use_custom_price = 0
                # st.checkbox(
                #     "I know my electricity rate",
                #     value=False,
                #     help="Check this if you know your electricity price per kWh"
                # )
                
                if use_custom_price:
                    electricity_price = st.number_input(
                        "Electricity Price (ETB/kWh)",
                        min_value=0.01,
                        max_value=10.0,
                        value=2.50,
                        step=0.10,
                        help="Current electricity price per kilowatt-hour in Ethiopian Birr"
                    )
                else:
                    # Default electricity prices by customer type (ETB/kWh) - Updated to match tariff schedule
                    default_prices = {
                        "residential": 0.27,  # Base tier, will be adjusted below
                        "commercial": 2.12, 
                        "industrial_lv": 1.53,
                        "industrial_mv": 1.19,
                        "industrial_hv": 1.19,
                        "street_light": 2.12
                    }
                    
                    # For residential, estimate the appropriate tier based on monthly bill
                    if customer_type_code == "residential" and monthly_bill > 0:
                        # Very rough estimation of monthly consumption
                        est_monthly_consumption = monthly_bill / 2.0  # Assuming average rate of 2.0 ETB/kWh
                        
                        # Select appropriate tier based on estimated consumption
                        if est_monthly_consumption <= 50:
                            electricity_price = 0.27
                        elif est_monthly_consumption <= 100:
                            electricity_price = 0.77
                        elif est_monthly_consumption <= 200:
                            electricity_price = 1.63
                        elif est_monthly_consumption <= 300:
                            electricity_price = 2.00
                        elif est_monthly_consumption <= 400:
                            electricity_price = 2.20
                        elif est_monthly_consumption <= 500:
                            electricity_price = 2.41
                        else:
                            electricity_price = 2.48
                    else:
                        # Non-residential rates are flat
                        electricity_price = default_prices.get(customer_type_code, 2.50)
                    
                    # Option to estimate from bill (separate from tiered estimate)
                    use_bill_estimate = 0
                    # st.checkbox(
                    #     "Use bill-based electricity rate estimate (ignores official tariffs)",
                    #     value=False
                    # )
                    
                    if use_bill_estimate and monthly_bill > 0:
                        try:
                            # Get estimate without using custom price
                            consumption_estimate = estimate_consumption_and_capacity(
                                monthly_bill, 
                                customer_type=customer_type_code,
                                peak_demand_kw=peak_demand_kw
                            )
                            
                            # Use the estimated price
                            electricity_price = consumption_estimate['average_electricity_price_etb']
                        except Exception as e:
                            st.warning(f"Could not estimate electricity price: {str(e)}")
                    
                    st.info(f"Using electricity rate: {electricity_price:.4f} ETB/kWh for {customer_type}")
                
                # # # Add a calculate button
                # calculate_button = st.button("Calculate System Size Recommendation")
            
            with col2:
                # System size recommendation in right column
                st.subheader("System Size Recommendation")
                
                # Display calculation results if available or if calculate button was pressed
                if 'consumption_estimate' in st.session_state:
                    with st.spinner("Calculating recommended system size..."):
                        try:
                            # Calculate estimated consumption and recommended capacity
                            if use_custom_price:
                                consumption_estimate = estimate_consumption_and_capacity(
                                    monthly_bill, 
                                    customer_type=customer_type_code,
                                    electricity_price=electricity_price,
                                    peak_demand_kw=peak_demand_kw
                                )
                            else:
                                consumption_estimate = estimate_consumption_and_capacity(
                                    monthly_bill,
                                    customer_type=customer_type_code,
                                    peak_demand_kw=peak_demand_kw
                                )
                            
                            # Store in session state
                            st.session_state.consumption_estimate = consumption_estimate
                            
                            # Display results in metrics
                            st.metric(
                                "Estimated Monthly Consumption", 
                                f"{consumption_estimate['estimated_monthly_consumption_kwh']:.0f} kWh"
                            )
                            st.metric(
                                "Average Electricity Price", 
                                f"{consumption_estimate['average_electricity_price_etb']:.2f} ETB/kWh"
                            )
                            st.metric(
                                "Recommended System Size", 
                                f"{consumption_estimate['recommended_capacity_kw']:.1f} kWp"
                            )
                            
                            # Calculate required roof area
                            panel_efficiency_decimal = 20 / 100  # Default 20%
                            panel_area = PANEL_WIDTH * PANEL_HEIGHT
                            panel_power = panel_area * 1000 * panel_efficiency_decimal
                            num_panels_needed = np.ceil(consumption_estimate['recommended_capacity_kw'] * 1000 / panel_power)
                            panel_spacing_area = panel_area * (1 + SPACING_FACTOR)
                            required_area = num_panels_needed * panel_spacing_area
                            
                            # Store in session state
                            st.session_state.recommended_roof_area = int(required_area)
                            st.session_state.recommended_size = consumption_estimate['recommended_capacity_kw']
                            
                            st.metric(
                                "Recommended Roof Area", 
                                f"{st.session_state.recommended_roof_area:.0f} m²"
                            )
                            
                        except Exception as e:
                            st.error(f"Error in calculation: {str(e)}")
                else:
                    st.info("Enter your financial details and click 'Calculate System Size Recommendation' to get a personalized recommendation.")
            
            # Add roof parameters section below both columns
            st.markdown("---")
            st.subheader("Roof Parameters")
            
            # Use the recommended value if it exists, otherwise use 100 as default
            default_roof_area = st.session_state.recommended_roof_area if st.session_state.recommended_roof_area is not None else 100
            
            # Create two columns for roof parameters
            roof_col1, roof_col2 = st.columns(2)
            
            with roof_col1:
                roof_area = st.number_input("Roof Area (sq. meters)", 
                                          min_value=10, max_value=1000, value=default_roof_area,
                                          help="Total available roof area for solar panels")
                roof_tilt = st.slider("Roof Tilt (degrees)", 
                                    min_value=0, max_value=60, value=15,
                                    help="Angle of the roof from horizontal")
                
                roof_azimuth = st.slider("Roof Azimuth (degrees)", 
                                       min_value=0, max_value=360, value=180,
                                       help="Direction the roof faces: 0=North, 90=East, 180=South, 270=West")
                
            with roof_col2:
                system_losses = st.slider("System Losses (%)", 
                                        min_value=10, max_value=30, value=14,
                                        help="Includes wiring losses, inverter losses, soiling, etc.")
                 
                panel_efficiency = st.slider("Panel Efficiency (%)", 
                                          min_value=15, max_value=23, value=20,
                                          help="Higher efficiency panels produce more power but cost more")
            
                # Show recommended size if available
                if st.session_state.recommended_size is not None:
                    st.success(f"Using recommended system size: {st.session_state.recommended_size:.1f} kWp (requires approximately {st.session_state.recommended_roof_area} m²)")
            
            # Calculate button
            if st.button("Calculate PV Potential", type="primary"):
                # Ensure we have financial inputs
                if 'consumption_estimate' not in st.session_state or st.session_state.consumption_estimate is None:
                    st.warning("Please complete the Financial Inputs tab first to get a system recommendation")
                    st.stop()
                
                with st.spinner("Calculating solar potential..."):
                    try:
                        # Get financial inputs from session state
                        consumption_estimate = st.session_state.consumption_estimate
                        customer_type_code = consumption_estimate.get('customer_type', 'residential')
                        electricity_price = consumption_estimate.get('average_electricity_price_etb', 2.50)
                        monthly_bill = consumption_estimate.get('monthly_bill', 500)
                        
                        # Get weather data
                        weather_df = get_weather_data(st.session_state.lat, st.session_state.lon)
                        
                        # Run calculations
                        weather_with_solar = get_solar_position(st.session_state.lat, 
                                                             st.session_state.lon, 
                                                             weather_df)
                        
                        pv_results = calculate_pv_production(
                            weather_with_solar,
                            roof_area,
                            efficiency=panel_efficiency/100,  # Convert to decimal
                            system_losses=system_losses/100,  # Convert to decimal
                            tilt=roof_tilt,
                            azimuth=roof_azimuth,
                            panel_width=PANEL_WIDTH,
                            panel_height=PANEL_HEIGHT,
                            spacing_factor=SPACING_FACTOR
                        )
                        
                        # Calculate how much of user's consumption will be covered
                        annual_energy = pv_results['annual_energy_kwh']
                        annual_consumption = consumption_estimate['estimated_yearly_consumption_kwh']
                        coverage_ratio = min(1.0, annual_energy / annual_consumption) if annual_consumption > 0 else 0
                        
                        # Add to results
                        pv_results['estimated_annual_consumption_kwh'] = annual_consumption
                        pv_results['consumption_coverage_ratio'] = coverage_ratio
                        pv_results['estimated_monthly_bill_etb'] = monthly_bill
                        
                        # Convert electricity price from ETB to USD for financial analysis
                        electricity_price_usd = electricity_price / CURRENCY_CONVERSION_RATE
                        
                        # Pass the user-specified financial parameters to the analysis function
                        financial_results = financial_analysis(
                            pv_results,
                            cost_per_watt=cost_per_watt/130,
                            electricity_price=electricity_price_usd,
                            customer_type=customer_type_code,  # Pass the customer type for tariff projection
                            current_year_quarter=(CURRENT_YEAR, CURRENT_QUARTER),  # Current year and quarter
                            annual_price_increase=0.03,  # Used for scenarios and fallback
                            lifetime=25,
                            discount_rate=0.06,
                            currency_conversion_rate=CURRENCY_CONVERSION_RATE
                        )
                        
                        # Add bill comparison if monthly bill is provided
                        if monthly_bill > 0:
                            yearly_bill = monthly_bill * 12
                            yearly_bill_usd = yearly_bill / CURRENCY_CONVERSION_RATE
                            yearly_savings_usd = financial_results['annual_savings_first_year_usd']
                            bill_offset_percent = min(100, (yearly_savings_usd / yearly_bill_usd * 100)) if yearly_bill_usd > 0 else 0
                            
                            # Store the additional metrics in financial results
                            financial_results['yearly_bill_usd'] = yearly_bill_usd
                            financial_results['yearly_bill_etb'] = yearly_bill
                            financial_results['bill_offset_percent'] = bill_offset_percent
                        
                        # Store results in session state
                        st.session_state.pv_results = pv_results
                        st.session_state.financial_results = financial_results
                        
                        # Auto-navigate to results tab
                        st.success("Calculation complete! View results in the 'Results' tab.")
                        # Use the improved tab navigation
                        st.markdown('<script>window.parent.document.querySelectorAll("button[role=\'tab\']")[3].click();</script>', unsafe_allow_html=True)
                        # st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error in calculation: {str(e)}")
                        import traceback
                        st.write(traceback.format_exc())
   # Tab 3: Results
    with tab3:
        st.markdown('<p class="subheader">Assessment Results</p>', unsafe_allow_html=True)
        
        if 'pv_results' not in st.session_state or st.session_state.pv_results is None:
            st.warning("No results available. Please complete the steps in the previous tabs.")
        else:
            try:
                # Get the data
                pv_results = st.session_state.pv_results
                financial_results = st.session_state.financial_results
                
                # Technical Results Section
                st.markdown("### Technical Assessment")
                
                # Create nice metric displays
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("System Capacity", f"{pv_results['system_capacity_kw']:.1f} kWp")
                with col2:
                    st.metric("Annual Production", f"{pv_results['annual_energy_kwh']:.0f} kWh")
                with col3:
                    st.metric("Avg Daily Production", f"{pv_results['avg_daily_production_kwh']:.1f} kWh")
                with col4:
                    st.metric("Capacity Factor", f"{pv_results['capacity_factor']:.1f}%")
                
                # Monthly production chart
                if 'monthly_energy_kwh' in pv_results:
                    try:
                        monthly_data = pv_results['monthly_energy_kwh']
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        
                        # For dictionary type (timestamp keys)
                        if isinstance(monthly_data, dict):
                            # Sort by timestamp
                            sorted_months = sorted(monthly_data.keys())
                            values = [monthly_data[m] for m in sorted_months]
                            
                            # Create DataFrame for plotting
                            chart_data = pd.DataFrame({
                                'Month': months,
                                'Energy (kWh)': values
                            })
                            
                            # Display chart
                            st.subheader("Monthly Energy Production")
                            st.bar_chart(chart_data.set_index('Month'))
                            
                        # For pandas Series or other types
                        else:
                            st.subheader("Monthly Energy Production")
                            st.bar_chart(monthly_data)
                            
                    except Exception as e:
                        st.warning(f"Could not display monthly chart: {str(e)}")
                
                # Financial Results Section
                st.markdown("### Financial Assessment")
                
                # Financial metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Investment Cost", format_currency(financial_results['investment_etb'], "ETB"))
                with col2:
                    st.metric("Annual Savings", format_currency(financial_results['annual_savings_first_year_etb'], "ETB"))
                with col3:
                    st.metric("Payback Period", f"{financial_results['payback_period_years']:.1f} years")
                with col4:
                    st.metric("LCOE", f"{financial_results['lcoe_etb_per_kwh']:.3f} ETB/kWh")
                
                # Cash flow visualization
                if 'cumulative_cash_flow_etb' in financial_results:
                    years = list(range(len(financial_results['cumulative_cash_flow_etb'])))
                    
                    # Create cash flow chart
                    cashflow_data = pd.DataFrame({
                        'Year': years,
                        'Cumulative Cash Flow (ETB)': financial_results['cumulative_cash_flow_etb']
                    })
                    
                    st.subheader("Cumulative Cash Flow")
                    st.line_chart(cashflow_data.set_index('Year'))
                
                # [TARIFF VISUALIZATION STARTS HERE] - ADD THE FOLLOWING CODE HERE
                # Display electricity price trends
                if 'electricity_prices' in financial_results:
                    st.subheader("Electricity Price Trends")
                    st.write("The financial analysis accounts for scheduled electricity tariff increases.")
                    
                    yearly_prices = financial_results['electricity_prices']['yearly_prices_etb']
                    yearly_savings = [s * CURRENCY_CONVERSION_RATE for s in financial_results['electricity_prices']['yearly_savings_usd']]
                    
                    # Create DataFrame for plotting electricity price trends
                    years = list(range(1, len(yearly_prices) + 1))
                    
                    price_data = pd.DataFrame({
                        'Year': years,
                        'Electricity Price (ETB/kWh)': yearly_prices,
                        'Annual Savings (ETB)': yearly_savings
                    })
                    
                    # Plot electricity price trend
                    st.write("**Projected Electricity Prices**")
                    st.line_chart(price_data.set_index('Year')['Electricity Price (ETB/kWh)'])
                    
                    # Plot annual savings over time
                    st.write("**Projected Annual Savings**")
                    st.line_chart(price_data.set_index('Year')['Annual Savings (ETB)'])
                    
                    # Create a table with the data
                    with st.expander("View Detailed Price and Savings Projection"):
                        price_data['Year'] = [f"Year {i}" for i in price_data['Year']]
                        st.table(price_data.set_index('Year'))
                # [TARIFF VISUALIZATION ENDS HERE]
                
                # Additional financial metrics
                st.markdown("### Additional Financial Metrics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Return on Investment (ROI)", f"{financial_results['roi_percent']:.1f}%")
                    if 'npv_etb' in financial_results:
                        st.metric("Net Present Value (NPV)", format_currency(financial_results['npv_etb'], "ETB"))
                with col2:
                    if 'cumulative_savings_etb' in financial_results:
                        st.metric("Lifetime Savings", format_currency(financial_results['cumulative_savings_etb'], "ETB"))
            
                # Bill comparison section (if bill data is available)
                if 'yearly_bill_etb' in financial_results:
                    st.markdown("### Electricity Bill Comparison")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Current Annual Electricity Bill", 
                            format_currency(financial_results['yearly_bill_etb'], "ETB")
                        )
                        st.metric(
                            "First Year Savings", 
                            format_currency(financial_results['annual_savings_first_year_etb'], "ETB")
                        )
                    
                    with col2:
                        st.metric(
                            "Bill Offset", 
                            f"{financial_results['bill_offset_percent']:.1f}%"
                        )
                        
                        # Calculate monthly savings
                        monthly_savings = financial_results['annual_savings_first_year_etb'] / 12
                        st.metric(
                            "Average Monthly Savings",
                            format_currency(monthly_savings, "ETB")
                        )
                    
            #         # Add a visualization comparing before and after
            #         st.subheader("Before vs After Solar Installation")
            #         bill_data = {
            #             'Scenario': ['Without Solar', 'With Solar'],
            #             'Annual Cost (ETB)': [
            #                 financial_results['yearly_bill_etb'],
            #                 max(0, financial_results['yearly_bill_etb'] - financial_results['annual_savings_first_year_etb'])
            #             ]
            #         }
            #         bill_df = pd.DataFrame(bill_data)
            #         st.bar_chart(bill_df.set_index('Scenario'))
                
            #     # Consumption analysis (if available)
            #     if 'estimated_annual_consumption_kwh' in pv_results:
            #         st.markdown("### Consumption Analysis")
                    
            #         col1, col2 = st.columns(2)
            #         with col1:
            #             st.metric(
            #                 "Yearly Consumption", 
            #                 f"{pv_results['estimated_annual_consumption_kwh']:.0f} kWh"
            #             )
            #             st.metric(
            #                 "PV Production", 
            #                 f"{pv_results['annual_energy_kwh']:.0f} kWh"
            #             )
                    
            #         with col2:
            #             st.metric(
            #                 "Consumption Coverage", 
            #                 f"{pv_results['consumption_coverage_ratio']*100:.1f}%"
            #             )
            #             st.metric(
            #                 "Monthly Bill", 
            #                 f"{pv_results['estimated_monthly_bill_etb']:.0f} ETB"
            #             )
                    
            #         # Visualization of consumption vs production
            #         st.subheader("Consumption vs Production")
            #         comparison_data = {
            #             'Category': ['Consumption', 'Production'],
            #             'Energy (kWh/year)': [
            #                 pv_results['estimated_annual_consumption_kwh'],
            #                 pv_results['annual_energy_kwh']
            #             ]
            #         }
            #         comparison_df = pd.DataFrame(comparison_data)
            #         st.bar_chart(comparison_df.set_index('Category'))
            
            except Exception as e:
                st.error(f"Error displaying results: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
