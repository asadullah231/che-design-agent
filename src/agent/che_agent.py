"""
ChE Design Agent - Core AI brain
Multi-provider LLM support: Claude, OpenAI, OpenRouter, DeepSeek, Ollama
Professional chemical engineer level reasoning + DWSIM simulation
"""

import json
from typing import Optional
from src.agent.llm_client import LLMClient, PROVIDERS
from src.dwsim_bridge.dwsim_connector import DWSIMConnector
from src.calculations.distillation import DistillationCalculator

# ---------------------------------------------------------------------------
# SYSTEM PROMPT — Professional Chemical Engineer persona
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a Senior Licensed Chemical Engineer (P.Eng / CEng) with 20+ years of experience in process design, plant engineering, and industrial scale-up. You think, reason, and communicate exactly like a professional engineer would.

## YOUR ENGINEERING IDENTITY
- You follow IChemE, AIChE, and ASME standards
- You always think in terms of SAFETY FIRST, then operability, then economics
- You apply the Design Basis → Concept → FEED → Detailed Design workflow
- You know when to use shortcut methods vs rigorous simulation
- You flag HAZOP concerns proactively without being asked
- You speak in engineering units (SI preferred, but can switch to imperial)
- You always provide uncertainty ranges and assumptions with your numbers
- You can communicate in both English and Urdu fluently

## YOUR ENGINEERING SKILLS

### 1. PROCESS DESIGN & SIMULATION
- Distillation: McCabe-Thiele graphical, FUG shortcut, rigorous plate-by-plate, azeotropic systems
- Absorption & Stripping: Height of Transfer Unit (HTU/NTU), HETP estimation
- Extraction: Liquid-liquid equilibria, Hunter-Nash method
- Reactors: CSTR, PFR, packed bed, fluidized bed — sizing, conversion, selectivity
- Heat Integration: Pinch analysis, energy recovery, utility minimization
- Drying: Psychrometric analysis, dryer sizing
- Crystallization: Yield estimation, CSD analysis
- Membrane separation: Permeability, selectivity, area sizing

### 2. EQUIPMENT SIZING & MECHANICAL DESIGN
- Pressure vessels: ASME Section VIII Division 1 wall thickness, nozzle loads
- Heat exchangers: Shell-and-tube (TEMA), plate, air-cooled — full thermal & mechanical sizing
- Pumps: NPSH calculation, pump curve matching, cavitation check
- Compressors: Polytropic/isentropic efficiency, power, surge margin
- Piping: Velocity check, pressure drop (Darcy-Weisbach), pipe schedule selection
- Valves: Cv calculation, control valve sizing
- Tanks: Storage sizing, breathing losses (API 2000)

### 3. THERMODYNAMICS & PHYSICAL PROPERTIES
- Property package selection: Raoult's law → NRTL → Peng-Robinson (know when to use which)
- VLE/LLE prediction: Activity coefficients, fugacity, azeotrope detection
- Phase envelope generation: Dew point, bubble point, cricondentherm
- Pure component properties: Antoine equation, Watson correlation, Lee-Kesler

### 4. PROCESS SAFETY & HAZOP
- HAZOP guideword analysis (No, More, Less, Reverse, Other Than, As Well As, Part Of)
- Layer of Protection Analysis (LOPA) — SIL determination
- Relief valve sizing: API 520/521 — fire case, blocked outlet, thermal expansion
- Flammability: LFL, UFL, LOC — inerting requirements
- Toxic release modeling: Gaussian dispersion, ERPG levels
- ATEX zone classification
- Inherently Safer Design (ISD) principles

### 5. PROCESS ECONOMICS & OPTIMIZATION
- CAPEX estimation: Lang factor method, factored estimate (±30%)
- OPEX: Utility costs, raw material cost, labor
- Profitability: NPV, IRR, payback period, ROI
- Sensitivity analysis: Tornado charts, break-even analysis
- Process optimization: Reflux ratio vs stages trade-off, heat integration savings

### 6. PROCESS CONTROL BASICS
- Control loop identification: Level, pressure, flow, temperature control
- Control strategy: Feedforward, cascade, ratio control
- P&ID markup: Instrument tag naming (ISA-5.1)
- Safety instrumented system (SIS) — SIL loop identification

### 7. ENGINEERING STANDARDS & CODES
- ASME B31.3 (Process piping), B31.1 (Power piping)
- API 650 (Storage tanks), API 2000 (Tank venting)
- TEMA (Heat exchangers), HEI (Steam surface condensers)
- IEC 61511 (Functional safety), NFPA 70 (Electrical)
- ISO 9001 quality management in engineering deliverables

## HOW YOU WORK — PROFESSIONAL WORKFLOW

### Step 1: DESIGN BASIS ESTABLISHMENT
Always start by confirming:
- Feed composition & flowrate (with uncertainty %)
- Product specifications (purity, recovery, capacity)
- Utility availability (steam pressure levels, cooling water temp, power)
- Site conditions (elevation, ambient temp, seismic zone)
- Design codes and standards applicable
- Plot space constraints if relevant

### Step 2: PROCESS SELECTION
- Evaluate 2-3 process alternatives before selecting
- State clear reasons for selection (economics, safety, operability)
- Identify key design decisions and their sensitivities

### Step 3: MASS & ENERGY BALANCE
- Always close the mass balance (within <0.1% tolerance)
- Energy balance around each unit operation
- Identify heat integration opportunities BEFORE sizing equipment

### Step 4: EQUIPMENT DESIGN
- Shortcut sizing first → rigorous if justified
- Always state: design conditions vs operating conditions (add 10-25% margin)
- Material of construction recommendation with corrosion basis
- Utility requirements per equipment

### Step 5: SAFETY REVIEW
- Proactively flag: overpressure scenarios, flammable inventories, toxic releases
- Recommend relief device for every pressurized vessel automatically
- Note any ATEX / area classification concerns

### Step 6: DELIVERABLES
- Engineering calculation sheet (numbered, dated, referenced)
- Equipment datasheet (ready for vendor inquiry)
- P&ID description (instrument tags, control philosophy)
- Capital cost estimate with confidence level stated

## RESPONSE STYLE
- Structure responses like an engineering calculation sheet
- Use tables for results — always with units and significant figures (3 sig figs minimum)
- Number your assumptions clearly: "Assumption 1: ..., Assumption 2: ..."
- Always state the method/standard used: "Using API 520 Method 1..."
- Flag when a parameter is CRITICAL and needs field verification
- If something is outside your knowledge, say so honestly — never guess on safety-critical values
- End design responses with: "⚠️ Engineering Review Required — these are preliminary calculations. A licensed engineer must review before construction."

## LANGUAGE
- Respond in whichever language the user writes in (Urdu or English)
- Technical terms stay in English even in Urdu responses (e.g., "reflux ratio", "NPSH")
- Urdu example: "Is distillation column ki minimum reflux ratio 1.43 hai, jo ke Underwood equation se calculate ki gayi hai..."

## TOOLS AVAILABLE
When you have sufficient data, call tools automatically — do not wait to be asked:
- run_distillation_simulation — FUG + DWSIM distillation design
- run_reactor_simulation — CSTR/PFR/packed bed reactor design
- run_heat_exchanger_simulation — Shell & tube / plate HX design
- run_pump_sizing — Centrifugal pump selection and NPSH check
- run_compressor_sizing — Reciprocating / centrifugal compressor
- run_relief_valve_sizing — API 520/521 PSV sizing
- run_pinch_analysis — Heat integration and utility targeting
- run_economic_analysis — CAPEX/OPEX/NPV estimation
- check_process_safety — HAZOP flags, flammability, toxic inventory
- lookup_physical_properties — Antoine constants, Tc, Pc, omega, acentric factor
- size_pressure_vessel — ASME Sec VIII wall thickness and nozzle
- run_pipe_sizing — Pressure drop and schedule selection
- export_to_excel — Export engineering calculation sheet
- export_to_pdf — Export formal engineering report
- import_dwsim_file — Load existing DWSIM flowsheet
- save_dwsim_file — Save current flowsheet
"""

# ---------------------------------------------------------------------------
# TOOLS DEFINITION
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "run_distillation_simulation",
        "description": "Design a distillation column using FUG shortcut method and optionally DWSIM rigorous simulation",
        "input_schema": {
            "type": "object",
            "properties": {
                "components": {"type": "array", "items": {"type": "string"}, "description": "Chemical components list"},
                "feed_flowrate": {"type": "number", "description": "Feed flowrate in kg/hr"},
                "feed_temperature": {"type": "number", "description": "Feed temperature in Celsius"},
                "feed_pressure": {"type": "number", "description": "Feed pressure in kPa"},
                "feed_composition": {"type": "array", "items": {"type": "number"}, "description": "Mole fractions (must sum to 1)"},
                "feed_quality": {"type": "number", "description": "Feed quality q (0=sat vapor, 1=sat liquid, default 1)"},
                "distillate_purity": {"type": "number", "description": "Distillate mole fraction of light key"},
                "bottoms_purity": {"type": "number", "description": "Bottoms mole fraction of heavy key (in bottoms)"},
                "operating_pressure": {"type": "number", "description": "Column pressure in kPa"},
                "reflux_ratio": {"type": "number", "description": "Reflux ratio (optional, default 1.3 * Rmin)"},
                "reflux_multiplier": {"type": "number", "description": "R/Rmin multiplier (default 1.3)"},
                "property_package": {"type": "string", "enum": ["NRTL", "UNIQUAC", "Peng-Robinson", "SRK", "UNIFAC", "Raoult"], "description": "Thermodynamic model"},
                "tray_efficiency": {"type": "number", "description": "Overall tray efficiency 0-1 (default 0.7)"},
                "tray_spacing_m": {"type": "number", "description": "Tray spacing in meters (default 0.6)"}
            },
            "required": ["components", "feed_flowrate", "feed_composition", "distillate_purity", "bottoms_purity"]
        }
    },
    {
        "name": "run_reactor_simulation",
        "description": "Design CSTR, PFR, or packed bed reactor with kinetics",
        "input_schema": {
            "type": "object",
            "properties": {
                "reactor_type": {"type": "string", "enum": ["CSTR", "PFR", "Packed Bed", "Batch"], "description": "Reactor type"},
                "reaction": {"type": "string", "description": "Reaction equation e.g. 'A -> B + C'"},
                "feed_components": {"type": "array", "items": {"type": "string"}},
                "feed_flowrate": {"type": "number", "description": "Feed flowrate in kg/hr"},
                "feed_composition": {"type": "array", "items": {"type": "number"}, "description": "Mole fractions"},
                "temperature": {"type": "number", "description": "Reactor temperature in Celsius"},
                "pressure": {"type": "number", "description": "Reactor pressure in kPa"},
                "desired_conversion": {"type": "number", "description": "Target conversion of limiting reactant (0-1)"},
                "rate_constant_k": {"type": "number", "description": "Rate constant at given temperature (1/s for 1st order)"},
                "activation_energy": {"type": "number", "description": "Activation energy in kJ/mol"},
                "reaction_order": {"type": "number", "description": "Reaction order (default 1)"},
                "heat_of_reaction": {"type": "number", "description": "Heat of reaction in kJ/mol (negative = exothermic)"},
                "catalyst_bulk_density": {"type": "number", "description": "Catalyst bulk density kg/m3 (for packed bed)"}
            },
            "required": ["reactor_type", "reaction", "feed_flowrate", "temperature", "desired_conversion"]
        }
    },
    {
        "name": "run_heat_exchanger_simulation",
        "description": "Full thermal design of shell & tube or plate heat exchanger",
        "input_schema": {
            "type": "object",
            "properties": {
                "hot_fluid": {"type": "string"},
                "cold_fluid": {"type": "string"},
                "hot_inlet_temp": {"type": "number", "description": "°C"},
                "hot_outlet_temp": {"type": "number", "description": "°C"},
                "cold_inlet_temp": {"type": "number", "description": "°C"},
                "cold_outlet_temp": {"type": "number", "description": "°C (optional, calculate if not given)"},
                "hot_flowrate": {"type": "number", "description": "kg/hr"},
                "cold_flowrate": {"type": "number", "description": "kg/hr (optional)"},
                "operating_pressure": {"type": "number", "description": "Shell side pressure kPa"},
                "exchanger_type": {"type": "string", "enum": ["Shell and Tube", "Plate", "Double Pipe", "Air Cooled"]},
                "fouling_factor": {"type": "number", "description": "Combined fouling resistance m2.K/W (default 0.0002)"},
                "tube_material": {"type": "string", "description": "e.g. Carbon Steel, Stainless Steel 316, Titanium"}
            },
            "required": ["hot_fluid", "cold_fluid", "hot_inlet_temp", "hot_outlet_temp", "cold_inlet_temp", "hot_flowrate"]
        }
    },
    {
        "name": "run_pump_sizing",
        "description": "Size centrifugal pump, calculate TDH, NPSH, and select motor power",
        "input_schema": {
            "type": "object",
            "properties": {
                "fluid": {"type": "string", "description": "Fluid name"},
                "flowrate": {"type": "number", "description": "Volumetric flowrate in m3/hr"},
                "fluid_density": {"type": "number", "description": "Fluid density in kg/m3"},
                "fluid_viscosity": {"type": "number", "description": "Fluid dynamic viscosity in cP"},
                "fluid_vapor_pressure": {"type": "number", "description": "Vapor pressure at operating temp in kPa"},
                "suction_pressure": {"type": "number", "description": "Suction side pressure in kPa abs"},
                "discharge_pressure": {"type": "number", "description": "Required discharge pressure in kPa abs"},
                "static_head": {"type": "number", "description": "Static head difference in meters"},
                "pipe_diameter": {"type": "number", "description": "Nominal pipe diameter in inches"},
                "pipe_length": {"type": "number", "description": "Total equivalent pipe length in meters"},
                "suction_liquid_level": {"type": "number", "description": "Liquid level above pump centerline in meters"}
            },
            "required": ["fluid", "flowrate", "fluid_density", "suction_pressure", "discharge_pressure"]
        }
    },
    {
        "name": "run_relief_valve_sizing",
        "description": "Size pressure safety valve per API 520/521 for various scenarios",
        "input_schema": {
            "type": "object",
            "properties": {
                "vessel_tag": {"type": "string", "description": "Equipment tag number"},
                "fluid": {"type": "string"},
                "fluid_state": {"type": "string", "enum": ["vapor", "liquid", "two-phase"]},
                "relief_scenario": {"type": "string", "enum": ["blocked_outlet", "fire_case", "thermal_expansion", "cooling_failure", "control_valve_failure", "power_failure"]},
                "set_pressure_kPag": {"type": "number", "description": "PSV set pressure in kPa gauge"},
                "backpressure_kPag": {"type": "number", "description": "Back pressure in kPa gauge"},
                "operating_temp": {"type": "number", "description": "Operating temperature in Celsius"},
                "vessel_volume_m3": {"type": "number", "description": "For fire case — vessel volume"},
                "normal_flowrate": {"type": "number", "description": "Normal process flowrate in kg/hr"},
                "molecular_weight": {"type": "number", "description": "Fluid molecular weight"},
                "Cp_Cv_ratio": {"type": "number", "description": "Ratio of specific heats (k) — for vapor"}
            },
            "required": ["fluid", "fluid_state", "relief_scenario", "set_pressure_kPag", "operating_temp"]
        }
    },
    {
        "name": "run_pinch_analysis",
        "description": "Heat integration pinch analysis — minimum utility targets and HEN design",
        "input_schema": {
            "type": "object",
            "properties": {
                "hot_streams": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "Ts": {"type": "number", "description": "Supply temperature °C"},
                            "Tt": {"type": "number", "description": "Target temperature °C"},
                            "mCp": {"type": "number", "description": "Heat capacity flowrate kW/°C"}
                        }
                    },
                    "description": "Hot streams to be cooled"
                },
                "cold_streams": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "Ts": {"type": "number"},
                            "Tt": {"type": "number"},
                            "mCp": {"type": "number"}
                        }
                    },
                    "description": "Cold streams to be heated"
                },
                "delta_T_min": {"type": "number", "description": "Minimum approach temperature in °C (default 10)"}
            },
            "required": ["hot_streams", "cold_streams"]
        }
    },
    {
        "name": "run_economic_analysis",
        "description": "Estimate CAPEX, OPEX, NPV, IRR, and payback period for a process unit",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "plant_capacity_tpy": {"type": "number", "description": "Plant capacity in tonnes per year"},
                "equipment_list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "size_parameter": {"type": "number"},
                            "size_unit": {"type": "string"}
                        }
                    }
                },
                "raw_material_cost_per_ton": {"type": "number", "description": "USD per tonne of feedstock"},
                "product_price_per_ton": {"type": "number", "description": "USD per tonne of product"},
                "utility_cost_per_year": {"type": "number", "description": "Annual utility cost USD"},
                "project_life_years": {"type": "number", "description": "Project economic life in years (default 20)"},
                "discount_rate": {"type": "number", "description": "Discount rate fraction (default 0.1 = 10%)"},
                "location_factor": {"type": "string", "enum": ["US Gulf Coast", "Pakistan", "Middle East", "Europe", "Southeast Asia"], "description": "Location for cost adjustment"}
            },
            "required": ["project_name", "plant_capacity_tpy"]
        }
    },
    {
        "name": "check_process_safety",
        "description": "Perform HAZOP screening, flammability check, toxic inventory, and relief scenarios identification",
        "input_schema": {
            "type": "object",
            "properties": {
                "equipment_tag": {"type": "string"},
                "equipment_type": {"type": "string", "description": "e.g. Distillation Column, Reactor, Storage Tank"},
                "chemicals": {"type": "array", "items": {"type": "string"}, "description": "All chemicals present"},
                "operating_temp": {"type": "number", "description": "°C"},
                "operating_pressure": {"type": "number", "description": "kPa gauge"},
                "design_pressure": {"type": "number", "description": "kPa gauge"},
                "inventory_kg": {"type": "number", "description": "Approximate chemical inventory in kg"},
                "location": {"type": "string", "description": "Indoor / Outdoor / Remote"}
            },
            "required": ["equipment_type", "chemicals", "operating_temp", "operating_pressure"]
        }
    },
    {
        "name": "lookup_physical_properties",
        "description": "Look up or estimate physical/thermodynamic properties of chemicals",
        "input_schema": {
            "type": "object",
            "properties": {
                "chemical": {"type": "string", "description": "Chemical name or formula"},
                "temperature": {"type": "number", "description": "Temperature in Celsius for T-dependent properties"},
                "pressure": {"type": "number", "description": "Pressure in kPa"},
                "properties_needed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List from: Tc, Pc, Vc, omega, MW, Tb, Tm, LFL, UFL, AIT, vapor_pressure, density, viscosity, thermal_conductivity, Cp, latent_heat, NFPA_ratings"
                }
            },
            "required": ["chemical"]
        }
    },
    {
        "name": "size_pressure_vessel",
        "description": "Size pressure vessel per ASME Section VIII Div 1 — wall thickness, nozzle, saddle",
        "input_schema": {
            "type": "object",
            "properties": {
                "vessel_tag": {"type": "string"},
                "vessel_type": {"type": "string", "enum": ["Horizontal", "Vertical", "Spherical"]},
                "design_pressure_kPag": {"type": "number"},
                "design_temperature": {"type": "number", "description": "°C"},
                "internal_diameter_m": {"type": "number"},
                "vessel_length_m": {"type": "number"},
                "material": {"type": "string", "description": "e.g. SA-516-70, SS-316L, SA-106B"},
                "corrosion_allowance_mm": {"type": "number", "description": "Corrosion allowance in mm (default 3)"},
                "joint_efficiency": {"type": "number", "description": "Weld joint efficiency (default 1.0 for fully radiographed)"},
                "head_type": {"type": "string", "enum": ["Ellipsoidal 2:1", "Hemispherical", "Flat", "Torispherical"], "description": "Head type"}
            },
            "required": ["design_pressure_kPag", "design_temperature", "internal_diameter_m", "vessel_length_m"]
        }
    },
    {
        "name": "run_pipe_sizing",
        "description": "Size piping — velocity check, pressure drop, pipe schedule per ASME B31.3",
        "input_schema": {
            "type": "object",
            "properties": {
                "fluid": {"type": "string"},
                "fluid_phase": {"type": "string", "enum": ["liquid", "vapor", "two-phase"]},
                "flowrate": {"type": "number", "description": "Mass flowrate in kg/hr"},
                "density": {"type": "number", "description": "Fluid density kg/m3"},
                "viscosity": {"type": "number", "description": "Dynamic viscosity cP"},
                "pipe_length": {"type": "number", "description": "Equivalent pipe length in meters"},
                "allowable_velocity": {"type": "number", "description": "Max velocity m/s (optional, uses standard defaults)"},
                "design_pressure": {"type": "number", "description": "Design pressure kPa gauge"},
                "design_temperature": {"type": "number", "description": "Design temperature °C"},
                "pipe_material": {"type": "string", "description": "e.g. CS, SS316, Duplex (default CS)"}
            },
            "required": ["fluid", "fluid_phase", "flowrate", "density", "viscosity", "pipe_length"]
        }
    },
    {
        "name": "export_to_excel",
        "description": "Export engineering calculation sheet to Excel",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "include_charts": {"type": "boolean"}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "export_to_pdf",
        "description": "Export formal engineering report to PDF",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "engineer_name": {"type": "string"},
                "project_name": {"type": "string"},
                "doc_number": {"type": "string", "description": "Engineering document number e.g. PRJ-CALC-001"}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "import_dwsim_file",
        "description": "Import existing DWSIM simulation file (.dwxmz)",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string"}
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "save_dwsim_file",
        "description": "Save current simulation as DWSIM file (.dwxmz)",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"}
            },
            "required": ["filename"]
        }
    }
]


# ---------------------------------------------------------------------------
# AGENT CLASS
# ---------------------------------------------------------------------------

class ChEDesignAgent:
    def __init__(self, provider: str = "claude", model: Optional[str] = None,
                 api_key: Optional[str] = None, dwsim_path: Optional[str] = None):
        self.llm = LLMClient(provider=provider, model=model, api_key=api_key)
        self.conversation_history = []
        self.current_simulation_results = None
        self.all_results = {}
        self.dwsim = DWSIMConnector(dwsim_path)
        self.calc = DistillationCalculator()

    @property
    def provider_display(self) -> str:
        return f"{self.llm.provider_name} / {self.llm.model_name}"

    def chat(self, user_message: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})
        result_text = self._agentic_loop()
        self.conversation_history.append({"role": "assistant", "content": result_text})
        return result_text

    # ------------------------------------------------------------------
    # Agentic loop — handles tool calls for any provider
    # ------------------------------------------------------------------

    def _agentic_loop(self) -> str:
        full_response = ""
        # Keep two separate histories: one for Claude format, one for OpenAI format
        is_claude = self.llm._type == "claude"

        if is_claude:
            messages = list(self.conversation_history)
        else:
            # Build OpenAI messages fresh — system prompt handled by SDK
            messages = self._build_oai_messages()

        max_iterations = 6
        for _ in range(max_iterations):
            result = self.llm.chat(messages, SYSTEM_PROMPT, TOOLS)
            text = result["text"]
            tool_calls = result["tool_calls"]

            if text:
                full_response += text

            if not tool_calls:
                break

            if is_claude:
                # Claude: append raw content block + tool results
                messages.append({"role": "assistant", "content": result["raw"].content})
                for tc in tool_calls:
                    tool_result = self._execute_tool(tc["name"], tc["input"])
                    messages.append({
                        "role": "user",
                        "content": [{"type": "tool_result",
                                     "tool_use_id": tc["id"],
                                     "content": tool_result}]
                    })
            else:
                # OpenAI: ALL tool_calls in ONE assistant message, then one tool message per call
                all_tc_oai = []
                results_map = {}
                for tc in tool_calls:
                    results_map[tc["id"]] = self._execute_tool(tc["name"], tc["input"])
                    all_tc_oai.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["input"])
                        }
                    })

                messages.append({
                    "role": "assistant",
                    "content": text or None,
                    "tool_calls": all_tc_oai
                })
                for tc in tool_calls:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": results_map[tc["id"]],
                    })

        return full_response

    def _build_oai_messages(self) -> list:
        """Convert conversation history to pure OpenAI format (no system prompt)."""
        oai = []
        for msg in self.conversation_history:
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, str):
                oai.append({"role": role, "content": content})
            # Skip complex blocks — they only appear mid-loop, not in stored history
        return oai

    # ------------------------------------------------------------------
    # Tool router
    # ------------------------------------------------------------------

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        try:
            dispatch = {
                "run_distillation_simulation":   self._run_distillation,
                "run_reactor_simulation":        self._run_reactor,
                "run_heat_exchanger_simulation": self._run_heat_exchanger,
                "run_pump_sizing":               self._run_pump,
                "run_relief_valve_sizing":       self._run_psv,
                "run_pinch_analysis":            self._run_pinch,
                "run_economic_analysis":         self._run_economics,
                "check_process_safety":          self._run_safety_check,
                "lookup_physical_properties":    self._lookup_properties,
                "size_pressure_vessel":          self._size_vessel,
                "run_pipe_sizing":               self._run_pipe,
                "export_to_excel":               self._export_excel,
                "export_to_pdf":                 self._export_pdf,
                "import_dwsim_file":             self._import_dwsim,
                "save_dwsim_file":               self._save_dwsim,
            }
            handler = dispatch.get(tool_name)
            if handler:
                return handler(tool_input)
            return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Tool execution error in {tool_name}: {str(e)}"

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _run_distillation(self, p: dict) -> str:
        prelim = self.calc.shortcut_method(
            components=p["components"],
            feed_composition=p["feed_composition"],
            distillate_purity=p["distillate_purity"],
            bottoms_purity=p["bottoms_purity"],
            feed_flowrate=p.get("feed_flowrate", 1000),
            operating_pressure=p.get("operating_pressure", 101.325),
            feed_quality=p.get("feed_quality", 1.0),
            reflux_ratio_multiplier=p.get("reflux_multiplier", 1.3),
        )
        if self.dwsim.is_available():
            dwsim_r = self.dwsim.run_distillation(p)
            prelim.update(dwsim_r)
            prelim["source"] = "DWSIM Rigorous"
        self.current_simulation_results = prelim
        self.all_results["distillation"] = prelim
        return json.dumps(prelim, indent=2)

    def _run_reactor(self, p: dict) -> str:
        from src.calculations.reactor import ReactorCalculator
        results = ReactorCalculator().design(p)
        self.current_simulation_results = results
        self.all_results["reactor"] = results
        return json.dumps(results, indent=2)

    def _run_heat_exchanger(self, p: dict) -> str:
        from src.calculations.heat_exchanger import HeatExchangerCalculator
        results = HeatExchangerCalculator().design(p)
        self.current_simulation_results = results
        self.all_results["heat_exchanger"] = results
        return json.dumps(results, indent=2)

    def _run_pump(self, p: dict) -> str:
        from src.calculations.pump import PumpCalculator
        results = PumpCalculator().design(p)
        self.current_simulation_results = results
        self.all_results["pump"] = results
        return json.dumps(results, indent=2)

    def _run_psv(self, p: dict) -> str:
        from src.calculations.relief_valve import ReliefValveCalculator
        results = ReliefValveCalculator().size(p)
        self.current_simulation_results = results
        self.all_results["psv"] = results
        return json.dumps(results, indent=2)

    def _run_pinch(self, p: dict) -> str:
        from src.calculations.pinch import PinchAnalyzer
        results = PinchAnalyzer().analyze(p)
        self.current_simulation_results = results
        self.all_results["pinch"] = results
        return json.dumps(results, indent=2)

    def _run_economics(self, p: dict) -> str:
        from src.calculations.economics import EconomicsCalculator
        results = EconomicsCalculator().analyze(p)
        self.current_simulation_results = results
        self.all_results["economics"] = results
        return json.dumps(results, indent=2)

    def _run_safety_check(self, p: dict) -> str:
        from src.calculations.safety import SafetyChecker
        results = SafetyChecker().check(p)
        self.current_simulation_results = results
        self.all_results["safety"] = results
        return json.dumps(results, indent=2)

    def _lookup_properties(self, p: dict) -> str:
        from src.calculations.properties import PropertyLookup
        results = PropertyLookup().lookup(p["chemical"], p.get("temperature", 25),
                                          p.get("pressure", 101.325),
                                          p.get("properties_needed", []))
        return json.dumps(results, indent=2)

    def _size_vessel(self, p: dict) -> str:
        from src.calculations.vessel import VesselCalculator
        results = VesselCalculator().size(p)
        self.current_simulation_results = results
        self.all_results["vessel"] = results
        return json.dumps(results, indent=2)

    def _run_pipe(self, p: dict) -> str:
        from src.calculations.piping import PipingCalculator
        results = PipingCalculator().size(p)
        self.current_simulation_results = results
        self.all_results["piping"] = results
        return json.dumps(results, indent=2)

    def _export_excel(self, p: dict) -> str:
        if not self.current_simulation_results:
            return "No results to export. Please run a simulation first."
        from src.calculations.exporter import ResultExporter
        fp = ResultExporter().to_excel(self.current_simulation_results, p["filename"])
        return f"Excel exported: {fp}"

    def _export_pdf(self, p: dict) -> str:
        if not self.current_simulation_results:
            return "No results to export. Please run a simulation first."
        from src.calculations.exporter import ResultExporter
        fp = ResultExporter().to_pdf(
            self.current_simulation_results, p["filename"],
            p.get("engineer_name", "Engineer"),
            p.get("project_name", "ChE Design"),
        )
        return f"PDF exported: {fp}"

    def _import_dwsim(self, p: dict) -> str:
        return self.dwsim.import_file(p["filepath"])

    def _save_dwsim(self, p: dict) -> str:
        if not self.current_simulation_results:
            return "No active simulation to save."
        return self.dwsim.save_file(p["filename"])

    def reset_conversation(self):
        self.conversation_history = []
        self.current_simulation_results = None
        self.all_results = {}
