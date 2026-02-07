import requests

# Test various possible routes
base_url = "https://face-reg.onrender.com"

routes_to_check = [
    '/',
    '/landing',
    '/dashboard',
    '/login',
    '/register',
    '/signup',
    '/privacy',
    '/help'
]

print("🔍 Checking available routes...")
print("=" * 40)

for route in routes_to_check:
    try:
        response = requests.get(f"{base_url}{route}", timeout=5)
        status = "✅" if response.status_code == 200 else f"❌ ({response.status_code})"
        print(f"{status} {route}")
    except Exception as e:
        print(f"❌ {route} - Error: {str(e)[:50]}")

print("\n" + "=" * 40)
print("💡 The working routes are accessible in your browser!")