"""
Quick test to verify DeepSeek API connectivity
"""
import asyncio
import httpx

API_KEY = "sk-2b9fece2424a4a1aa69fd22123a82e36"
BASE_URL = "https://api.deepseek.com"

async def test_api():
    url = BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Say 'hi' in one word"}],
        "temperature": 0.3,
        "stream": False,
    }

    print("Testing DeepSeek API connection...")
    print(f"URL: {url}")
    print(f"API Key: {API_KEY[:15]}...")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, headers=headers, json=payload)
            print(f"\nStatus: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                print(f"✅ API WORKING!")
                print(f"Response: {data['choices'][0]['message']['content']}")
            else:
                print(f"❌ API Error:")
                print(r.text)
                
    except Exception as e:
        print(f"❌ Connection Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
