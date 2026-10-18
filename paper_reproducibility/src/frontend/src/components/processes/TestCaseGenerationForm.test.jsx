import { describe, expect, it } from 'vitest';
import { normalizeTestScenarios } from './testCaseGenerationUtils';

describe('normalizeTestScenarios', () => {
  const scenarios = [{ ScenarioID: 'SC-1', Title: 'Example' }];

  it('keeps an array response unchanged', () => {
    expect(normalizeTestScenarios(scenarios)).toBe(scenarios);
  });

  it('unwraps the object shape returned while process data is loading', () => {
    expect(normalizeTestScenarios({ TestScenarios: scenarios })).toEqual(scenarios);
  });

  it('returns an empty array for missing or unexpected data', () => {
    expect(normalizeTestScenarios(null)).toEqual([]);
    expect(normalizeTestScenarios({ pending: true })).toEqual([]);
  });
});
