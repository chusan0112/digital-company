import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from api import handle_request

# Test 1: Health check
print('=== Test 1: Health Check ===')
result = handle_request('/api/health', 'GET')
print('Result:', result)
print('Auth enabled:', result.get('auth_enabled'))

# Test 2: Login via API
print('\n=== Test 2: Login via API ===')
body = json.dumps({'username': 'admin', 'password': 'admin123'})
result = handle_request('/api/auth/login', 'POST', body)
print('Success:', result.get('success'))
print('Token:', result.get('token', '')[:50] + '...')

token = result.get('token')

# Test 3: Verify token via API
print('\n=== Test 3: Verify Token via API ===')
headers = {'Authorization': 'Bearer ' + token}
result = handle_request('/api/auth/verify', 'GET', None, headers)
print('Success:', result.get('success'))
print('User:', result.get('user'))

# Test 4: Logout via API
print('\n=== Test 4: Logout via API ===')
result = handle_request('/api/auth/logout', 'POST', None, headers)
print('Success:', result.get('success'))

# Test 5: Verify after logout - should fail
print('\n=== Test 5: Verify After Logout ===')
result = handle_request('/api/auth/verify', 'GET', None, headers)
print('Success:', result.get('success'))
print('Error:', result.get('error'))

print('\n=== API Module tests completed! ===')
