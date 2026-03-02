"""Test approval endpoints"""
import sys
sys.path.insert(0, '.')

from app.main import app
from fastapi.testclient import TestClient
import json

client = TestClient(app)

print("=" * 60)
print("Testing Approval Endpoints")
print("=" * 60)

# Test 1: GET /approval/pending
print("\n1️⃣ GET /approval/pending")
response = client.get('/approval/pending')
print(f"Status: {response.status_code}")
data = response.json()
print(f"Total items: {data['data']['total']}")

if data['data']['items']:
    print("\nFirst item:")
    first_item = data['data']['items'][0]
    print(f"  - ID: {first_item['tweet_id']}")
    print(f"  - Status: {first_item['status']}")
    print(f"  - Tweet: {first_item['generated_tweet'][:80]}...")
    print(f"  - Title: {first_item['content_item']['title'][:80]}...")
    
    test_id = first_item['tweet_id']
    
    # Test 2: POST /approval/approve/{id}
    print(f"\n2️⃣ POST /approval/approve/{test_id}")
    response = client.post(f'/approval/approve/{test_id}')
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test 3: Verify item is no longer pending
    print("\n3️⃣ GET /approval/pending (after approve)")
    response = client.get('/approval/pending')
    data = response.json()
    print(f"Total items: {data['data']['total']}")
    
else:
    print("\n⚠️ No pending items to test approve/reject")
    
    # Test with fake ID
    print("\n2️⃣ POST /approval/approve/fake_id (should fail)")
    response = client.post('/approval/approve/fake_id')
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

print("\n" + "=" * 60)
print("✅ All tests completed")
print("=" * 60)
