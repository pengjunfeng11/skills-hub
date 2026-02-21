import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_api_key, decrypt_api_key
from app.core.security import generate_api_key, get_current_user
from app.database import get_db
from app.models.api_key import ApiKey
from app.models.user import User
from app.schemas.skill import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyDetailResponse,
    ApiKeyResponse,
    ApiKeyUpdate,
)

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    raw_key, key_hash = generate_api_key()

    api_key = ApiKey(
        user_id=user.id,
        key_hash=key_hash,
        key_encrypted=encrypt_api_key(raw_key),
        name=data.name,
        scopes=data.scopes,
        allowed_tags=data.allowed_tags,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        scopes=api_key.scopes,
        allowed_tags=api_key.allowed_tags,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        key=raw_key,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{key_id}", response_model=ApiKeyDetailResponse)
async def get_api_key_detail(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    decrypted_key = None
    if api_key.key_encrypted:
        try:
            decrypted_key = decrypt_api_key(api_key.key_encrypted)
        except Exception:
            decrypted_key = None

    return ApiKeyDetailResponse(
        id=api_key.id,
        name=api_key.name,
        scopes=api_key.scopes,
        allowed_tags=api_key.allowed_tags,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        key=decrypted_key,
    )


@router.put("/{key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    key_id: uuid.UUID,
    data: ApiKeyUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    if data.name is not None:
        api_key.name = data.name
    if data.allowed_tags is not None:
        api_key.allowed_tags = data.allowed_tags

    await db.commit()
    await db.refresh(api_key)
    return api_key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(api_key)
    await db.commit()
