"""
models_config.py
---------------
Merkezi AI model konfigürasyonu. Tüm süreçlerde kullanılabilir modellerin
tek bir yerden yönetilmesi için oluşturulmuştur.
"""

from typing import List, Dict, Any

# Tüm kullanılabilir AI modelleri - Tek kaynak
AVAILABLE_MODELS: List[Dict[str, Any]] = [
    # =====================================================
    # LOCAL LM STUDIO MODELS (Temel Modeller)
    # =====================================================
    {
        "key": "codegeex4:9b",
        "name": "CodeGeeX4 (9B)",
        "description": "Code generation optimized model with 9B parameters",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "9B",
        "category": "code",
        "performance": "fast"
    },
    {
        "key": "codellama:7b",
        "name": "Code Llama (7B)",
        "description": "Meta's code-focused model based on Llama 2 architecture",
        "type": "local",
        "provider": "LM Studio", 
        "parameters": "7B",
        "category": "code",
        "performance": "fast"
    },
    {
        "key": "deepseek-coder:6.7b",
        "name": "DeepSeek Coder (6.7B)",
        "description": "DeepSeek's coding model optimized for code generation",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "6.7B", 
        "category": "code",
        "performance": "fast"
    },
    {
        "key": "gemma2:2b",
        "name": "Gemma 2 (2B)",
        "description": "Google's lightweight model for efficient processing",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "2B",
        "category": "general",
        "performance": "very-fast"
    },
    {
        "key": "gemma3:4b",
        "name": "Gemma 3 (4B)",
        "description": "Google's enhanced model with improved capabilities",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "4B",
        "category": "general", 
        "performance": "fast"
    },
    {
        "key": "google/gemma-3-12b",
        "name": "Gemma 3 (12B)",
        "description": "Google's large Gemma model for complex tasks",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "12B",
        "category": "general",
        "performance": "medium"
    },
    {
        "key": "llama3.2:3b",
        "name": "Llama 3.2 (3B)",
        "description": "Meta's latest efficient model optimized for fast responses",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "3B",
        "category": "general",
        "performance": "fast"
    },
    {
        "key": "qwen2.5:7b",
        "name": "Qwen 2.5 (7B)",
        "description": "Alibaba's advanced multilingual model",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "7B",
        "category": "multilingual",
        "performance": "fast"
    },
    {
        "key": "qwen2.5-7b-instruct-1m",
        "name": "Qwen 2.5 (7B-1M)",
        "description": "Large context version for processing extensive content",
        "type": "local",
        "provider": "LM Studio", 
        "parameters": "7B",
        "category": "multilingual",
        "performance": "medium"
    },
    {
        "key": "qwen2.5-coder:3b",
        "name": "Qwen 2.5 Coder (3B)",
        "description": "Coding-focused Qwen model for lightweight development tasks",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "3B",
        "category": "code",
        "performance": "fast"
    },
    {
        "key": "qwen/qwen3-14b",
        "name": "Qwen 3 (14B)",
        "description": "Alibaba's latest large model with enhanced reasoning",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "14B", 
        "category": "multilingual",
        "performance": "medium"
    },
    {
        "key": "stable-code:3b",
        "name": "Stable Code (3B)",
        "description": "Stability AI's code model for reliable generation",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "3B",
        "category": "code",
        "performance": "fast"
    },
    {
        "key": "starcoder2:7b",
        "name": "StarCoder 2 (7B)",
        "description": "BigCode's enhanced model for advanced code tasks",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "7B",
        "category": "code",
        "performance": "fast"
    },

    # =====================================================
    # LARGE SCALE MODELS (Test Case Optimization için)
    # =====================================================
    {
        "key": "meta/llama-3.3-70b",
        "name": "Llama 3.3 (70B)",
        "description": "Meta's latest large language model with 70B parameters",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "70B",
        "category": "general",
        "performance": "slow"
    },
    {
        "key": "mistralai/codestral-22b-v0.1", 
        "name": "Codestral (22B)",
        "description": "Mistral AI's code-specialized model for complex analysis",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "22B",
        "category": "code",
        "performance": "medium"
    },
    {
        "key": "openai/gpt-oss-20b",
        "name": "GPT OSS (20B)",
        "description": "OpenAI's open source large model for complex reasoning",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "20B",
        "category": "general",
        "performance": "medium"
    },
    {
        "key": "qwen/qwq-32b",
        "name": "QwQ (32B)",
        "description": "Qwen's reasoning-focused large model for problem solving",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "32B",
        "category": "reasoning",
        "performance": "slow"
    },

    # =====================================================
    # ADVANCED OPTIMIZATION MODELS (Yeni Eklenenler)
    # =====================================================
    {
        "key": "codellama:70b-instruct",
        "name": "CodeLlama 70B Instruct",
        "description": "Large instruction-following model for complex code analysis",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "70B",
        "category": "code",
        "performance": "slow",
        "optimization_ready": True
    },
    {
        "key": "kimi-dev:72b",
        "name": "Kimi Dev 72B", 
        "description": "Development-focused model with 72B parameters",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "72B",
        "category": "development",
        "performance": "slow",
        "optimization_ready": True
    },
    {
        "key": "openai/gpt-oss-120b",
        "name": "GPT OSS 120B",
        "description": "Massive open-source model for complex reasoning tasks",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "120B",
        "category": "general", 
        "performance": "very-slow",
        "optimization_ready": True
    },
    {
        "key": "deepseek-r1-distill:32b",
        "name": "DeepSeek R1 Distill 32B",
        "description": "Distilled reasoning model for analytical tasks",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "32B",
        "category": "reasoning",
        "performance": "slow",
        "optimization_ready": True
    },
    {
        "key": "google/gemma-3-27b",
        "name": "Google Gemma 3 27B",
        "description": "Large Gemma model for detailed analysis (may be slow)",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "27B",
        "category": "general",
        "performance": "slow",
        "optimization_ready": True,
        "note": "May require performance optimization"
    },
    {
        "key": "qwen/qwen3-coder-30b",
        "name": "Qwen 3 Coder 30B",
        "description": "Advanced coding model with 30B parameters (may be slow)",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "30B",
        "category": "code",
        "performance": "slow",
        "optimization_ready": True,
        "note": "May require performance optimization"
    },
    {
        "key": "deepseek/deepseek-r1-qwen3-8b",
        "name": "DeepSeek R1 Qwen3 8B",
        "description": "Reasoning-optimized model based on Qwen 3",
        "type": "local",
        "provider": "LM Studio",
        "parameters": "8B",
        "category": "reasoning",
        "performance": "medium",
        "optimization_ready": True
    },

    # =====================================================
    # EXTERNAL API MODELS
    # =====================================================
    {
        "key": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "description": "Google's latest fast model for quick responses",
        "type": "api",
        "provider": "Google",
        "parameters": "Unknown",
        "category": "general",
        "performance": "very-fast",
        "requires_api_key": True
    },
    {
        "key": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "description": "Google's latest pro model for complex tasks",
        "type": "api",
        "provider": "Google",
        "parameters": "Unknown",
        "category": "general", 
        "performance": "medium",
        "requires_api_key": True
    },
    {
        "key": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro",
        "description": "Google's pro model for professional use",
        "type": "api",
        "provider": "Google",
        "parameters": "Unknown",
        "category": "general",
        "performance": "medium", 
        "requires_api_key": True
    },
    {
        "key": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash",
        "description": "Google's fast model for quick processing",
        "type": "api",
        "provider": "Google",
        "parameters": "Unknown",
        "category": "general",
        "performance": "fast",
        "requires_api_key": True
    }
]

# Model kategorilerine göre filtreleme fonksiyonları
def get_models_by_type(model_type: str) -> List[Dict[str, Any]]:
    """Model tipine göre modelleri filtrele (local/api)"""
    return [model for model in AVAILABLE_MODELS if model["type"] == model_type]

def get_models_by_category(category: str) -> List[Dict[str, Any]]:
    """Kategoriye göre modelleri filtrele (code/general/reasoning/etc.)"""
    return [model for model in AVAILABLE_MODELS if model["category"] == category]

def get_models_by_performance(performance: str) -> List[Dict[str, Any]]:
    """Performans seviyesine göre modelleri filtrele"""
    return [model for model in AVAILABLE_MODELS if model["performance"] == performance]

def get_optimization_ready_models() -> List[Dict[str, Any]]:
    """Test Case Optimization için optimize edilmiş modelleri getir"""
    return [model for model in AVAILABLE_MODELS if model.get("optimization_ready", False)]

def get_fast_models() -> List[Dict[str, Any]]:
    """Hızlı modelleri getir (fast ve very-fast)"""
    return [model for model in AVAILABLE_MODELS if model["performance"] in ["fast", "very-fast"]]

def get_api_models() -> List[Dict[str, Any]]:
    """API gerektiren modelleri getir"""
    return [model for model in AVAILABLE_MODELS if model.get("requires_api_key", False)]

def get_model_by_key(model_key: str) -> Dict[str, Any]:
    """Model anahtarına göre model bilgilerini getir"""
    for model in AVAILABLE_MODELS:
        if model["key"] == model_key:
            return model
    return None

# Model açıklamaları ve detayları
MODEL_DESCRIPTIONS = {
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
    "qwen2.5-7b-instruct-1m": [
        "A high-capacity 7B parameter model optimized for processing large content (1M+ tokens).",
        "Auto-selected when file contents exceed 100,000 tokens.",
        "Ideal for analyzing very large documents and codebases."
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
}

def get_model_descriptions(model_key: str) -> List[str]:
    """Model anahtarına göre açıklamaları getir"""
    return MODEL_DESCRIPTIONS.get(model_key, [])

# Uyumluluk için eski format
def get_legacy_model_list() -> List[Dict[str, str]]:
    """Eski API uyumluluğu için basitleştirilmiş model listesi - provider field'ı ile"""
    return [
        {
            "key": model["key"],
            "name": model["name"], 
            "description": model["description"],
            "type": model["type"],
            "provider": model.get("provider", "Unknown")  # Provider field'ı ekle
        }
        for model in AVAILABLE_MODELS
    ]