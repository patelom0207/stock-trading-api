"""
Reset a user's balance and clear their trades/holdings.
Usage: python -m scripts.reset_user <api_key>
"""
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Trade, Holding
from app.config import settings


def reset_user(api_key: str):
    """Reset user's account to initial state."""
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.api_key == api_key).first()

        if not user:
            print(f"❌ User not found with API key: {api_key}")
            sys.exit(1)

        # Delete all trades
        trades_deleted = db.query(Trade).filter(Trade.user_id == user.id).delete()

        # Delete all holdings
        holdings_deleted = db.query(Holding).filter(Holding.user_id == user.id).delete()

        # Reset balance
        user.balance = settings.DEFAULT_BALANCE

        db.commit()

        print(f"\n✅ User account reset successfully!")
        print(f"User ID: {user.id}")
        print(f"Trades deleted: {trades_deleted}")
        print(f"Holdings deleted: {holdings_deleted}")
        print(f"Balance reset to: ${user.balance:,.2f}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error resetting user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.reset_user <api_key>")
        sys.exit(1)

    reset_user(sys.argv[1])
