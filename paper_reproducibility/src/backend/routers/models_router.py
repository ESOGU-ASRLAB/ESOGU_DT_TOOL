"""
models_router.py
---------------
Merkezi AI model yönetimi için API endpoint'leri.
Tüm süreçlerde kullanılabilir modellerin REST API üzerinden sunulması.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import logging

# Merkezi model konfigürasyonunu import et
from config.models_config import (
    AVAILABLE_MODELS,
    get_models_by_type,
    get_models_by_category,
    get_models_by_performance,
    get_optimization_ready_models,
    get_fast_models,
    get_api_models,
    get_model_by_key,
    get_model_descriptions,
    get_legacy_model_list
)

logger = logging.getLogger(__name__)

# Router oluştur
router = APIRouter(
    prefix="/api/models",
    tags=["models"]
)

@router.get("/")
async def get_all_models(
    model_type: Optional[str] = Query(None, description="Filter by type (local/api)"),
    category: Optional[str] = Query(None, description="Filter by category (code/general/reasoning/etc.)"),
    performance: Optional[str] = Query(None, description="Filter by performance (fast/medium/slow/etc.)"),
    optimization_ready: Optional[bool] = Query(None, description="Filter optimization-ready models"),
    requires_api_key: Optional[bool] = Query(None, description="Filter models that require API key"),
    legacy_format: Optional[bool] = Query(False, description="Return in legacy format for compatibility")
):
    """
    Tüm kullanılabilir AI modellerini getir.
    Çeşitli filtreleme seçenekleri ile modelleri kategorize edebilir.
    """
    try:
        models = AVAILABLE_MODELS.copy()
        
        # Filtreleme işlemleri
        if model_type:
            models = [m for m in models if m["type"] == model_type]
            
        if category:
            models = [m for m in models if m["category"] == category]
            
        if performance:
            models = [m for m in models if m["performance"] == performance]
            
        if optimization_ready is not None:
            models = [m for m in models if m.get("optimization_ready", False) == optimization_ready]
            
        if requires_api_key is not None:
            models = [m for m in models if m.get("requires_api_key", False) == requires_api_key]
        
        # Legacy format dönüşümü
        if legacy_format:
            models = [
                {
                    "key": model["key"],
                    "name": model["name"],
                    "description": model["description"],
                    "type": model["type"],
                    "provider": model.get("provider")
                }
                for model in models
            ]
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Retrieved {len(models)} models successfully",
                "data": models,
                "metadata": {
                    "total_count": len(models),
                    "filtered": any([model_type, category, performance, optimization_ready, requires_api_key]),
                    "legacy_format": legacy_format
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_all_models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_model_categories():
    """
    Mevcut model kategorilerini getir.
    """
    try:
        categories = list(set(model["category"] for model in AVAILABLE_MODELS))
        categories.sort()
        
        # Her kategori için model sayısı
        category_counts = {}
        for category in categories:
            category_counts[category] = len([m for m in AVAILABLE_MODELS if m["category"] == category])
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Model categories retrieved successfully",
                "data": {
                    "categories": categories,
                    "counts": category_counts,
                    "total_categories": len(categories)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_model_categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types")
async def get_model_types():
    """
    Mevcut model tiplerini getir (local/api).
    """
    try:
        types = list(set(model["type"] for model in AVAILABLE_MODELS))
        types.sort()
        
        # Her tip için model sayısı
        type_counts = {}
        for model_type in types:
            type_counts[model_type] = len([m for m in AVAILABLE_MODELS if m["type"] == model_type])
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Model types retrieved successfully",
                "data": {
                    "types": types,
                    "counts": type_counts,
                    "total_types": len(types)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_model_types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-levels")
async def get_performance_levels():
    """
    Mevcut performans seviyelerini getir.
    """
    try:
        performance_levels = list(set(model["performance"] for model in AVAILABLE_MODELS))
        performance_levels.sort()
        
        # Her performans seviyesi için model sayısı
        performance_counts = {}
        for level in performance_levels:
            performance_counts[level] = len([m for m in AVAILABLE_MODELS if m["performance"] == level])
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Performance levels retrieved successfully",
                "data": {
                    "levels": performance_levels,
                    "counts": performance_counts,
                    "total_levels": len(performance_levels)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_performance_levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fast")
async def get_fast_models_endpoint():
    """
    Hızlı modelleri getir (fast ve very-fast performanslı).
    """
    try:
        fast_models = get_fast_models()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Retrieved {len(fast_models)} fast models successfully",
                "data": fast_models
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_fast_models_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimization-ready")
async def get_optimization_models():
    """
    Test Case Optimization için optimize edilmiş modelleri getir.
    """
    try:
        optimization_models = get_optimization_ready_models()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Retrieved {len(optimization_models)} optimization-ready models successfully",
                "data": optimization_models
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_optimization_models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api-models")
async def get_api_models_endpoint():
    """
    API key gerektiren modelleri getir.
    """
    try:
        api_models = get_api_models()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Retrieved {len(api_models)} API models successfully",
                "data": api_models
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_api_models_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_key:path}/descriptions")
async def get_model_descriptions_endpoint(model_key: str):
    """
    Belirli bir model için detaylı açıklamaları getir.
    """
    try:
        from urllib.parse import unquote
        model_key = unquote(model_key)
        descriptions = get_model_descriptions(model_key)
        
        if not descriptions:
            raise HTTPException(
                status_code=404,
                detail=f"No descriptions found for model '{model_key}'"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Descriptions for '{model_key}' retrieved successfully",
                "data": {
                    "model_key": model_key,
                    "descriptions": descriptions,
                    "description_count": len(descriptions)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_model_descriptions_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_model_statistics():
    """
    Model istatistiklerinin özetini getir.
    """
    try:
        total_models = len(AVAILABLE_MODELS)
        
        # Tip bazlı sayılar
        local_count = len([m for m in AVAILABLE_MODELS if m["type"] == "local"])
        api_count = len([m for m in AVAILABLE_MODELS if m["type"] == "api"])
        
        # Kategori bazlı sayılar
        categories = {}
        for model in AVAILABLE_MODELS:
            category = model["category"]
            categories[category] = categories.get(category, 0) + 1
        
        # Performans bazlı sayılar
        performance_stats = {}
        for model in AVAILABLE_MODELS:
            performance = model["performance"]
            performance_stats[performance] = performance_stats.get(performance, 0) + 1
        
        # Özel özellikler
        optimization_ready_count = len([m for m in AVAILABLE_MODELS if m.get("optimization_ready", False)])
        api_key_required_count = len([m for m in AVAILABLE_MODELS if m.get("requires_api_key", False)])
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Model statistics retrieved successfully",
                "data": {
                    "total_models": total_models,
                    "by_type": {
                        "local": local_count,
                        "api": api_count
                    },
                    "by_category": categories,
                    "by_performance": performance_stats,
                    "special_features": {
                        "optimization_ready": optimization_ready_count,
                        "api_key_required": api_key_required_count
                    }
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_model_statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy uyumluluk endpoint'i (mevcut sistemle uyumluluk için)
@router.get("/legacy/available")
async def get_available_models_legacy():
    """
    Mevcut Test Case Optimization endpoint'i ile uyumluluk için.
    Eski format ile model listesi döndürür.
    """
    try:
        legacy_models = get_legacy_model_list()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Available models retrieved successfully (legacy format)",
                "data": legacy_models
            }
        )
        
    except Exception as e:
        logger.error(f"Error in get_available_models_legacy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# NOTE: Path-parametreli route'lar en sona alınmalıdır.
# {model_key:path} her şeyi match edeceğinden sabit route'lar önce tanımlanmıştır.

@router.get("/{model_key:path}")
async def get_model_details(model_key: str):
    """
    Belirli bir model hakkında detaylı bilgi getir.
    """
    try:
        from urllib.parse import unquote
        model_key = unquote(model_key)

        model = get_model_by_key(model_key)

        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Model with key '{model_key}' not found"
            )

        # Model açıklamalarını ekle
        descriptions = get_model_descriptions(model_key)
        model_with_descriptions = model.copy()
        model_with_descriptions["detailed_descriptions"] = descriptions

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Model details for '{model_key}' retrieved successfully",
                "data": model_with_descriptions
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_model_details: {e}")
        raise HTTPException(status_code=500, detail=str(e))