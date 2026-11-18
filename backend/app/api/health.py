from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict:
    return {
        "status": "ok",
        "version": "0.1.0",
        "mode": "local-development",
        "rag_ready": False,
        "mock_chat_enabled": request.app.state.settings.enable_mock_chat,
    }
