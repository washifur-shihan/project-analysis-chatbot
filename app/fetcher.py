import httpx
from app.config import SOURCE_API_URL

async def fetch_projects():
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(SOURCE_API_URL)
        response.raise_for_status()
        return response.json()
    
