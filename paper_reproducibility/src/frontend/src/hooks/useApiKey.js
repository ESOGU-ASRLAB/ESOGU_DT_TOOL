import { useSelector, useDispatch } from 'react-redux';
import { useCallback, useEffect } from 'react';
import {
  setApiKey,
  removeApiKey,
  updateSettings,
  clearValidationErrors,
  validateGoogleApiKey,
  selectApiKeys,
  selectApiKey,
  selectValidationStatus,
  selectAllValidationStatus,
  selectApiKeySettings,
  selectIsAnyKeyValidating,
  selectHasValidApiKey,
  selectAvailableProviders,
} from '../store/slices/apiKeySlice';

/**
 * Custom hook for managing API keys with Redux
 * Provides centralized API key management across the application
 */
export const useApiKey = () => {
  const dispatch = useDispatch();
  
  // Selectors
  const apiKeys = useSelector(selectApiKeys);
  const validationStatus = useSelector(selectAllValidationStatus);
  const settings = useSelector(selectApiKeySettings);
  const isAnyKeyValidating = useSelector(selectIsAnyKeyValidating);
  const availableProviders = useSelector(selectAvailableProviders);

  // Actions
  const setKey = useCallback((provider, key) => {
    dispatch(setApiKey({ provider, key }));
  }, [dispatch]);

  const removeKey = useCallback((provider) => {
    dispatch(removeApiKey({ provider }));
  }, [dispatch]);

  const updateAppSettings = useCallback((newSettings) => {
    dispatch(updateSettings(newSettings));
  }, [dispatch]);

  const clearErrors = useCallback(() => {
    dispatch(clearValidationErrors());
  }, [dispatch]);

  const validateKey = useCallback((provider, key) => {
    switch (provider) {
      case 'google':
        return dispatch(validateGoogleApiKey(key));
      // Add other providers as needed
      default:
        console.warn(`Validation not implemented for provider: ${provider}`);
        return Promise.resolve();
    }
  }, [dispatch]);

  // Utility functions
  const getApiKey = useCallback((provider) => {
    return apiKeys[provider];
  }, [apiKeys]);

  const getValidationStatus = useCallback((provider) => {
    return validationStatus[provider] || { 
      isValidating: false, 
      isValid: null, 
      error: null, 
      lastValidated: null 
    };
  }, [validationStatus]);

  const hasValidKey = useCallback((provider) => {
    const key = apiKeys[provider];
    const validation = validationStatus[provider];
    return key && validation?.isValid === true;
  }, [apiKeys, validationStatus]);

  const isKeyValidating = useCallback((provider) => {
    return validationStatus[provider]?.isValidating || false;
  }, [validationStatus]);

  const getKeyError = useCallback((provider) => {
    return validationStatus[provider]?.error || null;
  }, [validationStatus]);

  // Auto-validate keys on mount if autoValidate is enabled
  // Manual validation only - no auto validation to prevent loops
  // Use validateKey function explicitly when needed

  return {
    // State
    apiKeys,
    validationStatus,
    settings,
    isAnyKeyValidating,
    availableProviders,
    
    // Actions
    setKey,
    removeKey,
    updateSettings: updateAppSettings,
    clearErrors,
    validateKey,
    
    // Utilities
    getApiKey,
    getValidationStatus,
    hasValidKey,
    isKeyValidating,
    getKeyError,
  };
};

/**
 * Hook for specific provider API key management
 */
export const useProviderApiKey = (provider) => {
  const dispatch = useDispatch();
  
  // Selectors for specific provider
  const apiKey = useSelector(selectApiKey(provider));
  const validationStatus = useSelector(selectValidationStatus(provider));
  const hasValidKey = useSelector(selectHasValidApiKey(provider));
  
  // Provider-specific actions
  const setKey = useCallback((key) => {
    dispatch(setApiKey({ provider, key }));
  }, [dispatch, provider]);

  const removeKey = useCallback(() => {
    dispatch(removeApiKey({ provider }));
  }, [dispatch, provider]);

  const validateKey = useCallback((key = apiKey) => {
    if (key) {
      switch (provider) {
        case 'google':
          return dispatch(validateGoogleApiKey(key));
        // Add other providers as needed
        default:
          console.warn(`Validation not implemented for provider: ${provider}`);
          return Promise.resolve();
      }
    }
  }, [dispatch, provider, apiKey]);

  return {
    // State
    apiKey,
    validationStatus: validationStatus || { 
      isValidating: false, 
      isValid: null, 
      error: null, 
      lastValidated: null 
    },
    hasValidKey,
    
    // Actions
    setKey,
    removeKey,
    validateKey,
    
    // Computed values
    isValidating: validationStatus?.isValidating || false,
    isValid: validationStatus?.isValid,
    error: validationStatus?.error,
    lastValidated: validationStatus?.lastValidated,
  };
};