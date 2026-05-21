"""
Distillation calculations - Shortcut and rigorous methods
Fenske-Underwood-Gilliland (FUG) shortcut method
"""

import math
from typing import List, Optional


# Relative volatility database (alpha relative to water or heavy key)
RELATIVE_VOLATILITY = {
    ("Ethanol", "Water"): 2.3,
    ("Methanol", "Water"): 3.8,
    ("Acetone", "Water"): 8.0,
    ("Benzene", "Toluene"): 2.5,
    ("Propane", "Butane"): 2.0,
    ("n-Butane", "n-Pentane"): 2.8,
    ("Isopropanol", "Water"): 2.1,
}


class DistillationCalculator:

    def shortcut_method(
        self,
        components: List[str],
        feed_composition: List[float],
        distillate_purity: float,
        bottoms_purity: float,
        feed_flowrate: float = 1000.0,
        operating_pressure: float = 101.325,
        feed_quality: float = 1.0,  # q=1 saturated liquid
        reflux_ratio_multiplier: float = 1.3,
    ) -> dict:
        """
        Fenske-Underwood-Gilliland shortcut distillation design.
        Returns dict with all key design parameters.
        """
        if len(components) < 2:
            return {"error": "Need at least 2 components"}

        light_key = components[0]
        heavy_key = components[1]
        z_lk = feed_composition[0]   # light key feed mole fraction
        z_hk = feed_composition[1]   # heavy key feed mole fraction

        x_d = distillate_purity       # distillate light key mole fraction
        x_b = 1 - bottoms_purity      # bottoms light key mole fraction

        # Get relative volatility
        alpha = self._get_alpha(light_key, heavy_key, operating_pressure)

        # --- Material Balance ---
        # F = D + B, F*z = D*x_d + B*x_b
        F = feed_flowrate
        D = F * (z_lk - x_b) / (x_d - x_b)
        B = F - D
        recovery_lk = (D * x_d) / (F * z_lk) * 100

        # --- Fenske: Minimum Stages ---
        N_min = math.log((x_d / (1 - x_d)) * ((1 - x_b) / x_b)) / math.log(alpha)

        # --- Underwood: Minimum Reflux ---
        # Simplified Underwood for binary system
        theta = self._underwood_theta(alpha, z_lk, feed_quality)
        R_min = (x_d / (alpha - theta)) - 1
        if R_min < 0:
            R_min = abs(R_min)

        # --- Actual Reflux Ratio ---
        R = reflux_ratio_multiplier * R_min

        # --- Gilliland: Actual Stages ---
        X = (R - R_min) / (R + 1)
        Y = 1 - math.exp((1 + 54.4 * X) / (11 + 117.2 * X) * (X - 1) / X ** 0.5)
        N_actual = (N_min + Y) / (1 - Y)
        N_actual = math.ceil(N_actual)

        # --- Feed Stage (Kirkbride) ---
        feed_stage = self._kirkbride_feed_stage(
            N_actual, z_lk, z_hk, x_d, x_b, D, B
        )

        # --- Column Sizing (approximate) ---
        vapor_flowrate = (R + 1) * D  # kmol/hr approx
        column_diameter = self._estimate_diameter(vapor_flowrate, operating_pressure)
        column_height = N_actual * 0.6  # 0.6 m tray spacing

        # --- Heat Duties ---
        condenser_duty = self._condenser_duty(R, D, components, x_d)
        reboiler_duty = self._reboiler_duty(condenser_duty, F, D, B)

        return {
            "method": "Fenske-Underwood-Gilliland Shortcut",
            "components": components,
            "feed_flowrate_kghr": round(F, 2),
            "distillate_flowrate_kghr": round(D, 2),
            "bottoms_flowrate_kghr": round(B, 2),
            "light_key_recovery_pct": round(recovery_lk, 2),
            "relative_volatility": round(alpha, 3),
            "minimum_stages": round(N_min, 1),
            "actual_stages": N_actual,
            "feed_stage": feed_stage,
            "minimum_reflux_ratio": round(R_min, 3),
            "operating_reflux_ratio": round(R, 3),
            "column_diameter_m": round(column_diameter, 2),
            "column_height_m": round(column_height, 2),
            "condenser_duty_kW": round(condenser_duty, 1),
            "reboiler_duty_kW": round(reboiler_duty, 1),
            "operating_pressure_kPa": operating_pressure,
            "distillate_composition": {
                light_key: round(x_d, 4),
                heavy_key: round(1 - x_d, 4)
            },
            "bottoms_composition": {
                light_key: round(x_b, 4),
                heavy_key: round(1 - x_b, 4)
            }
        }

    def _get_alpha(self, light_key: str, heavy_key: str, pressure: float) -> float:
        key = (light_key, heavy_key)
        rev_key = (heavy_key, light_key)
        if key in RELATIVE_VOLATILITY:
            return RELATIVE_VOLATILITY[key]
        elif rev_key in RELATIVE_VOLATILITY:
            return 1.0 / RELATIVE_VOLATILITY[rev_key]
        # Default assumption
        return 2.5

    def _underwood_theta(self, alpha: float, z_lk: float, q: float) -> float:
        # Simplified: theta between 1 and alpha for binary
        # Solve: alpha*z_lk/(alpha-theta) + z_hk/(1-theta) = 1 - q
        z_hk = 1 - z_lk
        # Numerical solve simplified
        for theta in [x * 0.01 for x in range(101, int(alpha * 100))]:
            lhs = alpha * z_lk / (alpha - theta) + z_hk / (1 - theta)
            if abs(lhs - (1 - q)) < 0.05:
                return theta
        return (1 + alpha) / 2  # fallback midpoint

    def _kirkbride_feed_stage(self, N, z_lk, z_hk, x_d, x_b, D, B) -> int:
        try:
            ratio = (z_hk / z_lk) * (x_b / (1 - x_d)) ** 2 * (B / D)
            feed_ratio = ratio ** 0.206
            nr = N / (1 + 1 / feed_ratio)
            return max(1, min(N - 1, round(nr)))
        except Exception:
            return N // 2

    def _estimate_diameter(self, vapor_kmolhr: float, pressure_kPa: float) -> float:
        # Approximate using flooding velocity concept
        vapor_vol_flow = vapor_kmolhr * 22.4 / 3600  # m3/s at STP approx
        u_flood = 0.5  # m/s typical flooding velocity
        area = vapor_vol_flow / (0.7 * u_flood)
        diameter = math.sqrt(4 * area / math.pi)
        return max(0.3, diameter)

    def _condenser_duty(self, R: float, D: float, components: list, x_d: float) -> float:
        # Approximate: Q_c = R * D * lambda (latent heat)
        # Average latent heat ~35 kJ/mol, MW ~46 (ethanol-water mix approx)
        MW_avg = 46 * x_d + 18 * (1 - x_d)
        lambda_kJkg = 900  # kJ/kg approximate
        D_kgs = D / 3600
        return R * D_kgs * lambda_kJkg  # kW

    def _reboiler_duty(self, Q_c: float, F: float, D: float, B: float) -> float:
        # Energy balance: Q_r ≈ Q_c + small correction
        return Q_c * 1.05  # reboiler slightly more than condenser
