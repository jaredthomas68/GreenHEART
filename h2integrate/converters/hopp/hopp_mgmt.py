import copy
import warnings

import numpy as np
from hopp.simulation.hopp_interface import HoppInterface
from hopp.simulation.technologies.sites import SiteInfo


def recreate_hopp_config_for_optimization(
    hopp_config,
    pv_rating_kw=None,
    wind_turbine_rating_kw=None,
    battery_rating_kw=None,
    battery_rating_kwh=None,
):
    hopp_config_internal = copy.deepcopy(hopp_config)
    rating_tol = 50.0
    min_tol = 50.0
    smooth_tol = 1.0

    if wind_turbine_rating_kw is not None and "wind" in hopp_config_internal["technologies"]:
        if pv_rating_kw <= min_tol and wind_turbine_rating_kw <= min_tol:
            hopp_config_internal["technologies"]["wind"]["turbine_rating_kw"] = min_tol
        elif wind_turbine_rating_kw <= rating_tol:
            if wind_turbine_rating_kw <= smooth_tol:
                hopp_config_internal["technologies"].pop("wind")
                hopp_config_internal["site"]["wind"] = False
                hopp_config_internal["config"]["cost_info"].pop("wind_installed_cost_mw")
                hopp_config_internal["config"]["cost_info"].pop("wind_om_per_kw")
                hopp_config_internal["config"]["simulation_options"]["wind"]["skip_financial"] = (
                    True
                )
            else:
                wind_turbine_rating_kw = np.interp(
                    wind_turbine_rating_kw, [smooth_tol, rating_tol], [smooth_tol, 0.1 * rating_tol]
                )
        else:
            hopp_config_internal["technologies"]["wind"]["turbine_rating_kw"] = (
                wind_turbine_rating_kw
            )

    if pv_rating_kw is not None:
        if pv_rating_kw <= min_tol and wind_turbine_rating_kw <= min_tol:
            hopp_config_internal["technologies"]["pv"]["system_capacity_kw"] = min_tol
        elif pv_rating_kw <= rating_tol:
            if pv_rating_kw <= smooth_tol:
                hopp_config_internal["technologies"].pop("pv")
                hopp_config_internal["site"]["solar"] = False
                hopp_config_internal["site"].pop("solar_resource_file")
                hopp_config_internal["config"]["cost_info"].pop("solar_installed_cost_mw")
                hopp_config_internal["config"]["cost_info"].pop("pv_om_per_kw")
            else:
                pv_rating_kw = np.interp(
                    pv_rating_kw, [smooth_tol, rating_tol], [smooth_tol, 0.1 * rating_tol]
                )
        else:
            hopp_config_internal["technologies"]["pv"]["system_capacity_kw"] = pv_rating_kw

    if battery_rating_kw is not None:
        if battery_rating_kw <= rating_tol:
            if battery_rating_kw <= smooth_tol:
                hopp_config_internal["technologies"].pop("battery")
                hopp_config_internal["config"].pop("dispatch_options")
                hopp_config_internal["config"]["cost_info"].pop("storage_installed_cost_mwh")
                hopp_config_internal["config"]["cost_info"].pop("storage_installed_cost_mw")
                hopp_config_internal["config"]["cost_info"].pop("battery_om_per_kw")
            else:
                battery_rating_kw = np.interp(
                    battery_rating_kw, [smooth_tol, rating_tol], [smooth_tol, 0.1 * rating_tol]
                )
        else:
            if (
                hopp_config_internal["config"]["cost_info"]
                and "battery_om_per_kwh" in hopp_config_internal["config"]["cost_info"]
            ):
                batt_om_per_kwh = hopp_config_internal["config"]["cost_info"]["battery_om_per_kwh"]
                batt_om_per_kw = hopp_config_internal["config"]["cost_info"]["battery_om_per_kw"]
                total_batt_om_per_kw = (
                    battery_rating_kw * batt_om_per_kw + battery_rating_kwh * batt_om_per_kwh
                ) / battery_rating_kw
                hopp_config_internal["config"]["cost_info"]["battery_om_per_kw"] = (
                    total_batt_om_per_kw
                )

            hopp_config_internal["technologies"]["battery"]["system_capacity_kw"] = (
                battery_rating_kw
            )
        if (
            hopp_config_internal["config"]["cost_info"]
            and "battery_om_per_kwh" in hopp_config_internal["config"]["cost_info"]
        ):
            hopp_config_internal["config"]["cost_info"].pop("battery_om_per_kwh")
    if battery_rating_kwh is not None and "battery" in hopp_config_internal["technologies"]:
        if battery_rating_kwh <= rating_tol:
            if battery_rating_kwh <= smooth_tol:
                hopp_config_internal["technologies"].pop("battery")
                hopp_config_internal["config"].pop("dispatch_options")
                hopp_config_internal["config"]["cost_info"].pop("storage_installed_cost_mwh")
                hopp_config_internal["config"]["cost_info"].pop("storage_installed_cost_mw")
                hopp_config_internal["config"]["cost_info"].pop("battery_om_per_kw")
            else:
                battery_rating_kwh = np.interp(
                    battery_rating_kwh, [smooth_tol, rating_tol], [smooth_tol, 0.1 * rating_tol]
                )
        else:
            hopp_config_internal["technologies"]["battery"]["system_capacity_kwh"] = (
                battery_rating_kwh
            )

    return hopp_config_internal


# Function to set up the HOPP model
def setup_hopp(
    hopp_config,
    pv_rating_kw=None,
    wind_turbine_rating_kw=None,
    battery_rating_kw=None,
    battery_rating_kwh=None,
    electrolyzer_rating=None,
):
    # overwrite individual fin_model values with cost_info values
    hopp_config_internal = overwrite_fin_values(hopp_config)

    # TODO: improve this if logic to correctly account for if the user
    # defines a desired schedule or uses the electrolyzer rating as the desired schedule
    if "battery" in hopp_config_internal["technologies"].keys() and (
        "desired_schedule" not in hopp_config_internal["site"].keys()
        or hopp_config_internal["site"]["desired_schedule"] == []
    ):
        hopp_config_internal["site"]["desired_schedule"] = [10.0] * 8760

    if electrolyzer_rating is not None:
        hopp_config_internal["site"]["desired_schedule"] = [electrolyzer_rating] * 8760

    hopp_site = SiteInfo(**hopp_config_internal["site"])

    # setup hopp interface
    if np.any([pv_rating_kw, wind_turbine_rating_kw, battery_rating_kw, battery_rating_kwh]):
        hopp_config_internal = recreate_hopp_config_for_optimization(
            hopp_config=hopp_config_internal,
            wind_turbine_rating_kw=wind_turbine_rating_kw,
            pv_rating_kw=pv_rating_kw,
            battery_rating_kw=battery_rating_kw,
            battery_rating_kwh=battery_rating_kwh,
        )
    else:
        hopp_config_internal = copy.deepcopy(hopp_config)

    if "wave" in hopp_config_internal["technologies"].keys():
        wave_cost_dict = hopp_config_internal["technologies"]["wave"].pop("cost_inputs")

    if "battery" in hopp_config_internal["technologies"].keys():
        hopp_config_internal["site"].update({"desired_schedule": hopp_site.desired_schedule})

    hi = HoppInterface(hopp_config_internal)
    hi.system.site = hopp_site

    if "wave" in hi.system.technologies.keys():
        hi.system.wave.create_mhk_cost_calculator(wave_cost_dict)

    return hi


# Function to run hopp from provided inputs from setup_hopp()
def run_hopp(hi, project_lifetime, verbose=True):
    hi.simulate(project_life=project_lifetime)

    capex = 0.0
    opex = 0.0
    try:
        solar_capex = hi.system.pv.total_installed_cost
        solar_opex = hi.system.pv.om_total_expense[0]
        capex += solar_capex
        opex += solar_opex
    except AttributeError:
        pass

    try:
        wind_capex = hi.system.wind.total_installed_cost
        wind_opex = hi.system.wind.om_total_expense[0]
        capex += wind_capex
        opex += wind_opex
    except AttributeError:
        pass

    try:
        battery_capex = hi.system.battery.total_installed_cost
        battery_opex = hi.system.battery.om_total_expense[0]
        capex += battery_capex
        opex += battery_opex
    except AttributeError:
        pass

    grid_outputs = hi.system.grid._system_model.Outputs
    # store results for later use
    hopp_results = {
        "hopp_interface": hi,
        "hybrid_plant": hi.system,
        "combined_hybrid_power_production_hopp": grid_outputs.system_pre_interconnect_kwac[0:8760],
        "combined_hybrid_curtailment_hopp": hi.system.grid.generation_curtailed,
        "energy_shortfall_hopp": hi.system.grid.missed_load,
        "annual_energies": hi.system.annual_energies,
        "hybrid_npv": hi.system.net_present_values.hybrid,
        "npvs": hi.system.net_present_values,
        "lcoe": hi.system.lcoe_real,
        "lcoe_nom": hi.system.lcoe_nom,
        "capex": capex,
        "opex": opex,
    }
    if verbose:
        print("\nHOPP Results")
        print("Hybrid Annual Energy: ", hopp_results["annual_energies"])
        print("Capacity factors: ", hi.system.capacity_factors)
        print("Real LCOE from HOPP: ", hi.system.lcoe_real)

    return hopp_results


def overwrite_fin_values(hopp_config):
    # override individual fin_model values with cost_info values
    if "wind" in hopp_config["technologies"]:
        if ("wind_om_per_kw" in hopp_config["config"]["cost_info"]) and (
            hopp_config["technologies"]["wind"]["fin_model"]["system_costs"]["om_capacity"][0]
            != hopp_config["config"]["cost_info"]["wind_om_per_kw"]
        ):
            for i in range(
                len(hopp_config["technologies"]["wind"]["fin_model"]["system_costs"]["om_capacity"])
            ):
                hopp_config["technologies"]["wind"]["fin_model"]["system_costs"]["om_capacity"][
                    i
                ] = hopp_config["config"]["cost_info"]["wind_om_per_kw"]

                om_fixed_wind_fin_model = hopp_config["technologies"]["wind"]["fin_model"][
                    "system_costs"
                ]["om_capacity"][i]
                wind_om_per_kw = hopp_config["config"]["cost_info"]["wind_om_per_kw"]
                msg = (
                    f"'om_capacity[{i}]' in the wind 'fin_model' was {om_fixed_wind_fin_model},"
                    f" but 'wind_om_per_kw' in 'cost_info' was {wind_om_per_kw}. The 'om_capacity'"
                    " value in the wind 'fin_model' is being overwritten with the value from the"
                    " 'cost_info'"
                )
                warnings.warn(msg, UserWarning)
        if ("wind_om_per_mwh" in hopp_config["config"]["cost_info"]) and (
            hopp_config["technologies"]["wind"]["fin_model"]["system_costs"]["om_production"][0]
            != hopp_config["config"]["cost_info"]["wind_om_per_mwh"]
        ):
            # Use this to set the Production-based O&M amount [$/MWh]
            for i in range(
                len(
                    hopp_config["technologies"]["wind"]["fin_model"]["system_costs"][
                        "om_production"
                    ]
                )
            ):
                hopp_config["technologies"]["wind"]["fin_model"]["system_costs"]["om_production"][
                    i
                ] = hopp_config["config"]["cost_info"]["wind_om_per_mwh"]
            om_wind_variable_cost = hopp_config["technologies"]["wind"]["fin_model"][
                "system_costs"
            ]["om_production"][i]
            wind_om_per_mwh = hopp_config["config"]["cost_info"]["wind_om_per_mwh"]
            msg = (
                f"'om_production' in the wind 'fin_model' was {om_wind_variable_cost}, but"
                f" 'wind_om_per_mwh' in 'cost_info' was {wind_om_per_mwh}. The 'om_production'"
                " value in the wind 'fin_model' is being overwritten with the value from the"
                " 'cost_info'"
            )
            warnings.warn(msg, UserWarning)

    if "pv" in hopp_config["technologies"]:
        if ("pv_om_per_kw" in hopp_config["config"]["cost_info"]) and (
            hopp_config["technologies"]["pv"]["fin_model"]["system_costs"]["om_capacity"][0]
            != hopp_config["config"]["cost_info"]["pv_om_per_kw"]
        ):
            for i in range(
                len(hopp_config["technologies"]["pv"]["fin_model"]["system_costs"]["om_capacity"])
            ):
                hopp_config["technologies"]["pv"]["fin_model"]["system_costs"]["om_capacity"][i] = (
                    hopp_config["config"]["cost_info"]["pv_om_per_kw"]
                )

                om_fixed_pv_fin_model = hopp_config["technologies"]["pv"]["fin_model"][
                    "system_costs"
                ]["om_capacity"][i]
                pv_om_per_kw = hopp_config["config"]["cost_info"]["pv_om_per_kw"]
                msg = (
                    f"'om_capacity[{i}]' in the pv 'fin_model' was {om_fixed_pv_fin_model}, but"
                    f" 'pv_om_per_kw' in 'cost_info' was {pv_om_per_kw}. The 'om_capacity' value"
                    " in the pv 'fin_model' is being overwritten with the value from the"
                    " 'cost_info'"
                )
                warnings.warn(msg, UserWarning)
        if ("pv_om_per_mwh" in hopp_config["config"]["cost_info"]) and (
            hopp_config["technologies"]["pv"]["fin_model"]["system_costs"]["om_production"][0]
            != hopp_config["config"]["cost_info"]["pv_om_per_mwh"]
        ):
            # Use this to set the Production-based O&M amount [$/MWh]
            for i in range(
                len(hopp_config["technologies"]["pv"]["fin_model"]["system_costs"]["om_production"])
            ):
                hopp_config["technologies"]["pv"]["fin_model"]["system_costs"]["om_production"][
                    i
                ] = hopp_config["config"]["cost_info"]["pv_om_per_mwh"]
            om_pv_variable_cost = hopp_config["technologies"]["pv"]["fin_model"]["system_costs"][
                "om_production"
            ][i]
            pv_om_per_mwh = hopp_config["config"]["cost_info"]["pv_om_per_mwh"]
            msg = (
                f"'om_production' in the pv 'fin_model' was {om_pv_variable_cost}, but"
                f" 'pv_om_per_mwh' in 'cost_info' was {pv_om_per_mwh}. The 'om_production' value"
                " in the pv 'fin_model' is being overwritten with the value from the 'cost_info'"
            )
            warnings.warn(msg, UserWarning)

    if "battery" in hopp_config["technologies"]:
        if ("battery_om_per_kw" in hopp_config["config"]["cost_info"]) and (
            hopp_config["technologies"]["battery"]["fin_model"]["system_costs"]["om_capacity"][0]
            != hopp_config["config"]["cost_info"]["battery_om_per_kw"]
        ):
            for i in range(
                len(
                    hopp_config["technologies"]["battery"]["fin_model"]["system_costs"][
                        "om_capacity"
                    ]
                )
            ):
                hopp_config["technologies"]["battery"]["fin_model"]["system_costs"]["om_capacity"][
                    i
                ] = hopp_config["config"]["cost_info"]["battery_om_per_kw"]
                hopp_config["technologies"]["battery"]["fin_model"]["system_costs"][
                    "om_batt_capacity_cost"
                ] = hopp_config["config"]["cost_info"]["battery_om_per_kw"]

            om_batt_fixed_cost = hopp_config["technologies"]["battery"]["fin_model"][
                "system_costs"
            ]["om_capacity"][-1]
            battery_om_per_kw = hopp_config["config"]["cost_info"]["battery_om_per_kw"]
            msg = (
                f"'om_capacity' in the battery 'fin_model' was {om_batt_fixed_cost}, but"
                f" 'battery_om_per_kw' in 'cost_info' was {battery_om_per_kw}. The"
                " 'om_capacity' value in the battery 'fin_model' is being overwritten with the"
                " value from the 'cost_info'"
            )
            warnings.warn(msg, UserWarning)
        if ("battery_om_per_mwh" in hopp_config["config"]["cost_info"]) and (
            hopp_config["technologies"]["battery"]["fin_model"]["system_costs"]["om_production"][0]
            != hopp_config["config"]["cost_info"]["battery_om_per_mwh"]
        ):
            # Use this to set the Production-based O&M amount [$/MWh]
            for i in range(
                len(
                    hopp_config["technologies"]["battery"]["fin_model"]["system_costs"][
                        "om_production"
                    ]
                )
            ):
                hopp_config["technologies"]["battery"]["fin_model"]["system_costs"][
                    "om_production"
                ][i] = hopp_config["config"]["cost_info"]["battery_om_per_mwh"]
            om_batt_variable_cost = hopp_config["technologies"]["battery"]["fin_model"][
                "system_costs"
            ]["om_production"][i]
            battery_om_per_mwh = hopp_config["config"]["cost_info"]["battery_om_per_mwh"]
            msg = (
                f"'om_production' in the battery 'fin_model' was {om_batt_variable_cost}, but"
                f" 'battery_om_per_mwh' in 'cost_info' was {battery_om_per_mwh}. The"
                " 'om_production' value in the battery 'fin_model' is being overwritten with the"
                " value from the 'cost_info'",
            )
            warnings.warn(msg, UserWarning)
    return hopp_config
