const assert = require('node:assert/strict');
const { forecastGeometry, staffingScenario } = require('../dashboard/logic.js');

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

console.log(`${passed} dashboard logic tests passed`);
