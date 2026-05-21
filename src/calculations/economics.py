"""
Process Economics — CAPEX/OPEX estimation, NPV, IRR, payback
Lang Factor method + factored CAPEX estimate
"""

import math


# Location cost factors relative to US Gulf Coast
LOCATION_FACTORS = {
    "US Gulf Coast": 1.00,
    "Pakistan":      0.65,
    "Middle East":   0.90,
    "Europe":        1.35,
    "Southeast Asia": 0.80,
}

# Equipment purchase cost exponents (Power law: C = C_ref * (S/S_ref)^n)
# (C_ref in USD 2024, S_ref in base unit)
EQUIPMENT_COST_DB = {
    "Distillation Column": {"C_ref": 180000, "S_ref": 10, "n": 0.7, "unit": "m3 volume"},
    "Heat Exchanger":      {"C_ref": 35000,  "S_ref": 50, "n": 0.6, "unit": "m2 area"},
    "Reactor":             {"C_ref": 150000, "S_ref": 5,  "n": 0.65,"unit": "m3 volume"},
    "Pump":                {"C_ref": 8000,   "S_ref": 10, "n": 0.4, "unit": "kW"},
    "Compressor":          {"C_ref": 90000,  "S_ref": 75, "n": 0.6, "unit": "kW"},
    "Storage Tank":        {"C_ref": 25000,  "S_ref": 50, "n": 0.55,"unit": "m3"},
    "Pressure Vessel":     {"C_ref": 60000,  "S_ref": 5,  "n": 0.65,"unit": "m3"},
    "Filter":              {"C_ref": 12000,  "S_ref": 5,  "n": 0.5, "unit": "m2"},
}

# Lang factors by plant type
LANG_FACTORS = {
    "Fluid Processing":       4.74,
    "Mixed (Fluid-Solid)":    3.63,
    "Solid Processing":       3.10,
}


class EconomicsCalculator:

    def analyze(self, p: dict) -> dict:
        project = p.get("project_name", "New Project")
        capacity = p.get("plant_capacity_tpy", 10000)
        loc_factor = LOCATION_FACTORS.get(p.get("location_factor", "US Gulf Coast"), 1.0)
        location = p.get("location_factor", "US Gulf Coast")

        # Equipment cost estimate
        eq_list = p.get("equipment_list", [])
        eq_costs = self._estimate_equipment_costs(eq_list, loc_factor)
        C_equipment = sum(eq_costs.values()) if eq_costs else self._capacity_estimate(capacity)

        # Lang factor CAPEX
        lang = LANG_FACTORS["Fluid Processing"]
        CAPEX = C_equipment * lang * loc_factor
        CAPEX_low = CAPEX * 0.7
        CAPEX_high = CAPEX * 1.3

        # Working capital
        working_capital = CAPEX * 0.15

        # OPEX
        raw_mat_cost = p.get("raw_material_cost_per_ton", 200) * capacity
        utility_cost = p.get("utility_cost_per_year", CAPEX * 0.03)
        labor_cost = max(200000, CAPEX * 0.02)
        maintenance = CAPEX * 0.025
        overhead = (labor_cost + maintenance) * 0.6
        depreciation = CAPEX / p.get("project_life_years", 20)
        OPEX = raw_mat_cost + utility_cost + labor_cost + maintenance + overhead

        # Revenue
        product_price = p.get("product_price_per_ton", 500)
        revenue = product_price * capacity * 0.95   # 95% operating factor

        # Profitability
        EBITDA = revenue - OPEX
        EBIT = EBITDA - depreciation
        tax = max(0, EBIT * 0.25)
        net_income = EBIT - tax

        years = int(p.get("project_life_years", 20))
        discount_rate = p.get("discount_rate", 0.10)

        npv, irr, payback = self._profitability(
            CAPEX + working_capital, net_income + depreciation, years, discount_rate
        )

        return {
            "project_name": project,
            "location": location,
            "plant_capacity_tpy": capacity,
            "estimate_accuracy": "±30% (Lang Factor / Order of Magnitude)",
            "equipment_purchase_cost_USD": round(C_equipment, 0),
            "equipment_costs_breakdown": eq_costs,
            "lang_factor_used": lang,
            "CAPEX_USD": round(CAPEX, 0),
            "CAPEX_range_USD": f"${CAPEX_low:,.0f} — ${CAPEX_high:,.0f}",
            "working_capital_USD": round(working_capital, 0),
            "total_investment_USD": round(CAPEX + working_capital, 0),
            "annual_revenue_USD": round(revenue, 0),
            "annual_OPEX_USD": round(OPEX, 0),
            "raw_material_cost_USD": round(raw_mat_cost, 0),
            "utility_cost_USD": round(utility_cost, 0),
            "labor_cost_USD": round(labor_cost, 0),
            "annual_EBITDA_USD": round(EBITDA, 0),
            "annual_net_income_USD": round(net_income, 0),
            "NPV_USD": round(npv, 0),
            "IRR_pct": round(irr * 100, 1),
            "payback_period_years": round(payback, 1),
            "project_viable": "YES" if irr > discount_rate else "NO — IRR below hurdle rate",
            "standard": "AACE International Class 5 Estimate (Lang Factor Method)",
            "note": "Costs in 2024 USD. Escalate to project year using CEPCI index."
        }

    def _estimate_equipment_costs(self, eq_list: list, loc: float) -> dict:
        costs = {}
        for eq in eq_list:
            name = eq.get("name", "Equipment")
            etype = eq.get("type", "")
            size = eq.get("size_parameter", 1)
            db = EQUIPMENT_COST_DB.get(etype, {})
            if db:
                C = db["C_ref"] * (size / db["S_ref"]) ** db["n"]
            else:
                C = 50000  # default unknown equipment
            costs[name] = round(C, 0)
        return costs

    def _capacity_estimate(self, capacity_tpy: float) -> float:
        # Rough correlation: C_equip ~ 2000 * capacity^0.6 USD
        return 2000 * (capacity_tpy ** 0.6)

    def _profitability(self, investment: float, annual_cf: float, years: int, r: float):
        # NPV
        npv = sum(annual_cf / (1 + r) ** t for t in range(1, years + 1)) - investment

        # Payback (simple)
        payback = investment / annual_cf if annual_cf > 0 else 999

        # IRR — Newton-Raphson
        irr = self._irr(investment, annual_cf, years)

        return npv, irr, payback

    def _irr(self, investment: float, annual_cf: float, years: int) -> float:
        if annual_cf <= 0:
            return 0
        # Binary search
        lo, hi = -0.5, 5.0
        for _ in range(100):
            mid = (lo + hi) / 2
            npv = sum(annual_cf / (1 + mid) ** t for t in range(1, years + 1)) - investment
            if abs(npv) < 1:
                return mid
            if npv > 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
