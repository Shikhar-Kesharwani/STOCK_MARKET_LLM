from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

from starlette.requests import Request
from starlette.responses import Response

@app.middleware("http")
async def head_to_get_middleware(request: Request, call_next):
    if request.method == "HEAD":
        request.scope["method"] = "GET"
        response = await call_next(request)
        return Response(status_code=response.status_code, headers=dict(response.headers))
    return await call_next(request)

@app.get('/health')
async def health_check():
    return {'status': 'ok', 'service': 'stock-intelligence-backend'}
