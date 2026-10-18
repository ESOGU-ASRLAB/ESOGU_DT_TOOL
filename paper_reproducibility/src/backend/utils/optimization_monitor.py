"""
optimization_monitor.py
-----------------------
Test Case Optimization süreçlerini basit izleme
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class OptimizationMonitor:
    """Test Case Optimization süreçlerini izler"""
    
    def __init__(self):
        self.comparison_stats = {
            "total_comparisons": 0,
            "successful_comparisons": 0,
            "failed_comparisons": 0,
            "retry_comparisons": 0
        }
        self.error_counts = defaultdict(int)
        self.session_logs = []
        
    def log_comparison_attempt(
        self, 
        case1_id: str, 
        case2_id: str, 
        success: bool, 
        attempt_number: int = 1,
        error_message: Optional[str] = None,
        model_used: str = "unknown"
    ):
        """Karşılaştırma denemesini logla"""
        
        self.comparison_stats["total_comparisons"] += 1
        
        if success:
            self.comparison_stats["successful_comparisons"] += 1
            if attempt_number > 1:
                self.comparison_stats["retry_comparisons"] += 1
                logger.info(f"Comparison succeeded after {attempt_number} attempts: {case1_id} vs {case2_id}")
        else:
            self.comparison_stats["failed_comparisons"] += 1
            if error_message:
                error_type = self._categorize_error(error_message)
                self.error_counts[error_type] += 1
                logger.warning(f"Comparison failed: {case1_id} vs {case2_id} - {error_type}")
        
        # Session log ekle
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "case1_id": case1_id,
            "case2_id": case2_id,
            "success": success,
            "attempt_number": attempt_number,
            "error_message": error_message,
            "model_used": model_used
        }
        self.session_logs.append(log_entry)
    
    def _categorize_error(self, error_message: str) -> str:
        """Hata mesajını kategorize et"""
        error_lower = error_message.lower()
        
        if "503" in error_message or "service unavailable" in error_lower:
            return "service_unavailable"
        elif "429" in error_message or "rate limit" in error_lower:
            return "rate_limit"
        elif "timeout" in error_lower:
            return "timeout"
        elif "connection" in error_lower or "network" in error_lower:
            return "connection_error"
        elif "json" in error_lower or "parse" in error_lower:
            return "parsing_error"
        else:
            return "other_error"
    
    def get_success_rate(self) -> float:
        """Başarı oranını döndür"""
        if self.comparison_stats["total_comparisons"] == 0:
            return 100.0
        return (self.comparison_stats["successful_comparisons"] / self.comparison_stats["total_comparisons"]) * 100
    
    def get_stats_summary(self) -> Dict:
        """İstatistik özetini döndür"""
        return {
            "comparison_stats": self.comparison_stats.copy(),
            "success_rate": self.get_success_rate(),
            "error_counts": dict(self.error_counts),
            "total_errors": sum(self.error_counts.values()),
            "most_common_error": max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None
        }
    
    def should_continue(self, max_failure_rate: float = 0.7) -> bool:
        """İşlemin devam etmesi gerekip gerekmediğini kontrol et"""
        if self.comparison_stats["total_comparisons"] < 5:  # En az 5 deneme olsun
            return True
        
        failure_rate = 1.0 - (self.get_success_rate() / 100.0)
        return failure_rate <= max_failure_rate
    
    def log_session_summary(self, session_type: str = "individual"):
        """Session özetini logla"""
        summary = self.get_stats_summary()
        
        logger.info(f"Optimization Session Summary ({session_type}):")
        logger.info(f"  Total Comparisons: {summary['comparison_stats']['total_comparisons']}")
        logger.info(f"  Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"  Successful: {summary['comparison_stats']['successful_comparisons']}")
        logger.info(f"  Failed: {summary['comparison_stats']['failed_comparisons']}")
        logger.info(f"  Retries: {summary['comparison_stats']['retry_comparisons']}")
        
        if summary['error_counts']:
            logger.info(f"  Error Distribution: {summary['error_counts']}")
        
        if summary['most_common_error']:
            logger.info(f"  Most Common Error: {summary['most_common_error']}")
    
    def reset_stats(self):
        """İstatistikleri sıfırla"""
        self.comparison_stats = {
            "total_comparisons": 0,
            "successful_comparisons": 0,
            "failed_comparisons": 0,
            "retry_comparisons": 0
        }
        self.error_counts.clear()
        self.session_logs.clear()

# Global monitor instance
optimization_monitor = OptimizationMonitor()
