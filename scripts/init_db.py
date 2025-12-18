"""
Initialize the database with tables.
Usage: python -m scripts.init_db
"""
from app.database import engine, Base
from app.models import User, Trade, Holding, PriceCache, HistoricalData


def init_database():
    """Create all database tables."""
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("✅ Database tables created successfully!")
    print("\nCreated tables:")
    print("  - users")
    print("  - trades")
    print("  - holdings")
    print("  - price_cache")
    print("  - historical_data")


if __name__ == "__main__":
    init_database()
