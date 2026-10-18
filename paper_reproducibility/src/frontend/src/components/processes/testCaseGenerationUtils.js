export const normalizeTestScenarios = (value) => {
  if (Array.isArray(value)) return value;
  if (!value || typeof value !== 'object') return [];

  const candidates = [
    value.TestScenarios,
    value.test_scenarios,
    value.scenarios,
    value.output?.TestScenarios,
    value.output?.test_scenarios,
  ];
  return candidates.find(Array.isArray) || [];
};
