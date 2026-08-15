const assert = require('node:assert/strict');
const model = require('../dashboard/data/model.json');
const {
  feedbackStats,
  forecastGeometry,
  routeComplaint,
  staffingScenario,
  thresholdScenario
} = require('../dashboard/logic.js');

let passed = 0;
const test = (name, fn) => {
  fn();
  passed += 1;
  console.log(`ok - ${name}`);
};

test('forecast interval begins at its lower bound', () => {
  const result = forecastGeometry(20, 25, 30, 50, 100);
  assert.deepEqual(result, { bandBottom: 40, bandHeight: 20, pointHeight: 50 });
});

test('stress applies to point and upper-bound demand', () => {
  const result = staffingScenario(
    [{ team: 'Cards', peak_weekly_demand: 20, planning_demand: 30 }],
    0.25,
    24,
    1650
  );
  assert.equal(result.teams[0].pointDemand, 25);
  assert.equal(result.teams[0].planningDemand, 38);
});

test('scenario headcount, capacity, utilization, and cost reconcile', () => {
  const result = staffingScenario(
    [{ team: 'Cards', peak_weekly_demand: 20, planning_demand: 30 }],
    0.25,
    24,
    1650
  );
  assert.equal(result.totalAgents, 2);
  assert.equal(result.teams[0].capacity, 48);
  assert.equal(result.teams[0].utilization, 25 / 48);
  assert.equal(result.weeklyCost, 3300);
});

test('invalid forecast geometry is rejected', () => {
  assert.throws(() => forecastGeometry(30, 20, 40, 50), RangeError);
});

test('browser model routes a clear credit-card narrative', () => {
  const result = routeComplaint(
    'the same card purchase was charged twice and the merchant refund never appeared',
    model
  );
  assert.equal(result.label, 'Credit card');
  assert.ok(result.recognizedTokens > 0);
  assert.ok(Math.abs(result.ranking.reduce((sum, item) => sum + item.probability, 0) - 1) < 1e-12);
});

test('unrecognized language is reserved for human review', () => {
  const result = routeComplaint('quartz zephyr xylophone', model);
  assert.equal(result.recognizedTokens, 0);
  assert.equal(result.decision, 'human-review');
});

test('recognized but ambiguous language is reserved for human review', () => {
  const result = routeComplaint(
    'I need help resolving a problem with my account. Customer service transferred me twice and the response did not address my evidence.',
    model
  );
  assert.ok(result.recognizedTokens > 0);
  assert.ok(result.confidence < model.threshold);
  assert.equal(result.decision, 'human-review');
});

test('threshold scenarios clamp to the available curve', () => {
  const curve = [{ threshold: 0.5 }, { threshold: 0.9 }];
  assert.equal(thresholdScenario(curve, 99).threshold, 0.9);
  assert.equal(thresholdScenario(curve, -4).threshold, 0.5);
});

test('device feedback summary ignores invalid ratings', () => {
  const result = feedbackStats([{ rating: 5 }, { rating: 3 }, { rating: 9 }]);
  assert.deepEqual(result, { count: 2, average: 4 });
});

console.log(`${passed} dashboard logic tests passed`);
