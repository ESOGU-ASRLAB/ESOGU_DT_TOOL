import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useModels } from '../../hooks/useModels';

// Custom hook to manage model information
function useModelInfo(selectedModel) {
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
      "Provides high-accuracy code in various programming languages.",
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
    "mistralai/codestral-22b-v0.1": [
      "A 22B parameter model specialized for code generation and analysis.",
      "Excellent performance in complex coding tasks and multi-language support.",
      "Optimized for software development workflows."
    ],
    "qwen/qwq-32b": [
      "A 32B parameter reasoning-focused model for complex problem solving.",
      "Excels in analytical thinking and step-by-step reasoning.",
      "Ideal for complex logic and mathematical computations."
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
    ],
    // New models added for Test Case Optimization
    "codellama:70b-instruct": [
      "A 70B parameter CodeLlama model optimized for instruction-following.",
      "Excellent for complex code analysis and test case optimization.",
      "High-performance model with detailed reasoning capabilities."
    ],
    "kimi-dev:72b": [
      "A large 72B parameter development-focused model.",
      "Specialized for software development and testing workflows.",
      "Advanced reasoning for complex test case analysis."
    ],
    "openai/gpt-oss-120b": [
      "A massive 120B parameter open-source GPT model.",
      "Exceptional performance in complex reasoning and analysis.",
      "Ideal for comprehensive test case optimization and planning."
    ],
    "deepseek-r1-distill:32b": [
      "A 32B parameter distilled model from DeepSeek R1.",
      "Optimized for reasoning and analytical tasks.",
      "Efficient performance in test case analysis and optimization."
    ],
    "google/gemma-3-27b": [
      "Google's 27B parameter Gemma 3 model.",
      "Advanced language understanding and generation capabilities.",
      "Suitable for detailed test case analysis and optimization."
    ],
    "qwen/qwen3-coder-30b": [
      "A 30B parameter Qwen 3 model specialized for coding tasks.",
      "Excellent for code analysis and test case generation.",
      "Advanced understanding of software testing methodologies."
    ],
    "deepseek/deepseek-r1-qwen3-8b": [
      "An 8B parameter DeepSeek R1 model based on Qwen 3.",
      "Optimized for reasoning and code analysis tasks.",
      "Good balance of performance and efficiency for test optimization."
    ]
  };

  // Return model information based on the selected model
  return modelDescriptions[selectedModel] || [];
}

export default function TestPlanningForm({ process, onAIModelUpdate, onOutputFormatUpdate, aiModels, disabled }) {
  const [model, setModel] = useState(aiModels?.[process?.id] || 'llama3.2: 1B');
  const [modelInfo, setModelInfo] = useState([]);
  const [outputFormat, setOutputFormat] = useState('JSON');

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

  // Call onAIModelUpdate when component mounts to set initial model
  useEffect(() => {
    if (process && onAIModelUpdate && !aiModels?.[process?.id]) {
      onAIModelUpdate(process.id, model);
    }
    
    // Set initial output format
    if (process && onOutputFormatUpdate) {
      onOutputFormatUpdate(process.id, outputFormat);
    }
  }, []); // Only run once on mount

  const handleModelChange = (e) => {
    const selectedModel = e.target.value;
    console.log(`[TestPlanningForm] Model changed to: ${selectedModel}`);
    setModel(selectedModel);
    setModelInfo(useModelInfo(selectedModel));
    
    if (process && onAIModelUpdate) {
      onAIModelUpdate(process.id, selectedModel);
    }
  };

  const handleOutputFormatChange = (e) => {
    const selectedFormat = e.target.value;
    setOutputFormat(selectedFormat);
    console.log(`[TestPlanningForm] Output format changed to: ${selectedFormat}`);
    
    if (process && onOutputFormatUpdate) {
      onOutputFormatUpdate(process.id, selectedFormat);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <form className="space-y-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Process Configuration</h2>
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

TestPlanningForm.propTypes = {
  process: PropTypes.object.isRequired,
  onAIModelUpdate: PropTypes.func,
  onOutputFormatUpdate: PropTypes.func,
  aiModels: PropTypes.object,
  disabled: PropTypes.bool
};