# performance_profiler.py
# Performance profiling and monitoring for PromptForge system

import time
import psutil
import logging
from typing import Dict, Any, List
from functools import wraps
import tracemalloc

logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """
    Performance profiler for monitoring system performance
    """
    
    def __init__(self):
        self.profiler_stats = {}
        self.memory_snapshots = []
        
    def profile_function(self, func_name: str):
        """
        Decorator for profiling function performance
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Start timing
                start_time = time.time()
                
                # Start memory tracking
                tracemalloc.start()
                
                # Execute function
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    # Stop timing
                    end_time = time.time()
                    execution_time = end_time - start_time
                    
                    # Get memory usage
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    
                    # Store statistics
                    if func_name not in self.profiler_stats:
                        self.profiler_stats[func_name] = {
                            "execution_times": [],
                            "memory_usage": [],
                            "peak_memory": []
                        }
                    
                    self.profiler_stats[func_name]["execution_times"].append(execution_time)
                    self.profiler_stats[func_name]["memory_usage"].append(current)
                    self.profiler_stats[func_name]["peak_memory"].append(peak)
                    
                    logger.info(
                        f"[profiler] {func_name} - Time: {execution_time:.3f}s, "
                        f"Memory: {current/1024:.1f}KB, Peak: {peak/1024:.1f}KB"
                    )
                    
            return wrapper
        return decorator
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        """
        report = {}
        
        for func_name, stats in self.profiler_stats.items():
            if stats["execution_times"]:
                avg_time = sum(stats["execution_times"]) / len(stats["execution_times"])
                max_time = max(stats["execution_times"])
                min_time = min(stats["execution_times"])
                avg_memory = sum(stats["memory_usage"]) / len(stats["memory_usage"])
                peak_memory = max(stats["peak_memory"])
                
                report[func_name] = {
                    "average_time": round(avg_time, 4),
                    "max_time": round(max_time, 4),
                    "min_time": round(min_time, 4),
                    "average_memory_kb": round(avg_memory/1024, 2),
                    "peak_memory_kb": round(peak_memory/1024, 2),
                    "call_count": len(stats["execution_times"])
                }
        
        return report
    
    def monitor_system_resources(self) -> Dict[str, Any]:
        """
        Monitor system resources
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round((disk.used / disk.total) * 100, 2)
        }
    
    def reset_profiler(self):
        """
        Reset profiler statistics
        """
        self.profiler_stats.clear()
        self.memory_snapshots.clear()

# Global profiler instance
profiler = PerformanceProfiler()

# Performance monitoring decorators for key system functions
@profiler.profile_function("core_memory_extraction")
def profiled_extract_core_memories(user_id: str, session_result: Dict[str, Any], session_id: str):
    """
    Profiled version of core memory extraction
    """
    from memory.core_memory_extractor import extract_and_store_core_memories
    return extract_and_store_core_memories(user_id, session_result, session_id)

@profiler.profile_function("feedback_generation")
def profiled_generate_feedback(orchestrator_decision: Dict[str, Any], session_result: Dict[str, Any] = None):
    """
    Profiled version of feedback generation
    """
    from agents.enhanced_feedback import generate_processing_feedback
    return generate_processing_feedback(orchestrator_decision, session_result)

@profiler.profile_function("session_finalization")
def profiled_finalize_conversation(final_result: Dict[str, Any]):
    """
    Profiled version of conversation finalization
    """
    from agents.enhanced_feedback import finalize_conversation
    return finalize_conversation(final_result)

# Export for use in other modules
__all__ = [
    "PerformanceProfiler",
    "profiler",
    "profiled_extract_core_memories",
    "profiled_generate_feedback",
    "profiled_finalize_conversation"
]
