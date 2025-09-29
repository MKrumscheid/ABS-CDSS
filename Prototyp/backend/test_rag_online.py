#!/usr/bin/env python3
"""
Test script for the modified RAG service with online embeddings
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from rag_service_advanced import AdvancedRAGService

def test_rag_service_initialization():
    """Test RAG service initialization with online embeddings"""
    print("\n🔧 Testing RAG Service Initialization...")
    
    try:
        # Create RAG service instance
        rag_service = AdvancedRAGService()
        
        print("✅ RAG Service initialized successfully!")
        print(f"  Device: {rag_service.device}")
        print(f"  Embedding dimension: {rag_service.embedding_model.get_dimension()}")
        print(f"  Data directory: {rag_service.data_dir}")
        
        return rag_service, True
        
    except Exception as e:
        print(f"❌ RAG Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def test_embedding_functionality(rag_service):
    """Test embedding functionality"""
    print("\n🧠 Testing Embedding Functionality...")
    
    try:
        # Test single text embedding
        test_text = "Amoxicillin/Clavulansäure bei ambulant erworbener Pneumonie"
        
        # Use the internal embedding method
        embeddings = rag_service.embedding_model.encode([test_text])
        
        print(f"✅ Single text embedding successful!")
        print(f"  Text: '{test_text}'")
        print(f"  Embedding shape: {embeddings.shape}")
        print(f"  First 5 values: {embeddings[0][:5]}")
        
        # Test multiple texts
        test_texts = [
            "Pneumonie-Therapie bei immunsupprimierten Patienten",
            "Dosisanpassung bei Niereninsuffizienz erforderlich",
            "Multiresistente Erreger erfordern spezielle Antibiotika"
        ]
        
        embeddings_batch = rag_service.embedding_model.encode(test_texts)
        
        print(f"✅ Batch embedding successful!")
        print(f"  Processed {len(test_texts)} texts")
        print(f"  Embeddings shape: {embeddings_batch.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_query(rag_service):
    """Test a simple query without full index"""
    print("\n🔍 Testing Simple Query...")
    
    try:
        # Test if we can create embeddings for query
        query_text = "Welche Antibiotika werden bei Pneumonie empfohlen?"
        
        query_embedding = rag_service.embedding_model.encode([query_text])
        
        print(f"✅ Query embedding successful!")
        print(f"  Query: '{query_text}'")
        print(f"  Query embedding shape: {query_embedding.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Modified RAG Service with Online Embeddings")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check if online embeddings are enabled
    use_online = os.getenv('USE_ONLINE_EMBEDDINGS', 'false').lower()
    print(f"USE_ONLINE_EMBEDDINGS: {use_online}")
    
    if use_online != 'true':
        print("⚠️  Online embeddings not enabled in .env file")
        print("   Set USE_ONLINE_EMBEDDINGS=true to use online embeddings")
    
    # Run tests
    tests = []
    
    # Test 1: Initialization
    rag_service, init_success = test_rag_service_initialization()
    tests.append(("Initialization", init_success))
    
    if not init_success or rag_service is None:
        print("\n❌ Cannot continue with other tests - initialization failed")
    else:
        # Test 2: Embedding functionality
        embedding_success = test_embedding_functionality(rag_service)
        tests.append(("Embedding Functionality", embedding_success))
        
        # Test 3: Simple query
        query_success = test_simple_query(rag_service)
        tests.append(("Simple Query", query_success))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG service is ready with online embeddings.")
    else:
        print("⚠️  Some tests failed. Check the configuration and setup.")

if __name__ == "__main__":
    main()