import os
from email_tracking import EmailTrackingService

# Load env
try:
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found")

# Initialize service
service = EmailTrackingService()

print("Testing Email Tracking Service")
print("=" * 50)

# Test 1: Sync a contact with known email history
print("\nTest 1: Sync nocodecanada@gmail.com (known to have 1 email)")
print("-" * 50)
result = service.sync_contact_emails("nocodecanada@gmail.com", 1)
print(f"Result: {result}")

# Test 2: Update after send
print("\n\nTest 2: Simulate send update for yusheng.kuo@datagen.dev")
print("-" * 50)
result = service.update_after_send(2, "yusheng.kuo@datagen.dev")
print(f"Result: {result}")

print("\n\n" + "=" * 50)
print("Testing complete!")
