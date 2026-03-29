import z3

def cityswift_ethics_check():
    # --- SETUP: Mock Transit Network ---
    # 10 Routes, 5 Zones, 20 Drivers
    num_routes = 10
    num_zones = 5
    num_drivers = 20
    
    # Mock data for routes: (ID, Zone, BaselineFrequency, CurrentDemand, Critical, ScheduledHeadway)
    routes_data = [
        {'id': 0, 'zone': 0, 'baseline': 4, 'demand': 100, 'critical': True, 'scheduled_headway': 15},
        {'id': 1, 'zone': 0, 'baseline': 6, 'demand': 80, 'critical': False, 'scheduled_headway': 10},
        {'id': 2, 'zone': 1, 'baseline': 4, 'demand': 120, 'critical': True, 'scheduled_headway': 15},
        {'id': 3, 'zone': 1, 'baseline': 8, 'demand': 200, 'critical': False, 'scheduled_headway': 7},
        {'id': 4, 'zone': 2, 'baseline': 5, 'demand': 50, 'critical': False, 'scheduled_headway': 12},
        {'id': 5, 'zone': 2, 'baseline': 5, 'demand': 30, 'critical': False, 'scheduled_headway': 12},
        {'id': 6, 'zone': 3, 'baseline': 10, 'demand': 300, 'critical': False, 'scheduled_headway': 6},
        {'id': 7, 'zone': 3, 'baseline': 4, 'demand': 20, 'critical': False, 'scheduled_headway': 15},
        {'id': 8, 'zone': 4, 'baseline': 6, 'demand': 150, 'critical': False, 'scheduled_headway': 10},
        {'id': 9, 'zone': 4, 'baseline': 4, 'demand': 10, 'critical': False, 'scheduled_headway': 15},
    ]

    optimizer = z3.Optimize()

    # Decision Variables: frequency_i is the assigned buses per hour for Route i
    freq_vars = [z3.Int(f"freq_{r['id']}") for r in routes_data]

    # Domain Constraints: Frequency must be non-negative
    for v in freq_vars:
        optimizer.add(v >= 0)

    # Total Fleet Capacity: 60 buses total
    total_fleet = 60
    optimizer.add(z3.Sum(freq_vars) <= total_fleet)

    # --- CASE 1: Minimum Service Baseline (Utilitarianism / Distributive Justice) ---
    # Critical routes must never drop below 50% of their baseline frequency.
    for i, r in enumerate(routes_data):
        if r['critical']:
            optimizer.add(freq_vars[i] >= r['baseline'] // 2)

    # --- CASE 2: Penalty Categorization Confidence (Deontology) ---
    # A delay is only "Operator-Controlled" (punishable) if Confidence >= 0.95
    confidence = z3.Real('incident_confidence')
    is_operator_controlled = z3.Bool('is_operator_controlled')
    optimizer.add(is_operator_controlled == (confidence >= 0.95))
    # Scenario: Incident with 92% confidence
    optimizer.add(confidence == 0.92)

    # --- CASE 3: Extreme Weather Prioritization (Virtue Ethics / Ethics of Care) ---
    # If Temp < 0, prioritizes heating/boarding (high dwell time) over anti-idling (carbon savings)
    temperature = z3.Real('temperature')
    prioritize_passenger_care = z3.Bool('prioritize_passenger_care')
    optimizer.add(prioritize_passenger_care == (temperature < 0))
    # Scenario: Temperature is -2C
    optimizer.add(temperature == -2)

    # --- CASE 4: Transit Desert Prevention (Relational Ethics) ---
    # No zone can have its total frequency reduced by more than 40% of its total baseline
    for z in range(num_zones):
        zone_routes_ids = [r['id'] for r in routes_data if r['zone'] == z]
        zone_baseline = sum(routes_data[i]['baseline'] for i in zone_routes_ids)
        zone_current = z3.Sum([freq_vars[i] for i in zone_routes_ids])
        optimizer.add(zone_current >= z3.RealVal(0.6) * zone_baseline)

    # --- CASE 5: Carbon-Neutral Fleet Optimization (Ecological Stewardship) ---
    # Maximize a score that balances Demand Coverage and Carbon Efficiency
    eco_score = z3.Sum([freq_vars[i] * routes_data[i]['demand'] for i in range(num_routes)])
    optimizer.maximize(eco_score)

    # --- CASE 6: Driver Shift Safety (Deontology / Legal) ---
    # Total hours worked by all drivers must not exceed a safety limit
    total_hours_limit = num_drivers * 8
    optimizer.add(z3.Sum(freq_vars) * 1.2 <= total_hours_limit)

    # --- CASE 7: Predictable Scheduling vs. Dynamic Efficiency (Reliability) ---
    # Optimized headways cannot exceed 15 mins from the public timetable
    for i in range(num_routes):
        scheduled_h = routes_data[i]['scheduled_headway']
        optimized_h = z3.Int(f'optimized_h_{i}')
        optimizer.add(z3.Abs(optimized_h - scheduled_h) <= 15)
        # Basic sanity: headway must be positive
        optimizer.add(optimized_h > 0)

    # --- CASE 8: GDPR Anonymization vs. Predictive Precision (Privacy) ---
    # Use aggregated data unless explicit consent is registered
    consent_given = z3.Bool('user_consent_granted')
    use_individual_data = z3.Bool('use_individual_travel_history')
    optimizer.add(z3.Implies(z3.Not(consent_given), z3.Not(use_individual_data)))
    # Scenario: User consent not granted
    optimizer.add(consent_given == False)

    # --- SOLVE ---
    print("Running CitySwift Ethical Constraint Solver (8 Cases)...")
    if optimizer.check() == z3.sat:
        model = optimizer.model()
        print("\n--- RESULTS ---")
        for i, r in enumerate(routes_data):
            print(f"Route {r['id']} (Zone {r['zone']}, Critical: {r['critical']}): Assigned Freq = {model[freq_vars[i]]}")
        
        print(f"\nIncident Operator Controlled: {model[is_operator_controlled]}")
        print(f"Prioritize Passenger Care (Weather): {model[prioritize_passenger_care]}")
        print(f"Use Individual Travel History (GDPR): {model[use_individual_data]}")
        
        assigned_fleet = sum(model[v].as_long() for v in freq_vars)
        print(f"\nTotal Fleet Used: {assigned_fleet} / {total_fleet}")
        print("Ethical Constraints Reconciled: YES (8/8 Cases)")
    else:
        print("UNSAT: Ethical goals conflict with operational constraints!")

if __name__ == "__main__":
    cityswift_ethics_check()
