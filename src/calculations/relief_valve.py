"""
Pressure Safety Valve Sizing per API 520 Part I / API 521
"""

import math


# API 520 discharge coefficient for conventional PSV
Kd = 0.975   # effective discharge coefficient
Kb = 1.0     # back pressure correction (conventional, <10% set P)
Kc = 1.0     # combination correction (no rupture disc)


class ReliefValveCalculator:

    def size(self, p: dict) -> dict:
        scenario = p.get("relief_scenario", "blocked_outlet")
        fluid = p.get("fluid", "Unknown")
        state = p.get("fluid_state", "vapor")
        P_set = p.get("set_pressure_kPag", 500)
        P_back = p.get("backpressure_kPag", 0)
        T_op = p.get("operating_temp", 100)
        MW = p.get("molecular_weight", 44)
        k = p.get("Cp_Cv_ratio", 1.3)

        # Relieving conditions (API 520: 10% accumulation for single PSV)
        P_relieve_kPa = (P_set * 1.1) + 101.325  # kPa abs
        T_relieve_K = (T_op + 273.15) * 1.1       # conservative

        # Required relief rate
        W_req = self._required_flowrate(p, scenario, P_set)

        if state == "vapor":
            result = self._size_vapor(W_req, P_relieve_kPa, T_relieve_K, MW, k, P_back)
        elif state == "liquid":
            result = self._size_liquid(W_req, P_relieve_kPa, P_back, p.get("fluid_density", 800))
        else:
            result = self._size_two_phase(W_req, P_relieve_kPa, T_relieve_K, MW, k)

        result.update({
            "equipment_tag": p.get("vessel_tag", "TBD"),
            "fluid": fluid,
            "fluid_state": state,
            "relief_scenario": scenario,
            "set_pressure_kPag": P_set,
            "backpressure_kPag": P_back,
            "relieving_pressure_kPa_abs": round(P_relieve_kPa, 1),
            "relieving_temperature_C": round(T_relieve_K - 273.15, 1),
            "required_relief_flowrate_kghr": round(W_req, 1),
            "standard": "API 520 Part I (9th Edition) / API 521",
            "warning": "⚠️ PSV sizing must be reviewed by a licensed engineer. Verify scenario flow rates from process data."
        })
        return result

    def _required_flowrate(self, p: dict, scenario: str, P_set: float) -> float:
        W_normal = p.get("normal_flowrate", 1000)   # kg/hr
        V_vessel = p.get("vessel_volume_m3", 1.0)

        if scenario == "blocked_outlet":
            return W_normal * 1.1

        elif scenario == "fire_case":
            # API 521 Eq: Q = 43200 * F * A^0.82 (BTU/hr) for wetted surface
            # Simplified: W = 0.1 * P_set^0.5 * V^0.6 in kg/hr
            A_wetted = 3.14 * (V_vessel ** (2/3)) * 4    # rough wetted area m2
            Q_fire_kW = 43200 * 1.0 * (A_wetted ** 0.82) * 0.29307 / 1000  # kW
            lambda_vap = 350   # kJ/kg estimate
            return Q_fire_kW / lambda_vap * 3600

        elif scenario == "cooling_failure":
            return W_normal * 1.5

        elif scenario == "thermal_expansion":
            return V_vessel * 0.02 * 800 * 3600  # very small, liquid expansion

        elif scenario == "control_valve_failure":
            return W_normal * 2.0

        elif scenario == "power_failure":
            return W_normal * 0.8

        return W_normal

    def _size_vapor(self, W: float, P1: float, T: float, MW: float, k: float, P_back: float) -> dict:
        # API 520 Eq 1: A = W / (C * Kd * P1 * Kb * Kc) * sqrt(T*Z/MW)
        # C = 520 * sqrt(k * (2/(k+1))^((k+1)/(k-1)))
        C = 520 * math.sqrt(k * (2 / (k + 1)) ** ((k + 1) / (k - 1)))
        Z = 1.0   # compressibility (assume ideal)

        A_cm2 = (W / 3600) / (C * Kd * (P1 / 101.325) * Kb * Kc) * math.sqrt(T * Z / MW) * 10000

        api_orifice = self._select_api_orifice(A_cm2)

        return {
            "C_constant": round(C, 1),
            "required_orifice_area_cm2": round(A_cm2, 4),
            "required_orifice_area_mm2": round(A_cm2 * 100, 2),
            "selected_api_orifice": api_orifice["designation"],
            "selected_orifice_area_cm2": api_orifice["area_cm2"],
            "sizing_method": "API 520 Vapor Flow (Eq. 1)",
        }

    def _size_liquid(self, W: float, P1: float, P_back: float, rho: float) -> dict:
        # API 520 liquid: A = Q / (Kd * Kw * Kc * Kv) * sqrt(rho / (P1 - P_back))
        Kw = 1.0
        Kv = 1.0
        dP = max(P1 - (P_back + 101.325), 10)   # kPa differential
        Q_m3s = (W / 3600) / rho

        A_cm2 = Q_m3s / (Kd * Kw * Kc * Kv) * math.sqrt(rho / (2 * dP * 1000)) * 10000

        api_orifice = self._select_api_orifice(A_cm2)

        return {
            "required_orifice_area_cm2": round(A_cm2, 4),
            "differential_pressure_kPa": round(dP, 1),
            "selected_api_orifice": api_orifice["designation"],
            "selected_orifice_area_cm2": api_orifice["area_cm2"],
            "sizing_method": "API 520 Liquid Flow",
        }

    def _size_two_phase(self, W: float, P1: float, T: float, MW: float, k: float) -> dict:
        # Omega method (simplified) — use vapor sizing as conservative
        result = self._size_vapor(W, P1, T, MW, k, 0)
        result["sizing_method"] = "API 520 Two-Phase (conservative vapor basis — Omega method recommended)"
        result["note"] = "For rigorous two-phase relief sizing, use HEM/Omega method per API 520 Appendix C"
        return result

    def _select_api_orifice(self, A_required_cm2: float) -> dict:
        # API 526 standard orifice designations
        api_orifices = [
            {"designation": "D", "area_cm2": 0.71},
            {"designation": "E", "area_cm2": 1.26},
            {"designation": "F", "area_cm2": 1.98},
            {"designation": "G", "area_cm2": 3.25},
            {"designation": "H", "area_cm2": 5.06},
            {"designation": "J", "area_cm2": 8.30},
            {"designation": "K", "area_cm2": 11.40},
            {"designation": "L", "area_cm2": 18.41},
            {"designation": "M", "area_cm2": 23.23},
            {"designation": "N", "area_cm2": 27.10},
            {"designation": "P", "area_cm2": 41.16},
            {"designation": "Q", "area_cm2": 71.61},
            {"designation": "R", "area_cm2": 103.23},
            {"designation": "T", "area_cm2": 167.74},
        ]
        for o in api_orifices:
            if o["area_cm2"] >= A_required_cm2:
                return o
        return {"designation": "T+", "area_cm2": A_required_cm2 * 1.1}
