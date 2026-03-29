import z3

def cityswift_ethics_check():
    """
    Formal Z3 model of the CitySwift Ethical Logic Engine.
    
    DEFINITIONS:
    - Reference Baseline: The target service level (buses/hr).
    - Ethical Minimum (Floor): The absolute limit (e.g. 50% or 60% of baseline).
    - Demand: The predicted passenger volume (pax).
    - Criticality: Boolean flag for essential infrastructure.
    """
    # --- KEY SYSTEM INPUTS (Raw Scenario Data) ---
    num_drivers = 20
    hours_per_shift = 8.0
    total_fleet_limit = 60
    driver_hours_limit = num_drivers * hours_per_shift
    
    # (RouteID, ZoneID, Baseline, Demand, IsCritical, SchedHeadway)
    raw_input_data = [
        (0, "Z0", 4, 100, True, 15),
        (1, "Z0", 6, 80, False, 10),
        (2, "Z1", 4, 120, True, 15),
        (3, "Z1", 8, 200, False, 7),
        (4, "Z2", 5, 50, False, 12),
        (5, "Z2", 5, 30, False, 12),
        (6, "Z3", 10, 300, False, 6),
        (7, "Z3", 4, 20, False, 15),
        (8, "Z4", 6, 150, False, 10),
        (9, "Z4", 4, 10, False, 15),
    ]
    # ---------------------------------------------

    print("Executing CitySwift Ethical Logic Engine...")
    print(f"Scenario Parameters:")
    print(f"- Total Fleet Limit: {total_fleet_limit} buses")
    print(f"- Driver Capacity: {num_drivers} drivers ({hours_per_shift} hrs/shift)")
    print("- Input Mock Routes [ID | Zone | Base | Demand | Critical]:")
    for r_id, z_id, base, d, crit, shift in raw_input_data:
        c_str = "Yes" if crit else "No"
        print(f"  R{r_id:<2} | {z_id:<4} | {base:<4} | {d:<6} | {c_str}")
    print("")

    # 1. Create Formal Sorts for semantic modeling (Route, Zone)
    Route = z3.DeclareSort('Route')
    Zone = z3.DeclareSort('Zone')
    
    # 2. Define Relations and properties for each bus route
    is_critical = z3.Function('is_critical', Route, z3.BoolSort())
    route_zone = z3.Function('route_zone', Route, Zone)
    demand = z3.Function('demand', Route, z3.IntSort())
    baseline_freq = z3.Function('baseline_freq', Route, z3.IntSort())
    scheduled_h = z3.Function('scheduled_h', Route, z3.IntSort())
    
    # 3. Define Decision Variables (AI control points)
    frequency = z3.Function('frequency', Route, z3.IntSort())
    opt_headway = z3.Function('opt_headway', Route, z3.IntSort())
    
    # 4. Initialize the Optimizer
    optimizer = z3.Optimize()
    
    # 3. Populate Data & Basic Physical Constraints
    routes = []
    zones_map = {}
    
    # Map the raw data into Z3 objects
    mock_data = []
    for r_id, z_id, base, d, crit, shift in raw_input_data:
        r_const = z3.Const(f'R{r_id}', Route)
        if z_id not in zones_map:
            zones_map[z_id] = z3.Const(z_id, Zone)
        z_const = zones_map[z_id]
        
        routes.append(r_const)
        mock_data.append((r_const, z_const, base, d, crit, shift))
    
    zones = list(zones_map.values())
    
    for r, z, b, d, c, sh in mock_data:
        optimizer.add(route_zone(r) == z)
        optimizer.add(baseline_freq(r) == b)
        optimizer.add(demand(r) == d)
        optimizer.add(is_critical(r) == c)
        optimizer.add(scheduled_h(r) == sh)

    # 6. Global Rules: Physical constraints
    for r in routes:
        optimizer.add(frequency(r) >= 0)
        optimizer.add(opt_headway(r) > 0)

    optimizer.add(z3.Sum([frequency(r) for r in routes]) <= total_fleet_limit)

    # 7. Ethical Constraints (8 Cases)
    # Case 1: Minimum Service Baseline
    for r in routes:
        optimizer.add(z3.Implies(is_critical(r), frequency(r) >= baseline_freq(r) / 2))

    # Case 2: Transparency Audit
    confidence = z3.Real('confidence')
    is_operator_controlled = z3.Bool('is_operator_controlled')
    optimizer.add(is_operator_controlled == (confidence >= 0.95))
    optimizer.add(confidence == 0.92) 

    # Case 3: Virtue Ethics (Soft Constraint)
    temperature = z3.Real('temperature')
    prioritize_passenger_care = z3.Bool('prioritize_passenger_care')
    optimizer.add(prioritize_passenger_care == (temperature < 0))
    optimizer.add(temperature == -2) 
    optimizer.add_soft(prioritize_passenger_care == True, weight=100)

    # Case 4: Transit Desert Prevention (Ensuring each zone gets >= 60% of baseline)
    for z in zones:
        # Finding all routes that belong to this specific zone
        routes_in_zone = [r for r, r_zone, b, d, c, sh in mock_data if r_zone == z]
        
        # Sum of baselines and current frequencies for this zone
        zone_baseline = z3.Sum([baseline_freq(r) for r in routes_in_zone])
        zone_current = z3.Sum([frequency(r) for r in routes_in_zone])
        
        # 60% requirement constraint
        optimizer.add(z3.ToReal(zone_current) >= 0.6 * z3.ToReal(zone_baseline))

    # Case 5: Utilitarianism - Maximizing carbon-efficiency across the network
    # We use maximize() to find the "best" allocation after safety rules are met
    eco_score = z3.Sum([frequency(r) * demand(r) for r in routes])
    optimizer.maximize(eco_score)

    # Case 6: Driver Fatigue Management (Hard Safety Constraint)
    driver_hours_limit = 20 * 8 # Limit per driver * drivers
    # Multiplication by 1.2 models overhead/prep time
    optimizer.add(z3.ToReal(z3.Sum([frequency(r) for r in routes])) * 1.2 <= driver_hours_limit)

    # Case 7: Predictable Scheduling (Timetable deviations)
    for r in routes:
        optimizer.add(z3.Abs(opt_headway(r) - scheduled_h(r)) <= 15)

    # Case 8: GDPR Anonymization
    consent_given = z3.Bool('user_consent_granted')
    use_individual_data = z3.Bool('use_individual_travel_history')
    optimizer.add(z3.Implies(z3.Not(consent_given), z3.Not(use_individual_data)))
    optimizer.add(consent_given == False)

    # 8. Run Solver and Print Results in Lab Style
    print("Executing CitySwift Ethical Logic Engine...")
    result = optimizer.check()
    print(f"Solver Result: {result}")
    
    if result == z3.sat:
        model = optimizer.model()
        print("\nSUCCESSFUL. All ethical constraints are satisfied.\n")
        
        # Table Header
        header = f"{'Route ID':<9} | {'Zone':<8} | {'Allocated (Base)':<18} | {'Demand':<10} | {'Status'}"
        print(header)
        print("-" * len(header))
        
        for i, r in enumerate(routes):
            freq = str(model.evaluate(frequency(r)))
            base = str(model.evaluate(baseline_freq(r)))
            dem = str(model.evaluate(demand(r)))
            # Clean up the Sort output (Zone!val!3 -> Z3)
            z_raw = str(model.evaluate(route_zone(r)))
            z_val = z_raw.replace("Zone!val!", "Z")
            is_crit = " [CRITICAL]" if model.evaluate(is_critical(r)) else ""
            print(f"Route {i:<4} | {z_val:<8} | {freq:<2} ({base:<2}) buses/hr | {dem:<6} pax | {is_crit}")
            
        print("\nZone Coverage Summary (Distributive Justice):")
        print("-" * 45)
        for z in zones:
            routes_in_zone = [r for r, r_zone, b, d, c, sh in mock_data if r_zone == z]
            z_baseline = sum([b for r, r_zone, b, d, c, sh in mock_data if r_zone == z])
            z_current = sum([model.evaluate(frequency(r)).as_long() for r in routes_in_zone])
            coverage = (z_current / z_baseline) * 100
            print(f"{str(z):<8}: {z_current:>2.1f}/{z_baseline:>2.1f} buses/hr ({coverage:>3.1f}%) - [SATISFIED]")

        # Logic for Driver Average Hours
        total_freq = sum([model.evaluate(frequency(r)).as_long() for r in routes])
        total_hours = total_freq * 1.2
        avg_hours = total_hours / 20 # 20 drivers

        print("\nEthical Governance Status:")
        print(f"- [Case 1] Hospital/School Protection: {model.evaluate(z3.And([z3.Implies(is_critical(r), frequency(r) >= baseline_freq(r)/2) for r in routes]))}")
        print(f"- [Case 4] Transit Desert Prevention: Minimum 60% coverage enforced per zone.")
        print(f"- [Case 5] Utilitarian Optimization: Efficiency maximized (Score: {model.evaluate(z3.Sum([frequency(r) * demand(r) for r in routes]))})")
        print(f"- [Case 6] Driver Safety: Avg workload {avg_hours:.1f} hrs/shift (Limit: 8.0).")
        print(f"\nOperational Metadata:")
        print(f"- Weather Care Mode: {model.evaluate(prioritize_passenger_care)}")
        print(f"- Audit Status: {model.evaluate(is_operator_controlled)} (Confidence {model.evaluate(confidence)})")
        print("- GDPR Status: Anonymized")
    else:
        print("\nFAILED. Operational constraints violate ethical safety rules.")

if __name__ == "__main__":
    cityswift_ethics_check()
