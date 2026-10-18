import React from 'react';
import { SparklesIcon } from '@heroicons/react/24/outline';

/**
 * Global AI Configuration — minimal, single-model selector for the pipeline.
 * The chosen model is applied to every pipeline step automatically.
 *
 * Props:
 *   selectedModel   {string}   controlled model id
 *   onModelChange   {fn}       called with new model id on change
 */
export default function GlobalAIConfig({ selectedModel = 'qwen2.5-7b-instruct-1m', onModelChange }) {
  const availableModels = [
    // API Models (External)
    { id: 'gemini-2.5-flash',              name: 'Gemini 2.5 Flash',         provider: 'Google',    type: 'api' },
    { id: 'gemini-2.5-pro',                name: 'Gemini 2.5 Pro',           provider: 'Google',    type: 'api' },
    { id: 'gemini-1.5-pro',                name: 'Gemini 1.5 Pro',           provider: 'Google',    type: 'api' },
    { id: 'gemini-1.5-flash',              name: 'Gemini 1.5 Flash',         provider: 'Google',    type: 'api' },
    // Local Models (LM Studio)
    { id: 'codegeex4:9b',                  name: 'CodeGeeX4 (9B)',           provider: 'LM Studio', type: 'local' },
    { id: 'codellama:7b',                  name: 'Code Llama (7B)',          provider: 'LM Studio', type: 'local' },
    { id: 'deepseek-coder:6.7b',           name: 'DeepSeek Coder (6.7B)',   provider: 'LM Studio', type: 'local' },
    { id: 'gemma2:2b',                     name: 'Gemma 2 (2B)',             provider: 'LM Studio', type: 'local' },
    { id: 'gemma3:4b',                     name: 'Gemma 3 (4B)',             provider: 'LM Studio', type: 'local' },
    { id: 'google/gemma-3-12b',            name: 'Gemma 3 (12B)',           provider: 'LM Studio', type: 'local' },
    { id: 'llama3.2:3b',                   name: 'Llama 3.2 (3B)',          provider: 'LM Studio', type: 'local' },
    { id: 'qwen2.5:7b',                    name: 'Qwen 2.5 (7B)',           provider: 'LM Studio', type: 'local' },
    { id: 'qwen2.5-7b-instruct-1m',                 name: 'Qwen 2.5 (7B-1M)',        provider: 'LM Studio', type: 'local' },
    { id: 'qwen2.5-coder:3b',              name: 'Qwen 2.5 Coder (3B)',     provider: 'LM Studio', type: 'local' },
    { id: 'qwen/qwen3-14b',                name: 'Qwen 3 (14B)',            provider: 'LM Studio', type: 'local' },
    { id: 'stable-code:3b',                name: 'Stable Code (3B)',         provider: 'LM Studio', type: 'local' },
    { id: 'starcoder2:7b',                 name: 'StarCoder 2 (7B)',         provider: 'LM Studio', type: 'local' },
    { id: 'meta/llama-3.3-70b',            name: 'Llama 3.3 (70B)',         provider: 'LM Studio', type: 'local' },
    { id: 'mistralai/codestral-22b-v0.1',  name: 'Codestral (22B)',          provider: 'LM Studio', type: 'local' },
    { id: 'openai/gpt-oss-20b',            name: 'GPT OSS (20B)',            provider: 'LM Studio', type: 'local' },
    { id: 'qwen/qwq-32b',                  name: 'QwQ (32B)',                provider: 'LM Studio', type: 'local' },
    { id: 'codellama:70b-instruct',        name: 'CodeLlama 70B Instruct',  provider: 'LM Studio', type: 'local' },
    { id: 'kimi-dev:72b',                  name: 'Kimi Dev 72B',             provider: 'LM Studio', type: 'local' },
    { id: 'openai/gpt-oss-120b',           name: 'GPT OSS 120B',             provider: 'LM Studio', type: 'local' },
    { id: 'deepseek-r1-distill:32b',       name: 'DeepSeek R1 Distill 32B', provider: 'LM Studio', type: 'local' },
    { id: 'google/gemma-3-27b',            name: 'Google Gemma 3 27B',      provider: 'LM Studio', type: 'local' },
    { id: 'qwen/qwen3-coder-30b',          name: 'Qwen 3 Coder 30B',        provider: 'LM Studio', type: 'local' },
    { id: 'deepseek/deepseek-r1-qwen3-8b', name: 'DeepSeek R1 Qwen3 8B',   provider: 'LM Studio', type: 'local' },
  ];

  const selected = availableModels.find(m => m.id === selectedModel);
  const isLocal   = selected?.type === 'local';

  return (
    <div className="border rounded-lg bg-white shadow-sm">
      <div className="px-4 py-3 bg-gradient-to-r from-purple-50 to-pink-50 border-b border-purple-100 flex items-center space-x-3 rounded-t-lg">
        <SparklesIcon className="h-5 w-5 text-purple-600 flex-shrink-0" />
        <div>
          <h3 className="font-semibold text-gray-900 text-sm">AI Model</h3>
          <p className="text-xs text-gray-500">Applied to every pipeline step</p>
        </div>
      </div>

      <div className="px-4 py-3 flex items-center gap-3">
        <select
          value={selectedModel}
          onChange={e => onModelChange?.(e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <optgroup label="API Models (External)">
            {availableModels.filter(m => m.type === 'api').map(model => (
              <option key={model.id} value={model.id}>{model.name} ({model.provider})</option>
            ))}
          </optgroup>
          <optgroup label="Local Models (LM Studio)">
            {availableModels.filter(m => m.type === 'local').map(model => (
              <option key={model.id} value={model.id}>{model.name}</option>
            ))}
          </optgroup>
        </select>

        <span className={`text-xs font-medium px-2 py-1 rounded-full flex-shrink-0 ${
          isLocal
            ? 'bg-green-100 text-green-700'
            : 'bg-blue-100 text-blue-700'
        }`}>
          {isLocal ? 'Local' : 'API'}
        </span>
      </div>
    </div>
  );
}
