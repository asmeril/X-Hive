import aiohttp
import asyncio

async def test():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    }
    
    async with aiohttp.ClientSession() as session:
        url = 'https://old.reddit.com/r/Python/top/?t=day'
        async with session.get(url, headers=headers) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                text = await response.text()
                print(f"Content length: {len(text)}")
                print("First 500 chars:")
                print(text[:500])
            else:
                print(f"Error: {response.status}")

asyncio.run(test())
