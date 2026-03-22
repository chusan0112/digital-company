import requests
import json
import time

BASE_URL = "http://127.0.0.1:8080"

# Wait for server to start
time.sleep(1)

print("=== Testing Flask API ===\n")

# Test 1: Login
print("=== Test 1: Login ===")
resp = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"username": "admin", "password": "admin123"}
)
print(f"Status: {resp.status_code}")
login_data = resp.json()
print(f"Success: {login_data.get('success')}")
token = login_data.get("token")

# Test 2: Verify token
print("\n=== Test 2: Verify Token ===")
resp = requests.get(
    f"{BASE_URL}/api/auth/verify",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")

# Test 3: Protected endpoint
print("\n=== Test 3: Protected Endpoint ===")
resp = requests.get(
    f"{BASE_URL}/api/protected/dashboard",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"Status: {resp.status_code}")
print(f"Success: {resp.json().get('success')}")

# Test 4: Logout
print("\n=== Test 4: Logout ===")
resp = requests.post(
    f"{BASE_URL}/api/auth/logout",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"Status: {resp.status_code}")
print(f"Success: {resp.json().get('success')}")

# Test 5: Verify after logout - should fail
print("\n=== Test 5: Verify After Logout (should fail) ===")
resp = requests.get(
    f"{BASE_URL}/api/auth/verify",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"Status: {resp.status_code}")
if resp.status_code == 401:
    print("Correctly returned 401 for revoked token")
else:
    print(f"Response: {resp.text}")

# Test 6: Login with wrong password
print("\n=== Test 6: Login with Wrong Password ===")
resp = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"username": "admin", "password": "wrongpassword"}
)
print(f"Status: {resp.status_code}")
print(f"Success: {resp.json().get('success')}, Error: {resp.json().get('error')}")

# Test 7: Access protected endpoint without token
print("\n=== Test 7: Access Protected Without Token ===")
resp = requests.get(f"{BASE_URL}/api/protected/dashboard")
print(f"Status: {resp.status_code}")
print(f"Success: {resp.json().get('success')}, Error: {resp.json().get('error')}")

print("\n=== All tests completed! ===")
