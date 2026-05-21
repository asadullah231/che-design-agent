"""
Pressure Vessel Sizing — ASME Section VIII Division 1
Wall thickness, head design, weight estimation
"""

import math


# Allowable stress (S) in MPa for common materials at temperature
# Source: ASME Sec II Part D (approximate values)
MATERIAL_STRESS = {
    "SA-516-70":  {20: 137.9, 100: 137.9, 200: 129.6, 300: 120.7, 400: 103.4},
    "SA-516-60":  {20: 120.7, 100: 120.7, 200: 115.1, 300: 103.4},
    "SS-316L":    {20: 115.1, 100: 115.1, 200: 110.3, 300: 103.4, 400: 93.1},
    "SS-304L":    {20: 115.1, 100: 115.1, 200: 110.3, 300: 103.4},
    "SA-106B":    {20: 120.7, 100: 120.7, 200: 117.2, 300: 113.8, 400: 103.4},
    "Hastelloy-C276": {20: 206.8, 100: 206.8, 200: 200.0, 300: 193.0},
}

# Density kg/m3
MATERIAL_DENSITY = {
    "SA-516-70": 7850, "SA-516-60": 7850, "SA-106B": 7850,
    "SS-316L": 7980, "SS-304L": 7930,
    "Hastelloy-C276": 8890,
}

HEAD_THICKNESS_FACTOR = {
    "Ellipsoidal 2:1": 1.0,      # same formula as shell
    "Hemispherical": 0.5,
    "Torispherical": 1.77,       # flat ASME F&D head
    "Flat": 0.0,                 # separate formula
}


class VesselCalculator:

    def size(self, p: dict) -> dict:
        P_d = p.get("design_pressure_kPag", 500)     # kPa gauge
        T_d = p.get("design_temperature", 150)        # °C
        D_i = p.get("internal_diameter_m", 1.0)       # m
        L = p.get("vessel_length_m", 3.0)             # m
        material = p.get("material", "SA-516-70")
        CA = p.get("corrosion_allowance_mm", 3.0)     # mm
        E = p.get("joint_efficiency", 1.0)
        head_type = p.get("head_type", "Ellipsoidal 2:1")
        vessel_type = p.get("vessel_type", "Vertical")
        tag = p.get("vessel_tag", "V-001")

        # Design pressure in MPa
        P_MPa = P_d / 1000

        # Allowable stress
        S = self._allowable_stress(material, T_d)

        # Shell wall thickness (ASME VIII Div 1, UG-27)
        # t = P*R / (S*E - 0.6*P)
        R_i = D_i / 2 * 1000  # mm
        t_shell = (P_MPa * R_i) / (S * E - 0.6 * P_MPa)
        t_shell_design = t_shell + CA  # add corrosion allowance
        t_shell_nominal = self._next_plate_thickness(t_shell_design)

        # Head thickness
        t_head = self._head_thickness(P_MPa, R_i, S, E, CA, head_type)
        t_head_nominal = self._next_plate_thickness(t_head)

        # Actual D_o
        D_o_mm = D_i * 1000 + 2 * t_shell_nominal
        D_o_m = D_o_mm / 1000

        # Weight estimate
        rho_mat = MATERIAL_DENSITY.get(material, 7850)
        V_shell = math.pi * (D_o_m ** 2 - D_i ** 2) / 4 * L
        V_head = 2 * math.pi / 6 * (D_i ** 3) * 0.05   # approx 2:1 ellipsoidal heads
        weight_shell_kg = (V_shell + V_head) * rho_mat
        weight_empty_kg = weight_shell_kg * 1.15  # +15% for nozzles, supports

        # Hydrostatic test pressure
        P_test = P_d * 1.3

        # MAWP at design temp (back-calculate from nominal thickness)
        t_net = t_shell_nominal - CA
        MAWP = S * E * t_net / (R_i + 0.6 * t_net)  # MPa
        MAWP_kPag = MAWP * 1000

        return {
            "vessel_tag": tag,
            "vessel_type": vessel_type,
            "internal_diameter_m": D_i,
            "tangent_to_tangent_length_m": L,
            "design_pressure_kPag": P_d,
            "design_temperature_C": T_d,
            "material": material,
            "allowable_stress_MPa": round(S, 1),
            "joint_efficiency": E,
            "corrosion_allowance_mm": CA,
            "head_type": head_type,
            "shell_thickness_calculated_mm": round(t_shell, 2),
            "shell_thickness_with_CA_mm": round(t_shell_design, 2),
            "shell_thickness_nominal_mm": t_shell_nominal,
            "head_thickness_nominal_mm": t_head_nominal,
            "outer_diameter_m": round(D_o_m, 4),
            "MAWP_kPag": round(MAWP_kPag, 1),
            "hydrostatic_test_pressure_kPag": round(P_test, 1),
            "vessel_empty_weight_kg": round(weight_empty_kg, 0),
            "standard": "ASME Section VIII Division 1 (UG-27, UG-32)",
            "warning": "⚠️ This is a preliminary sizing. Final design must be certified by an ASME-authorized engineer and stamped per code."
        }

    def _allowable_stress(self, material: str, T_C: float) -> float:
        stress_table = MATERIAL_STRESS.get(material, MATERIAL_STRESS["SA-516-70"])
        temps = sorted(stress_table.keys())
        for i, t in enumerate(temps):
            if T_C <= t:
                if i == 0:
                    return stress_table[t]
                t_lo, t_hi = temps[i - 1], t
                S_lo, S_hi = stress_table[t_lo], stress_table[t_hi]
                return S_lo + (S_hi - S_lo) * (T_C - t_lo) / (t_hi - t_lo)
        return stress_table[temps[-1]]  # extrapolate (conservative = use last value)

    def _head_thickness(self, P, R_i, S, E, CA, head_type) -> float:
        if head_type == "Hemispherical":
            t = P * R_i / (2 * S * E - 0.2 * P)
        elif head_type == "Flat":
            C = 0.33  # flat head factor
            t = D = R_i * 2
            t = C * D * math.sqrt(P / (S * E))
        else:
            # Ellipsoidal 2:1 and Torispherical — same as shell (approx)
            t = P * R_i / (S * E - 0.6 * P)
        return t + CA

    def _next_plate_thickness(self, t_mm: float) -> float:
        standard = [3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 30, 32, 38, 40, 50, 60, 75]
        for s in standard:
            if s >= t_mm:
                return s
        return math.ceil(t_mm / 5) * 5
