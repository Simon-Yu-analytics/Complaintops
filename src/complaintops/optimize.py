from __future__ import annotations

import math


def staffing_plan(
    forecast: dict[str, list[int]],
    cases_per_agent_week: int = 45,
    service_level_buffer: float = 1.15,
    weekly_cost_per_agent: int = 1_650,
) -> dict[str, object]:
    if cases_per_agent_week <= 0:
        raise ValueError("cases_per_agent_week must be positive")
    teams = []
    total_agents = 0
    for product, values in sorted(forecast.items()):
        peak = max(values) if values else 0
        required = math.ceil(peak * service_level_buffer / cases_per_agent_week)
        total_agents += required
        teams.append(
            {
                "team": product,
                "peak_weekly_demand": peak,
                "recommended_agents": required,
                "weekly_capacity": required * cases_per_agent_week,
                "utilization": round(peak / (required * cases_per_agent_week), 3) if required else 0,
            }
        )
    return {
        "teams": teams,
        "total_agents": total_agents,
        "weekly_cost": total_agents * weekly_cost_per_agent,
        "assumptions": {
            "cases_per_agent_week": cases_per_agent_week,
            "service_level_buffer": service_level_buffer,
            "weekly_cost_per_agent": weekly_cost_per_agent,
        },
    }

