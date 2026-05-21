"""
Pipe Sizing — Velocity check, pressure drop, ASME B31.3 schedule selection
Darcy-Weisbach method
"""

import math


# Allowable velocity ranges (m/s) per fluid phase and service
VELOCITY_LIMITS = {
    "liquid":    {"min": 0.5, "max": 3.0, "recommended": 1.5},
    "vapor":     {"min": 15,  "max": 30,  "recommended": 20},
    "two-phase": {"min": 3,   "max": 10,  "recommended": 5},
    "steam":     {"min": 20,  "max": 50,  "recommended": 30},
}

# ASME B31.3 — Allowable stress for CS pipe (kPa) at temperature
# SA-106B Seamless (approximate)
PIPE_ALLOWABLE_STRESS_kPa = {20: 137900, 100: 137900, 200: 117200, 300: 113800}

# Standard pipe schedule OD and wall thickness (inches → mm)
PIPE_SCHEDULES = {
    # NPS: {schedule: (OD_mm, t_mm)}
    0.5:  {"40": (21.3, 2.77),  "80": (21.3, 3.73)},
    0.75: {"40": (26.7, 2.87),  "80": (26.7, 3.91)},
    1:    {"40": (33.4, 3.38),  "80": (33.4, 4.55)},
    1.5:  {"40": (48.3, 3.68),  "80": (48.3, 5.08)},
    2:    {"40": (60.3, 3.91),  "80": (60.3, 5.54)},
    3:    {"40": (88.9, 5.49),  "80": (88.9, 7.62)},
    4:    {"40": (114.3, 6.02), "80": (114.3, 8.56)},
    6:    {"40": (168.3, 7.11), "80": (168.3, 10.97)},
    8:    {"40": (219.1, 8.18), "80": (219.1, 12.70)},
    10:   {"40": (273.1, 9.27), "80": (273.1, 15.09)},
    12:   {"40": (323.8, 9.53), "80": (323.8, 17.48)},
    16:   {"40": (406.4, 9.53), "80": (406.4, 21.44)},
    20:   {"40": (508.0, 9.53), "80": (508.0, 26.19)},
}

PIPE_ROUGHNESS = {
    "CS": 0.046e-3,       # m — commercial steel
    "SS316": 0.015e-3,
    "Duplex": 0.015e-3,
    "PVC": 0.0015e-3,
    "GRP": 0.01e-3,
}


class PipingCalculator:

    def size(self, p: dict) -> dict:
        fluid = p.get("fluid", "Process")
        phase = p.get("fluid_phase", "liquid")
        W_kghr = p.get("flowrate", 10000)
        rho = p.get("density", 800)
        mu = p.get("viscosity", 1.0)    # cP
        L_eq = p.get("pipe_length", 100)
        material = p.get("pipe_material", "CS")
        P_d = p.get("design_pressure", 1000)   # kPa gauge
        T_d = p.get("design_temperature", 100)

        W_kgs = W_kghr / 3600
        Q_m3s = W_kgs / rho
        limits = VELOCITY_LIMITS.get(phase, VELOCITY_LIMITS["liquid"])

        # Select NPS based on recommended velocity
        v_rec = limits["recommended"]
        A_req = Q_m3s / v_rec
        D_req_m = math.sqrt(4 * A_req / math.pi)

        nps, schedule, OD_mm, t_mm = self._select_pipe(D_req_m, P_d, T_d, material)
        D_i_mm = OD_mm - 2 * t_mm
        D_i_m = D_i_mm / 1e3
        A_actual = math.pi * D_i_m ** 2 / 4
        velocity = Q_m3s / A_actual

        # Reynolds number & friction factor
        mu_Pa_s = mu * 1e-3
        Re = rho * velocity * D_i_m / mu_Pa_s
        roughness = PIPE_ROUGHNESS.get(material, 0.046e-3)
        f = self._friction_factor(Re, roughness, D_i_m)

        # Pressure drop (Darcy-Weisbach)
        dP_Pa = f * (L_eq / D_i_m) * rho * velocity ** 2 / 2
        dP_kPa = dP_Pa / 1000
        dP_bar = dP_kPa / 100

        # Velocity check
        v_status = "OK"
        if velocity < limits["min"]:
            v_status = f"LOW — risk of settling/slugging (min {limits['min']} m/s)"
        elif velocity > limits["max"]:
            v_status = f"HIGH — erosion/noise risk (max {limits['max']} m/s)"

        return {
            "fluid": fluid,
            "fluid_phase": phase,
            "mass_flowrate_kghr": W_kghr,
            "volumetric_flowrate_m3hr": round(Q_m3s * 3600, 3),
            "selected_NPS_inches": nps,
            "schedule": schedule,
            "OD_mm": OD_mm,
            "wall_thickness_mm": t_mm,
            "ID_mm": round(D_i_mm, 2),
            "fluid_velocity_ms": round(velocity, 2),
            "velocity_status": v_status,
            "recommended_velocity_ms": v_rec,
            "reynolds_number": round(Re, 0),
            "flow_regime": "Turbulent" if Re > 4000 else "Transitional" if Re > 2300 else "Laminar",
            "friction_factor_darcy": round(f, 5),
            "pressure_drop_kPa": round(dP_kPa, 2),
            "pressure_drop_bar_per_100m": round(dP_bar / L_eq * 100, 4),
            "pipe_material": material,
            "design_pressure_kPag": P_d,
            "design_temperature_C": T_d,
            "standard": "ASME B31.3 Process Piping",
            "note": "Pressure drop excludes fittings — multiply by 1.3 for typical fitting allowance"
        }

    def _select_pipe(self, D_req_m: float, P_d_kPag: float, T_d: float, material: str):
        D_req_mm = D_req_m * 1000
        best_nps, best_sch, best_OD, best_t = 2, "40", 60.3, 3.91

        for nps, scheds in PIPE_SCHEDULES.items():
            for sch, (OD, t) in scheds.items():
                D_i = OD - 2 * t
                if D_i >= D_req_mm * 0.9:
                    # Check wall thickness per ASME B31.3: t_min = P*D/(2*S*E + 2*P*Y)
                    S = 137900   # kPa, CS allowable
                    E = 1.0
                    Y = 0.4      # for T < 900°F
                    t_min_mm = (P_d_kPag * OD) / (2 * S * E + 2 * P_d_kPag * Y)
                    if t >= t_min_mm:
                        best_nps, best_sch, best_OD, best_t = nps, sch, OD, t
                        break
            else:
                continue
            break

        return best_nps, best_sch, best_OD, best_t

    def _friction_factor(self, Re: float, roughness: float, D: float) -> float:
        if Re < 2300:
            return 64 / Re
        er = roughness / D
        f = 0.25 / (math.log10(er / 3.7 + 5.74 / Re ** 0.9)) ** 2
        return f
