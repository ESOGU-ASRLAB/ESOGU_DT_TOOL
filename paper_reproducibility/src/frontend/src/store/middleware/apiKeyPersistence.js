// Middleware for persisting API key state to localStorage
export const apiKeyPersistenceMiddleware = (store) => (next) => (action) => {
  const result = next(action);
  
  // Only persist on API key related actions
  if (action.type?.startsWith('apiKey/')) {
    const state = store.getState();
    
    // Save API keys to localStorage
    try {
      localStorage.setItem('stlc_api_keys', JSON.stringify(state.apiKey.apiKeys));
      
      // Save settings to localStorage
      localStorage.setItem('stlc_api_key_settings', JSON.stringify(state.apiKey.settings));
    } catch (error) {
      console.error('Error persisting API key state:', error);
    }
  }
  
  return result;
};

// Load persisted state
export const loadPersistedApiKeyState = () => {
  try {
    const apiKeys = localStorage.getItem('stlc_api_keys');
    const settings = localStorage.getItem('stlc_api_key_settings');
    
    return {
      apiKeys: apiKeys ? JSON.parse(apiKeys) : {
        google: null,
        openai: null,
        anthropic: null,
      },
      settings: settings ? JSON.parse(settings) : {
        autoValidate: true,
        showApiKeyStatus: true,
        defaultProvider: 'google',
      }
    };
  } catch (error) {
    console.error('Error loading persisted API key state:', error);
    return {
      apiKeys: {
        google: null,
        openai: null,
        anthropic: null,
      },
      settings: {
        autoValidate: true,
        showApiKeyStatus: true,
        defaultProvider: 'google',
      }
    };
  }
};