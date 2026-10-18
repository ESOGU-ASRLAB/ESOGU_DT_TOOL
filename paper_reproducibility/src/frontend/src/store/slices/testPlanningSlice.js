import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { processService } from '../../services/processService';

export const runTestPlanning = createAsyncThunk(
  'testPlanning/runPlanning',
  async ({files, model, customPrompt, sessionId, apiKey}) => {
    try {
      // İstersen model bilgisini gösterebilirsin
      // window.alert(`Selected model: ${model}`);
      const response = await processService.runTestPlanning(files, model, customPrompt, sessionId, apiKey);
      if (!response || !response.plans) {
        throw new Error('Invalid response format');
      }
      return response;
    } catch (error) {
      throw error;
    }
  }
);

const testPlanningSlice = createSlice({
  name: 'testPlanning',
  initialState: {
    plans: [],
    metadata: null,
    status: 'idle',
    error: null,
    history: []
  },
  reducers: {
    clearPlans: (state) => {
      state.plans = [];
      state.status = 'idle';
      state.error = null;
    },
    addToHistory: (state) => {
      state.history.push({
        plans: state.plans,
        metadata: state.metadata,
        timestamp: new Date().toISOString()
      });
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(runTestPlanning.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(runTestPlanning.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.plans = action.payload.plans;
        state.metadata = action.payload.metadata;
        state.error = null;
      })
      .addCase(runTestPlanning.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      });
  }
});

export const { clearPlans } = testPlanningSlice.actions;
export default testPlanningSlice.reducer;