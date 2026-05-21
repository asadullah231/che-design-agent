"""
Centrifugal Pump Sizing — TDH, NPSH, motor power
Per Hydraulic Institute standards
"""

import math


# Standard motor sizes in kW
MOTOR_SIZES_kW = [0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3.0, 4.0, 5.5, 7.5,
                  11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200]

# Typical velocities per service (m/s)
VELOCITY_LIMITS = {
    "suction": 1.0,
    "discharge": 3.0,
    "default_suction": 0.9,
    "default_discharge": 2.5,
}


class PumpCalculator:

    def design(self, p: dict) -> dict:
        Q_m3hr = p.get("flowrate", 10)
        Q_m3s = Q_m3hr / 3600
        rho = p.get("fluid_density", 1000)      # kg/m3
        mu = p.get("fluid_viscosity", 1.0)      # cP
        Pv = p.get("fluid_vapor_pressure", 3.0) # kPa abs
        P_s = p.get("suction_pressure", 101.3)  # kPa abs
        P_d = p.get("discharge_pressure", 400)  # kPa abs
        static_head = p.get("static_head", 0)   # m
        D_pipe_in = p.get("pipe_diameter", 3)   # inches
        L_eq = p.get("pipe_length", 50)         # m
        z_s = p.get("suction_liquid_level", 1.0) # m above pump centerline
        g = 9.81

        # Pipe sizing
        D_pipe_m = D_pipe_in * 0.0254
        A_pipe = math.pi * D_pipe_m ** 2 / 4
        v_suction = Q_m3s / A_pipe
        v_discharge = Q_m3s / A_pipe

        # Friction losses (Darcy-Weisbach)
        Re = rho * v_suction * D_pipe_m / (mu * 1e-3)
        f = self._friction_factor(Re)
        hf_suction = f * (L_eq / 2) * v_suction ** 2 / (2 * g * D_pipe_m)
        hf_discharge = f * (L_eq / 2) * v_discharge ** 2 / (2 * g * D_pipe_m)

        # Total Dynamic Head (TDH)
        head_pressure = (P_d - P_s) * 1000 / (rho * g)   # m
        head_velocity = (v_discharge ** 2 - v_suction ** 2) / (2 * g)
        TDH = head_pressure + static_head + hf_suction + hf_discharge + head_velocity

        # Hydraulic power
        P_hydraulic = rho * g * Q_m3s * TDH / 1000  # kW

        # Pump efficiency estimate
        eta_pump = self._estimate_efficiency(Q_m3hr, TDH)
        eta_motor = 0.93

        P_shaft = P_hydraulic / eta_pump
        P_motor_required = P_shaft / eta_motor
        P_motor_selected = self._select_motor(P_motor_required * 1.15)  # 15% margin

        # NPSH available
        NPSHa = (P_s * 1000 / (rho * g)) + z_s - hf_suction - (Pv * 1000 / (rho * g))
        NPSHr_typical = max(0.5, TDH * 0.05)  # rough estimate: 5% of TDH

        npsh_status = "OK" if NPSHa > NPSHr_typical + 0.6 else "WARNING — Risk of cavitation!"

        # Reynolds number for fluid category
        fluid_category = "Water-like" if mu < 5 else "Viscous — apply HI viscosity correction"

        return {
            "fluid": p.get("fluid", "Process Fluid"),
            "flowrate_m3hr": Q_m3hr,
            "fluid_density_kgm3": rho,
            "fluid_viscosity_cP": mu,
            "suction_pressure_kPa": P_s,
            "discharge_pressure_kPa": P_d,
            "total_dynamic_head_m": round(TDH, 2),
            "head_pressure_component_m": round(head_pressure, 2),
            "friction_losses_m": round(hf_suction + hf_discharge, 2),
            "static_head_m": static_head,
            "pipe_velocity_ms": round(v_suction, 2),
            "reynolds_number": round(Re, 0),
            "friction_factor": round(f, 5),
            "hydraulic_power_kW": round(P_hydraulic, 2),
            "pump_efficiency_pct": round(eta_pump * 100, 1),
            "shaft_power_kW": round(P_shaft, 2),
            "motor_power_required_kW": round(P_motor_required, 2),
            "motor_power_selected_kW": P_motor_selected,
            "NPSHa_m": round(NPSHa, 2),
            "NPSHr_estimated_m": round(NPSHr_typical, 2),
            "NPSH_status": npsh_status,
            "fluid_category": fluid_category,
            "standard": "Hydraulic Institute (HI) Standards",
            "warning": "Verify NPSHr from pump vendor curve before ordering."
        }

    def _friction_factor(self, Re: float, roughness: float = 0.046e-3, D: float = 0.1) -> float:
        if Re < 2300:
            return 64 / Re
        # Colebrook-White (simplified Swamee-Jain)
        er = roughness / D
        f = 0.25 / (math.log10(er / 3.7 + 5.74 / Re ** 0.9)) ** 2
        return f

    def _estimate_efficiency(self, Q_m3hr: float, H: float) -> float:
        # Correlation for centrifugal pump efficiency
        Ns = Q_m3hr ** 0.5 / H ** 0.75  # specific speed (metric, approx)
        eta = min(0.88, max(0.50, 0.55 + 0.15 * math.log(max(1, Q_m3hr))))
        return eta

    def _select_motor(self, P_required: float) -> float:
        for size in MOTOR_SIZES_kW:
            if size >= P_required:
                return size
        return MOTOR_SIZES_kW[-1]
