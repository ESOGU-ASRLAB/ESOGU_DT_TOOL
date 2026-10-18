import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { processService } from '../../services/processService';

export const runRequirementAnalysis = createAsyncThunk(
  'requirementAnalysis/runAnalysis',
  async ({files, model, customPrompt, sessionId, apiKey}) => {
    try {
      window.alert(`Selected model: ${model}`);
      const response = await processService.runRequirementAnalysis(files, model, customPrompt, sessionId, apiKey);
      if (!response) {
        throw new Error('Invalid response format');
      }
      return response;
    } catch (error) {
      throw error;
    }
  }
);

const requirementAnalysisSlice = createSlice({
  name: 'requirementAnalysis',
  initialState: {
    result: null,
    status: 'idle',
    error: null,
    history: []
  },
  reducers: {
    clearResult: (state) => {
      state.result = null;
      state.status = 'idle';
      state.error = null;
    },
    addToHistory: (state) => {
      state.history.push({
        result: state.result,
        timestamp: new Date().toISOString()
      });
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(runRequirementAnalysis.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(runRequirementAnalysis.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.result = action.payload;
        state.error = null;
      })
      .addCase(runRequirementAnalysis.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      });
  }
});

export const { clearResult } = requirementAnalysisSlice.actions;
export default requirementAnalysisSlice.reducer; 