from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ApiKeyValidationRequest(BaseModel):
    api_key: str

class ApiKeyValidationResponse(BaseModel):
    success: bool
    message: str
    provider: str

@router.post("/test-google-api-key", response_model=ApiKeyValidationResponse)
async def test_google_api_key(request: ApiKeyValidationRequest):
    """
    Test Google API key validity by attempting to configure and list models
    """
    try:
        # Import lazily to avoid startup errors
        import google.generativeai as genai
        
        # Configure the API key
        genai.configure(api_key=request.api_key)
        
        # Test the key by listing available models
        models = list(genai.list_models())
        
        if models:
            return ApiKeyValidationResponse(
                success=True,
                message="Google API key is valid and working",
                provider="google"
            )
        else:
            return ApiKeyValidationResponse(
                success=False,
                message="Google API key validation failed - no models returned",
                provider="google"
            )
            
    except ImportError:
        logger.error("Google GenerativeAI package not installed")
        return ApiKeyValidationResponse(
            success=False,
            message="Google GenerativeAI package not installed on server",
            provider="google"
        )
    except Exception as e:
        logger.error(f"Google API key validation error: {str(e)}")
        return ApiKeyValidationResponse(
            success=False,
            message=f"Google API key validation failed: {str(e)}",
            provider="google"
        )

@router.post("/test-openai-api-key", response_model=ApiKeyValidationResponse)
async def test_openai_api_key(request: ApiKeyValidationRequest):
    """
    Test OpenAI API key validity
    """
    try:
        # Import OpenAI client lazily
        from openai import OpenAI
        
        # Initialize client with the provided API key
        client = OpenAI(api_key=request.api_key)
        
        # Test the key by listing models
        models = client.models.list()
        
        if models.data:
            return ApiKeyValidationResponse(
                success=True,
                message="OpenAI API key is valid and working",
                provider="openai"
            )
        else:
            return ApiKeyValidationResponse(
                success=False,
                message="OpenAI API key validation failed - no models returned",
                provider="openai"
            )
            
    except ImportError:
        logger.error("OpenAI package not installed")
        return ApiKeyValidationResponse(
            success=False,
            message="OpenAI package not installed on server",
            provider="openai"
        )
    except Exception as e:
        logger.error(f"OpenAI API key validation error: {str(e)}")
        return ApiKeyValidationResponse(
            success=False,
            message=f"OpenAI API key validation failed: {str(e)}",
            provider="openai"
        )