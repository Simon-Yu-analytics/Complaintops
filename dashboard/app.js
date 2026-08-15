const $ = (selector) => document.querySelector(selector);
const pct = (value) => `${(value * 100).toFixed(1)}%`;
const money = (value) => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(value);

document.querySelectorAll('.nav-item').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.nav-item,.page').forEach(element => element.classList.remove('active'));
  button.classList.add('active');
  document.getElementById(button.dataset.page).classList.add('active');
}));

fetch('data/results.json').then(response => response.json()).then(data => {
  $('#mode').textContent = data.mode.replace('-', ' ');
  $('#records').textContent = data.records.toLocaleString();
  $('#date-range').textContent = `${data.date_range[0]} — ${data.date_range[1]}`;
  $('#accuracy').textContent = pct(data.classification.accuracy);
  $('#f1').textContent = pct(data.classification.macro_f1);
  $('#agents').textContent = data.staffing.total_agents;
  $('#ring-score').textContent = pct(data.classification.macro_f1);
  $('.score-ring').style.setProperty('--score', `${data.classification.macro_f1 * 360}deg`);
  $('#weekly-cost').textContent = `${money(data.staffing.weekly_cost)} / week`;

  const maxProduct = Math.max(...Object.values(data.product_counts));
  $('#product-bars').innerHTML = Object.entries(data.product_counts).map(([name,value]) => `<div class="bar-row"><span>${name}</span><div class="bar-track"><div class="bar-fill" style="width:${value/maxProduct*100}%"></div></div><strong>${value}</strong></div>`).join('');
  const products = Object.entries(data.product_counts);
  const largest = products[0];
  const staffingPeak = [...data.staffing.teams].sort((a,b)=>b.peak_weekly_demand-a.peak_weekly_demand)[0];
  const averageWape = Object.values(data.forecast_wape).reduce((a,b)=>a+b,0)/Object.values(data.forecast_wape).length;
  $('#insights').innerHTML = [
    `${largest[0]} is the largest queue at ${largest[1]} cases in the current analysis window.`,
    `${staffingPeak.team} has the highest forecast peak and is the primary near-term capacity constraint.`,
    `The transparent moving-average baseline backtests at ${pct(averageWape)} average WAPE across products.`,
    `Recommended capacity totals ${data.staffing.total_agents} agents under a ${(data.staffing.assumptions.service_level_buffer*100-100).toFixed(0)}% service buffer.`
  ].map(text=>`<li>${text}</li>`).join('');
  $('#issue-list').innerHTML = Object.entries(data.top_issues).map(([name,value])=>`<div class="issue"><span>${name}</span><strong>${value}</strong></div>`).join('');

  const maxForecast = Math.max(...Object.values(data.forecast).flat());
  $('#forecast-chart').innerHTML = Object.entries(data.forecast).map(([product,values])=>`<div class="forecast-group">${values.map((value,index)=>`<div class="forecast-bar" title="Week ${index+1}: ${value}" style="height:${value/maxForecast*88}%"></div>`).join('')}<span>${product}</span></div>`).join('');
  $('#staffing-body').innerHTML = data.staffing.teams.map(team=>`<tr><td>${team.team}</td><td>${team.peak_weekly_demand}</td><td><strong>${team.recommended_agents}</strong></td><td>${team.weekly_capacity}</td><td>${pct(team.utilization)}</td></tr>`).join('');
}).catch(error => {
  console.error(error);
  $('#mode').textContent = 'Run make run';
});

