(function attachComplaintOpsLogic(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.ComplaintOpsLogic = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, () => {
  const assertFinite = (value, name) => {
    if (!Number.isFinite(value)) throw new TypeError(`${name} must be finite`);
  };

  const tokenize = text => String(text).toLowerCase().match(/[a-z][a-z']+/g) || [];

  const routeComplaint = (text, model, threshold = model?.threshold) => {
    if (!model || !Array.isArray(model.classes) || !model.classes.length) {
      throw new TypeError('a fitted dashboard model is required');
    }
    assertFinite(threshold, 'threshold');
    if (threshold < 0 || threshold > 1) throw new RangeError('threshold must be between 0 and 1');
    const alpha = Number(model.alpha);
    assertFinite(alpha, 'alpha');
    const vocabulary = new Set(model.vocabulary || []);
    const frequencies = new Map();
    tokenize(text).forEach(token => frequencies.set(token, (frequencies.get(token) || 0) + 1));
    const recognized = [...frequencies].filter(([token]) => vocabulary.has(token));
    const totalDocuments = model.classes.reduce((sum, item) => sum + item.documents, 0);
    const vocabularySize = Math.max(1, vocabulary.size);
    const scored = model.classes.map(item => {
      const denominator = item.total_tokens + alpha * vocabularySize;
      let score = Math.log(item.documents / totalDocuments);
      recognized.forEach(([token, count]) => {
        score += count * Math.log(((item.token_counts[token] || 0) + alpha) / denominator);
      });
      return { ...item, denominator, score };
    });
    const peak = Math.max(...scored.map(item => item.score));
    const normalizer = scored.reduce((sum, item) => sum + Math.exp(item.score - peak), 0);
    const ranking = scored.map(item => ({
      label: item.label,
      probability: Math.exp(item.score - peak) / normalizer
    })).sort((a, b) => b.probability - a.probability);
    const winner = scored.find(item => item.label === ranking[0].label);
    const runnerUp = scored.find(item => item.label === ranking[1]?.label) || winner;
    const evidence = recognized.map(([token, count]) => ({
      token,
      score: count * (
        Math.log(((winner.token_counts[token] || 0) + alpha) / winner.denominator)
        - Math.log(((runnerUp.token_counts[token] || 0) + alpha) / runnerUp.denominator)
      )
    })).filter(item => item.score > 0).sort((a, b) => b.score - a.score).slice(0, 5);
    const confidence = ranking[0].probability;
    return {
      label: ranking[0].label,
      confidence,
      decision: recognized.length > 0 && confidence >= threshold ? 'auto-route' : 'human-review',
      ranking,
      evidence,
      recognizedTokens: recognized.reduce((sum, [, count]) => sum + count, 0),
      threshold
    };
  };

  const thresholdScenario = (curve, index) => {
    if (!Array.isArray(curve) || !curve.length) throw new TypeError('curve is required');
    assertFinite(index, 'index');
    const bounded = Math.max(0, Math.min(curve.length - 1, Math.round(index)));
    return curve[bounded];
  };

  const feedbackStats = entries => {
    if (!Array.isArray(entries)) throw new TypeError('feedback entries must be an array');
    const valid = entries.filter(entry => Number.isInteger(entry.rating)
      && entry.rating >= 1 && entry.rating <= 5);
    return {
      count: valid.length,
      average: valid.length
        ? valid.reduce((sum, entry) => sum + entry.rating, 0) / valid.length
        : 0
    };
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

  return {
    feedbackStats,
    forecastGeometry,
    routeComplaint,
    staffingScenario,
    thresholdScenario,
    tokenize
  };
}));
