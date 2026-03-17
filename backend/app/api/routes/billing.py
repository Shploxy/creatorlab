from fastapi import APIRouter, HTTPException, status

from app.core.auth import get_available_plans

router = APIRouter(tags=["billing"])


@router.get("/billing/plans")
async def billing_plans():
    return {"plans": get_available_plans(), "provider": "stripe-ready-placeholder"}


@router.post("/billing/checkout-session")
async def create_checkout_session():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Billing checkout is not wired yet. The project is structured for Stripe integration later.",
    )
