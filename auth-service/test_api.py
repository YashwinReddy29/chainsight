"""
Test script for the authentication API
Run this after starting the server with: uvicorn main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_register():
    """Test user registration"""
    print("\n=== Testing User Registration ===")
    user_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "securepass123",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 201


def test_login():
    """Test user login and get token"""
    print("\n=== Testing User Login ===")
    login_data = {
        "username": "testuser",
        "password": "securepass123"
    }
    
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"Response: {json.dumps(token_data, indent=2)}")
        return token_data["access_token"]
    else:
        print(f"Error: {response.json()}")
        return None


def test_get_current_user(token):
    """Test getting current user info with token"""
    print("\n=== Testing Get Current User ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_protected_endpoint(token):
    """Test protected endpoint"""
    print("\n=== Testing Protected Endpoint ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/users/me/items", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_invalid_token():
    """Test with invalid token"""
    print("\n=== Testing Invalid Token ===")
    headers = {"Authorization": "Bearer invalid_token_here"}
    
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 401


def main():
    """Run all tests"""
    print("=" * 60)
    print("FastAPI Authentication Service - API Tests")
    print("=" * 60)
    
    try:
        # Test health check
        if not test_health():
            print("\n❌ Health check failed!")
            return
        
        # Test registration (may fail if user already exists)
        test_register()
        
        # Test login
        token = test_login()
        if not token:
            print("\n❌ Login failed!")
            return
        
        # Test authenticated endpoints
        test_get_current_user(token)
        test_protected_endpoint(token)
        
        # Test invalid token
        test_invalid_token()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Make sure the server is running with: uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()

# Made with Bob