"""
DWSIM Connector - Python automation bridge to DWSIM
Uses DWSIM's Python automation API via pythonnet / COM
"""

import os
import sys
import json
from typing import Optional


DWSIM_DEFAULT_PATH = r"C:\DWSIM"


class DWSIMConnector:
    def __init__(self, dwsim_path: Optional[str] = None):
        self.dwsim_path = dwsim_path or DWSIM_DEFAULT_PATH
        self.automation = None
        self.flowsheet = None
        self._connected = False
        self._try_connect()

    def _try_connect(self):
        try:
            sys.path.append(self.dwsim_path)
            import clr
            clr.AddReference(os.path.join(self.dwsim_path, "DWSIM.Automation.dll"))
            clr.AddReference(os.path.join(self.dwsim_path, "DWSIM.Interfaces.dll"))
            from DWSIM.Automation import Automation3
            self.automation = Automation3()
            self._connected = True
            print("[DWSIM] Connected successfully")
        except Exception as e:
            self._connected = False
            print(f"[DWSIM] Not connected (will use fallback calculations): {e}")

    def is_available(self) -> bool:
        return self._connected

    def run_distillation(self, params: dict) -> dict:
        if not self._connected:
            return {"error": "DWSIM not connected"}

        try:
            self.flowsheet = self.automation.CreateFlowsheet()

            # Add components
            for comp in params["components"]:
                self.flowsheet.Database.SelectedCompounds.Add(comp)

            # Set property package
            pp_name = params.get("property_package", "NRTL")
            self.flowsheet.AddPropertyPackage(pp_name)

            # Create feed stream
            feed = self.flowsheet.AddObject("MaterialStream", 100, 100, "Feed")
            feed_obj = self.flowsheet.GetFlowsheetObject("Feed")
            feed_obj.SetPropertyPackage(pp_name)
            feed_obj.SetTemperature(params.get("feed_temperature", 25) + 273.15)
            feed_obj.SetPressure(params.get("feed_pressure", 101.325) * 1000)
            feed_obj.SetMassFlow(params.get("feed_flowrate", 1000) / 3600)

            for i, comp in enumerate(params["components"]):
                feed_obj.SetComposition(comp, params["feed_composition"][i])

            # Add distillation column
            col = self.flowsheet.AddObject("DistillationColumn", 300, 100, "Column1")
            col_obj = self.flowsheet.GetFlowsheetObject("Column1")

            # Run simulation
            self.flowsheet.Solve()

            # Extract results
            results = self._extract_column_results(col_obj)
            return results

        except Exception as e:
            return {"dwsim_error": str(e)}

    def _extract_column_results(self, col_obj) -> dict:
        try:
            return {
                "num_stages": col_obj.NumberOfStages,
                "condenser_duty_kW": col_obj.CondenserDuty / 1000,
                "reboiler_duty_kW": col_obj.ReboilerDuty / 1000,
                "distillate_flowrate_kghr": col_obj.DistillateFlowrate * 3600,
                "bottoms_flowrate_kghr": col_obj.BottomsFlowrate * 3600,
                "reflux_ratio": col_obj.RefluxRatio,
                "column_diameter_m": col_obj.ColumnDiameter,
                "column_height_m": col_obj.ColumnHeight,
            }
        except Exception as e:
            return {"extraction_error": str(e)}

    def import_file(self, filepath: str) -> str:
        if not self._connected:
            return "DWSIM not connected. Cannot import file."
        try:
            self.flowsheet = self.automation.LoadFlowsheet(filepath)
            return f"Successfully imported: {filepath}"
        except Exception as e:
            return f"Import error: {str(e)}"

    def save_file(self, filename: str) -> str:
        if not self._connected or not self.flowsheet:
            return "No active flowsheet to save."
        try:
            export_dir = os.path.join(os.getcwd(), "designs")
            os.makedirs(export_dir, exist_ok=True)
            filepath = os.path.join(export_dir, f"{filename}.dwxmz")
            self.automation.SaveFlowsheet(self.flowsheet, filepath, True)
            return f"Saved to: {filepath}"
        except Exception as e:
            return f"Save error: {str(e)}"
