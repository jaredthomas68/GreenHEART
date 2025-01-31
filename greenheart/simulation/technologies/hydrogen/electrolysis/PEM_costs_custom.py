def calc_custom_electrolysis_capex_fom(electrolyzer_physics_results, electrolyzer_config):
    capacity_kW = electrolyzer_physics_results["H2_Results"]["system capacity [kW]"]
    electrolyzer_capex = electrolyzer_config["electrolyzer_capex"] * capacity_kW
    if "fixed_om" in electrolyzer_config.keys():
        electrolyzer_fopex = electrolyzer_config["fixed_om"] * capacity_kW
    else:
        electrolyzer_fopex = 0.0
    return electrolyzer_capex, electrolyzer_fopex
