from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.wallet import TransactionType


class WalletResponse(BaseModel):
    id: UUID
    user_id: UUID
    balance: float
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WalletTransactionResponse(BaseModel):
    id: UUID
    wallet_id: UUID
    type: TransactionType
    amount: float
    description: str
    reference_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class WalletAddMoney(BaseModel):
    amount: float
    payment_transaction_id: str
