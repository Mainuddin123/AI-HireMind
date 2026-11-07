
from backend.authentication.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)


# Test password hashing
password = "TestPassword123!"

hashed = hash_password(password)

print("Password hashing:", "PASSED" if hashed != password else "FAILED")


# Test password verification
verified = verify_password(password, hashed)

print("Password verification:", "PASSED" if verified else "FAILED")


# Test JWT generation
token = create_access_token({
    "sub": "test@example.com",
    "role": "candidate"
})

print("JWT generation:", "PASSED" if token else "FAILED")


# Test JWT validation
payload = decode_access_token(token)

print("JWT validation:", "PASSED" if payload["sub"] == "test@example.com" else "FAILED")
