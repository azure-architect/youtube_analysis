# utils/retry_handler.py
import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Any, Optional
from models.schemas import Error

T = TypeVar('T')

logger = logging.getLogger(__name__)

class RetryHandler:
    """Handles retry logic for API calls and LLM operations"""
    
    @staticmethod
    async def retry_async(
        func: Callable[..., T], 
        max_retries: int = 2, 
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        phase_name: str = "unknown",
        *args, **kwargs
    ) -> tuple[Optional[T], Optional[Error]]:
        """
        Retry an async function with exponential backoff
        
        Returns:
            tuple: (result, error) - if successful, error is None
        """
        error = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} for {phase_name}")
                    
                result = await func(*args, **kwargs)
                return result, None
                
            except Exception as e:
                wait_time = delay * (backoff_factor ** attempt)
                error = Error(
                    phase=phase_name,
                    message=str(e),
                    retry_count=attempt
                )
                
                logger.error(f"Error in {phase_name} (attempt {attempt+1}/{max_retries+1}): {str(e)}")
                
                if attempt < max_retries:
                    logger.info(f"Waiting {wait_time:.2f}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries ({max_retries}) reached for {phase_name}")
                    return None, error
    
    @staticmethod
    def retry_sync(
        func: Callable[..., T], 
        max_retries: int = 2, 
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        phase_name: str = "unknown",
        *args, **kwargs
    ) -> tuple[Optional[T], Optional[Error]]:
        """
        Retry a synchronous function with exponential backoff
        
        Returns:
            tuple: (result, error) - if successful, error is None
        """
        error = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} for {phase_name}")
                    
                result = func(*args, **kwargs)
                return result, None
                
            except Exception as e:
                wait_time = delay * (backoff_factor ** attempt)
                error = Error(
                    phase=phase_name,
                    message=str(e),
                    retry_count=attempt
                )
                
                logger.error(f"Error in {phase_name} (attempt {attempt+1}/{max_retries+1}): {str(e)}")
                
                if attempt < max_retries:
                    logger.info(f"Waiting {wait_time:.2f}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries ({max_retries}) reached for {phase_name}")
                    return None, error

def with_retries(max_retries: int = 2, phase_name: Optional[str] = None):
    """Decorator for adding retry logic to async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = phase_name or func.__name__
            result, error = await RetryHandler.retry_async(
                func, 
                max_retries=max_retries,
                phase_name=func_name,
                *args, **kwargs
            )
            
            if error:
                # Could raise an exception here or just return the error
                return None, error
                
            return result, None
        return wrapper
    return decorator