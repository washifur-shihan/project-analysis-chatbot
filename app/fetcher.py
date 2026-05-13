import httpx

from app.config import (
    BACKEND_SERVICE_HEADER,
    GLOBAL_PROJECTS_PATH,
    SINGLE_PROJECT_PATH,
    SOURCE_API_BASE_URL,
    SOURCE_API_URL,
)


def _headers() -> dict:
    headers = {}

    if BACKEND_SERVICE_HEADER:
        headers["x-backend-service"] = BACKEND_SERVICE_HEADER

    return headers


def _url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path

    return f"{SOURCE_API_BASE_URL}/{path.lstrip('/')}"


async def fetch_projects():
    url = SOURCE_API_URL or _url(GLOBAL_PROJECTS_PATH)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=_headers())
        response.raise_for_status()
        return response.json()


async def fetch_project(project_id: str):
    path = SINGLE_PROJECT_PATH.format(id=project_id)
    url = _url(path)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=_headers())
        response.raise_for_status()
        return response.json()