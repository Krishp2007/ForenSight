"""
Memory Profiler — ForenSight AI
===================================
Tracks process Resident Set Size (RSS) memory usage in MB at key application checkpoints.
Does NOT log secrets, user credentials, or evidence contents.
"""

import os
import logging
import tracemalloc

logger = logging.getLogger("memory_profiler")
tracemalloc.start()


def get_process_memory_mb() -> float:
    """Return current process RSS memory usage in MB."""
    # 1. Try psutil if available
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        return round(proc.memory_info().rss / (1024 * 1024), 2)
    except Exception:
        pass

    # 2. Try Linux /proc/self/status for Docker / Render container
    try:
        if os.path.exists("/proc/self/status"):
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        return round(float(parts[1]) / 1024.0, 2)
    except Exception:
        pass

    # 3. Fallback to tracemalloc
    try:
        current, _ = tracemalloc.get_traced_memory()
        return round(current / (1024 * 1024), 2)
    except Exception:
        return 0.0


def log_memory(stage_name: str) -> float:
    """Log current process RSS memory checkpoint."""
    mem_mb = get_process_memory_mb()
    logger.info(f"🧠 [MEMORY] {stage_name:<40} | Process RSS: {mem_mb:.2f} MB")
    return mem_mb
