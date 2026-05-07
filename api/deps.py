"""
FastAPI 依赖注入

- get_current_user: 从 Authorization header 提取用户
- require_tenant: 租户角色校验
- require_platform_admin: 平台管理员角色校验
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth import UserInfo, UserRole, decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInfo:
    """
    从 Authorization: Bearer <token> 提取并验证用户

    Raises:
        HTTPException 401: token 缺失或无效
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "UNAUTHORIZED", "message": "缺少认证 token"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "UNAUTHORIZED", "message": "token 无效或已过期"},
        )

    return UserInfo(
        user_id=payload.user_id,
        email=payload.email,
        role=payload.role,
        enterprise_id=payload.enterprise_id,
        plan=payload.plan,
        name=payload.name,
    )


async def require_tenant(
    user: UserInfo = Depends(get_current_user),
) -> UserInfo:
    """校验租户角色（非平台管理员）"""
    if user.role == UserRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "平台管理员不得使用租户 API"},
        )
    return user


async def require_platform_admin(
    user: UserInfo = Depends(get_current_user),
) -> UserInfo:
    """校验平台管理员角色"""
    if user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "需要平台管理员权限"},
        )
    return user


def verify_enterprise_id(request_enterprise_id: str, user: UserInfo) -> None:
    """
    校验 enterprise_id 与 token 中的一致性

    Raises:
        HTTPException 403: enterprise_id 不匹配
    """
    if user.enterprise_id and request_enterprise_id != user.enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "enterprise_id 不匹配"},
        )
