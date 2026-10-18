import React, { useState } from 'react';
import { useApiKey, useProviderApiKey } from '../../hooks/useApiKey';
import './ApiKeySettings.css';

const ApiKeySettings = ({ isModal = false }) => {
  const { settings, updateSettings, clearErrors, availableProviders } = useApiKey();
  const googleApiKey = useProviderApiKey('google');
  const openaiApiKey = useProviderApiKey('openai');
  
  const [localKeys, setLocalKeys] = useState({
    google: '',
    openai: '',
  });

  const [showKeys, setShowKeys] = useState({
    google: false,
    openai: false,
  });

  const handleKeyChange = (provider, value) => {
    setLocalKeys(prev => ({
      ...prev,
      [provider]: value
    }));
  };

  const handleSaveKey = (provider) => {
    const key = localKeys[provider].trim();
    if (key) {
      if (provider === 'google') {
        googleApiKey.setKey(key);
        // Manual validation only - user can click validate button
      } else if (provider === 'openai') {
        openaiApiKey.setKey(key);
      }
      
      // Clear local input
      setLocalKeys(prev => ({
        ...prev,
        [provider]: ''
      }));
    }
  };

  const handleRemoveKey = (provider) => {
    if (provider === 'google') {
      googleApiKey.removeKey();
    } else if (provider === 'openai') {
      openaiApiKey.removeKey();
    }
  };

  const handleValidateKey = (provider) => {
    if (provider === 'google') {
      googleApiKey.validateKey();
    } else if (provider === 'openai') {
      // Add OpenAI validation when implemented
      console.log('OpenAI validation not implemented yet');
    }
  };

  const toggleShowKey = (provider) => {
    setShowKeys(prev => ({
      ...prev,
      [provider]: !prev[provider]
    }));
  };

  const handleSettingsChange = (setting, value) => {
    updateSettings({ [setting]: value });
  };

  const providers = [
    {
      key: 'google',
      name: 'Google AI',
      description: 'Google Gemini models',
      hook: googleApiKey,
      validationSupported: true,
    },
    {
      key: 'openai',
      name: 'OpenAI',
      description: 'GPT models',
      hook: openaiApiKey,
      validationSupported: false, // Will be true when implemented
    },
  ];

  return (
    <div className={`api-key-settings ${isModal ? 'modal-mode' : ''}`}>
      {!isModal && (
        <div className="settings-header">
          <h2>API Key Management</h2>
          <p>Manage your API keys for different AI providers. Keys are stored locally and encrypted.</p>
        </div>
      )}

      {/* Global Settings */}
      <div className="settings-section">
        <h3>General Settings</h3>
        {/* Auto-validate setting temporarily disabled to prevent infinite loops
        <div className="setting-item">
          <label>
            <input
              type="checkbox"
              checked={settings.autoValidate}
              onChange={(e) => handleSettingsChange('autoValidate', e.target.checked)}
            />
            Auto-validate API keys
          </label>
          <span className="setting-description">
            Automatically validate API keys when they are added or changed
          </span>
        </div>
        */}
        
        <div className="setting-item">
          <label>
            <input
              type="checkbox"
              checked={settings.showApiKeyStatus}
              onChange={(e) => handleSettingsChange('showApiKeyStatus', e.target.checked)}
            />
            Show API key status in model dropdowns
          </label>
          <span className="setting-description">
            Display validation status indicators for API models in dropdown menus
          </span>
        </div>

        <div className="setting-item">
          <label>Default Provider:</label>
          <select
            value={settings.defaultProvider}
            onChange={(e) => handleSettingsChange('defaultProvider', e.target.value)}
            className="setting-select"
          >
            <option value="google">Google AI</option>
            <option value="openai">OpenAI</option>
            <option value="local">Local Models</option>
          </select>
        </div>
      </div>

      {/* API Keys Management */}
      <div className="settings-section">
        <h3>API Keys</h3>
        {providers.map((provider) => (
          <div key={provider.key} className="api-key-item">
            <div className="provider-header">
              <div className="provider-info">
                <h4>{provider.name}</h4>
                <span className="provider-description">{provider.description}</span>
              </div>
              <div className="provider-status">
                {provider.hook.apiKey && (
                  <span className={`status-badge ${
                    provider.hook.isValid === true ? 'valid' : 
                    provider.hook.isValid === false ? 'invalid' : 'unknown'
                  }`}>
                    {provider.hook.isValidating ? 'Validating...' :
                     provider.hook.isValid === true ? 'Valid' :
                     provider.hook.isValid === false ? 'Invalid' : 'Not Validated'}
                  </span>
                )}
              </div>
            </div>

            {provider.hook.apiKey ? (
              <div className="existing-key">
                <div className="key-display">
                  <input
                    type={showKeys[provider.key] ? 'text' : 'password'}
                    value={provider.hook.apiKey}
                    readOnly
                    className="key-input readonly"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey(provider.key)}
                    className="toggle-visibility"
                  >
                    {showKeys[provider.key] ? '👁️‍🗨️' : '👁️'}
                  </button>
                </div>
                
                <div className="key-actions">
                  {provider.validationSupported && (
                    <button
                      onClick={() => handleValidateKey(provider.key)}
                      disabled={provider.hook.isValidating}
                      className="validate-btn"
                    >
                      {provider.hook.isValidating ? 'Validating...' : 'Validate'}
                    </button>
                  )}
                  <button
                    onClick={() => handleRemoveKey(provider.key)}
                    className="remove-btn"
                  >
                    Remove
                  </button>
                </div>

                {provider.hook.error && (
                  <div className="error-message">
                    {provider.hook.error}
                  </div>
                )}
              </div>
            ) : (
              <div className="add-key">
                <div className="key-input-group">
                  <input
                    type="password"
                    placeholder={`Enter ${provider.name} API key`}
                    value={localKeys[provider.key]}
                    onChange={(e) => handleKeyChange(provider.key, e.target.value)}
                    className="key-input"
                  />
                  <button
                    onClick={() => handleSaveKey(provider.key)}
                    disabled={!localKeys[provider.key].trim()}
                    className="save-btn"
                  >
                    Save
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Available Providers Summary */}
      {availableProviders.length > 0 && (
        <div className="settings-section">
          <h3>Available Providers</h3>
          <div className="available-providers">
            {availableProviders.map(provider => (
              <span key={provider} className="provider-badge">
                {provider}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="settings-actions">
        <button onClick={clearErrors} className="clear-errors-btn">
          Clear All Errors
        </button>
      </div>
    </div>
  );
};

export default ApiKeySettings;