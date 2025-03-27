# -*- coding: utf-8 -*-
"""
Created on Sat Mar 15 16:39:43 2025

@author: kumab
"""

import numpy as np

def project_electricity_price(customer_type, current_year_quarter, base_price, years=25):
    """
    Projects electricity prices based on the official tariff schedule and beyond
    
    Parameters:
    -----------
    customer_type : str
        Type of customer (residential, commercial, etc.)
    current_year_quarter : tuple
        (year, quarter) tuple indicating the starting point (e.g., (2024, 1))
    base_price : float
        Current electricity price in ETB/kWh
    years : int
        Number of years to project
        
    Returns:
    --------
    list
        Yearly average electricity prices for the specified period
    """
    # Official tariff schedule (2024-2028) as per the provided table
    # Note: The first quarter entries are for 2024/25 Q1, not for current tariff
    tariff_schedule = {
        "residential": {
            # Residential is complicated because it's tiered. We'll use the middle tier (101-200 kWh) as default
            "base": 1.63,  # Current tariff for middle tier (101-200 kWh)
            "tier1": {  # 0-50 kWh
                "base": 0.27,  # Current tariff
                "increases": {
                    (2024, 1): 0.35, (2024, 2): 0.43, (2024, 3): 0.52, (2024, 4): 0.60,
                    (2025, 1): 0.68, (2025, 2): 0.76, (2025, 3): 0.84, (2025, 4): 0.92,
                    (2026, 1): 1.00, (2026, 2): 1.08, (2026, 3): 1.16, (2026, 4): 1.24,
                    (2027, 1): 1.32, (2027, 2): 1.40, (2027, 3): 1.48, (2027, 4): 1.56
                }
            },
            "tier2": {  # 51-100 kWh
                "base": 0.77,  # Current tariff
                "increases": {
                    (2024, 1): 0.95, (2024, 2): 1.13, (2024, 3): 1.31, (2024, 4): 1.49,
                    (2025, 1): 1.67, (2025, 2): 1.85, (2025, 3): 2.03, (2025, 4): 2.21,
                    (2026, 1): 2.39, (2026, 2): 2.57, (2026, 3): 2.76, (2026, 4): 2.94,
                    (2027, 1): 3.12, (2027, 2): 3.30, (2027, 3): 3.48, (2027, 4): 3.66
                }
            },
            "tier3": {  # 101-200 kWh
                "base": 1.63,  # Current tariff
                "increases": {
                    (2024, 1): 1.89, (2024, 2): 2.15, (2024, 3): 2.41, (2024, 4): 2.67,
                    (2025, 1): 2.93, (2025, 2): 3.19, (2025, 3): 3.45, (2025, 4): 3.72,
                    (2026, 1): 3.98, (2026, 2): 4.24, (2026, 3): 4.50, (2026, 4): 4.76,
                    (2027, 1): 5.02, (2027, 2): 5.28, (2027, 3): 5.55, (2027, 4): 5.81
                }
            },
            "tier4": {  # 201-300 kWh
                "base": 2.00,  # Current tariff
                "increases": {
                    (2024, 1): 2.46, (2024, 2): 2.92, (2024, 3): 3.38, (2024, 4): 3.84,
                    (2025, 1): 4.30, (2025, 2): 4.76, (2025, 3): 5.22, (2025, 4): 5.68,
                    (2026, 1): 6.14, (2026, 2): 6.60, (2026, 3): 7.06, (2026, 4): 7.52,
                    (2027, 1): 7.98, (2027, 2): 8.44, (2027, 3): 8.89, (2027, 4): 9.35
                }
            },
            "tier5": {  # 301-400 kWh
                "base": 2.20,  # Current tariff
                "increases": {
                    (2024, 1): 2.66, (2024, 2): 3.12, (2024, 3): 3.57, (2024, 4): 4.03,
                    (2025, 1): 4.49, (2025, 2): 4.95, (2025, 3): 5.41, (2025, 4): 5.86,
                    (2026, 1): 6.32, (2026, 2): 6.78, (2026, 3): 7.24, (2026, 4): 7.70,
                    (2027, 1): 8.15, (2027, 2): 8.61, (2027, 3): 9.07, (2027, 4): 9.53
                }
            },
            "tier6": {  # 401-500 kWh
                "base": 2.41,  # Current tariff
                "increases": {
                    (2024, 1): 2.85, (2024, 2): 3.29, (2024, 3): 3.73, (2024, 4): 4.17,
                    (2025, 1): 4.62, (2025, 2): 5.06, (2025, 3): 5.50, (2025, 4): 5.94,
                    (2026, 1): 6.39, (2026, 2): 6.83, (2026, 3): 7.27, (2026, 4): 7.71,
                    (2027, 1): 8.16, (2027, 2): 8.60, (2027, 3): 9.04, (2027, 4): 9.48
                }
            },
            "tier7": {  # Above 500 kWh
                "base": 2.48,  # Current tariff
                "increases": {
                    (2024, 1): 2.92, (2024, 2): 3.35, (2024, 3): 3.79, (2024, 4): 4.23,
                    (2025, 1): 4.66, (2025, 2): 5.10, (2025, 3): 5.54, (2025, 4): 5.97,
                    (2026, 1): 6.41, (2026, 2): 6.84, (2026, 3): 7.28, (2026, 4): 7.72,
                    (2027, 1): 8.15, (2027, 2): 8.59, (2027, 3): 9.03, (2027, 4): 9.46
                }
            },
            # For projections, we'll use the middle tier (tier3) increases as default
            "increases": {
                (2024, 1): 1.89, (2024, 2): 2.15, (2024, 3): 2.41, (2024, 4): 2.67,
                (2025, 1): 2.93, (2025, 2): 3.19, (2025, 3): 3.45, (2025, 4): 3.72,
                (2026, 1): 3.98, (2026, 2): 4.24, (2026, 3): 4.50, (2026, 4): 4.76,
                (2027, 1): 5.02, (2027, 2): 5.28, (2027, 3): 5.55, (2027, 4): 5.81
            }
        },
        "commercial": {
            "base": 2.12,  # Current tariff
            "increases": {
                (2024, 1): 2.61, (2024, 2): 3.09, (2024, 3): 3.57, (2024, 4): 4.05,
                (2025, 1): 4.53, (2025, 2): 5.01, (2025, 3): 5.50, (2025, 4): 5.98,
                (2026, 1): 6.46, (2026, 2): 6.94, (2026, 3): 7.42, (2026, 4): 7.90,
                (2027, 1): 8.39, (2027, 2): 8.87, (2027, 3): 9.35, (2027, 4): 9.83
            }
        },
        "industrial_lv": {  # Light Industry
            "base": 1.53,  # Current tariff
            "increases": {
                (2024, 1): 1.76, (2024, 2): 2.02, (2024, 3): 2.29, (2024, 4): 2.56,
                (2025, 1): 2.82, (2025, 2): 3.09, (2025, 3): 3.36, (2025, 4): 3.62,
                (2026, 1): 3.88, (2026, 2): 4.15, (2026, 3): 4.41, (2026, 4): 4.68,
                (2027, 1): 4.93, (2027, 2): 5.20, (2027, 3): 5.46, (2027, 4): 5.73
            }
        },
        "industrial_mv": {  # Medium Industry
            "base": 1.19,  # Current tariff
            "increases": {
                (2024, 1): 1.39, (2024, 2): 1.61, (2024, 3): 1.83, (2024, 4): 2.05,
                (2025, 1): 2.27, (2025, 2): 2.49, (2025, 3): 2.71, (2025, 4): 2.94,
                (2026, 1): 3.16, (2026, 2): 3.38, (2026, 3): 3.60, (2026, 4): 3.82,
                (2027, 1): 4.04, (2027, 2): 4.26, (2027, 3): 4.48, (2027, 4): 4.70
            }
        },
        "industrial_hv": {  # High Voltage Industry - assume same as medium for now
            "base": 1.19,  # Current tariff (same as medium industry)
            "increases": {
                (2024, 1): 1.39, (2024, 2): 1.61, (2024, 3): 1.83, (2024, 4): 2.05,
                (2025, 1): 2.27, (2025, 2): 2.49, (2025, 3): 2.71, (2025, 4): 2.94,
                (2026, 1): 3.16, (2026, 2): 3.38, (2026, 3): 3.60, (2026, 4): 3.82,
                (2027, 1): 4.04, (2027, 2): 4.26, (2027, 3): 4.48, (2027, 4): 4.70
            }
        },
        "street_light": {
            "base": 2.12,  # Current tariff
            "increases": {
                (2024, 1): 0.35, (2024, 2): 0.43, (2024, 3): 0.52, (2024, 4): 0.60,
                (2025, 1): 0.68, (2025, 2): 0.76, (2025, 3): 0.84, (2025, 4): 0.92,
                (2026, 1): 1.00, (2026, 2): 1.08, (2026, 3): 1.16, (2026, 4): 1.24,
                (2027, 1): 1.32, (2027, 2): 1.40, (2027, 3): 1.48, (2027, 4): 1.56
            }
        }
    }
    
    # For residential customers, adjust base_price based on consumption level if possible
    if customer_type == "residential":
        # If base_price is provided, try to determine which tier it falls into
        if base_price is not None and base_price > 0:
            # Find the closest matching tier
            diffs = [abs(base_price - tariff_schedule["residential"][f"tier{i}"]["base"]) 
                    for i in range(1, 8)]
            closest_tier = diffs.index(min(diffs)) + 1
            
            # Use the increases from that tier
            tier_increases = tariff_schedule["residential"][f"tier{closest_tier}"]["increases"]
            tariff_schedule["residential"]["increases"] = tier_increases
    
    # Initialize result with the current price
    result = []
    
    # Use customer type data if available, otherwise use standard increase rate
    if customer_type in tariff_schedule:
        tariff_data = tariff_schedule[customer_type]
        
        # Generate prices for each quarter
        current_year, current_quarter = current_year_quarter
        
        for year in range(years):
            for quarter in range(1, 5):
                # Calculate the actual year and quarter
                target_year = current_year + year
                target_quarter = ((current_quarter - 1 + quarter) % 4) + 1
                if (target_quarter < current_quarter) and (target_year == current_year):
                    target_year += 1
                
                # Check if we have specific tariff data for this period
                if (target_year, target_quarter) in tariff_data["increases"]:
                    price = tariff_data["increases"][(target_year, target_quarter)]
                else:
                    # After 2028, use annual increase of 5%
                    # Calculate how many quarters since the last known rate
                    last_known_year = 2027
                    last_known_quarter = 4
                    quarters_diff = (target_year - last_known_year) * 4 + (target_quarter - last_known_quarter)
                    
                    # Last known price from the schedule
                    last_price = tariff_data["increases"][(last_known_year, last_known_quarter)]
                    
                    # Apply quarterly increase (5% annual = ~1.23% quarterly)
                    quarterly_increase = 0.0123  # 5% annual increase
                    price = last_price * ((1 + quarterly_increase) ** quarters_diff)
                
                result.append(price)
    else:
        # If customer type not found in schedule, use the base_price and standard increases
        price = base_price
        for _ in range(years * 4):  # 4 quarters per year
            result.append(price)
            # Apply quarterly increase (3% annual = ~0.74% quarterly)
            price *= 1.0074
    
    # Convert to yearly averages
    yearly_prices = []
    for i in range(years):
        start_idx = i * 4
        end_idx = start_idx + 4
        if end_idx <= len(result):
            yearly_avg = sum(result[start_idx:end_idx]) / 4
            yearly_prices.append(yearly_avg)
        else:
            # If we don't have 4 quarters, use what we have
            yearly_avg = sum(result[start_idx:]) / len(result[start_idx:])
            yearly_prices.append(yearly_avg)
    
    return yearly_prices

def financial_analysis(pv_results, cost_per_watt=1.5, electricity_price=0.05, 
                       customer_type="residential", current_year_quarter=(2024, 1),
                       annual_price_increase=0.03, lifetime=25, discount_rate=0.06,
                       create_scenarios=True, currency_conversion_rate=130):
    """
    Perform comprehensive financial analysis for PV system
    
    Parameters:
    -----------
    pv_results : dict
        Results from PV production calculation
    cost_per_watt : float
        Installation cost per watt in USD (default: 1.5)
    electricity_price : float
        Current electricity price in USD/kWh (default: 0.05)
    customer_type : str
        Type of customer (residential, commercial, industrial_lv, etc.)
    current_year_quarter : tuple
        (year, quarter) tuple indicating the starting point (e.g., (2024, 1))
    annual_price_increase : float
        Annual electricity price increase rate (default: 0.03 or 3%) - used if no tariff data
    lifetime : int
        System lifetime in years (default: 25)
    discount_rate : float
        Discount rate for NPV calculation (default: 0.06 or 6%)
    create_scenarios : bool
        Whether to create optimistic and pessimistic scenarios
    currency_conversion_rate : float
        Conversion rate from USD to local currency (ETB)
        
    Returns:
    --------
    dict
        Financial metrics including NPV, IRR, payback period, LCOE
    """
    
    system_capacity = pv_results['system_capacity_kw']
    annual_energy = pv_results['annual_energy_kwh']
    
    # Investment cost
    investment = system_capacity * 1000 * cost_per_watt
    
    # Get projected electricity prices in ETB
    electricity_price_etb = electricity_price * currency_conversion_rate
    yearly_prices_etb = project_electricity_price(
        customer_type, 
        current_year_quarter, 
        electricity_price_etb, 
        years=lifetime
    )
    
    # Convert to USD for calculations
    yearly_prices_usd = [price / currency_conversion_rate for price in yearly_prices_etb]
    
    # Annual electricity savings
    savings = []
    for price in yearly_prices_usd:
        annual_saving = annual_energy * price
        savings.append(annual_saving)
    
    # Calculate NPV
    npv = -investment
    for i, saving in enumerate(savings):
        npv += saving / ((1 + discount_rate) ** (i + 1))
    
    # Payback period calculation
    cumulative_savings = 0
    payback_period = lifetime  # Default if never paid back
    
    for i, saving in enumerate(savings):
        cumulative_savings += saving
        if cumulative_savings >= investment:
            payback_period = i + 1
            break
    
    # ROI calculation
    roi = (sum(savings) - investment) / investment * 100
    
    # Calculate net cash flows
    cash_flows = [-investment]  # Initial investment
    for saving in savings:
        cash_flows.append(saving)
    
    # Calculate cumulative cash flow
    cumulative_cash_flow = np.cumsum(cash_flows)
    
    # Calculate LCOE
    lcoe = investment / (annual_energy * lifetime) if annual_energy > 0 else 0
    
    # Scenarios - only create if flag is True
    scenarios = {}
    if create_scenarios:  # This prevents infinite recursion
        # Optimistic scenario: higher electricity prices, lower costs
        scenarios['optimistic'] = financial_analysis(
            pv_results,
            cost_per_watt=cost_per_watt * 0.9,  # 10% lower cost
            electricity_price=electricity_price * 1.1,  # 10% higher price
            customer_type=customer_type,
            current_year_quarter=current_year_quarter,
            annual_price_increase=annual_price_increase * 1.2,  # 20% higher increase
            discount_rate=discount_rate * 0.9,  # 10% lower discount rate
            create_scenarios=False,  # Very important! Don't create nested scenarios
            currency_conversion_rate=currency_conversion_rate
        )
        
        # Pessimistic scenario: lower electricity prices, higher costs
        scenarios['pessimistic'] = financial_analysis(
            pv_results,
            cost_per_watt=cost_per_watt * 1.1,  # 10% higher cost
            electricity_price=electricity_price * 0.9,  # 10% lower price
            customer_type=customer_type,
            current_year_quarter=current_year_quarter,
            annual_price_increase=annual_price_increase * 0.8,  # 20% lower increase
            discount_rate=discount_rate * 1.1,  # 10% higher discount rate
            create_scenarios=False,  # Very important! Don't create nested scenarios
            currency_conversion_rate=currency_conversion_rate
        )
    
    # Store yearly electricity prices for reference
    electricity_prices = {
        'yearly_prices_etb': yearly_prices_etb,
        'yearly_prices_usd': yearly_prices_usd,
        'yearly_savings_usd': savings
    }
    
    # Return comprehensive financial metrics with currency conversion
    results = {
        'investment_usd': investment,
        'investment_etb': investment * currency_conversion_rate,
        'annual_savings_first_year_usd': savings[0],
        'annual_savings_first_year_etb': savings[0] * currency_conversion_rate,
        'cumulative_savings_usd': sum(savings),
        'cumulative_savings_etb': sum(savings) * currency_conversion_rate,
        'npv_usd': npv,
        'npv_etb': npv * currency_conversion_rate,
        'payback_period_years': payback_period,
        'roi_percent': roi,
        'lcoe_usd_per_kwh': lcoe,
        'lcoe_etb_per_kwh': lcoe * currency_conversion_rate,
        'cash_flows': cash_flows,
        'cash_flows_etb': [flow * currency_conversion_rate for flow in cash_flows],
        'cumulative_cash_flow': cumulative_cash_flow.tolist(),
        'cumulative_cash_flow_etb': [flow * currency_conversion_rate for flow in cumulative_cash_flow],
        'currency_conversion_rate': currency_conversion_rate,
        'electricity_prices': electricity_prices,
        'scenarios': scenarios
    }
    
    return results

def estimate_consumption_and_capacity(monthly_bill, customer_type="residential", 
                                     electricity_price=None, phase=0, peak_demand_kw=None):
    """
    Estimates monthly electricity consumption and recommended PV capacity
    based on the user's monthly electricity bill
    
    Parameters:
    -----------
    monthly_bill : float
        Average monthly electricity bill in ETB
    customer_type : str
        Type of customer ("residential", "commercial", "industrial_lv", "industrial_mv", 
        "industrial_hv", "street_light")
    electricity_price : float, optional
        Known electricity price in ETB/kWh. If None, will use Ethiopia's tariff structure
    phase : int
        Current tariff phase (0-15) representing the quarterly increase phase
    peak_demand_kw : float, optional
        Monthly peak demand in kW (for industrial customers)
        
    Returns:
    --------
    dict
        Contains estimated consumption, recommended capacity, and other metrics
    """
    # Official tariff data structure from the 2024-2028 tariff file
    tariff_data = {
        "residential": {
            "phases": {
                0: [  # Current tariffs
                    {'min': 0, 'max': 50, 'price': 0.27},
                    {'min': 50, 'max': 100, 'price': 0.77},
                    {'min': 100, 'max': 200, 'price': 1.63},
                    {'min': 200, 'max': 300, 'price': 2.00},
                    {'min': 300, 'max': 400, 'price': 2.20},
                    {'min': 400, 'max': 500, 'price': 2.41},
                    {'min': 500, 'max': float('inf'), 'price': 2.48}
                ],
            }
        },
        "commercial": {
            "phases": {
                0: [{'min': 0, 'max': float('inf'), 'price': 2.12}],  # Current tariff
            }
        },
        "industrial_lv": {  # Light Industry
            "phases": {
                0: [{'min': 0, 'max': float('inf'), 'price': 1.53}],  # Current tariff
            },
            "demand_charge": 53.58  # ETB/kW (placeholder, update with actual if known)
        },
        "industrial_mv": {  # Medium Industry
            "phases": {
                0: [{'min': 0, 'max': float('inf'), 'price': 1.19}],  # Current tariff
            },
            "demand_charge": 53.58  # ETB/kW (placeholder, update with actual if known)
        },
        "industrial_hv": {  # This would be a different category if available
            "phases": {
                0: [{'min': 0, 'max': float('inf'), 'price': 1.19}],  # Using Medium Industry rate
            },
            "demand_charge": 53.58  # ETB/kW (placeholder)
        },
        "street_light": {
            "phases": {
                0: [{'min': 0, 'max': float('inf'), 'price': 2.12}],  # Current tariff
            }
        }
    }
    
    # Initialize avg_price to a default value in case it's not set
    avg_price = 0
    
    # Get the appropriate tariff brackets for the customer type and phase
    if customer_type not in tariff_data:
        customer_type = "residential"  # Default to residential if type not found
    
    customer_tariffs = tariff_data[customer_type]["phases"]
    current_phase = min(phase, max(customer_tariffs.keys()))
    tariff_brackets = customer_tariffs[current_phase]
    
    # If electricity price is provided, use it directly
    if electricity_price is not None:
        # For industrial customers with demand charges
        if "industrial" in customer_type and peak_demand_kw is not None and "demand_charge" in tariff_data[customer_type]:
            # Subtract demand charge portion from bill to estimate energy consumption
            demand_charge_rate = tariff_data[customer_type]["demand_charge"]
            demand_charge = peak_demand_kw * demand_charge_rate
            energy_bill = max(0, monthly_bill - demand_charge)  # Ensure non-negative
            
            # Use energy bill for consumption estimation
            estimated_consumption = energy_bill / electricity_price if electricity_price > 0 else 0
        else:
            # Simple calculation for other customers
            estimated_consumption = monthly_bill / electricity_price if electricity_price > 0 else 0
        
        avg_price = electricity_price
    else:
        # For industrial customers with demand charges
        if "industrial" in customer_type and peak_demand_kw is not None and "demand_charge" in tariff_data[customer_type]:
            # Get the flat rate for energy
            flat_rate_price = tariff_brackets[0]['price']  # Industrial tariffs use flat rate
            
            # Subtract demand charge portion from bill to estimate energy consumption
            demand_charge_rate = tariff_data[customer_type]["demand_charge"]
            demand_charge = peak_demand_kw * demand_charge_rate
            energy_bill = max(0, monthly_bill - demand_charge)  # Ensure non-negative
            
            # Use energy bill for consumption estimation
            estimated_consumption = energy_bill / flat_rate_price if energy_bill > 0 and flat_rate_price > 0 else 0
            avg_price = flat_rate_price
        elif "industrial" in customer_type or "commercial" in customer_type or "street_light" in customer_type:
            # For flat rate customers (industrial without peak demand, commercial, street light)
            flat_rate_price = tariff_brackets[0]['price']
            estimated_consumption = monthly_bill / flat_rate_price if flat_rate_price > 0 else 0
            avg_price = flat_rate_price
        else:
            # For residential customers with tiered tariffs
            # This is an approximation method using bisection search
            min_consumption = 0
            max_consumption = 10000  # Reasonable upper limit
            
            def calculate_bill(consumption):
                # Calculate bill for a given consumption using the tariff structure
                bill = 0
                remaining = consumption
                
                for bracket in tariff_brackets:
                    if remaining <= 0:
                        break
                    
                    bracket_min = bracket['min']
                    bracket_max = bracket['max']
                    
                    if remaining > 0 and bracket_min < bracket_max:
                        units = min(remaining, bracket_max - bracket_min)
                        bill += units * bracket['price']
                        remaining -= units
                    
                # Add fixed charges and taxes (simplified)
                bill += 10  # Fixed service charge
                bill *= 1.15  # 15% VAT
                
                return bill
            
            # Binary search to find consumption that matches the bill
            while max_consumption - min_consumption > 1:
                mid = (min_consumption + max_consumption) / 2
                calculated_bill = calculate_bill(mid)
                
                if calculated_bill < monthly_bill:
                    min_consumption = mid
                else:
                    max_consumption = mid
            
            estimated_consumption = (min_consumption + max_consumption) / 2
            avg_price = monthly_bill / estimated_consumption if estimated_consumption > 0 else tariff_brackets[0]['price']
    
    # If no valid consumption was estimated, set a default
    if 'estimated_consumption' not in locals() or estimated_consumption <= 0:
        # Use a default consumption based on customer type
        default_consumptions = {
            "residential": 250,  # Average household
            "commercial": 500,
            "industrial_lv": 1000,
            "industrial_mv": 5000,
            "industrial_hv": 10000,
            "street_light": 300
        }
        estimated_consumption = default_consumptions.get(customer_type, 250)
        
        # Use the standard rate for the customer type
        if avg_price <= 0:
            avg_price = tariff_brackets[0]['price']
    
    # Recommended capacity calculation
    # Assuming:
    # - 4.5 peak sun hours per day in Ethiopia (average)
    # - 80% of consumption to be covered by solar
    # - System losses of 14%
    # - Capacity factor of 16.5%
    
    daily_consumption = estimated_consumption / 30  # Average daily consumption
    target_coverage = 0.8  # Target to cover 80% of consumption
    daily_production_needed = daily_consumption * target_coverage
    
    # Using capacity factor approach
    capacity_factor = 0.165  # 16.5% is typical for Ethiopia
    hours_per_day = 24
    recommended_capacity_kw = daily_production_needed / (capacity_factor * hours_per_day)
    
    # Alternative calculation using peak sun hours
    peak_sun_hours = 4.5  # Average for Ethiopia
    system_efficiency = 0.86  # 14% losses
    recommended_capacity_kw_alt = daily_production_needed / (peak_sun_hours * system_efficiency)
    
    # Take the average of both methods
    recommended_capacity_kw = (recommended_capacity_kw + recommended_capacity_kw_alt) / 2
    
    # Adjust recommended capacity based on roof constraints
    min_capacity = 1.0  # Minimum viable system size
    
    # Round to nearest 0.5 kW for practical system sizing
    recommended_capacity_kw = max(min_capacity, round(recommended_capacity_kw * 2) / 2)
    
    results = {
        'estimated_monthly_consumption_kwh': estimated_consumption,
        'estimated_yearly_consumption_kwh': estimated_consumption * 12,
        'average_electricity_price_etb': avg_price,
        'recommended_capacity_kw': recommended_capacity_kw,
        'expected_coverage_percent': target_coverage * 100
    }
    
    return results