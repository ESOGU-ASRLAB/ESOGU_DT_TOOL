"""
Simple script to add test data to MongoDB for Docker UI testing
Bu script MongoDB'ye basit test verileri ekler ki UI'da Docker özelliğini test edebilesiniz
"""
import asyncio
import sys
from datetime import datetime
from core.database import get_database

async def add_simple_test_data():
    """Add simple test data for Docker execution testing"""
    try:
        db = await get_database()
        collection = db["session_history"]
        
        # Basit bir test senaryosu
        test_data = {
            "session_id": "docker-test-session-001",
            "timestamp": datetime.now().isoformat(),
            "processes": {
                "test_code_generation": {
                    "code_generation_process_name": "Docker_Simple_Math_Test",
                    "process_name": "Docker_Simple_Math_Test",
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed",
                    "input": {
                        "requirement": "Simple math operations test"
                    },
                    "output": {
                        "test_code": """# Simple Math Tests
print("="*50)
print("🐳 DOCKER TEST - Simple Math Operations")
print("="*50)

def test_addition():
    print("Testing addition...")
    result = 2 + 2
    assert result == 4, f"Expected 4, got {result}"
    print("✅ Addition test passed!")

def test_subtraction():
    print("Testing subtraction...")
    result = 10 - 5
    assert result == 5, f"Expected 5, got {result}"
    print("✅ Subtraction test passed!")

def test_multiplication():
    print("Testing multiplication...")
    result = 3 * 4
    assert result == 12, f"Expected 12, got {result}"
    print("✅ Multiplication test passed!")

def test_division():
    print("Testing division...")
    result = 20 / 4
    assert result == 5.0, f"Expected 5.0, got {result}"
    print("✅ Division test passed!")

# Run all tests
test_addition()
test_subtraction()
test_multiplication()
test_division()

print("\\n" + "="*50)
print("🎉 All tests passed successfully!")
print("="*50)
""",
                        "generated_tests": [
                            {
                                "name": "Test Addition",
                                "code": """def test_addition():
    print("Testing addition...")
    result = 2 + 2
    assert result == 4, f"Expected 4, got {result}"
    print("✅ Addition test passed!")

test_addition()"""
                            },
                            {
                                "name": "Test Subtraction",
                                "code": """def test_subtraction():
    print("Testing subtraction...")
    result = 10 - 5
    assert result == 5, f"Expected 5, got {result}"
    print("✅ Subtraction test passed!")

test_subtraction()"""
                            },
                            {
                                "name": "Test Multiplication",
                                "code": """def test_multiplication():
    print("Testing multiplication...")
    result = 3 * 4
    assert result == 12, f"Expected 12, got {result}"
    print("✅ Multiplication test passed!")

test_multiplication()"""
                            },
                            {
                                "name": "Test Division",
                                "code": """def test_division():
    print("Testing division...")
    result = 20 / 4
    assert result == 5.0, f"Expected 5.0, got {result}"
    print("✅ Division test passed!")

test_division()"""
                            }
                        ]
                    }
                }
            }
        }
        
        # NumPy ile test - daha gelişmiş
        numpy_test_data = {
            "session_id": "docker-test-session-002",
            "timestamp": datetime.now().isoformat(),
            "processes": {
                "test_code_generation": {
                    "code_generation_process_name": "Docker_NumPy_Array_Test",
                    "process_name": "Docker_NumPy_Array_Test",
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed",
                    "input": {
                        "requirement": "NumPy array operations test"
                    },
                    "output": {
                        "test_code": """# NumPy Array Test
import numpy as np

print("="*50)
print("🐳 DOCKER TEST - NumPy Array Operations")
print("📦 This test requires 'numpy' package")
print("="*50)

def test_numpy_installation():
    print("\\nTesting NumPy installation...")
    version = np.__version__
    print(f"✅ NumPy version: {version}")

def test_array_creation():
    print("\\nTesting array creation...")
    arr = np.array([1, 2, 3, 4, 5])
    assert len(arr) == 5, f"Expected length 5, got {len(arr)}"
    print(f"✅ Array created: {arr}")

def test_array_operations():
    print("\\nTesting array operations...")
    arr1 = np.array([1, 2, 3])
    arr2 = np.array([4, 5, 6])
    result = arr1 + arr2
    expected = np.array([5, 7, 9])
    assert np.array_equal(result, expected), f"Expected {expected}, got {result}"
    print(f"✅ Array addition: {arr1} + {arr2} = {result}")

# Run all tests
test_numpy_installation()
test_array_creation()
test_array_operations()

print("\\n" + "="*50)
print("🎉 All NumPy tests passed!")
print("="*50)
""",
                        "generated_tests": [
                            {
                                "name": "Test NumPy Installation",
                                "code": """import numpy as np

print("Testing NumPy installation...")
version = np.__version__
print(f"✅ NumPy version: {version}")"""
                            },
                            {
                                "name": "Test Array Creation",
                                "code": """import numpy as np

print("Testing array creation...")
arr = np.array([1, 2, 3, 4, 5])
assert len(arr) == 5, f"Expected length 5, got {len(arr)}"
print(f"✅ Array created: {arr}")"""
                            },
                            {
                                "name": "Test Array Operations",
                                "code": """import numpy as np

print("Testing array operations...")
arr1 = np.array([1, 2, 3])
arr2 = np.array([4, 5, 6])
result = arr1 + arr2
expected = np.array([5, 7, 9])
assert np.array_equal(result, expected), f"Expected {expected}, got {result}"
print(f"✅ Array addition: {arr1} + {arr2} = {result}")"""
                            }
                        ]
                    }
                }
            }
        }
        
        # Verileri ekle
        result1 = await collection.insert_one(test_data)
        result2 = await collection.insert_one(numpy_test_data)
        
        print("✅ Test verileri başarıyla eklendi!")
        print(f"\n📋 Eklenen test process'leri:")
        print(f"  1. Docker_Simple_Math_Test (ID: {result1.inserted_id})")
        print(f"  2. Docker_NumPy_Array_Test (ID: {result2.inserted_id})")
        print("\n🎯 Şimdi UI'da bu process'leri görebilirsiniz!")
        
        return True
        
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(add_simple_test_data())
