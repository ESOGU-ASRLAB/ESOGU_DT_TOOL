import { configureStore } from '@reduxjs/toolkit';
import codeReviewReducer from './slices/codeReviewSlice';
import requirementAnalysisReducer from './slices/requirementAnalysisSlice';
import testPlanningReducer from './slices/testPlanningSlice';
import environmentSetupReducer from './slices/environmentSetupSlice';
import apiKeyReducer from './slices/apiKeySlice';
import { apiKeyPersistenceMiddleware } from './middleware/apiKeyPersistence';

export const store = configureStore({
  reducer: {
    codeReview: codeReviewReducer,
    requirementAnalysis: requirementAnalysisReducer,
    testPlanning: testPlanningReducer,
    environmentSetup: environmentSetupReducer,
    apiKey: apiKeyReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }).concat(apiKeyPersistenceMiddleware),
});