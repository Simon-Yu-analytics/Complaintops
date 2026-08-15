from __future__ import annotations

import math


def staffing_plan(
    forecast: dict[str, list[int]],
    upper_forecast: dict[str, list[int]] | None = None,
    cases_per_agent_week: int = 24,
    service_level_buffer: float = 1.15,
    weekly_cost_per_agent: int = 1_650,
) -> dict[str, object]:
    if cases_per_agent_week <= 0:
        raise ValueError("cases_per_agent_week must be positive")
    teams = []
    total_agents = 0
    for product, values in sorted(forecast.items()):
        peak = max(values) if values else 0
        if upper_forecast is not None:
            planning_demand = max(upper_forecast.get(product, values)) if values else 0
        else:
            planning_demand = math.ceil(peak * service_level_buffer)
        required = math.ceil(planning_demand / cases_per_agent_week)
        total_agents += required
        teams.append(
            {
                "team": product,
                "peak_weekly_demand": peak,
                "planning_demand": planning_demand,
                "recommended_agents": required,
                "weekly_capacity": required * cases_per_agent_week,
                "point_utilization": (
                    round(peak / (required * cases_per_agent_week), 3)
                    if required
                    else 0
                ),
            }
        )
    assumptions: dict[str, object] = {
        "cases_per_agent_week": cases_per_agent_week,
        "weekly_cost_per_agent": weekly_cost_per_agent,
        "planning_basis": (
            "80% forecast upper bound"
            if upper_forecast is not None
            else "point forecast plus service buffer"
        ),
    }
    if upper_forecast is not None:
        assumptions["forecast_interval_coverage"] = 0.80
    else:
        assumptions["service_level_buffer"] = service_level_buffer
    return {
        "teams": teams,
        "total_agents": total_agents,
        "weekly_cost": total_agents * weekly_cost_per_agent,
        "assumptions": assumptions,
    }
