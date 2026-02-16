import requests

# 1. Setup
BASE_URL = "http://127.0.0.1:8000"  # Assuming your FastAPI app runs here
LOGIN_URL = f"{BASE_URL}/login"
PROTECTED_URL = f"{BASE_URL}/users/me"

def main():
    # ---------------------------------------------------------
    # STEP 1: LOGIN
    # We send the username and password as form data (data=...)
    # ---------------------------------------------------------
    print(f"1. Attempting to log in at {LOGIN_URL}...")
    
    login_data = {
        "username": "testuser",
        "password": "password123"
    }

    # Note: We use 'data=' for form data, not 'json='
    response = requests.post(LOGIN_URL, data=login_data)

    if response.status_code != 200:
        print(f"❌ Login failed! Status: {response.status_code}")
        print(response.text)
        return

    # Extract the token from the JSON response
    token_info = response.json()
    access_token = token_info["access_token"]
    token_type = token_info["token_type"]
    
    print(f"✅ Login successful!")
    print(f"   Token received: {access_token[:20]}... (truncated)")

    # ---------------------------------------------------------
    # STEP 2: ACCESS PROTECTED ROUTE
    # We must add the token to the 'Authorization' header
    # ---------------------------------------------------------
    print(f"\n2. Attempting to access protected data at {PROTECTED_URL}...")

    # The format is strictly: "Bearer <your_token_here>"
    headers = {
        "Authorization": f"{token_type.capitalize()} {access_token}"
    }

    response = requests.get(PROTECTED_URL, headers=headers)

    if response.status_code == 200:
        print(f"✅ Success! Protected data retrieved:")
        print(f"   {response.json()}")
    else:
        print(f"❌ Access denied! Status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()