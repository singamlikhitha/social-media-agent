import httpx


def print_instagram_guide():
    print("""
=== Instagram Graph API Setup Guide ===

Step 1: Create a Meta Developer App
  - Go to https://developers.facebook.com/
  - Click "My Apps" -> "Create App"
  - Choose "Business" type
  - Fill in the app name and contact email

Step 2: Add Instagram Graph API
  - In your app dashboard, click "Add Product"
  - Find "Instagram Graph API" and click "Set Up"

Step 3: Connect a Facebook Page
  - You need a Facebook Page linked to an Instagram Business/Creator account
  - Go to your Instagram app settings -> "Linked Accounts" -> connect your Facebook Page

Step 4: Generate Access Token
  - Go to Graph API Explorer: https://developers.facebook.com/tools/explorer/
  - Select your app
  - Add permissions: instagram_basic, instagram_content_publish, instagram_manage_insights, pages_show_list, pages_read_engagement
  - Click "Generate Access Token" and authorize

Step 5: Exchange for Long-Lived Token
  - Short-lived tokens expire in 1 hour
  - We'll exchange it for a 60-day token automatically

Step 6: Get Business Account ID
  - We'll retrieve this from the API automatically
""")


async def exchange_token(app_id: str, app_secret: str, short_token: str) -> str:
    url = "https://graph.facebook.com/v21.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    if "error" in data:
        raise RuntimeError(f"Token exchange failed: {data['error']['message']}")

    return data["access_token"]


async def get_business_account_id(access_token: str) -> str:
    url = "https://graph.facebook.com/v21.0/me/accounts"
    params = {"access_token": access_token}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()

    if "error" in data:
        raise RuntimeError(f"Failed to get pages: {data['error']['message']}")

    pages = data.get("data", [])
    if not pages:
        raise RuntimeError("No Facebook Pages found. Link a Page to your Instagram account.")

    page_id = pages[0]["id"]
    page_token = pages[0]["access_token"]

    ig_url = f"https://graph.facebook.com/v21.0/{page_id}"
    params = {
        "fields": "instagram_business_account",
        "access_token": page_token,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(ig_url, params=params)
        data = response.json()

    ig_account = data.get("instagram_business_account", {}).get("id")
    if not ig_account:
        raise RuntimeError("No Instagram Business Account linked to this Page.")

    return ig_account
