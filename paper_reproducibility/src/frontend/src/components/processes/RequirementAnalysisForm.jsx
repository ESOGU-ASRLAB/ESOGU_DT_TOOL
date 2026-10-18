import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useModels } from '../../hooks/useModels';

// Model açıklamaları (CodeReviewForm.jsx'den alınmıştır)
const modelDescriptions = {
  "codegeex4:9b": [
    "A multilingual code generation model with 9B parameters.",
    "Supports tasks like code completion, commenting, and function calls.",
    "Trained on GLM-4-9B and can handle 128K token context."
  ],
  "codellama:7b": [
    "A code generation model based on Meta's Llama 2 architecture.",
    "Supports various languages like Python, C++, Java, PHP, TypeScript, C#, and Bash.",
    "Capable of code completion, debugging, and natural language descriptions."
  ],
  "deepseek-coder:6.7b": [
    "A 6.7B parameter model optimized for code generation and interpretation.",
    "Provides high-accuracy code generation in various programming languages.",
    "Efficient at code completion and bug-fixing tasks."
  ],
  "gemma2:2b": [
    "A lightweight 2B parameter model for code generation.",
    "Ideal for small projects and low-resource environments.",
    "Supports basic code completion and suggestions."
  ],
  "gemma3:4b": [
    "A 4B parameter model optimized for mid-sized projects.",
    "Can handle more complex code structures.",
    "Balanced performance in code generation and interpretation."
  ],
  "llama3.2:3b": [
    "A 3B parameter model optimized for fast and efficient code generation.",
    "Effective for small and medium-sized code completion tasks.",
    "Provides low-latency responses."
  ],
  "qwen2.5:7b": [
    "A multilingual 7B parameter model for code generation.",
    "Generates high-accuracy code in multiple programming languages.",
    "Efficient at code completion and interpretation."
  ],
  "qwen2.5-coder:3b": [
    "A lightweight 3B parameter model for code generation.",
    "Ideal for small projects and low-resource environments.",
    "Supports basic code completion and suggestions."
  ],
  "stable-code:3b": [
    "A 3B parameter model known for its stable and reliable code generation.",
    "Effective at code completion and bug fixing.",
    "Supports a variety of programming languages."
  ],
  "starcoder2:7b": [
    "A 7B parameter model with advanced code generation and analysis capabilities.",
    "Handles complex code structures and projects well.",
    "Excels in code completion and suggestion tasks."
  ]
};

export default function RequirementAnalysisForm({ process, onAIModelUpdate, aiModels, disabled }) {
  const [model, setModel] = useState(aiModels?.[process?.id] || 'llama3.2: 1B');
  const [modelInfo, setModelInfo] = useState([]);

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
  }, []); // Only run once on mount

  const handleModelChange = (e) => {
    const selectedModel = e.target.value;
    setModel(selectedModel);
    setModelInfo(modelDescriptions[selectedModel] || []);
    if (process && onAIModelUpdate) {
      onAIModelUpdate(process.id, selectedModel);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <form className="space-y-6">
        {/* Model seçimi */}
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
            <h4 className="font-medium">Model Information:</h4>
            <ul className="list-disc pl-5">
              {modelInfo.map((info, index) => (
                <li key={index}>{info}</li>
              ))}
            </ul>
          </div>
        )}
      </form>
    </div>
  );
}

RequirementAnalysisForm.propTypes = {
  process: PropTypes.object.isRequired,
  onAIModelUpdate: PropTypes.func,
  aiModels: PropTypes.object,
  disabled: PropTypes.bool
}; 