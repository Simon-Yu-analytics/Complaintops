(function attachComplaintOpsLogic(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.ComplaintOpsLogic = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, () => {
  const assertFinite = (value, name) => {
    if (!Number.isFinite(value)) throw new TypeError(`${name} must be finite`);
  };

  const forecastGeometry = (lower, point, upper, maximum, scale = 88) => {
    [lower, point, upper, maximum, scale].forEach((value, index) => {
      assertFinite(value, ['lower', 'point', 'upper', 'maximum', 'scale'][index]);
    });
    if (lower < 0 || lower > point || point > upper || maximum <= 0 || upper > maximum) {
      throw new RangeError('forecast values must satisfy 0 <= lower <= point <= upper <= maximum');
    }
    return {
      bandBottom: lower / maximum * scale,
      bandHeight: Math.max(upper - lower, 1) / maximum * scale,
      pointHeight: point / maximum * scale
    };
  };

  const staffingScenario = (
    teams,
    stress,
    casesPerAgent,
    weeklyCostPerAgent
  ) => {
    [stress, casesPerAgent, weeklyCostPerAgent].forEach((value, index) => {
      assertFinite(value, ['stress', 'casesPerAgent', 'weeklyCostPerAgent'][index]);
    });
    if (!Array.isArray(teams) || stress < 0 || casesPerAgent <= 0 || weeklyCostPerAgent < 0) {
      throw new RangeError('invalid staffing scenario inputs');
    }
    let totalAgents = 0;
    const scenarioTeams = teams.map(team => {
      const pointDemand = Math.ceil(team.peak_weekly_demand * (1 + stress));
      const planningDemand = Math.ceil(team.planning_demand * (1 + stress));
      const agents = Math.ceil(planningDemand / casesPerAgent);
      const capacity = agents * casesPerAgent;
      totalAgents += agents;
      return {
        ...team,
        pointDemand,
        planningDemand,
        agents,
        capacity,
        utilization: capacity ? pointDemand / capacity : 0
      };
    });
    return {
      teams: scenarioTeams,
      totalAgents,
      weeklyCost: totalAgents * weeklyCostPerAgent
    };
  };

  return { forecastGeometry, staffingScenario };
}));
