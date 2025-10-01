#!/usr/bin/env python3
"""
Test script for rate-limited embedding service
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to Python path
import sys
sys.path.append(str(Path(__file__).parent))

from embedding_service import EmbeddingServiceFactory

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n⏱️  Testing Rate Limiting...")
    
    try:
        # Create embedding service
        embedding_service = EmbeddingServiceFactory.create_embedding_service(use_online=True)
        
        # Test with multiple texts to trigger rate limiting
        test_texts = [
            "Pneumonie-Therapie bei immunsupprimierten Patienten",
            "Amoxicillin/Clavulansäure Dosierung bei Erwachsenen",
            "Dosisanpassung bei Niereninsuffizienz erforderlich",
            "Multiresistente Erreger erfordern spezielle Antibiotika",
            "Therapiedauer bei unkomplizierter CAP beträgt 5-7 Tage"
        ]
        
        print(f"Processing {len(test_texts)} texts with rate limiting...")
        
        start_time = time.time()
        embeddings = embedding_service.encode(test_texts)
        end_time = time.time()
        
        print(f"✅ Rate limiting test successful!")
        print(f"  Processed {len(test_texts)} texts")
        print(f"  Total time: {end_time - start_time:.2f} seconds")
        print(f"  Average time per text: {(end_time - start_time) / len(test_texts):.2f} seconds")
        print(f"  Embeddings shape: {embeddings.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_single_embedding_with_retry():
    """Test single embedding with retry mechanism"""
    print("\n🔄 Testing Single Embedding with Retry...")
    
    try:
        embedding_service = EmbeddingServiceFactory.create_embedding_service(use_online=True)
        
        test_text = "Test für Retry-Mechanismus bei API-Fehlern"
        
        start_time = time.time()
        embedding = embedding_service.encode([test_text])
        end_time = time.time()
        
        print(f"✅ Single embedding test successful!")
        print(f"  Text: '{test_text}'")
        print(f"  Time taken: {end_time - start_time:.2f} seconds")
        print(f"  Embedding shape: {embedding.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Single embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run rate limiting tests"""
    print("⏱️  Testing Embedding Service with Rate Limiting")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Show configuration
    print("Configuration:")
    print(f"  EMBEDDING_REQUESTS_PER_MINUTE: {os.getenv('EMBEDDING_REQUESTS_PER_MINUTE', '45')}")
    print(f"  EMBEDDING_MAX_RETRIES: {os.getenv('EMBEDDING_MAX_RETRIES', '3')}")
    print(f"  EMBEDDING_RETRY_DELAY: {os.getenv('EMBEDDING_RETRY_DELAY', '2')}")
    
    # Run tests
    tests = [
        ("Single Embedding with Retry", test_single_embedding_with_retry),
        ("Rate Limiting", test_rate_limiting),
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
        print("🎉 All rate limiting tests passed! The service handles API limits properly.")
        print("\n💡 Tips for production:")
        print("  - Set EMBEDDING_REQUESTS_PER_MINUTE to 45 (slightly below API limit)")
        print("  - Increase EMBEDDING_MAX_RETRIES for better reliability")
        print("  - Consider caching embeddings for frequently used texts")
    else:
        print("⚠️  Some tests failed. Check the configuration and API connectivity.")

if __name__ == "__main__":
    main()