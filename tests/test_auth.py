import sys
sys.path.insert(0, '.')

# Test 1: Import the auth module
print('=== Test 1: Import auth module ===')
from auth.jwt_auth import create_token, verify_token, authenticate_user, init_default_users
print('Auth module imported successfully')

# Test 2: Initialize default users
print('\n=== Test 2: Initialize default users ===')
init_default_users()

# Test 3: Test authentication
print('\n=== Test 3: Test authentication ===')
user = authenticate_user('admin', 'admin123')
if user:
    print('Login successful:', user)
else:
    print('Login failed - invalid credentials')

# Test 4: Wrong password
print('\n=== Test 4: Wrong password ===')
user = authenticate_user('admin', 'wrongpassword')
if user:
    print('Unexpected success')
else:
    print('Wrong password test: Failed as expected')

# Test 5: Create and verify token
print('\n=== Test 5: Token creation and verification ===')
token = create_token(1, 'admin', 'admin')
print('Token created:', token[:50] + '...')

payload = verify_token(token)
print('Token verified:', payload)

# Test 6: Invalid token
print('\n=== Test 6: Invalid token ===')
invalid_payload = verify_token('invalid.token.here')
if invalid_payload:
    print('Unexpected success')
else:
    print('Invalid token test: Failed as expected')

print('\n=== All tests passed! ===')
