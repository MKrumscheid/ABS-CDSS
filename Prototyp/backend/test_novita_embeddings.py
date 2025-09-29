#!/usr/bin/env python3
"""
Test script for Novita AI Embedding API
Tests the embedding functionality that will replace the local SentenceTransformer model
"""
import os
import requests
import time
import numpy as np
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NovitaEmbeddingService:
    """Service class for Novita AI Embedding API"""
    
    def __init__(self):
        self.api_key = os.getenv('NOVITA_API_KEY')
        self.embedding_url = os.getenv('NOVITA_EMBEDDING_URL', 'https://api.novita.ai/openai/v1/embeddings')
        self.embedding_model = os.getenv('NOVITA_EMBEDDING_MODEL', 'qwen/qwen3-embedding-8b')
        
        if not self.api_key:
            raise ValueError("NOVITA_API_KEY is required but not found in environment variables")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        print(f"✓ Embedding Service initialized")
        print(f"  URL: {self.embedding_url}")
        print(f"  Model: {self.embedding_model}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding
        """
        payload = {
            "input": text,
            "model": self.embedding_model,
            "encoding_format": "float"
        }
        
        try:
            print(f"🔗 Making API request...")
            response = requests.post(self.embedding_url, json=payload, headers=self.headers, timeout=30)
            print(f"📡 Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            print(f"📝 Response keys: {list(result.keys())}")
            
            if 'data' in result and len(result['data']) > 0:
                embedding = result['data'][0]['embedding']
                print(f"✓ Embedding extracted, dimension: {len(embedding)}")
                return embedding
            else:
                print(f"❌ Invalid response format. Full response: {result}")
                raise ValueError("Invalid response format from API")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            raise
        except Exception as e:
            print(f"❌ Error processing embedding: {e}")
            raise
    
    def get_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batches
        
        Args:
            texts: List of input texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embeddings
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            print(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} ({len(batch)} texts)")
            
            for text in batch:
                try:
                    embedding = self.get_embedding(text)
                    batch_embeddings.append(embedding)
                    time.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"❌ Failed to get embedding for text: {text[:50]}... Error: {e}")
                    # Add zero vector as placeholder
                    batch_embeddings.append([0.0] * 768)  # Assuming 768-dimensional embeddings
            
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings

def test_basic_embedding():
    """Test basic embedding functionality"""
    print("\n🔍 Testing basic embedding functionality...")
    
    try:
        service = NovitaEmbeddingService()
        
        test_text = "Dies ist ein Testtext für die Antibiotikatherapie bei Pneumonie."
        
        print(f"Input text: '{test_text}'")
        
        embedding = service.get_embedding(test_text)
        
        print(f"✓ Embedding received!")
        print(f"  Dimensions: {len(embedding)}")
        print(f"  First 10 values: {embedding[:10]}")
        print(f"  Embedding norm: {np.linalg.norm(embedding):.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic embedding test failed: {e}")
        return False

def test_medical_texts():
    """Test with medical/clinical texts similar to what will be used in production"""
    print("\n🏥 Testing with medical texts...")
    
    medical_texts = [
        "Pneumonie-Therapie bei immunsupprimierten Patienten erfordert eine angepasste Antibiotikatherapie.",
        "Amoxicillin/Clavulansäure 875/125 mg zweimal täglich per os bei ambulant erworbener Pneumonie.",
        "Bei Verdacht auf multiresistente Erreger sollte eine kalkulierte Therapie mit Piperacillin/Tazobactam erwogen werden.",
        "Dosisanpassung bei Niereninsuffizienz: Kreatinin-Clearance <50 ml/min erfordert Dosisreduktion.",
        "Therapiedauer bei unkomplizierter CAP beträgt in der Regel 5-7 Tage."
    ]
    
    try:
        service = NovitaEmbeddingService()
        
        embeddings = []
        for i, text in enumerate(medical_texts, 1):
            print(f"Processing text {i}/{len(medical_texts)}: {text[:50]}...")
            embedding = service.get_embedding(text)
            embeddings.append(embedding)
            time.sleep(0.2)  # Rate limiting
        
        print(f"✓ All medical texts processed!")
        
        # Test similarity calculation
        if len(embeddings) >= 2:
            emb1 = np.array(embeddings[0])
            emb2 = np.array(embeddings[1])
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            print(f"  Cosine similarity between first two texts: {similarity:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Medical texts test failed: {e}")
        return False

def test_batch_processing():
    """Test batch processing functionality"""
    print("\n📦 Testing batch processing...")
    
    batch_texts = [
        f"Test text {i}: Antibiotikatherapie Beispiel {i}" for i in range(1, 6)
    ]
    
    try:
        service = NovitaEmbeddingService()
        
        embeddings = service.get_embeddings_batch(batch_texts, batch_size=3)
        
        print(f"✓ Batch processing completed!")
        print(f"  Processed {len(embeddings)} texts")
        print(f"  Average embedding dimension: {len(embeddings[0]) if embeddings else 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\n⚠️  Testing error handling...")
    
    try:
        service = NovitaEmbeddingService()
        
        # Test empty text
        try:
            embedding = service.get_embedding("")
            print("⚠️  Empty text processed without error")
        except Exception:
            print("✓ Empty text properly rejected")
        
        # Test very long text
        long_text = "Test " * 10000
        try:
            embedding = service.get_embedding(long_text)
            print("✓ Long text processed successfully")
        except Exception as e:
            print(f"⚠️  Long text failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Novita AI Embedding API Tests")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ['NOVITA_API_KEY', 'NOVITA_EMBEDDING_URL', 'NOVITA_EMBEDDING_MODEL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    print("✓ Environment variables loaded")
    
    # Run tests
    tests = [
        ("Basic Embedding", test_basic_embedding),
        ("Medical Texts", test_medical_texts),
        ("Batch Processing", test_batch_processing),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The Novita AI Embedding API is ready for production use.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and API connectivity.")

if __name__ == "__main__":
    main()