import z3

def cityswift_engine(scenario_name="Standard", trigger_failure=False):
    """
    CitySwift Ethical & Functional Logic Engine.
    
    DOMAIN ELEMENTS:
    - Routes: The set of transit lines (R0-R9).
    - Zones: Geographic regions (Z0-Z4) for distributive justice.
    - Capacity: Fleet limits (60 buses) and Driver limits (160 man-hours).
    - Demand: Historical and predicted passenger volumes per route.
    - Criticality: Flag for essential infrastructure (e.g., Hospitals).
    """
    # --- 1. DOMAIN DATA (Mock context for Bus Éireann Dublin) ---
    num_drivers = 20
    hours_per_shift = 8.0
    total_fleet_limit = 60
    driver_hours_limit = num_drivers * hours_per_shift
    
    # (RouteID, List_of_Zones, Baseline_Freq, Demand, IsCritical, Sched_Headway)
    raw_data = [
        (0, ["Z0", "Z1"], 4, 100, True, 15),
        (1, ["Z0", "Z2"], 6, 80, False, 10),
        (2, ["Z1", "Z3"], 4, 120, True, 15),
        (3, ["Z1", "Z0"], 8, 200, False, 7),
        (4, ["Z2", "Z4"], 5, 50, False, 12),
        (5, ["Z2"], 5, 30, False, 12),
        (6, ["Z3", "Z0"], 10, 300, False, 6),
        (7, ["Z3"], 4, 20, False, 15),
        (8, ["Z4", "Z0"], 6, 150, False, 10),
        (9, ["Z4"], 4, 10, False, 15),
    ]

    print(f"\n{'='*65}")
    print(f" RUNNING SCENARIO: {scenario_name}")
    print(f"{'='*65}")

    print(f"Scenario Parameters:")
    print(f"- Total Fleet Limit: {total_fleet_limit} buses")
    print(f"- Driver Capacity: {num_drivers} drivers ({hours_per_shift} hrs/shift)")
    print("Input Mock Routes:")
    i_header = f"{'Route ID':<9} | {'Zones':<12} | {'Base Freq':<10} | {'Demand':<10} | {'Critical'}"
    print(i_header)
    print("-" * len(i_header))
    for r_id, zones, base, d, crit, shift in raw_data:
        c_str = "Yes" if crit else "No"
        z_str = ",".join(zones)
        print(f"R{r_id:<8} | {z_str:<12} | {base:<10} | {d:<10} | {c_str}")
    print("")

    # --- 2. Z3 MODEL INITIALIZATION ---
    Route = z3.DeclareSort('Route')
    Zone = z3.DeclareSort('Zone')
    
    is_critical = z3.Function('is_critical', Route, z3.BoolSort())
    demand = z3.Function('demand', Route, z3.IntSort())
    baseline_f = z3.Function('baseline_f', Route, z3.IntSort())
    sched_h = z3.Function('sched_h', Route, z3.IntSort())
    
    frequency = z3.Function('frequency', Route, z3.IntSort())
    opt_headway = z3.Function('opt_headway', Route, z3.IntSort())
    
    optimizer = z3.Optimize()
    
    # Mapping Data to Z3
    routes = []
    zones_map = {}
    mock_data = [] # Stores (r_const, list_of_zone_consts, base, d, crit, sh)
    
    # Initialize all possible zones first from raw_data
    all_zone_ids = sorted(list(set([z for _, zs, _, _, _, _ in raw_data for z in zs])))
    for z_id in all_zone_ids:
        zones_map[z_id] = z3.Const(z_id, Zone)

    for r_id, z_ids, base, d, crit, sh in raw_data:
        r_const = z3.Const(f'R{r_id}', Route)
        routes.append(r_const)
        z_consts = [zones_map[z_id] for z_id in z_ids]
        mock_data.append((r_const, z_consts, base, d, crit, sh))
        
        optimizer.add(baseline_f(r_const) == base)
        optimizer.add(demand(r_const) == d)
        optimizer.add(is_critical(r_const) == crit)
        optimizer.add(sched_h(r_const) == sh)
        optimizer.add(frequency(r_const) >= 0)
        optimizer.add(opt_headway(r_const) > 0)

    # --- 3. GOAL ORDERING (F1-F3, E1-E6) ---
    PASSENGERS_PER_BUS = 50

    # [F1] Maximize Utility (Saturation Model)
    # Utility = min(Demand, Frequency * 50)
    def route_utility(r, d):
        coverage = frequency(r) * PASSENGERS_PER_BUS
        return z3.If(coverage <= d, coverage, d)

    utility = z3.Sum([route_utility(r, d) for r, zs, b, d, c, sh in mock_data])
    optimizer.maximize(utility)

    # [F2] Resource Constraint Satisfaction
    optimizer.add(z3.Sum([frequency(r) for r in routes]) <= total_fleet_limit)
    optimizer.add(z3.ToReal(z3.Sum([frequency(r) for r in routes])) * 1.2 <= driver_hours_limit)

    # [F3] Predictable Synchronization (+/- 15 mins)
    for r in routes:
        optimizer.add(z3.Abs(opt_headway(r) - sched_h(r)) <= 15)

    # [E1] Minimum Service Floor (Critical Routes >= 50%)
    for r in routes:
        optimizer.add(z3.Implies(is_critical(r), frequency(r) >= baseline_f(r) / 2))

    # [E2] Distributive Justice (60% zone coverage)
    # Refined: A route's frequency contributes to EVERY zone it passes through.
    for z_id, z_const in zones_map.items():
        # Find all routes that pass through this zone
        intersecting_routes = []
        z_total_baseline = 0
        for r_const, z_consts, base, d, crit, sh in mock_data:
            if z_const in z_consts:
                intersecting_routes.append(r_const)
                z_total_baseline += base
        
        if intersecting_routes:
            z_freq_sum = z3.Sum([frequency(r) for r in intersecting_routes])
            optimizer.add(z3.ToReal(z_freq_sum) >= 0.6 * float(z_total_baseline))

    # [E3] Operator Fairness (Confidence >= 95%)
    confidence = z3.Real('confidence')
    is_op_controlled = z3.Bool('is_op_controlled')
    optimizer.add(is_op_controlled == (confidence >= 0.95))
    optimizer.add(confidence == 23/25) # 0.92

    # [E4] Virtue of Care (Weather heating)
    temp = z3.Real('temp')
    prioritize_care = z3.Bool('prioritize_care')
    optimizer.add(prioritize_care == (temp < 0))
    optimizer.add(temp == -2) 

    # [E5] Driver Safety (Workload limit)
    optimizer.add(z3.ToReal(z3.Sum([frequency(r) for r in routes])) * 1.2 <= driver_hours_limit)

    # [E6] GDPR Privacy (Consent check)
    consent = z3.Bool('consent')
    use_indiv_data = z3.Bool('use_indiv_data')
    optimizer.add(z3.Implies(z3.Not(consent), z3.Not(use_indiv_data)))
    optimizer.add(consent == False)

    # --- TRIGGER FAILURE SCENARIO ---
    if trigger_failure:
        print("ALERT: Injecting impossible functional demand to trigger ethical safety violation...")
        for r in routes:
            optimizer.add(frequency(r) >= baseline_f(r) * 5) # Increased multiplier for multi-zone conflict

    # --- 4. VALIDATION ENGINE & OUTPUT ---
    check = optimizer.check()
    
    if check == z3.sat:
        m = optimizer.model()
        print("\n[ VALIDATION SUCCESSFUL ]")
        print("- Functional Goals: MET (Utility Maximized, Constraints Satisfied)")
        print("- Ethical Goals: MET (Normative Guardrails Verified)")
        
        header = f"{'Route ID':<9} | {'Zones':<12} | {'Allocated (Base)':<18} | {'Demand':<10} | {'Status'}"
        print(f"\n{header}")
        print("-" * len(header))
        for r_const, z_consts, base, d, crit, sh in mock_data:
            freq = m.evaluate(frequency(r_const)).as_long()
            r_id = str(r_const).replace('R', '')
            c_str = " [CRITICAL]" if crit else ""
            z_str = ",".join([str(z) for z in z_consts])
            print(f"Route {r_id:<4} | {z_str:<12} | {freq:<2} ({base:<2}) buses/hr | {d:<10} |{c_str}")
        
        print("\nZone Coverage Summary (Distributive Justice):")
        print("-" * 55)
        for z_id, z_const in zones_map.items():
            # Calculate actual sum and baseline sum for this zone
            z_actual_sum = 0
            z_base_sum = 0
            for r_const, z_consts, base, d, crit, sh in mock_data:
                if z_const in z_consts:
                    z_actual_sum += m.evaluate(frequency(r_const)).as_long()
                    z_base_sum += base
            
            coverage = (z_actual_sum / z_base_sum) * 100 if z_base_sum > 0 else 0
            print(f"{z_id:<8}: {z_actual_sum:>2.1f}/{z_base_sum:>2.1f} buses/hr ({coverage:>3.1f}%) - [SATISFIED]")

        print("\nEthical Governance Status:")
        print(f"- [Case E1] Critical Floor Protection: MET")
        print(f"- [Case E2] Distributive Justice: MET (Min 60% per zone)")
        print(f"- [Case E3] Operator Fairness: {m.evaluate(is_op_controlled)} (Conf: {m.evaluate(confidence)})")
        print(f"- [Case E4] Weather Care Mode: {m.evaluate(prioritize_care)} (Temp: {m.evaluate(temp)})")
        print(f"- [Case E5] Driver Safety: MET (Workload under cap)")
        print(f"- [Case E6] GDPR Status: ANONYMIZED")

        print(f"\nOperational Metadata:")
        print(f"- Total Network Utility Score: {m.evaluate(utility)}")
    else:
        print("\n[ VALIDATION FAILED ]")
        print("ERROR: Situation identified where goals cannot be reached.")
        print("CAUSE: Logical contradiction between Operational Limits and Ethical Constraints.")

if __name__ == "__main__":
    cityswift_engine(scenario_name="Standard Operation", trigger_failure=False)
    cityswift_engine(scenario_name="Resource Contradiction", trigger_failure=True)
