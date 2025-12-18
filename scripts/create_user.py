"""
Script to create a new user with an API key.
Usage: python -m scripts.create_user
"""
import secrets
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User
from app.config import settings


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


def create_user(balance: float = None) -> tuple[str, float]:
    """
    Create a new user with a unique API key.

    Args:
        balance: Initial balance (defaults to DEFAULT_BALANCE from settings)

    Returns:
        Tuple of (api_key, balance)
    """
    if balance is None:
        balance = settings.DEFAULT_BALANCE

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        api_key = generate_api_key()

        # Ensure unique API key
        while db.query(User).filter(User.api_key == api_key).first():
            api_key = generate_api_key()

        user = User(api_key=api_key, balance=balance)
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"\n✅ User created successfully!")
        print(f"User ID: {user.id}")
        print(f"API Key: {api_key}")
        print(f"Initial Balance: ${balance:,.2f}")
        print(f"\nStore this API key securely - it won't be shown again!")
        print(f"\nUsage in requests:")
        print(f'Authorization: Bearer {api_key}')

        return api_key, balance

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating user: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a new trading API user")
    parser.add_argument(
        "--balance",
        type=float,
        default=None,
        help=f"Initial balance (default: ${settings.DEFAULT_BALANCE:,.2f})"
    )

    args = parser.parse_args()
    create_user(balance=args.balance)
