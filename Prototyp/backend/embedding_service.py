import os
import requests
import time
import numpy as np
from typing import List, Optional, Union
from abc import ABC, abstractmethod
from dotenv import load_dotenv

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    print("✅ SentenceTransformers successfully loaded - using LOCAL embeddings")
except ImportError as e:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    print(f"⚠️ SentenceTransformers NOT available: {e}")
    print("🔄 Will fall back to ONLINE embeddings")

class EmbeddingServiceBase(ABC):
    """Abstract base class for embedding services"""
    
    @abstractmethod
    def encode(self, texts: Union[str, List[str]], convert_to_numpy: bool = True) -> np.ndarray:
        """Encode texts to embeddings"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of embeddings"""
        pass

class LocalEmbeddingService(EmbeddingServiceBase):
    """Local embedding service using SentenceTransformer"""
    
    def __init__(self, model_name: str, device: str = "cpu"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers ist nicht verfügbar. Bitte installieren Sie es oder verwenden Sie Online-Embeddings in der .env.")
        
        print(f"🔄 Loading local embedding model: {model_name} on {device}")
        self.model = SentenceTransformer(model_name, device=device)
        self.device = device
        print(f"✅ Local embedding model loaded successfully")
        
    def encode(self, texts: Union[str, List[str]], convert_to_numpy: bool = True) -> np.ndarray:
        """Encode texts using local SentenceTransformer model"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(texts, convert_to_numpy=convert_to_numpy)
        return embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension from the model"""
        return self.model.get_sentence_embedding_dimension()

class OnlineEmbeddingService(EmbeddingServiceBase):
    """Online embedding service using Novita AI API with rate limiting"""
    
    def __init__(self):
        load_dotenv()
        
        self.api_key = os.getenv('NOVITA_API_KEY')
        self.embedding_url = os.getenv('NOVITA_EMBEDDING_URL', 'https://api.novita.ai/openai/v1/embeddings')
        self.embedding_model = os.getenv('NOVITA_EMBEDDING_MODEL', 'qwen/qwen3-embedding-8b')
        
        if not self.api_key:
            print("❌ NOVITA_API_KEY not found in environment")
            raise ValueError("NOVITA_API_KEY is required for online embeddings")
        
        print(f"🌐 Initializing ONLINE embeddings (Novita API)")
        print(f"   Model: {self.embedding_model}")
        print(f"   API Key: {self.api_key[:8]}...") 
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Rate limiting configuration because API limits to 50 requests/minute
        self.requests_per_minute = int(os.getenv('EMBEDDING_REQUESTS_PER_MINUTE', '45'))  
        self.request_interval = 60.0 / self.requests_per_minute  # Seconds between requests
        
        print(f"⏱️ Rate limiting: {self.requests_per_minute} requests/minute (interval: {self.request_interval:.2f}s)")
        self.last_request_time = 0
        
        # Retry configuration 
        self.max_retries = int(os.getenv('EMBEDDING_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('EMBEDDING_RETRY_DELAY', '2'))  
        
        # Test connection and get dimension
        self._dimension = None
        self._test_connection()
        
        print(f"✓ Online Embedding Service initialized")
        print(f"  URL: {self.embedding_url}")
        print(f"  Model: {self.embedding_model}")
        print(f"  Dimension: {self._dimension}")
        print(f"  Rate limit: {self.requests_per_minute} requests/minute")
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed the rate limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            print(f"⏱️  Rate limiting: waiting {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _test_connection(self):
        """Test API connection and determine embedding dimension"""
        try:
            test_embedding = self._get_single_embedding("test")
            self._dimension = len(test_embedding)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to embedding API: {e}")
    
    def _get_single_embedding(self, text: str, retry_count: int = 0) -> List[float]:
        """Get embedding for a single text with retry logic"""
        self._wait_for_rate_limit()
        
        payload = {
            "input": text,
            "model": self.embedding_model,
            "encoding_format": "float"
        }
        
        try:
            response = requests.post(self.embedding_url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 429:  # Rate limit exceeded
                if retry_count < self.max_retries:
                    retry_delay = self.retry_delay * (2 ** retry_count)  # Exponential backoff
                    print(f"⏳ Rate limit hit. Retrying in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries})")
                    time.sleep(retry_delay)
                    return self._get_single_embedding(text, retry_count + 1)
                else:
                    raise Exception(f"Rate limit exceeded after {self.max_retries} retries")
            
            response.raise_for_status()
            
            result = response.json()
            
            if 'data' in result and len(result['data']) > 0:
                return result['data'][0]['embedding']
            else:
                raise ValueError("Invalid response format from API")
                
        except requests.exceptions.RequestException as e:
            if retry_count < self.max_retries and "429" not in str(e):
                retry_delay = self.retry_delay * (2 ** retry_count)
                print(f"🔄 Request failed. Retrying in {retry_delay}s (attempt {retry_count + 1}/{self.max_retries}): {e}")
                time.sleep(retry_delay)
                return self._get_single_embedding(text, retry_count + 1)
            else:
                raise
    
    def encode(self, texts: Union[str, List[str]], convert_to_numpy: bool = True) -> np.ndarray:
        """Encode texts using online API with smart batching and rate limiting"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        total_texts = len(texts)
        
        print(f"🔄 Processing {total_texts} texts with rate limiting...")
        
        
        for i, text in enumerate(texts):
            try:
                if i > 0: 
                    progress = (i / total_texts) * 100
                    print(f"  Progress: {i}/{total_texts} ({progress:.1f}%)")
                
                embedding = self._get_single_embedding(text)
                embeddings.append(embedding)
                
            except Exception as e:
                print(f"⚠️  Failed to get embedding for text: {text[:50]}... Error: {e}")
                # Add zero vector as placeholder
                embeddings.append([0.0] * self._dimension)
        
        if convert_to_numpy:
            return np.array(embeddings, dtype=np.float32)
        else:
            return embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        if self._dimension is None:
            raise ValueError("Dimension not determined. Service may not be properly initialized.")
        return self._dimension

class EmbeddingServiceFactory:
    """Factory class to create appropriate embedding service"""
    
    @staticmethod
    def create_embedding_service(use_online: bool = None, 
                                model_name: str = None, 
                                device: str = "cpu") -> EmbeddingServiceBase:
        """
        Create embedding service based on configuration
        
        Args:
            use_online: Whether to use online embeddings. If None, check environment
            model_name: Model name for local embeddings
            device: Device for local embeddings
            
        Returns:
            EmbeddingServiceBase: Appropriate embedding service
        """
        load_dotenv()
        
        
        if use_online is None:
            use_online = os.getenv('USE_ONLINE_EMBEDDINGS', 'false').lower() == 'true'
        
        print(f"🔍 Embedding configuration:")
        print(f"   USE_ONLINE_EMBEDDINGS: {os.getenv('USE_ONLINE_EMBEDDINGS', 'not set')}")
        print(f"   use_online parameter: {use_online}")
        print(f"   SENTENCE_TRANSFORMERS_AVAILABLE: {SENTENCE_TRANSFORMERS_AVAILABLE}")
        
        if use_online:
            print("🌐 Using ONLINE embeddings (Novita API)")
            return OnlineEmbeddingService()
        else:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                print("❌ WARNING: SentenceTransformers not available, falling back to ONLINE embeddings")
                print("💡 To fix: Install sentence-transformers with: pip install sentence-transformers")
                return OnlineEmbeddingService()
            
            if model_name is None:
                model_name = os.getenv('EMBEDDING_MODEL', 'NeuML/pubmedbert-base-embeddings')
            
            print(f"🖥️ Using LOCAL embeddings (model: {model_name}, device: {device})")
            return LocalEmbeddingService(model_name, device)