from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.oauth.token_manager import get_all_user_accounts, disconnect_account

router = APIRouter(prefix="/api/accounts", tags=["connected-accounts"])


@router.get("")
@router.get("/")
async def list_connected_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts = get_all_user_accounts(current_user.id, db)
    return {"accounts": accounts, "total": len(accounts)}


@router.delete("/{account_id}")
async def remove_connected_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = disconnect_account(current_user.id, account_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"detail": "Account disconnected"}


# Also serve at /api/oauth/accounts for convenience (returns flat array)
from fastapi import APIRouter as _AR
oauth_accounts_flat_router = _AR(prefix="/api/oauth", tags=["connected-accounts"])


@oauth_accounts_flat_router.get("/accounts")
@oauth_accounts_flat_router.get("/accounts/")
async def list_connected_accounts_flat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_all_user_accounts(current_user.id, db)
