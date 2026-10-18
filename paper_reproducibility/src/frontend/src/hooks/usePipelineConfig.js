import { useState, useCallback, useEffect } from 'react';

// All 11 pipeline steps — always active
const ALL_PIPELINE_STEPS = [
  'code-review',
  'requirement-analysis',
  'test-planning',
  'environment-setup',
  'test-scenario-generation',
  'test-case-generation',
  'test-case-optimization',
  'test-code-generation',
  'test-execution',
  'test-reporting',
  'test-closure',
];

/**
 * Default configuration for a pipeline step.
 * Provides sensible defaults so the pipeline can start without manual config.
 */
function defaultStepConfig(processId) {
  return {
    aiModel: 'qwen2.5-7b-instruct-1m',
    model: 'qwen2.5-7b-instruct-1m',
    temperature: 0.7,
    topP: 0.9,
    maxTokens: 4096,
    usingGlobalAI: false,
    isConfigured: true,
    configuredAt: new Date().toISOString(),
    // Step-specific defaults
    ...(processId === 'environment-setup' ? { environment_name: 'Default Environment' } : {}),
    ...(processId === 'test-scenario-generation' ? { test_type: 'Functional Testing', test_category: 'Functional' } : {}),
    ...(processId === 'test-case-optimization' ? { optimization_type: 'individual' } : {}),
    ...(processId === 'test-code-generation' ? { output_format: 'json' } : {}),
    ...(processId === 'test-execution' ? { execution_mode: 'standard' } : {}),
    ...(processId === 'test-reporting' ? { analysis_depth: 'detailed' } : {}),
  };
}

/**
 * Pipeline Configuration Hook
 * 
 * Her process için yapılan ayarlamaları yönetir.
 * Backend API'larla tam uyumlu config formatı sağlar.
 * 
 * Tüm 11 adım otomatik olarak varsayılan konfig ile başlatılır;
 * kullanıcı sadece özelleştirmek istediği adımları değiştirir.
 */
export function usePipelineConfig() {
  // Her process için yapılandırma durumu — tüm adımlar default config ile başlar
  const [pipelineConfigs, setPipelineConfigs] = useState(() => {
    const initial = {};
    ALL_PIPELINE_STEPS.forEach(id => {
      initial[id] = defaultStepConfig(id);
    });
    return initial;
  });
  
  // Global AI configuration state
  const [globalAIConfig, setGlobalAIConfig] = useState(null);
  
  /**
   * Global AI configuration'ı kaydet
   * @param {object} config - Global AI config (aiModel, temperature, topP, maxTokens)
   */
  const saveGlobalAIConfig = useCallback((config) => {
    setGlobalAIConfig(config);
    console.log('[usePipelineConfig] Global AI config saved:', config);
  }, []);
  
  /**
   * Global AI configuration'ı tüm seçili process'lere uygula
   * @param {Set} selectedProcesses - Seçili process ID'leri
   * @param {object} config - Global AI config
   */
  const applyGlobalAIToAll = useCallback((selectedProcesses, config) => {
    const processArray = Array.from(selectedProcesses);
    
    setPipelineConfigs(prev => {
      const updated = { ...prev };
      
      processArray.forEach(processId => {
        updated[processId] = {
          ...(updated[processId] || {}),
          aiModel: config.aiModel,
          temperature: config.temperature,
          topP: config.topP,
          maxTokens: config.maxTokens,
          usingGlobalAI: true,
          isConfigured: updated[processId]?.isConfigured || false
        };
      });
      
      return updated;
    });
    
    saveGlobalAIConfig(config);
    console.log(`[usePipelineConfig] Global AI config applied to ${processArray.length} processes`);
  }, [saveGlobalAIConfig]);
  
  /**
   * Bir process'in global AI kullanıp kullanmadığını kontrol et
   * @param {string} processId - Process ID
   * @returns {boolean} Global AI kullanıyor mu?
   */
  const isUsingGlobalAI = useCallback((processId) => {
    return pipelineConfigs[processId]?.usingGlobalAI === true;
  }, [pipelineConfigs]);
  
  /**
   * Bir process için konfigürasyonu kaydet
   * @param {string} processId - Process ID (örn: 'test-scenario-generation')
   * @param {object} config - Process configuration
   */
  const saveProcessConfig = useCallback((processId, config) => {
    setPipelineConfigs(prev => ({
      ...prev,
      [processId]: {
        ...config,
        isConfigured: true,
        configuredAt: new Date().toISOString(),
        // Eğer kullanıcı manuel AI ayarları yaptıysa, global AI bayrağını kaldır
        usingGlobalAI: config.aiModel ? false : (prev[processId]?.usingGlobalAI || false)
      }
    }));
    console.log(`[usePipelineConfig] Configuration saved for ${processId}:`, config);
  }, []);
  
  /**
   * Bir process'in konfigürasyonunu al
   * @param {string} processId - Process ID
   * @returns {object|null} Process configuration veya null
   */
  const getProcessConfig = useCallback((processId) => {
    return pipelineConfigs[processId] || null;
  }, [pipelineConfigs]);
  
  /**
   * Bir process'in configure edilip edilmediğini kontrol et
   * @param {string} processId - Process ID
   * @returns {boolean} Configure edilmiş mi?
   */
  const isProcessConfigured = useCallback((processId) => {
    return pipelineConfigs[processId]?.isConfigured === true;
  }, [pipelineConfigs]);
  
  /**
   * Bir process'in konfigürasyonunu sil
   * @param {string} processId - Process ID
   */
  const clearProcessConfig = useCallback((processId) => {
    setPipelineConfigs(prev => {
      const newConfigs = { ...prev };
      delete newConfigs[processId];
      return newConfigs;
    });
    console.log(`[usePipelineConfig] Configuration cleared for ${processId}`);
  }, []);
  
  /**
   * Tüm konfigürasyonları temizle
   */
  const clearAllConfigs = useCallback(() => {
    setPipelineConfigs({});
    console.log('[usePipelineConfig] All configurations cleared');
  }, []);
  
  /**
   * Pipeline'da seçili olan tüm process'lerin configure durumunu kontrol et
   * @param {Set} selectedProcesses - Seçili process ID'leri
   * @returns {object} { allConfigured: boolean, missingConfigs: string[] }
   */
  const validatePipelineConfigs = useCallback((selectedProcesses) => {
    const processArray = Array.from(selectedProcesses);
    const missingConfigs = processArray.filter(processId => !isProcessConfigured(processId));
    
    return {
      allConfigured: missingConfigs.length === 0,
      missingConfigs,
      configuredCount: processArray.length - missingConfigs.length,
      totalCount: processArray.length
    };
  }, [isProcessConfigured]);
  
  /**
   * Process konfigürasyonunu backend API formatına dönüştür
   * @param {string} processId - Process ID
   * @returns {object|null} Backend'e gönderilecek config veya null
   */
  const getBackendConfig = useCallback((processId) => {
    const config = pipelineConfigs[processId];
    if (!config) return null;
    
    // Backend API'larla uyumlu format
    // Her process'in kendi API formatına göre dönüştürme yapılabilir
    const backendConfig = {
      ...config,
      processId,
      // Backend'e gönderilmeyecek frontend-only alanları kaldır
      isConfigured: undefined,
      configuredAt: undefined
    };
    
    // Undefined alanları temizle
    Object.keys(backendConfig).forEach(key => {
      if (backendConfig[key] === undefined) {
        delete backendConfig[key];
      }
    });
    
    return backendConfig;
  }, [pipelineConfigs]);
  
  return {
    pipelineConfigs,
    globalAIConfig,
    saveProcessConfig,
    getProcessConfig,
    isProcessConfigured,
    clearProcessConfig,
    clearAllConfigs,
    validatePipelineConfigs,
    getBackendConfig,
    saveGlobalAIConfig,
    applyGlobalAIToAll,
    isUsingGlobalAI
  };
}
