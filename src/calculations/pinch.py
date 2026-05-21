"""
Pinch Analysis — Heat Integration
Minimum utility targeting using Problem Table Algorithm (Linnhoff & Hindmarsh)
"""


class PinchAnalyzer:

    def analyze(self, p: dict) -> dict:
        hot_streams = p.get("hot_streams", [])
        cold_streams = p.get("cold_streams", [])
        dT_min = p.get("delta_T_min", 10)

        if not hot_streams or not cold_streams:
            return {"error": "Need at least one hot and one cold stream"}

        # Shift temperatures: hot streams shifted down by dT_min/2, cold up by dT_min/2
        shift = dT_min / 2

        intervals = self._build_temperature_intervals(hot_streams, cold_streams, shift)
        heat_cascade = self._cascade_calculation(intervals)

        pinch_temp = self._find_pinch(intervals, heat_cascade)
        Q_hot_min = max(0, -min(heat_cascade))
        Q_cold_min = heat_cascade[-1] + Q_hot_min

        current_hot_util = sum(s["mCp"] * (s["Ts"] - s["Tt"]) for s in hot_streams)
        current_cold_util = sum(s["mCp"] * (s["Tt"] - s["Ts"]) for s in cold_streams)

        energy_saving = max(0, current_hot_util - Q_hot_min)
        saving_pct = (energy_saving / current_hot_util * 100) if current_hot_util > 0 else 0

        return {
            "method": "Linnhoff Pinch Analysis — Problem Table Algorithm",
            "delta_T_min_C": dT_min,
            "pinch_temperature_hot_C": round(pinch_temp + shift, 1) if pinch_temp else "N/A",
            "pinch_temperature_cold_C": round(pinch_temp - shift, 1) if pinch_temp else "N/A",
            "minimum_hot_utility_kW": round(Q_hot_min, 2),
            "minimum_cold_utility_kW": round(Q_cold_min, 2),
            "current_hot_utility_kW": round(current_hot_util, 2),
            "energy_saving_potential_kW": round(energy_saving, 2),
            "energy_saving_pct": round(saving_pct, 1),
            "number_of_hot_streams": len(hot_streams),
            "number_of_cold_streams": len(cold_streams),
            "recommendation": self._recommend(saving_pct),
            "next_step": "Design Heat Exchanger Network (HEN) using Pinch rules: no heat transfer across pinch, no cold utility above pinch, no hot utility below pinch"
        }

    def _build_temperature_intervals(self, hot, cold, shift):
        temps = set()
        for s in hot:
            temps.add(s["Ts"] - shift)
            temps.add(s["Tt"] - shift)
        for s in cold:
            temps.add(s["Ts"] + shift)
            temps.add(s["Tt"] + shift)
        temps = sorted(temps, reverse=True)

        intervals = []
        for i in range(len(temps) - 1):
            T_high = temps[i]
            T_low = temps[i + 1]
            dT = T_high - T_low

            hot_mCp = sum(s["mCp"] for s in hot
                          if min(s["Ts"], s["Tt"]) - shift <= T_low
                          and max(s["Ts"], s["Tt"]) - shift >= T_high)
            cold_mCp = sum(s["mCp"] for s in cold
                           if min(s["Ts"], s["Tt"]) + shift <= T_low
                           and max(s["Ts"], s["Tt"]) + shift >= T_high)

            intervals.append({
                "T_high": T_high,
                "T_low": T_low,
                "delta_H": (hot_mCp - cold_mCp) * dT
            })
        return intervals

    def _cascade_calculation(self, intervals):
        cascade = [0]
        for iv in intervals:
            cascade.append(cascade[-1] + iv["delta_H"])
        return cascade

    def _find_pinch(self, intervals, cascade):
        min_val = min(cascade)
        idx = cascade.index(min_val)
        if idx < len(intervals):
            return intervals[idx]["T_low"]
        return None

    def _recommend(self, saving_pct: float) -> str:
        if saving_pct > 30:
            return "HIGH potential for heat integration. Strongly recommend HEN design — significant utility cost savings possible."
        elif saving_pct > 10:
            return "MODERATE heat integration potential. Evaluate HEN design against capital cost."
        else:
            return "LOW integration potential. Process may already be well-integrated or streams are incompatible."
