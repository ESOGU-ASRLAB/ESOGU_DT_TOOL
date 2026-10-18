import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { processService } from '../../services/processService';

export const runEnvironmentSetup = createAsyncThunk(
  'environmentSetup/runSetup',
  async ({files, model, customPrompt, sessionId, environmentName, apiKey}) => {
    try {
      const response = await processService.runEnvironmentSetup(files, model, customPrompt, sessionId, environmentName, apiKey);
      if (!response || !response.setups) {
        throw new Error('Invalid response format');
      }
      return response;
    } catch (error) {
      throw error;
    }
  }
);

const environmentSetupSlice = createSlice({
  name: 'environmentSetup',
  initialState: {
    setups: [],
    metadata: null,
    status: 'idle',
    error: null,
    history: []
  },
  reducers: {
    clearSetups: (state) => {
      state.setups = [];
      state.status = 'idle';
      state.error = null;
    },
    addToHistory: (state) => {
      state.history.push({
        setups: state.setups,
        metadata: state.metadata,
        timestamp: new Date().toISOString()
      });
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(runEnvironmentSetup.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(runEnvironmentSetup.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.setups = action.payload.setups;
        state.metadata = action.payload.metadata;
        state.error = null;
      })
      .addCase(runEnvironmentSetup.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      });
  }
});

export const { clearSetups } = environmentSetupSlice.actions;
export default environmentSetupSlice.reducer; 