import ollama
from typing import Dict, Any, Optional, List, Union, Iterator
import time
import logging
import json
import re

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, model: str, max_retries: int = 2, retry_delay: int = 5):
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
    def _reset_token_usage(self):
        """Reset token usage stats"""
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
    def _update_token_usage(self, response: Dict[str, Any]):
        """Update token usage from response"""
        if 'eval_count' in response:
            self.token_usage["prompt_tokens"] = response.get('prompt_eval_count', 0)
            self.token_usage["completion_tokens"] = response.get('eval_count', 0)
            self.token_usage["total_tokens"] = self.token_usage["prompt_tokens"] + self.token_usage["completion_tokens"]
        
    def get_token_usage(self) -> Dict[str, int]:
        """Get current token usage stats"""
        return self.token_usage.copy()
        
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                format: str = "json",
                top_p: float = 0.9,
                top_k: int = 40,
                num_ctx: int = 4096,
                num_predict: int = 128,
                stop: Optional[Union[str, List[str]]] = None) -> Dict[str, Any]:
        """Generate a response using Ollama with retry logic"""
        self._reset_token_usage()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.max_retries + 1):
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    options={
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "num_ctx": num_ctx,
                        "num_predict": num_predict,
                        "stop": stop
                    },
                    format=format
                )
                self._update_token_usage(response)
                return response
            except Exception as e:
                if attempt < self.max_retries:
                    logger.warning(f"Attempt {attempt+1} failed with error: {str(e)}. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All {self.max_retries+1} attempts failed with error: {str(e)}")
                    raise

    def generate_stream(self, 
                      prompt: str, 
                      system_prompt: Optional[str] = None,
                      temperature: float = 0.7,
                      format: Optional[str] = None,
                      top_p: float = 0.9,
                      top_k: int = 40,
                      num_ctx: int = 4096,
                      num_predict: int = 128,
                      stop: Optional[Union[str, List[str]]] = None) -> Iterator[Dict[str, Any]]:
        """Stream response generation from Ollama"""
        self._reset_token_usage()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.max_retries + 1):
            try:
                last_chunk = None
                stream = ollama.chat(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    options={
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "num_ctx": num_ctx,
                        "num_predict": num_predict,
                        "stop": stop
                    },
                    format=format
                )
                for chunk in stream:
                    last_chunk = chunk
                    yield chunk
                
                if last_chunk:
                    self._update_token_usage(last_chunk)
                return
            except Exception as e:
                if attempt < self.max_retries:
                    logger.warning(f"Attempt {attempt+1} failed with error: {str(e)}. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All {self.max_retries+1} attempts failed with error: {str(e)}")
                    raise

    # [Rest of methods with token tracking added similar to above...]
    
    def log_performance(self, duration_ms: float, prompt_length: int):
        """Log performance metrics"""
        tokens_per_second = 0
        if duration_ms > 0:
            tokens_per_second = (self.token_usage["completion_tokens"] / (duration_ms / 1000))
        
        logger.info(
            f"Performance metrics: {tokens_per_second:.2f} tokens/sec, "
            f"prompt: {prompt_length} chars / {self.token_usage['prompt_tokens']} tokens, "
            f"completion: {self.token_usage['completion_tokens']} tokens"
        )
        return {
            "tokens_per_second": tokens_per_second,
            "prompt_chars": prompt_length,
            "prompt_tokens": self.token_usage["prompt_tokens"],
            "completion_tokens": self.token_usage["completion_tokens"],
            "total_tokens": self.token_usage["total_tokens"]
        }