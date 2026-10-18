import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useModels } from '../../hooks/useModels';

// Model açıklamaları örnek
function useModelInfo(selectedModel) {
    const modelDescriptions = {
        "codegeex4: 9B": [
          "A multilingual code generation model with 9B parameters.",
          "Supports tasks like code completion, commenting, and function calls.",
          "Trained on GLM-4-9B and can handle 128K token context."
        ],
        "codellama: 7B": [
          "A code generation model based on Meta's Llama 2 architecture.",
          "Supports various languages like Python, C++, Java, PHP, TypeScript, C#, and Bash.",
          "Capable of code completion, debugging, and natural language descriptions."
        ],
        "deepseek-coder: 6.7B": [
          "A 6.7B parameter model optimized for code generation and interpretation.",
          "Provides high-accuracy code generation in various programming languages.",
          "Efficient at code completion and bug-fixing tasks."
        ],
        "gemma2: 2B": [
          "A lightweight 2B parameter model for code generation.",
          "Ideal for small projects and low-resource environments.",
          "Supports basic code completion and suggestions."
        ],
        "gemma3: 4B": [
          "A 4B parameter model optimized for mid-sized projects.",
          "Can handle more complex code structures.",
          "Balanced performance in code generation and interpretation."
        ],
        "llama3.2: 3B": [
          "A 3B parameter model optimized for fast and efficient code generation.",
          "Effective for small and medium-sized code completion tasks.",
          "Provides low-latency responses."
        ],
        "qwen2.5: 7B": [
          "A multilingual 7B parameter model for code generation.",
          "Generates high-accuracy code in multiple programming languages.",
          "Efficient at code completion and interpretation."
        ],
        "qwen2.5-coder: 3B": [
          "A lightweight 3B parameter model for code generation.",
          "Ideal for small projects and low-resource environments.",
          "Supports basic code completion and suggestions."
        ],
        "stable-code: 3B": [
          "A 3B parameter model known for its stable and reliable code generation.",
          "Effective at code completion and bug fixing.",
          "Supports a variety of programming languages."
        ],
        "starcoder2: 7B": [
          "A 7B parameter model with advanced code generation and analysis capabilities.",
          "Handles complex code structures and projects well.",
          "Excels in code completion and suggestion tasks."
        ]
      };
  return modelDescriptions[selectedModel] || [];
}

export default function EnvironmentSetupForm({ process, onAIModelUpdate, onOutputFormatUpdate, aiModels, disabled, onEnvironmentNameUpdate, environmentNames }) {
  const [model, setModel] = useState(aiModels?.[process?.id] || 'llama3.2: 1B');
  const [modelInfo, setModelInfo] = useState([]);
  const [outputFormat, setOutputFormat] = useState('JSON');
  const [environmentName, setEnvironmentName] = useState(environmentNames?.[process?.id] || '');

  // Merkezi model hook'unu kullan
  const { 
    models: availableModels, 
    loading: modelsLoading, 
    error: modelsError,
    getModelDescriptions
  } = useModels({ 
    autoFetch: true,
    includeDescriptions: true 
  });

  useEffect(() => {
    if (process && onAIModelUpdate && !aiModels?.[process?.id]) {
      onAIModelUpdate(process.id, model);
    }
    
    // Set initial output format
    if (process && onOutputFormatUpdate) {
      onOutputFormatUpdate(process.id, outputFormat);
    }
  }, []);

  const handleModelChange = (e) => {
    const selectedModel = e.target.value;
    setModel(selectedModel);
    setModelInfo(useModelInfo(selectedModel));
    if (process && onAIModelUpdate) {
      onAIModelUpdate(process.id, selectedModel);
    }
  };

  const handleOutputFormatChange = (e) => {
    const selectedFormat = e.target.value;
    setOutputFormat(selectedFormat);
    console.log(`[EnvironmentSetupForm] Output format changed to: ${selectedFormat}`);
    
    if (process && onOutputFormatUpdate) {
      onOutputFormatUpdate(process.id, selectedFormat);
    }
  };

  const handleEnvironmentNameChange = (e) => {
    const name = e.target.value;
    setEnvironmentName(name);
    console.log(`[EnvironmentSetupForm] Environment name changed to: ${name}`);
    
    if (process && onEnvironmentNameUpdate) {
      onEnvironmentNameUpdate(process.id, name);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <form className="space-y-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Process Configuration</h2>
          
          {/* Environment Name Field */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Environment Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={environmentName}
              onChange={handleEnvironmentNameChange}
              placeholder="e.g., Development, Testing, Production, Local Setup..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              disabled={disabled}
            />
            <p className="mt-1 text-sm text-gray-500">
              Enter a descriptive name for this environment configuration. This will be used to identify the setup in Test Code Generation.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">AI Model</label>
            <select
              value={model}
              onChange={handleModelChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              disabled={disabled || modelsLoading}
            >
              <option value="">
                {modelsLoading ? "Loading models..." : "Default model: llama3.2: 1B"}
              </option>
              {availableModels && availableModels.map(m => (
                <option key={m.key} value={m.key}>{m.displayName}</option>
              ))}
            </select>
            {modelsError && (
              <p className="mt-1 text-sm text-red-600">
                Error loading models: {modelsError}
              </p>
            )}
          </div>
          <div className="mt-2 text-sm text-blue-600 font-semibold">
            Currently selected model: {model || 'llama3.2: 1B'}
          </div>
          {modelInfo.length > 0 && (
            <div className="mt-4 text-sm text-gray-600">
              <h4 className="font-medium">Model Bilgisi:</h4>
              <ul className="list-disc pl-5">
                {modelInfo.map((info, index) => (
                  <li key={index}>{info}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Output Format</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700">Format</label>
            <select
              value={outputFormat}
              onChange={handleOutputFormatChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              disabled={disabled}
            >
              <option value="JSON">JSON</option>
              <option value="XML">XML</option>
            </select>
          </div>
        </div>
      </form>
    </div>
  );
}

EnvironmentSetupForm.propTypes = {
  process: PropTypes.object.isRequired,
  onAIModelUpdate: PropTypes.func,
  onOutputFormatUpdate: PropTypes.func,
  onEnvironmentNameUpdate: PropTypes.func,
  aiModels: PropTypes.object,
  environmentNames: PropTypes.object,
  disabled: PropTypes.bool
}; 