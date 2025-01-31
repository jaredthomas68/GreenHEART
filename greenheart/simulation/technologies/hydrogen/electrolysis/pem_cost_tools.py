import numpy as np


def summarize_electrolysis_cost_and_performance(electrolyzer_physics_results, electrolyzer_config):
    capacity_kW = electrolyzer_physics_results["H2_Results"]["system capacity [kW]"]
    annual_performance = electrolyzer_physics_results["H2_Results"]["Performance Schedules"]

    if "var_om" in electrolyzer_config.keys():
        electrolyzer_vopex_pr_kg = (
            electrolyzer_config["var_om"]
            * annual_performance["Annual Average Efficiency [kWh/kg]"].values
        )
    else:
        electrolyzer_vopex_pr_kg = 0.0

    refurb_complex = annual_performance["Refurbishment Schedule [MW replaced/year]"].values / (
        capacity_kW / 1e3
    )
    refurb_simple = np.zeros(len(annual_performance))
    refurb_period = int(
        round(electrolyzer_physics_results["H2_Results"]["Time Until Replacement [hrs]"] / 8760)
    )
    refurb_simple[refurb_period : len(annual_performance) : refurb_period] = 1.0

    complex_refurb_cost = list(
        np.array(refurb_complex * electrolyzer_config["replacement_cost_percent"])
    )
    simple_refurb_cost = list(
        np.array(refurb_simple * electrolyzer_config["replacement_cost_percent"])
    )
    annual_energy_consumption = annual_performance["Annual Energy Used [kWh/year]"].values

    electrolyzer_cost_res = {
        "electrolyzer_utilization": annual_performance["Capacity Factor [-]"].to_list(),
        "electrolyzer_capacity_kg_pr_day": electrolyzer_physics_results["H2_Results"][
            "Rated BOL: H2 Production [kg/hr]"
        ]
        * 24,
        "electrolyzer_var_om": electrolyzer_vopex_pr_kg,
        "electrolyzer_water_feedstock": electrolyzer_physics_results["H2_Results"][
            "Rated BOL: Gal H2O per kg-H2"
        ],
        "electrolyzer_energy_feedstock_kW": annual_energy_consumption,
        "electrolyzer_eff_kWh_pr_kg": annual_performance[
            "Annual Average Efficiency [kWh/kg]"
        ].to_list(),
        "stack_replacement_sched_simple": refurb_simple,
        "stack_replacement_sched_complex": refurb_complex,
        "refurb_cost_simple": simple_refurb_cost,
        "refurb_cost_complex": complex_refurb_cost,
    }
    return electrolyzer_cost_res
