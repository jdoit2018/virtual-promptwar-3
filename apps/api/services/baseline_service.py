"""
apps/api/services/baseline_service.py
Service for baseline calculation based on onboarding quiz.
"""

from models.schemas import QuizResponses


def calculate_baseline_values(responses: QuizResponses) -> dict:
    """
    Calculates carbon footprint baseline values for each pillar in MT CO2e.
    Returns:
        dict: {
            "housing_co2e": float,
            "transport_co2e": float,
            "diet_co2e": float,
            "consumption_co2e": float,
            "total_co2e": float
        }
    """
    # ── 1. Housing Pillar ──────────────────────────────────────────────────────
    # Q1: Property Type (Detached: 4.0, Townhouse: 2.5, Apartment: 1.5)
    h_base = 1.5
    if responses.property_type == "detached":
        h_base = 4.0
    elif responses.property_type == "townhouse":
        h_base = 2.5

    # Q2: Heating Multiplier (Natural Gas/Oil: 1.2, Electricity/Heat Pump: 0.8, Renewables/Solar: 0.2)
    h_heat = 0.8
    if responses.heating_type == "gas_oil":
        h_heat = 1.2
    elif responses.heating_type == "renewables_solar":
        h_heat = 0.2

    # Q3: Sharing household size
    n_people = max(1, responses.household_size)

    housing_co2e = round((h_base * h_heat) / n_people, 2)

    # ── 2. Transportation Pillar ──────────────────────────────────────────────
    # Q4 & Q5: Drive Emissions
    t_drive = 0.0
    if responses.transport_mode == "gas_car":
        if responses.weekly_mileage == "low":
            t_drive = 0.8
        elif responses.weekly_mileage == "medium":
            t_drive = 2.2
        elif responses.weekly_mileage == "high":
            t_drive = 4.5
    elif responses.transport_mode == "ev":
        if responses.weekly_mileage == "low":
            t_drive = 0.3
        elif responses.weekly_mileage == "medium":
            t_drive = 0.8
        elif responses.weekly_mileage == "high":
            t_drive = 1.5
    elif responses.transport_mode == "public_transit":
        t_drive = 0.5

    # Q6: Flights Emissions
    t_flight = 0.0
    if responses.flights_profile == "short_haul":
        t_flight = 0.6
    elif responses.flights_profile == "long_haul":
        t_flight = 2.5
    elif responses.flights_profile == "frequent":
        t_flight = 6.0

    transport_co2e = round(t_drive + t_flight, 2)

    # ── 3. Diet Pillar ────────────────────────────────────────────────────────
    # Q7: Diet Type
    diet_co2e = 2.0
    if responses.diet_type == "heavy_meat":
        diet_co2e = 3.0
    elif responses.diet_type == "poultry_pescatarian":
        diet_co2e = 1.4
    elif responses.diet_type == "vegetarian":
        diet_co2e = 1.1
    elif responses.diet_type == "vegan":
        diet_co2e = 0.7

    diet_co2e = round(diet_co2e, 2)

    # ── 4. Consumption Pillar ─────────────────────────────────────────────────
    # Q8: Fashion Frequency
    c_fashion = 0.4
    if responses.fashion_frequency == "rarely":
        c_fashion = 0.1
    elif responses.fashion_frequency == "frequently":
        c_fashion = 0.9

    # Q9: Electronics
    c_electronics = 0.0
    if responses.electronics_frequency == "one":
        c_electronics = 0.3
    elif responses.electronics_frequency == "two_or_more":
        c_electronics = 0.6

    consumption_co2e = round(c_fashion + c_electronics, 2)

    # ── Total calculation ──────────────────────────────────────────────────────
    total_co2e = round(housing_co2e + transport_co2e + diet_co2e + consumption_co2e, 2)

    return {
        "housing_co2e": housing_co2e,
        "transport_co2e": transport_co2e,
        "diet_co2e": diet_co2e,
        "consumption_co2e": consumption_co2e,
        "total_co2e": total_co2e
    }
