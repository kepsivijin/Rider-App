from typing import Dict, Any
import razorpay
from app.core.config import settings

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_payment_order(amount: float, receipt: str, notes: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Create a Razorpay payment order
    
    Args:
        amount: Amount in rupees
        receipt: Unique receipt ID (e.g., ride_id)
        notes: Additional information
    
    Returns:
        Order details including order_id
    """
    order_data = {
        'amount': int(amount * 100),
        'currency': 'INR',
        'receipt': receipt,
        'payment_capture': 1
    }
    
    if notes:
        order_data['notes'] = notes
    
    try:
        order = razorpay_client.order.create(data=order_data)
        return order
    except Exception as e:
        print(f"Razorpay order creation failed: {e}")
        return None


def verify_payment_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
) -> bool:
    """
    Verify Razorpay payment signature for security
    
    Returns:
        True if signature is valid
    """
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
        return True
    except Exception as e:
        print(f"Payment signature verification failed: {e}")
        return False


def get_payment_details(payment_id: str) -> Dict[str, Any]:
    """Fetch payment details from Razorpay"""
    try:
        payment = razorpay_client.payment.fetch(payment_id)
        return payment
    except Exception as e:
        print(f"Failed to fetch payment details: {e}")
        return None
