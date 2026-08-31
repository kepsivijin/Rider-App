from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction, TransactionType
from app.models.ride import Ride, PaymentStatus
from app.schemas.wallet import WalletResponse, WalletTransactionResponse, WalletAddMoney
from app.services.payment import create_payment_order, verify_payment_signature

router = APIRouter()


@router.get("/wallet", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's wallet"""
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        wallet = Wallet(user_id=current_user.id, balance=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    return WalletResponse.model_validate(wallet)


@router.post("/wallet/add-money", response_model=dict)
async def add_money_to_wallet(
    data: WalletAddMoney,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add money to wallet"""
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        wallet = Wallet(user_id=current_user.id, balance=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    wallet.balance += data.amount
    
    transaction = WalletTransaction(
        wallet_id=wallet.id,
        type=TransactionType.CREDIT,
        amount=data.amount,
        description=f"Money added to wallet",
        reference_id=data.payment_transaction_id
    )
    
    db.add(transaction)
    db.commit()
    
    return {
        "message": "Money added successfully",
        "new_balance": wallet.balance
    }


@router.post("/create-order", response_model=dict)
async def create_razorpay_order(
    amount: float,
    ride_id: str = None,
    current_user: User = Depends(get_current_user)
):
    """Create Razorpay payment order"""
    receipt = ride_id if ride_id else f"wallet_{current_user.id}"
    
    order = create_payment_order(
        amount=amount,
        receipt=receipt,
        notes={"user_id": str(current_user.id)}
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment order"
        )
    
    return order


@router.post("/verify-payment", response_model=dict)
async def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    ride_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify Razorpay payment signature"""
    is_valid = verify_payment_signature(
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    
    if ride_id:
        ride = db.query(Ride).filter(Ride.id == UUID(ride_id)).first()
        if ride:
            ride.payment_status = PaymentStatus.COMPLETED
            ride.payment_transaction_id = razorpay_payment_id
            db.commit()
    
    return {
        "message": "Payment verified successfully",
        "payment_id": razorpay_payment_id
    }
