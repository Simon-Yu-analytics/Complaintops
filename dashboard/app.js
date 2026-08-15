const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const {
  feedbackStats,
  forecastGeometry,
  routeComplaint,
  staffingScenario,
  thresholdScenario
} = window.ComplaintOpsLogic;

const pct = value => `${(Number(value) * 100).toFixed(1)}%`;
const money = value => new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 0
}).format(value);
const escapeHtml = value => String(value).replace(/[&<>'"]/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
})[character]);

const samples = {
  card: 'The same card purchase was charged twice. The merchant refund never appeared on my card statement, and I need the issuer to correct the account.',
  mortgage: 'My mortgage payment was applied to the wrong month. The servicer changed the escrow amount without explaining the calculation.',
  reporting: 'An account I do not recognize remains on my credit file. The credit bureau has not corrected the information after my dispute.',
  ambiguous: 'I need help resolving a problem with my account. Customer service transferred me twice and the response did not address my evidence.'
};

const supportAnswers = {
  status: 'A real service would show updates against a secure case reference. In this portfolio demo, create a demo case after analyzing a narrative and its reference will appear on this device.',
  review: 'Human review is used when the model confidence falls below the frozen threshold. That prevents the system from forcing uncertain complaints into the wrong queue.',
  privacy: 'This demo does not send your text to a server. Complaint text, demo cases, and feedback stay in this browser. Please do not enter personal information.',
  human: 'I created a demo request for a human specialist. In a production system, this step would enter a secure queue with identity verification and service-level tracking.',
  documents: 'Do not upload personal or financial documents here. A production service would use an authenticated and encrypted document portal.'
};

let memoryStore = {};
let lastRouting = null;
let selectedRating = 0;

const readLocalArray = key => {
  try {
    const value = window.localStorage.getItem(key);
    return value ? JSON.parse(value) : (memoryStore[key] || []);
  } catch (error) {
    return memoryStore[key] || [];
  }
};

const writeLocalArray = (key, value) => {
  memoryStore[key] = value;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    // Private browsing can block storage; in-memory state still supports the demo.
  }
};

const showPage = (pageName, updateHash = true) => {
  const page = document.getElementById(pageName);
  const button = document.querySelector(`.nav-item[data-page="${pageName}"]`);
  if (!page || !button) return;
  $$('.nav-item,.page').forEach(element => element.classList.remove('active'));
  button.classList.add('active');
  page.classList.add('active');
  if (updateHash) window.history.replaceState(null, '', `#${pageName}`);
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

$$('.nav-item').forEach(button => {
  button.addEventListener('click', () => showPage(button.dataset.page));
});
$$('[data-open-page]').forEach(button => {
  button.addEventListener('click', () => showPage(button.dataset.openPage));
});

const appendChat = (speaker, message) => {
  const wrapper = document.createElement('div');
  wrapper.className = `chat-message ${speaker === 'customer' ? 'customer' : 'assistant'}`;
  const label = document.createElement('span');
  label.textContent = speaker === 'customer' ? 'You' : 'ComplaintOps support';
  const paragraph = document.createElement('p');
  paragraph.textContent = message;
  wrapper.append(label, paragraph);
  $('#chat-log').append(wrapper);
  $('#chat-log').scrollTop = $('#chat-log').scrollHeight;
};

const answerSupportQuestion = question => {
  const normalized = String(question).toLowerCase();
  if (/status|reference|track|update/.test(normalized)) return supportAnswers.status;
  if (/review|uncertain|confidence|why/.test(normalized)) return supportAnswers.review;
  if (/privacy|stored|save|information|data/.test(normalized)) return supportAnswers.privacy;
  if (/human|person|agent|specialist|representative/.test(normalized)) return supportAnswers.human;
  if (/document|upload|evidence|receipt/.test(normalized)) return supportAnswers.documents;
  return 'I can explain case status, human review, privacy, document handling, or how to request a specialist. This guided assistant does not provide financial or legal advice.';
};

const createDemoCase = source => {
  const reference = `DEMO-${Date.now().toString(36).slice(-5).toUpperCase()}-${Math.floor(Math.random() * 90 + 10)}`;
  const cases = readLocalArray('complaintops-demo-cases');
  cases.push({
    reference,
    source,
    queue: lastRouting?.label || 'Human review',
    created_at: new Date().toISOString()
  });
  writeLocalArray('complaintops-demo-cases', cases.slice(-20));
  return reference;
};

const renderFeedbackSummary = () => {
  const entries = readLocalArray('complaintops-feedback');
  const stats = feedbackStats(entries);
  $('#feedback-summary').innerHTML = stats.count
    ? `<span>This device</span><strong>${stats.average.toFixed(1)} / 5 · ${stats.count} submission${stats.count === 1 ? '' : 's'}</strong>`
    : '<span>This device</span><strong>No feedback submitted yet</strong>';
};

const initializeCustomerExperience = model => {
  const input = $('#complaint-input');
  const updateCount = () => {
    $('#character-count').textContent = `${input.value.length} / 800`;
    $('#input-guidance').textContent = input.value.trim().length >= 20
      ? 'Ready to analyze.'
      : 'Use at least 20 characters.';
  };
  input.addEventListener('input', updateCount);

  $$('[data-sample]').forEach(button => {
    button.addEventListener('click', () => {
      input.value = samples[button.dataset.sample];
      updateCount();
      input.focus();
    });
  });

  $('#routing-form').addEventListener('submit', event => {
    event.preventDefault();
    const narrative = input.value.trim();
    if (narrative.length < 20) {
      $('#input-guidance').textContent = 'Please add more detail before analysis.';
      input.focus();
      return;
    }
    lastRouting = routeComplaint(narrative, model);
    $('#empty-result').hidden = true;
    $('#routing-result').hidden = false;
    const isReview = lastRouting.decision === 'human-review';
    $('#routing-decision').textContent = isReview ? 'Human review recommended' : 'Eligible for auto-route';
    $('#routing-decision').classList.toggle('review', isReview);
    $('#routing-queue').textContent = lastRouting.label;
    $('#routing-confidence').textContent = pct(lastRouting.confidence);
    $('#probability-list').innerHTML = lastRouting.ranking.map(item => `
      <div class="probability-row"><span>${escapeHtml(item.label)}</span>
      <div class="probability-track"><div class="probability-fill" style="width:${item.probability * 100}%"></div></div>
      <strong>${pct(item.probability)}</strong></div>
    `).join('');
    $('#evidence-tokens').innerHTML = lastRouting.evidence.length
      ? lastRouting.evidence.map(item => `<b>${escapeHtml(item.token)}</b>`).join('')
      : '<b>No discriminating model words found</b>';
    $('#routing-note').textContent = lastRouting.recognizedTokens === 0
      ? 'The model did not recognize enough relevant language, so the case is reserved for a person.'
      : isReview
        ? `Confidence is below the frozen ${pct(model.threshold)} threshold, so the safer action is human review.`
        : `Confidence meets the frozen ${pct(model.threshold)} threshold selected on the calibration window.`;
    $('#case-confirmation').hidden = true;
  });

  $('#create-demo-case').addEventListener('click', () => {
    if (!lastRouting) return;
    const reference = createDemoCase('routing-result');
    $('#case-confirmation').hidden = false;
    $('#case-confirmation').textContent = `Demo case ${reference} created · Queue: ${lastRouting.label} · Stored on this device only.`;
  });

  $$('[data-support-question]').forEach(button => {
    button.addEventListener('click', () => {
      appendChat('customer', button.textContent);
      appendChat('assistant', supportAnswers[button.dataset.supportQuestion]);
    });
  });

  $('#support-form').addEventListener('submit', event => {
    event.preventDefault();
    const supportInput = $('#support-input');
    const question = supportInput.value.trim();
    if (!question) return;
    appendChat('customer', question);
    appendChat('assistant', answerSupportQuestion(question));
    supportInput.value = '';
  });

  $('#human-support-action').addEventListener('click', () => {
    const reference = createDemoCase('support-request');
    $('#support-status').textContent = `Human-support demo request created: ${reference}. No message was sent externally.`;
    appendChat('assistant', supportAnswers.human);
  });

  $$('#rating-buttons button').forEach(button => {
    button.addEventListener('click', () => {
      selectedRating = Number(button.dataset.rating);
      $$('#rating-buttons button').forEach(item => {
        const selected = Number(item.dataset.rating) === selectedRating;
        item.classList.toggle('selected', selected);
        item.setAttribute('aria-checked', String(selected));
      });
      $('#feedback-status').textContent = '';
    });
  });

  $('#feedback-form').addEventListener('submit', event => {
    event.preventDefault();
    if (!selectedRating) {
      $('#feedback-status').textContent = 'Choose a rating before submitting.';
      return;
    }
    const entries = readLocalArray('complaintops-feedback');
    entries.push({
      rating: selectedRating,
      topic: $('#feedback-topic').value,
      comment: $('#feedback-comment').value.trim(),
      created_at: new Date().toISOString()
    });
    writeLocalArray('complaintops-feedback', entries.slice(-50));
    $('#feedback-comment').value = '';
    $('#feedback-status').textContent = 'Thank you. Your demo feedback was saved on this device only.';
    selectedRating = 0;
    $$('#rating-buttons button').forEach(item => {
      item.classList.remove('selected');
      item.setAttribute('aria-checked', 'false');
    });
    renderFeedbackSummary();
  });

  renderFeedbackSummary();
  updateCount();
};

const initializeOperations = data => {
  const routing = data.classification.selective_routing;
  $('#mode').textContent = 'interactive synthetic demo';
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
  const wapeValues = Object.values(data.forecast_wape);
  const averageWape = wapeValues.reduce((a, b) => a + b, 0) / wapeValues.length;
  $('#insights').innerHTML = [
    `${largest[0]} is the largest queue at ${largest[1]} cases in the analysis window.`,
    `${staffingPeak.team} has the highest upper-bound planning demand at ${staffingPeak.planning_demand} weekly cases.`,
    `The selected product baselines backtest at ${pct(averageWape)} average WAPE.`,
    `${pct(routing.review_rate)} of low-confidence cases are reserved for human review.`
  ].map(text => `<li>${escapeHtml(text)}</li>`).join('');
  $('#issue-list').innerHTML = Object.entries(data.top_issues).map(([name, value]) => `
    <div class="issue"><span>${escapeHtml(name)}</span><strong>${value}</strong></div>
  `).join('');

  const curve = data.classification.calibration_curve;
  const thresholdIndex = curve.reduce((best, item, index) => (
    Math.abs(item.threshold - routing.threshold) < Math.abs(curve[best].threshold - routing.threshold)
      ? index : best
  ), 0);
  $('#threshold-slider').max = String(curve.length - 1);
  $('#threshold-slider').value = String(thresholdIndex);
  const renderPolicy = () => {
    const point = thresholdScenario(curve, Number($('#threshold-slider').value));
    const frozen = Math.abs(point.threshold - routing.threshold) < 0.0001 ? ' · frozen' : '';
    $('#policy-threshold').textContent = `${pct(point.threshold)}${frozen}`;
    $('#policy-accuracy').textContent = pct(point.accuracy);
    $('#policy-coverage').textContent = pct(point.coverage);
    $('#policy-review').textContent = pct(point.review_rate);
  };
  $('#threshold-slider').addEventListener('input', renderPolicy);
  renderPolicy();

  $('#forecast-methods').innerHTML = Object.entries(data.forecast_detail).map(([product, detail]) => `
    <article><span>${escapeHtml(product)}</span><strong>${escapeHtml(detail.method)}</strong>
    <small>${pct(detail.backtest_wape)} WAPE</small></article>
  `).join('');
  const forecastFilter = $('#forecast-product-filter');
  Object.keys(data.forecast_detail).forEach(product => {
    const option = document.createElement('option');
    option.value = product;
    option.textContent = product;
    forecastFilter.append(option);
  });
  const renderForecast = () => {
    const allEntries = Object.entries(data.forecast_detail);
    const entries = forecastFilter.value === 'all'
      ? allEntries
      : allEntries.filter(([product]) => product === forecastFilter.value);
    const maxForecast = Math.max(...entries.flatMap(([, detail]) => detail.upper), 1);
    $('#forecast-chart').innerHTML = entries.map(([product, detail]) => `
      <div class="forecast-group">${detail.point.map((value, index) => {
        const geometry = forecastGeometry(detail.lower[index], value, detail.upper[index], maxForecast);
        return `<div class="forecast-column" title="Week ${index + 1}: ${detail.lower[index]}–${detail.upper[index]} cases">
          <div class="forecast-range" style="bottom:${geometry.bandBottom}%;height:${geometry.bandHeight}%"></div>
          <div class="forecast-bar" style="height:${geometry.pointHeight}%"></div></div>`;
      }).join('')}<span>${escapeHtml(product)}</span></div>
    `).join('');
  };
  forecastFilter.addEventListener('change', renderForecast);
  renderForecast();

  const renderStaffing = () => {
    const stress = Number($('#stress-slider').value) / 100;
    const casesPerAgent = Number($('#productivity-slider').value);
    const weeklyCost = Number($('#cost-slider').value);
    const scenario = staffingScenario(data.staffing.teams, stress, casesPerAgent, weeklyCost);
    $('#staffing-body').innerHTML = scenario.teams.map(team => `
      <tr><td>${escapeHtml(team.team)}</td><td>${team.pointDemand}</td>
      <td>${team.planningDemand}</td><td><strong>${team.agents}</strong></td>
      <td>${team.capacity}</td><td>${pct(team.utilization)}</td></tr>
    `).join('');
    $('#weekly-cost').textContent = `${scenario.totalAgents} agents · ${money(scenario.weeklyCost)} / week`;
    $('#stress-label').textContent = `+${Math.round(stress * 100)}%`;
    $('#productivity-label').textContent = String(casesPerAgent);
    $('#cost-label').textContent = money(weeklyCost);
  };
  ['#stress-slider', '#productivity-slider', '#cost-slider'].forEach(selector => {
    $(selector).addEventListener('input', renderStaffing);
  });
  $('#scenario-reset').addEventListener('click', () => {
    $('#stress-slider').value = '0';
    $('#productivity-slider').value = String(data.staffing.assumptions.cases_per_agent_week);
    $('#cost-slider').value = String(data.staffing.assumptions.weekly_cost_per_agent);
    renderStaffing();
  });
  renderStaffing();
};

try {
  if (!window.COMPLAINTOPS_RESULTS || !window.COMPLAINTOPS_MODEL) {
    throw new Error('Generated application data is missing');
  }
  initializeOperations(window.COMPLAINTOPS_RESULTS);
  initializeCustomerExperience(window.COMPLAINTOPS_MODEL);
  const requestedPage = window.location.hash.slice(1);
  if (requestedPage) showPage(requestedPage, false);
} catch (error) {
  console.error(error);
  $('#mode').textContent = 'Run make run';
}
