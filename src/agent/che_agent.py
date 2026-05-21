"""
ChE Design Agent - Core AI brain using Claude API
Understands engineer's chat and orchestrates DWSIM simulations
"""

import anthropic
import json
from typing import Optional
from src.dwsim_bridge.dwsim_connector import DWSIMConnector
from src.calculations.distillation import DistillationCalculator

SYSTEM_PROMPT = """You are an expert Chemical Engineering Design Agent. You help engineers design chemical processes through natural conversation.

Your capabilities:
1. Distillation Column Design (McCabe-Thiele, shortcut methods, rigorous simulation)
2. Heat Exchanger Design (LMTD, NTU methods)
3. Reactor Design (CSTR, PFR, Batch)
4. Process simulation via DWSIM

When an engineer describes a problem:
- Extract key parameters (components, flowrates, conditions, specifications)
- Ask clarifying questions if parameters are missing
- Perform preliminary calculations
- Set up and run DWSIM simulation
- Present results clearly with units
- Suggest optimizations

Always respond in the same language the engineer uses (Urdu or English).
Format numerical results in clear tables.
When you have enough info to run a simulation, call the appropriate tool.

Available tools you can call:
- run_distillation_simulation: For distillation column design
- run_heat_exchanger_simulation: For heat exchanger design
- run_reactor_simulation: For reactor design
- export_to_excel: Export results to Excel
- export_to_pdf: Export results to PDF
- import_dwsim_file: Import existing DWSIM design file
- save_dwsim_file: Save current simulation as DWSIM file
"""

TOOLS = [
    {
        "name": "run_distillation_simulation",
        "description": "Run a distillation column simulation in DWSIM with given parameters",
        "input_schema": {
            "type": "object",
            "properties": {
                "components": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of chemical components e.g. ['Ethanol', 'Water']"
                },
                "feed_flowrate": {"type": "number", "description": "Feed flowrate in kg/hr"},
                "feed_temperature": {"type": "number", "description": "Feed temperature in Celsius"},
                "feed_pressure": {"type": "number", "description": "Feed pressure in kPa"},
                "feed_composition": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Mole fractions of each component in feed (must sum to 1)"
                },
                "distillate_purity": {"type": "number", "description": "Required distillate purity (mole fraction of light key)"},
                "bottoms_purity": {"type": "number", "description": "Required bottoms purity (mole fraction of heavy key)"},
                "operating_pressure": {"type": "number", "description": "Column operating pressure in kPa"},
                "reflux_ratio": {"type": "number", "description": "Reflux ratio (optional, will calculate minimum if not provided)"},
                "property_package": {
                    "type": "string",
                    "description": "Thermodynamic property package",
                    "enum": ["NRTL", "UNIQUAC", "Peng-Robinson", "SRK", "UNIFAC"]
                }
            },
            "required": ["components", "feed_flowrate", "feed_composition", "distillate_purity", "bottoms_purity"]
        }
    },
    {
        "name": "run_heat_exchanger_simulation",
        "description": "Design a heat exchanger using DWSIM",
        "input_schema": {
            "type": "object",
            "properties": {
                "hot_fluid": {"type": "string", "description": "Hot side fluid name"},
                "cold_fluid": {"type": "string", "description": "Cold side fluid name"},
                "hot_inlet_temp": {"type": "number", "description": "Hot fluid inlet temperature in Celsius"},
                "hot_outlet_temp": {"type": "number", "description": "Hot fluid outlet temperature in Celsius"},
                "cold_inlet_temp": {"type": "number", "description": "Cold fluid inlet temperature in Celsius"},
                "hot_flowrate": {"type": "number", "description": "Hot fluid flowrate in kg/hr"},
                "cold_flowrate": {"type": "number", "description": "Cold fluid flowrate in kg/hr"},
                "exchanger_type": {
                    "type": "string",
                    "enum": ["Shell and Tube", "Plate", "Double Pipe"],
                    "description": "Type of heat exchanger"
                }
            },
            "required": ["hot_fluid", "cold_fluid", "hot_inlet_temp", "hot_outlet_temp", "cold_inlet_temp", "hot_flowrate"]
        }
    },
    {
        "name": "export_to_excel",
        "description": "Export current simulation results to Excel file",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Output Excel filename"},
                "include_charts": {"type": "boolean", "description": "Include charts/plots in Excel"}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "export_to_pdf",
        "description": "Export current simulation results to PDF report",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Output PDF filename"},
                "engineer_name": {"type": "string", "description": "Engineer name for report header"},
                "project_name": {"type": "string", "description": "Project name for report header"}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "import_dwsim_file",
        "description": "Import an existing DWSIM simulation file (.dwxmz)",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Full path to the .dwxmz file"}
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
                "filename": {"type": "string", "description": "Output filename (without extension)"}
            },
            "required": ["filename"]
        }
    }
]


class ChEDesignAgent:
    def __init__(self, api_key: str, dwsim_path: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.conversation_history = []
        self.current_simulation_results = None
        self.dwsim = DWSIMConnector(dwsim_path)
        self.calc = DistillationCalculator()

    def chat(self, user_message: str) -> str:
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=self.conversation_history
        )

        result_text = self._process_response(response)

        self.conversation_history.append({
            "role": "assistant",
            "content": result_text
        })

        return result_text

    def _process_response(self, response) -> str:
        full_response = ""

        for block in response.content:
            if block.type == "text":
                full_response += block.text

            elif block.type == "tool_use":
                tool_result = self._execute_tool(block.name, block.input)
                tool_response = f"\n\n**[{block.name}]**\n{tool_result}"
                full_response += tool_response

                # Continue conversation with tool result
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })
                self.conversation_history.append({
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": block.id, "content": tool_result}]
                })

                follow_up = self.client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8096,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=self.conversation_history
                )
                for b in follow_up.content:
                    if b.type == "text":
                        full_response += "\n" + b.text

        return full_response

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        try:
            if tool_name == "run_distillation_simulation":
                return self._run_distillation(tool_input)
            elif tool_name == "run_heat_exchanger_simulation":
                return self._run_heat_exchanger(tool_input)
            elif tool_name == "export_to_excel":
                return self._export_excel(tool_input)
            elif tool_name == "export_to_pdf":
                return self._export_pdf(tool_input)
            elif tool_name == "import_dwsim_file":
                return self._import_dwsim(tool_input)
            elif tool_name == "save_dwsim_file":
                return self._save_dwsim(tool_input)
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Tool execution error: {str(e)}"

    def _run_distillation(self, params: dict) -> str:
        # First run preliminary calculations
        prelim = self.calc.shortcut_method(
            components=params["components"],
            feed_composition=params["feed_composition"],
            distillate_purity=params["distillate_purity"],
            bottoms_purity=params["bottoms_purity"],
            feed_flowrate=params.get("feed_flowrate", 1000),
            operating_pressure=params.get("operating_pressure", 101.325)
        )

        # Try DWSIM if available
        if self.dwsim.is_available():
            dwsim_result = self.dwsim.run_distillation(params)
            self.current_simulation_results = {**prelim, **dwsim_result, "source": "DWSIM"}
        else:
            self.current_simulation_results = {**prelim, "source": "Shortcut Method (DWSIM not connected)"}

        return json.dumps(self.current_simulation_results, indent=2)

    def _run_heat_exchanger(self, params: dict) -> str:
        from src.calculations.heat_exchanger import HeatExchangerCalculator
        hx_calc = HeatExchangerCalculator()
        results = hx_calc.design(params)
        self.current_simulation_results = results
        return json.dumps(results, indent=2)

    def _export_excel(self, params: dict) -> str:
        if not self.current_simulation_results:
            return "No simulation results to export. Please run a simulation first."
        from src.calculations.exporter import ResultExporter
        exporter = ResultExporter()
        filepath = exporter.to_excel(self.current_simulation_results, params["filename"])
        return f"Excel exported successfully: {filepath}"

    def _export_pdf(self, params: dict) -> str:
        if not self.current_simulation_results:
            return "No simulation results to export. Please run a simulation first."
        from src.calculations.exporter import ResultExporter
        exporter = ResultExporter()
        filepath = exporter.to_pdf(
            self.current_simulation_results,
            params["filename"],
            params.get("engineer_name", "Engineer"),
            params.get("project_name", "ChE Design Project")
        )
        return f"PDF exported successfully: {filepath}"

    def _import_dwsim(self, params: dict) -> str:
        result = self.dwsim.import_file(params["filepath"])
        return result

    def _save_dwsim(self, params: dict) -> str:
        if not self.current_simulation_results:
            return "No simulation to save."
        result = self.dwsim.save_file(params["filename"])
        return result

    def reset_conversation(self):
        self.conversation_history = []
        self.current_simulation_results = None
