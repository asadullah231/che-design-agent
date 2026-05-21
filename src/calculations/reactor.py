"""
Reactor Design — CSTR, PFR, Packed Bed, Batch
Design equations per Fogler "Elements of Chemical Reaction Engineering"
"""

import math


class ReactorCalculator:

    def design(self, p: dict) -> dict:
        rtype = p.get("reactor_type", "CSTR")
        if rtype == "CSTR":
            return self._cstr(p)
        elif rtype == "PFR":
            return self._pfr(p)
        elif rtype == "Packed Bed":
            return self._packed_bed(p)
        elif rtype == "Batch":
            return self._batch(p)
        return {"error": f"Unknown reactor type: {rtype}"}

    # ------------------------------------------------------------------
    def _cstr(self, p: dict) -> dict:
        X = p.get("desired_conversion", 0.9)
        T_C = p.get("temperature", 80)
        T_K = T_C + 273.15
        F_feed = p.get("feed_flowrate", 1000) / 3600   # kg/s
        k = self._effective_k(p, T_K)
        n = p.get("reaction_order", 1)
        Ca0 = p.get("initial_concentration", 1.0)    # kmol/m3 default

        # CSTR design equation: V = F_A0 * X / (-r_A) at exit
        # For nth order: -r_A = k * Ca0^n * (1-X)^n
        r_exit = k * (Ca0 ** n) * ((1 - X) ** n)      # kmol/m3/s
        FA0 = Ca0 * (F_feed / p.get("molecular_weight", 50))  # kmol/s approx
        V = FA0 * X / r_exit if r_exit > 0 else 999

        tau = Ca0 * X / r_exit if r_exit > 0 else 999
        volumetric_flow = F_feed / p.get("feed_density", 800)

        delta_H = p.get("heat_of_reaction", 0)
        Q_rxn = FA0 * X * delta_H * 1000 if delta_H else 0   # kW

        D, L = self._vessel_geometry(V, L_over_D=1.5)

        return {
            "reactor_type": "CSTR",
            "reaction": p.get("reaction", "A → Products"),
            "desired_conversion": X,
            "temperature_C": T_C,
            "pressure_kPa": p.get("pressure", 101.325),
            "rate_constant_k": round(k, 6),
            "reactor_volume_m3": round(V, 3),
            "residence_time_s": round(tau, 1),
            "residence_time_min": round(tau / 60, 2),
            "vessel_diameter_m": round(D, 3),
            "vessel_height_m": round(L, 3),
            "heat_of_reaction_kJmol": delta_H,
            "heat_duty_kW": round(Q_rxn, 2),
            "feed_flowrate_kghr": p.get("feed_flowrate", 1000),
            "note": "Design based on ideal CSTR assumption with perfect mixing"
        }

    def _pfr(self, p: dict) -> dict:
        X = p.get("desired_conversion", 0.9)
        T_C = p.get("temperature", 80)
        T_K = T_C + 273.15
        F_feed = p.get("feed_flowrate", 1000) / 3600
        k = self._effective_k(p, T_K)
        n = p.get("reaction_order", 1)
        Ca0 = p.get("initial_concentration", 1.0)

        # PFR: V = integral of dX / (-r_A/FA0)
        # For 1st order: V = FA0/k*Ca0 * ln(1/(1-X))
        # For nth order: numerical integration
        if n == 1:
            integral = math.log(1 / (1 - X))
        elif n == 2:
            integral = X / (Ca0 * (1 - X))
        else:
            # Simpson's rule
            integral = self._integrate_pfr(k, Ca0, n, X)

        FA0 = Ca0 * (F_feed / p.get("molecular_weight", 50))
        V = FA0 * integral / (k * Ca0 ** n)

        tau = Ca0 * integral / (k * Ca0 ** n)
        delta_H = p.get("heat_of_reaction", 0)
        Q_rxn = FA0 * X * delta_H * 1000 if delta_H else 0

        D, L = self._vessel_geometry(V, L_over_D=10)

        return {
            "reactor_type": "PFR (Plug Flow)",
            "reaction": p.get("reaction", "A → Products"),
            "desired_conversion": X,
            "temperature_C": T_C,
            "rate_constant_k": round(k, 6),
            "reactor_volume_m3": round(V, 3),
            "residence_time_s": round(tau, 1),
            "vessel_diameter_m": round(D, 3),
            "vessel_length_m": round(L, 3),
            "heat_duty_kW": round(Q_rxn, 2),
            "feed_flowrate_kghr": p.get("feed_flowrate", 1000),
            "note": "Isothermal PFR. For exothermic reactions, consider cooling jacket."
        }

    def _packed_bed(self, p: dict) -> dict:
        pfr_result = self._pfr(p)
        rho_cat = p.get("catalyst_bulk_density", 800)  # kg/m3
        V_bed = pfr_result["reactor_volume_m3"]
        W_cat = V_bed * rho_cat
        void_fraction = 0.4
        V_vessel = V_bed / (1 - void_fraction)
        D, L = self._vessel_geometry(V_vessel, L_over_D=5)
        WHSV = p.get("feed_flowrate", 1000) / W_cat if W_cat > 0 else 0

        pfr_result.update({
            "reactor_type": "Packed Bed Reactor (PBR)",
            "catalyst_bulk_density_kgm3": rho_cat,
            "catalyst_weight_kg": round(W_cat, 1),
            "bed_volume_m3": round(V_bed, 3),
            "vessel_volume_m3": round(V_vessel, 3),
            "vessel_diameter_m": round(D, 3),
            "vessel_length_m": round(L, 3),
            "void_fraction": void_fraction,
            "WHSV_hr": round(WHSV, 3),
            "note": "Isothermal PBR. Check pressure drop across bed (Ergun equation recommended)."
        })
        return pfr_result

    def _batch(self, p: dict) -> dict:
        X = p.get("desired_conversion", 0.9)
        T_C = p.get("temperature", 80)
        T_K = T_C + 273.15
        k = self._effective_k(p, T_K)
        n = p.get("reaction_order", 1)
        Ca0 = p.get("initial_concentration", 1.0)
        V_batch = p.get("batch_volume_m3", 1.0)

        if n == 1:
            t_rxn = math.log(1 / (1 - X)) / k
        elif n == 2:
            t_rxn = X / (k * Ca0 * (1 - X))
        else:
            t_rxn = X / (k * Ca0 ** (n - 1) * (1 - X) ** n)

        t_cycle = t_rxn + p.get("downtime_s", 3600)
        batches_per_day = 86400 / t_cycle
        daily_output = batches_per_day * V_batch * Ca0 * X * p.get("molecular_weight", 50)

        return {
            "reactor_type": "Batch Reactor",
            "reaction": p.get("reaction", "A → Products"),
            "desired_conversion": X,
            "temperature_C": T_C,
            "reaction_time_s": round(t_rxn, 1),
            "reaction_time_hr": round(t_rxn / 3600, 3),
            "cycle_time_hr": round(t_cycle / 3600, 3),
            "batches_per_day": round(batches_per_day, 1),
            "batch_volume_m3": V_batch,
            "daily_output_kg": round(daily_output, 1),
            "note": "Add filling, heating, cooling downtime to get total cycle time."
        }

    def _effective_k(self, p: dict, T_K: float) -> float:
        k_ref = p.get("rate_constant_k", 0.01)
        Ea = p.get("activation_energy", 50.0)  # kJ/mol
        T_ref = p.get("reference_temperature", 298.15)
        if Ea and T_ref:
            R = 8.314e-3  # kJ/mol/K
            k_eff = k_ref * math.exp(-Ea / R * (1 / T_K - 1 / T_ref))
        else:
            k_eff = k_ref
        return max(k_eff, 1e-12)

    def _integrate_pfr(self, k, Ca0, n, X, steps=1000) -> float:
        dx = X / steps
        integral = 0
        for i in range(steps):
            x = i * dx
            r = k * (Ca0 * (1 - x)) ** n
            integral += (Ca0 / r) * dx
        return integral * k * Ca0 ** n / Ca0

    def _vessel_geometry(self, V: float, L_over_D: float = 3.0):
        D = (4 * V / (math.pi * L_over_D)) ** (1 / 3)
        L = L_over_D * D
        return D, L
