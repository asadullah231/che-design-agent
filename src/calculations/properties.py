"""
Physical & Thermodynamic Properties Lookup
Antoine equation, DIPPR correlations, NFPA ratings
"""


PROPERTIES_DB = {
    "ethanol": {
        "CAS": "64-17-5", "MW": 46.07, "Tb_C": 78.37, "Tm_C": -114.1,
        "Tc_C": 241.0, "Pc_bar": 63.8, "Vc_cm3mol": 167.1, "omega": 0.645,
        "LFL_pct": 3.3, "UFL_pct": 19.0, "AIT_C": 365, "IDLH_ppm": 3300,
        "NFPA_H": 0, "NFPA_F": 3, "NFPA_R": 0,
        "Antoine_A": 8.04494, "Antoine_B": 1554.3, "Antoine_C": 222.65,  # log10(mmHg), T in C
        "Cp_liq_kJkgK": 2.44, "Cp_vap_kJkgK": 1.42,
        "rho_liq_kgm3": 789, "mu_liq_cP": 1.074, "lambda_vap_kJkg": 841,
        "k_liq_WmK": 0.167, "sigma_mNm": 21.97,
    },
    "water": {
        "CAS": "7732-18-5", "MW": 18.015, "Tb_C": 100.0, "Tm_C": 0.0,
        "Tc_C": 374.0, "Pc_bar": 220.9, "Vc_cm3mol": 55.9, "omega": 0.345,
        "LFL_pct": None, "UFL_pct": None, "AIT_C": None, "IDLH_ppm": None,
        "NFPA_H": 0, "NFPA_F": 0, "NFPA_R": 0,
        "Antoine_A": 8.07131, "Antoine_B": 1730.63, "Antoine_C": 233.426,
        "Cp_liq_kJkgK": 4.18, "Cp_vap_kJkgK": 2.01,
        "rho_liq_kgm3": 997, "mu_liq_cP": 0.89, "lambda_vap_kJkg": 2257,
        "k_liq_WmK": 0.607, "sigma_mNm": 72.8,
    },
    "methanol": {
        "CAS": "67-56-1", "MW": 32.04, "Tb_C": 64.7, "Tm_C": -97.6,
        "Tc_C": 239.4, "Pc_bar": 80.97, "Vc_cm3mol": 118.0, "omega": 0.565,
        "LFL_pct": 6.0, "UFL_pct": 36.5, "AIT_C": 385, "IDLH_ppm": 6000,
        "NFPA_H": 1, "NFPA_F": 3, "NFPA_R": 0,
        "Antoine_A": 7.87863, "Antoine_B": 1473.11, "Antoine_C": 230.0,
        "Cp_liq_kJkgK": 2.53, "Cp_vap_kJkgK": 1.37,
        "rho_liq_kgm3": 791, "mu_liq_cP": 0.544, "lambda_vap_kJkg": 1100,
        "k_liq_WmK": 0.200, "sigma_mNm": 22.5,
    },
    "acetone": {
        "CAS": "67-64-1", "MW": 58.08, "Tb_C": 56.05, "Tm_C": -95.35,
        "Tc_C": 235.0, "Pc_bar": 47.0, "Vc_cm3mol": 209.0, "omega": 0.307,
        "LFL_pct": 2.5, "UFL_pct": 12.8, "AIT_C": 465, "IDLH_ppm": 2500,
        "NFPA_H": 1, "NFPA_F": 3, "NFPA_R": 0,
        "Antoine_A": 7.02447, "Antoine_B": 1161.0, "Antoine_C": 224.0,
        "Cp_liq_kJkgK": 2.17, "Cp_vap_kJkgK": 1.31,
        "rho_liq_kgm3": 784, "mu_liq_cP": 0.306, "lambda_vap_kJkg": 518,
        "k_liq_WmK": 0.161, "sigma_mNm": 23.0,
    },
    "benzene": {
        "CAS": "71-43-2", "MW": 78.11, "Tb_C": 80.1, "Tm_C": 5.5,
        "Tc_C": 289.0, "Pc_bar": 48.9, "Vc_cm3mol": 259.0, "omega": 0.212,
        "LFL_pct": 1.2, "UFL_pct": 7.8, "AIT_C": 498, "IDLH_ppm": 500,
        "NFPA_H": 2, "NFPA_F": 3, "NFPA_R": 0,
        "Antoine_A": 6.90565, "Antoine_B": 1211.033, "Antoine_C": 220.79,
        "Cp_liq_kJkgK": 1.74, "Cp_vap_kJkgK": 1.06,
        "rho_liq_kgm3": 879, "mu_liq_cP": 0.604, "lambda_vap_kJkg": 394,
        "k_liq_WmK": 0.144, "sigma_mNm": 28.2,
    },
    "toluene": {
        "CAS": "108-88-3", "MW": 92.14, "Tb_C": 110.6, "Tm_C": -95.0,
        "Tc_C": 320.8, "Pc_bar": 41.1, "Vc_cm3mol": 316.0, "omega": 0.263,
        "LFL_pct": 1.1, "UFL_pct": 7.1, "AIT_C": 480, "IDLH_ppm": 500,
        "NFPA_H": 2, "NFPA_F": 3, "NFPA_R": 0,
        "Antoine_A": 6.95464, "Antoine_B": 1344.8, "Antoine_C": 219.48,
        "Cp_liq_kJkgK": 1.69, "Cp_vap_kJkgK": 1.13,
        "rho_liq_kgm3": 867, "mu_liq_cP": 0.560, "lambda_vap_kJkg": 351,
        "k_liq_WmK": 0.138, "sigma_mNm": 27.9,
    },
    "ammonia": {
        "CAS": "7664-41-7", "MW": 17.03, "Tb_C": -33.35, "Tm_C": -77.73,
        "Tc_C": 132.4, "Pc_bar": 113.5, "Vc_cm3mol": 72.5, "omega": 0.250,
        "LFL_pct": 15.0, "UFL_pct": 28.0, "AIT_C": 651, "IDLH_ppm": 300,
        "NFPA_H": 3, "NFPA_F": 1, "NFPA_R": 0,
        "Antoine_A": 7.36050, "Antoine_B": 926.13, "Antoine_C": 240.17,
        "Cp_liq_kJkgK": 4.70, "Cp_vap_kJkgK": 2.06,
        "rho_liq_kgm3": 682, "mu_liq_cP": 0.255, "lambda_vap_kJkg": 1371,
        "k_liq_WmK": 0.507, "sigma_mNm": 21.1,
    },
    "propane": {
        "CAS": "74-98-6", "MW": 44.10, "Tb_C": -42.1, "Tm_C": -187.7,
        "Tc_C": 96.7, "Pc_bar": 42.5, "Vc_cm3mol": 200.0, "omega": 0.152,
        "LFL_pct": 2.1, "UFL_pct": 9.5, "AIT_C": 450, "IDLH_ppm": 2100,
        "NFPA_H": 1, "NFPA_F": 4, "NFPA_R": 0,
        "Antoine_A": 6.82973, "Antoine_B": 813.20, "Antoine_C": 248.0,
        "Cp_liq_kJkgK": 2.53, "Cp_vap_kJkgK": 1.66,
        "rho_liq_kgm3": 493, "mu_liq_cP": 0.110, "lambda_vap_kJkg": 428,
        "k_liq_WmK": 0.097, "sigma_mNm": 7.0,
    },
}

import math


class PropertyLookup:

    def lookup(self, chemical: str, T_C: float = 25, P_kPa: float = 101.325,
               properties_needed: list = None) -> dict:
        key = chemical.lower().strip()
        data = PROPERTIES_DB.get(key)

        if not data:
            return {
                "chemical": chemical,
                "status": "Not in database",
                "available_chemicals": list(PROPERTIES_DB.keys()),
                "note": "Add to properties.py database or use DIPPR/NIST for unlisted compounds"
            }

        result = {"chemical": chemical, "CAS": data.get("CAS"), "MW_g_mol": data.get("MW")}

        props = properties_needed or []

        # If no specific request, return everything
        return_all = len(props) == 0

        if return_all or "Tc" in props:
            result["Tc_C"] = data.get("Tc_C")
            result["Tc_K"] = round(data["Tc_C"] + 273.15, 2) if data.get("Tc_C") else None
        if return_all or "Pc" in props:
            result["Pc_bar"] = data.get("Pc_bar")
            result["Pc_kPa"] = round(data["Pc_bar"] * 100, 1) if data.get("Pc_bar") else None
        if return_all or "omega" in props:
            result["acentric_factor_omega"] = data.get("omega")
        if return_all or "Tb" in props:
            result["normal_boiling_point_C"] = data.get("Tb_C")
        if return_all or "Tm" in props:
            result["melting_point_C"] = data.get("Tm_C")
        if return_all or "vapor_pressure" in props:
            Pv = self._antoine(data, T_C)
            result["vapor_pressure_kPa_at_T"] = round(Pv, 4) if Pv else None
            result["vapor_pressure_temp_C"] = T_C
        if return_all or "density" in props:
            result["liquid_density_kgm3_at_20C"] = data.get("rho_liq_kgm3")
        if return_all or "viscosity" in props:
            result["liquid_viscosity_cP_at_20C"] = data.get("mu_liq_cP")
        if return_all or "Cp" in props:
            result["Cp_liquid_kJkgK"] = data.get("Cp_liq_kJkgK")
            result["Cp_vapor_kJkgK"] = data.get("Cp_vap_kJkgK")
        if return_all or "latent_heat" in props:
            result["latent_heat_vaporization_kJkg"] = data.get("lambda_vap_kJkg")
        if return_all or "thermal_conductivity" in props:
            result["thermal_conductivity_liquid_WmK"] = data.get("k_liq_WmK")
        if return_all or "LFL" in props or "UFL" in props:
            result["LFL_pct_vol"] = data.get("LFL_pct")
            result["UFL_pct_vol"] = data.get("UFL_pct")
            result["AIT_C"] = data.get("AIT_C")
        if return_all or "NFPA_ratings" in props:
            result["NFPA_Health"] = data.get("NFPA_H")
            result["NFPA_Flammability"] = data.get("NFPA_F")
            result["NFPA_Reactivity"] = data.get("NFPA_R")
        if return_all or "IDLH" in props:
            result["IDLH_ppm"] = data.get("IDLH_ppm")

        result["source"] = "Internal database (DIPPR / Perry's Chemical Engineers Handbook)"
        return result

    def _antoine(self, data: dict, T_C: float):
        A = data.get("Antoine_A")
        B = data.get("Antoine_B")
        C = data.get("Antoine_C")
        if A and B and C:
            log_P = A - B / (T_C + C)   # log10(mmHg)
            P_mmHg = 10 ** log_P
            return P_mmHg * 0.133322  # kPa
        return None
