"""
Process Safety — HAZOP screening, flammability, toxic inventory assessment
"""


# Chemical hazard database — LFL, UFL, AIT, IDLH, Toxic category
HAZARD_DB = {
    "ethanol":       {"LFL": 3.3, "UFL": 19.0, "AIT": 365, "IDLH": 3300, "NFPA_H": 0, "NFPA_F": 3, "NFPA_R": 0},
    "methanol":      {"LFL": 6.0, "UFL": 36.5, "AIT": 385, "IDLH": 6000, "NFPA_H": 1, "NFPA_F": 3, "NFPA_R": 0},
    "acetone":       {"LFL": 2.5, "UFL": 12.8, "AIT": 465, "IDLH": 2500, "NFPA_H": 1, "NFPA_F": 3, "NFPA_R": 0},
    "benzene":       {"LFL": 1.2, "UFL": 7.8,  "AIT": 498, "IDLH": 500,  "NFPA_H": 2, "NFPA_F": 3, "NFPA_R": 0},
    "toluene":       {"LFL": 1.1, "UFL": 7.1,  "AIT": 480, "IDLH": 500,  "NFPA_H": 2, "NFPA_F": 3, "NFPA_R": 0},
    "hydrogen":      {"LFL": 4.0, "UFL": 75.0, "AIT": 500, "IDLH": None, "NFPA_H": 0, "NFPA_F": 4, "NFPA_R": 0},
    "ammonia":       {"LFL": 15.0,"UFL": 28.0, "AIT": 651, "IDLH": 300,  "NFPA_H": 3, "NFPA_F": 1, "NFPA_R": 0},
    "chlorine":      {"LFL": None,"UFL": None,  "AIT": None,"IDLH": 10,   "NFPA_H": 4, "NFPA_F": 0, "NFPA_R": 0},
    "propane":       {"LFL": 2.1, "UFL": 9.5,  "AIT": 450, "IDLH": 2100, "NFPA_H": 1, "NFPA_F": 4, "NFPA_R": 0},
    "natural gas":   {"LFL": 5.0, "UFL": 15.0, "AIT": 537, "IDLH": None, "NFPA_H": 1, "NFPA_F": 4, "NFPA_R": 0},
    "sulfuric acid": {"LFL": None,"UFL": None,  "AIT": None,"IDLH": 2,    "NFPA_H": 3, "NFPA_F": 0, "NFPA_R": 2},
    "water":         {"LFL": None,"UFL": None,  "AIT": None,"IDLH": None, "NFPA_H": 0, "NFPA_F": 0, "NFPA_R": 0},
}


class SafetyChecker:

    def check(self, p: dict) -> dict:
        eq_type = p.get("equipment_type", "Vessel")
        chemicals = [c.lower() for c in p.get("chemicals", [])]
        T_op = p.get("operating_temp", 25)
        P_op_g = p.get("operating_pressure", 0)     # kPag
        P_design_g = p.get("design_pressure", P_op_g * 1.1)
        inventory = p.get("inventory_kg", 0)
        location = p.get("location", "Outdoor")
        tag = p.get("equipment_tag", "TBD")

        hazards = self._assess_hazards(chemicals)
        hazop_nodes = self._hazop_screening(eq_type, chemicals, T_op, P_op_g)
        relief_scenarios = self._identify_relief_scenarios(eq_type, chemicals, T_op, P_op_g)
        atex_zone = self._atex_classification(hazards, location)
        overall_risk = self._risk_ranking(hazards, P_op_g, T_op, inventory)

        return {
            "equipment_tag": tag,
            "equipment_type": eq_type,
            "chemicals_assessed": p.get("chemicals", []),
            "operating_conditions": f"{T_op}°C / {P_op_g} kPag",
            "overall_risk_level": overall_risk,
            "flammability_hazards": hazards.get("flammable", []),
            "toxic_hazards": hazards.get("toxic", []),
            "reactive_hazards": hazards.get("reactive", []),
            "NFPA_ratings": hazards.get("nfpa", {}),
            "ATEX_classification": atex_zone,
            "HAZOP_key_concerns": hazop_nodes,
            "relief_scenarios_identified": relief_scenarios,
            "minimum_safeguards_required": self._minimum_safeguards(eq_type, P_design_g, hazards),
            "standard": "IEC 61511 / OSHA PSM (29 CFR 1910.119) / API 750",
            "disclaimer": "⚠️ This is a preliminary HAZOP screening only. A full HAZOP study facilitated by a qualified HAZOP leader is required before construction and operation."
        }

    def _assess_hazards(self, chemicals: list) -> dict:
        flammable = []
        toxic = []
        reactive = []
        nfpa = {}

        for chem in chemicals:
            data = HAZARD_DB.get(chem, {})
            if data.get("LFL"):
                flammable.append(f"{chem.title()}: LFL={data['LFL']}%, UFL={data['UFL']}%, AIT={data['AIT']}°C")
            if data.get("IDLH") and data["IDLH"] < 1000:
                toxic.append(f"{chem.title()}: IDLH={data['IDLH']} ppm — TOXIC")
            if data.get("NFPA_R", 0) >= 2:
                reactive.append(f"{chem.title()}: NFPA Reactivity={data['NFPA_R']}")
            if data:
                nfpa[chem.title()] = {
                    "Health": data.get("NFPA_H", "?"),
                    "Fire": data.get("NFPA_F", "?"),
                    "Reactivity": data.get("NFPA_R", "?")
                }

        return {"flammable": flammable, "toxic": toxic, "reactive": reactive, "nfpa": nfpa}

    def _hazop_screening(self, eq_type: str, chemicals: list, T: float, P: float) -> list:
        concerns = []

        concerns.append(f"MORE FLOW: Blocked outlet — overpressure risk. Require PSV sized for blocked outlet case.")
        concerns.append(f"NO FLOW: Pump cavitation / empty vessel — check NPSH and low-level trip (LAL).")
        concerns.append(f"MORE PRESSURE: Thermal expansion, external fire — verify relief device adequacy.")
        concerns.append(f"HIGH TEMPERATURE: Runaway reaction risk if exothermic chemistry present.")

        if P > 1000:
            concerns.append(f"HIGH PRESSURE SERVICE ({P} kPag) — pressure vessel integrity critical. Full radiography of welds recommended.")
        if T > 200:
            concerns.append(f"HIGH TEMPERATURE ({T}°C) — creep and material degradation risk. Verify material selection at design temp.")
        if any(c in chemicals for c in ["hydrogen", "methanol", "ethanol", "propane"]):
            concerns.append("FLAMMABLE MATERIAL — gas detector system, flame detector, and ESD system required.")
        if any(c in chemicals for c in ["chlorine", "ammonia", "sulfuric acid"]):
            concerns.append("TOXIC MATERIAL — continuous toxic gas monitor, emergency shower/eyewash, SCBA storage nearby required.")
        if eq_type.lower() in ["reactor", "cstr", "pfr"]:
            concerns.append("REACTOR — evaluate runaway reaction scenario. Emergency quench / dump tank / cooling failure analysis required.")

        return concerns

    def _identify_relief_scenarios(self, eq_type, chemicals, T, P) -> list:
        scenarios = ["Blocked outlet (control valve failure)"]
        if P > 0:
            scenarios.append("External fire case (if flammable inventory > threshold)")
        if T > 100:
            scenarios.append("Cooling failure / loss of coolant")
        if eq_type.lower() in ["reactor", "cstr", "pfr"]:
            scenarios.append("Runaway reaction — check whether PSV alone is adequate or dump/quench needed")
        scenarios.append("Thermal expansion (liquid-full system on blocked-in line)")
        scenarios.append("Power failure (pump trip — check if inlet isolation needed)")
        return scenarios

    def _atex_classification(self, hazards: dict, location: str) -> str:
        if not hazards["flammable"]:
            return "Non-classified (no flammable materials)"
        if location.lower() == "outdoor":
            return "Zone 2 (outdoor) — flammable vapors occasionally present under abnormal conditions"
        return "Zone 1 (indoor) — flammable vapors may be present under normal conditions. All electrical equipment must be ATEX rated."

    def _risk_ranking(self, hazards, P, T, inventory) -> str:
        score = 0
        if hazards["flammable"]: score += 2
        if hazards["toxic"]: score += 3
        if hazards["reactive"]: score += 2
        if P > 1000: score += 2
        if T > 200: score += 1
        if inventory > 10000: score += 2

        if score >= 7: return "HIGH — Formal HAZOP + LOPA required before operation"
        elif score >= 4: return "MEDIUM — HAZOP checklist + layer of protection review recommended"
        return "LOW — Standard operating procedure and risk assessment sufficient"

    def _minimum_safeguards(self, eq_type, P_design, hazards) -> list:
        guards = [
            "Pressure Safety Valve (PSV) — required for all pressurized equipment",
            "High pressure trip (PAHH) with solenoid valve",
            "Low level trip (LALL) to protect pump from dry run",
        ]
        if P_design > 345:  # 50 psig
            guards.append("Pressure vessel certification per ASME Sec VIII")
        if hazards["flammable"]:
            guards.append("Flammable gas detector + audible/visual alarm")
            guards.append("Earthing and bonding for static control")
        if hazards["toxic"]:
            guards.append("Toxic gas detector with alarm at 10% IDLH")
            guards.append("Emergency shower and eyewash station within 10 seconds travel")
        if eq_type.lower() in ["reactor", "cstr"]:
            guards.append("Emergency cooling / quench system (if exothermic reaction)")
            guards.append("High temperature trip (TAHH) on reactor")
        return guards
