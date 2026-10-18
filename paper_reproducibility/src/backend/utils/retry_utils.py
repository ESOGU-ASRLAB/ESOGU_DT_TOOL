"""
retry_utils.py
--------------
LLM API çağrıları için basit retry mekanizması
"""

import asyncio
import logging
import random
from typing import Callable, Any

logger = logging.getLogger(__name__)

async def retry_llm_call(
    func: Callable, 
    *args, 
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,  # 503 hataları için daha uzun max delay
    **kwargs
) -> Any:
    """
    LLM çağrıları için basit exponential backoff retry - 503 hataları için özel davranış
    
    Args:
        func: Retry yapılacak async fonksiyon
        *args: Fonksiyona geçilecek argümanlar
        max_retries: Maksimum retry sayısı
        base_delay: İlk retry için bekleme süresi (saniye)
        max_delay: Maksimum bekleme süresi (saniye)
        **kwargs: Fonksiyona geçilecek keyword argümanlar
    
    Returns:
        Fonksiyonun return değeri
    
    Raises:
        Son denemede aldığı hata
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 0:
                logger.info(f"✅ LLM call succeeded after {attempt} retries")
            return result
            
        except Exception as e:
            last_exception = e
            error_str = str(e)
            
            # Son deneme ise hata fırlat
            if attempt == max_retries:
                logger.error(f"❌ LLM call failed after {max_retries} retries: {error_str}")
                raise e
            
            # Retry yapılabilir hata mı kontrol et
            if not _is_retryable_error(error_str):
                logger.warning(f"⚠️  Non-retryable error, stopping retries: {error_str}")
                raise e
            
            # 503 hatası için özel bekleme süreleri
            if "503" in error_str or "service unavailable" in error_str.lower() or "unavailable" in error_str.lower():
                # 503 hataları için sabit 30s + rastgele 2-30s bekleme
                base_wait = 30
                random_wait = random.uniform(2, 30)
                delay = base_wait + random_wait
                
                logger.warning(f"🔴 503 Service Unavailable detected on attempt {attempt + 1}/{max_retries + 1}")
                logger.info(f"⏳ Applying 503-specific wait: {base_wait}s + {random_wait:.2f}s = {delay:.2f}s")
            
            # 500 Internal Error için de özel bekleme
            elif "500" in error_str and "internal" in error_str.lower():
                # 500 hataları için sabit 20s + rastgele 2-20s bekleme
                base_wait = 20
                random_wait = random.uniform(2, 20)
                delay = base_wait + random_wait
                
                logger.warning(f"🔴 500 Internal Error detected on attempt {attempt + 1}/{max_retries + 1}")
                logger.info(f"⏳ Applying 500-specific wait: {base_wait}s + {random_wait:.2f}s = {delay:.2f}s")
            
            else:
                # Diğer hatalar için normal exponential backoff
                delay = min(
                    base_delay * (2 ** attempt) + random.uniform(0, 0.5), 
                    max_delay
                )
                logger.warning(f"🔄 LLM call attempt {attempt + 1}/{max_retries + 1} failed: {error_str}")
                logger.info(f"⏱️  Standard retry wait: {delay:.2f} seconds...")
            
            await asyncio.sleep(delay)
    
    # Bu noktaya gelmemeli ama güvenlik için
    if last_exception:
        raise last_exception
    raise Exception("Unexpected error in retry mechanism")

def _is_retryable_error(error_str: str) -> bool:
    """
    Hatanın retry yapılabilir olup olmadığını kontrol eder
    """
    error_lower = error_str.lower()
    
    # HTTP hata kodları (geçici hatalar)
    retryable_codes = ["503", "502", "504", "429", "408", "500"]  # 500 Internal Error de retry edilebilir
    for code in retryable_codes:
        if code in error_str:
            return True
    
    # API-specific hatalar
    retryable_patterns = [
        "service unavailable",
        "temporarily unavailable", 
        "unavailable",  # Gemini "unavailable" hataları için
        "resource_exhausted",
        "quota exceeded",
        "rate limit",
        "timeout",
        "connection",
        "network",
        "internal server error",
        "internal error",  # Google API internal error için
        "bad gateway",
        "gateway timeout",
        "overloaded"  # Google servers overloaded için
    ]
    
    return any(pattern in error_lower for pattern in retryable_patterns)
