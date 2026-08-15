const $ = (selector) => document.querySelector(selector);
const pct = (value) => `${(Number(value) * 100).toFixed(1)}%`;
const money = (value) => new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 0
}).format(value);
const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
})[character]);

document.querySelectorAll('.nav-item').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.nav-item,.page').forEach(element => element.classList.remove('active'));
  button.classList.add('active');
  document.getElementById(button.dataset.page).classList.add('active');
}));

fetch('data/results.json')
  .then(response => {
    if (!response.ok) throw new Error(`Dashboard data returned ${response.status}`);
    return response.json();
  })
  .then(data => {
    const routing = data.classification.selective_routing;
    $('#mode').textContent = data.mode.replaceAll('-', ' ');
    $('#records').textContent = data.records.toLocaleString();
    $('#date-range').textContent = `${data.date_range[0]} — ${data.date_range[1]}`;
    $('#accuracy').textContent = pct(routing.accuracy);
    $('#f1').textContent = pct(routing.coverage);
    $('#agents').textContent = data.staffing.total_agents;
    $('#ring-score').textContent = pct(data.classification.macro_f1);
    $('.score-ring').style.setProperty('--score', `${data.classification.macro_f1 * 360}deg`);
    $('#overall-accuracy').textContent = pct(data.classification.accuracy);
    $('#review-rate').textContent = pct(routing.review_rate);
    $('#test-cutoff').textContent = data.classification.cutoff_date;
    $('#threshold-note').textContent = `Human review below ${pct(routing.threshold)}`;

    const maxProduct = Math.max(...Object.values(data.product_counts));
    $('#product-bars').innerHTML = Object.entries(data.product_counts).map(([name, value]) => `
      <div class="bar-row"><span>${escapeHtml(name)}</span><div class="bar-track">
      <div class="bar-fill" style="width:${value / maxProduct * 100}%"></div></div><strong>${value}</strong></div>
    `).join('');
    const largest = Object.entries(data.product_counts)[0];
    const staffingPeak = [...data.staffing.teams].sort((a, b) => b.planning_demand - a.planning_demand)[0];
    const averageWape = Object.values(data.forecast_wape).reduce((a, b) => a + b, 0) / Object.values(data.forecast_wape).length;
    $('#insights').innerHTML = [
      `${largest[0]} is the largest queue at ${largest[1]} cases in the analysis window.`,
      `${staffingPeak.team} has the highest upper-bound planning demand at ${staffingPeak.planning_demand} weekly cases.`,
      `The selected product baselines backtest at ${pct(averageWape)} average WAPE.`,
      `${pct(routing.review_rate)} of low-confidence cases are reserved for human review.`
    ].map(text => `<li>${escapeHtml(text)}</li>`).join('');
    $('#issue-list').innerHTML = Object.entries(data.top_issues).map(([name, value]) => `
      <div class="issue"><span>${escapeHtml(name)}</span><strong>${value}</strong></div>
    `).join('');

    $('#forecast-methods').innerHTML = Object.entries(data.forecast_detail).map(([product, detail]) => `
      <article><span>${escapeHtml(product)}</span><strong>${escapeHtml(detail.method)}</strong>
      <small>${pct(detail.backtest_wape)} WAPE</small></article>
    `).join('');
    const maxForecast = Math.max(...Object.values(data.forecast_detail).flatMap(detail => detail.upper), 1);
    $('#forecast-chart').innerHTML = Object.entries(data.forecast_detail).map(([product, detail]) => `
      <div class="forecast-group">${detail.point.map((value, index) => `
        <div class="forecast-column" title="Week ${index + 1}: ${detail.lower[index]}–${detail.upper[index]} cases">
          <div class="forecast-range" style="height:${detail.upper[index] / maxForecast * 88}%">
            <div class="forecast-bar" style="height:${value / Math.max(detail.upper[index], 1) * 100}%"></div>
          </div>
        </div>`).join('')}<span>${escapeHtml(product)}</span></div>
    `).join('');

    const renderStaffing = () => {
      const stress = Number($('#stress-slider').value) / 100;
      const casesPerAgent = data.staffing.assumptions.cases_per_agent_week;
      const weeklyCost = data.staffing.assumptions.weekly_cost_per_agent;
      let totalAgents = 0;
      const rows = data.staffing.teams.map(team => {
        const planningDemand = Math.ceil(team.planning_demand * (1 + stress));
        const agents = Math.ceil(planningDemand / casesPerAgent);
        const capacity = agents * casesPerAgent;
        totalAgents += agents;
        return `<tr><td>${escapeHtml(team.team)}</td><td>${team.peak_weekly_demand}</td>
          <td>${planningDemand}</td><td><strong>${agents}</strong></td><td>${capacity}</td>
          <td>${pct(capacity ? team.peak_weekly_demand / capacity : 0)}</td></tr>`;
      });
      $('#staffing-body').innerHTML = rows.join('');
      $('#weekly-cost').textContent = `${totalAgents} agents · ${money(totalAgents * weeklyCost)} / week`;
      $('#stress-label').textContent = `+${Math.round(stress * 100)}%`;
    };
    $('#stress-slider').addEventListener('input', renderStaffing);
    renderStaffing();
  })
  .catch(error => {
    console.error(error);
    $('#mode').textContent = 'Run make run';
  });
