"""
Heat Exchanger Design - LMTD and NTU methods
"""

import math


# Overall heat transfer coefficients (W/m2.K) - typical values
U_VALUES = {
    "Shell and Tube": {
        ("water", "water"): 1000,
        ("steam", "water"): 2000,
        ("oil", "water"): 300,
        ("gas", "water"): 50,
        "default": 500,
    },
    "Plate": {
        ("water", "water"): 3000,
        ("steam", "water"): 4000,
        "default": 2000,
    },
    "Double Pipe": {
        "default": 800,
    }
}

# Specific heat capacities (kJ/kg.K)
CP_DATA = {
    "water": 4.18,
    "steam": 2.01,
    "air": 1.005,
    "oil": 2.0,
    "ethanol": 2.44,
    "methanol": 2.53,
}


class HeatExchangerCalculator:

    def design(self, params: dict) -> dict:
        hot_fluid = params["hot_fluid"].lower()
        cold_fluid = params["cold_fluid"].lower()
        T_hi = params["hot_inlet_temp"]
        T_ho = params["hot_outlet_temp"]
        T_ci = params["cold_inlet_temp"]
        m_h = params["hot_flowrate"] / 3600   # kg/s
        m_c = params.get("cold_flowrate", 0) / 3600
        hx_type = params.get("exchanger_type", "Shell and Tube")

        Cp_h = CP_DATA.get(hot_fluid, 4.18)
        Cp_c = CP_DATA.get(cold_fluid, 4.18)

        # Heat duty
        Q = m_h * Cp_h * (T_hi - T_ho) * 1000  # W

        # Cold side outlet temperature
        if m_c > 0:
            T_co = T_ci + Q / (m_c * Cp_c * 1000)
        else:
            # Calculate required cold flowrate for 10 deg rise
            T_co = T_ci + 10
            m_c = Q / (Cp_c * 1000 * (T_co - T_ci))

        # LMTD (counterflow assumed)
        delta_T1 = T_hi - T_co
        delta_T2 = T_ho - T_ci

        if delta_T1 <= 0 or delta_T2 <= 0:
            lmtd = abs(delta_T1 - delta_T2) / 2
        elif delta_T1 == delta_T2:
            lmtd = delta_T1
        else:
            lmtd = (delta_T1 - delta_T2) / math.log(delta_T1 / delta_T2)

        # F correction factor (assume 0.9 for shell & tube 1-2 pass)
        F = 0.9 if hx_type == "Shell and Tube" else 1.0

        # Overall U
        U = self._get_U(hx_type, hot_fluid, cold_fluid)

        # Heat transfer area
        if lmtd > 0 and F > 0:
            A = Q / (U * F * lmtd)
        else:
            A = 0

        # NTU
        C_min = min(m_h * Cp_h, m_c * Cp_c) * 1000
        NTU = U * A / C_min if C_min > 0 else 0

        return {
            "exchanger_type": hx_type,
            "hot_fluid": params["hot_fluid"],
            "cold_fluid": params["cold_fluid"],
            "heat_duty_kW": round(Q / 1000, 2),
            "hot_inlet_temp_C": T_hi,
            "hot_outlet_temp_C": T_ho,
            "cold_inlet_temp_C": round(T_ci, 2),
            "cold_outlet_temp_C": round(T_co, 2),
            "LMTD_C": round(lmtd, 2),
            "F_correction": F,
            "U_overall_W_m2K": U,
            "heat_transfer_area_m2": round(A, 2),
            "NTU": round(NTU, 3),
            "hot_flowrate_kghr": round(m_h * 3600, 2),
            "cold_flowrate_kghr": round(m_c * 3600, 2),
        }

    def _get_U(self, hx_type: str, hot: str, cold: str) -> float:
        table = U_VALUES.get(hx_type, {})
        return (
            table.get((hot, cold))
            or table.get((cold, hot))
            or table.get("default", 500)
        )
