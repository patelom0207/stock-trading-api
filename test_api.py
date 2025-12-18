"""
Simple test script to verify API is working correctly.
Run this after setting up the API to ensure everything works.

Usage: python test_api.py YOUR_API_KEY
"""
import sys
import requests
from typing import Optional


def test_api(api_key: str, base_url: str = "http://localhost:8000/api"):
    """Test all API endpoints."""
    headers = {"Authorization": f"Bearer {api_key}"}

    print("🧪 Testing Stock Trading API\n")
    print(f"Base URL: {base_url}")
    print(f"API Key: {api_key[:10]}...\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Health Check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url.replace('/api', '')}/health")
        response.raise_for_status()
        print("   ✅ Health check passed\n")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Health check failed: {e}\n")
        tests_failed += 1

    # Test 2: Price Endpoint
    print("2. Testing /price endpoint...")
    try:
        response = requests.get(f"{base_url}/price", params={"symbol": "AAPL"}, headers=headers)
        response.raise_for_status()
        data = response.json()
        assert "symbol" in data
        assert "price" in data
        assert "market" in data
        print(f"   ✅ Price endpoint passed")
        print(f"   AAPL Price: ${data['price']:.2f}\n")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Price endpoint failed: {e}\n")
        tests_failed += 1

    # Test 3: Balance Endpoint
    print("3. Testing /balance endpoint...")
    try:
        response = requests.get(f"{base_url}/balance", headers=headers)
        response.raise_for_status()
        data = response.json()
        assert "balance" in data
        initial_balance = data['balance']
        print(f"   ✅ Balance endpoint passed")
        print(f"   Balance: ${initial_balance:,.2f}\n")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Balance endpoint failed: {e}\n")
        tests_failed += 1
        return

    # Test 4: Trade Endpoint (Buy)
    print("4. Testing /trade endpoint (BUY)...")
    try:
        trade_data = {"symbol": "AAPL", "side": "buy", "quantity": 1}
        response = requests.post(f"{base_url}/trade", json=trade_data, headers=headers)
        response.raise_for_status()
        data = response.json()
        assert data['status'] == 'success'
        print(f"   ✅ Buy trade passed")
        print(f"   Bought 1 share at ${data['trade']['price']:.2f}\n")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Buy trade failed: {e}\n")
        tests_failed += 1

    # Test 5: Holdings Endpoint
    print("5. Testing /holdings endpoint...")
    try:
        response = requests.get(f"{base_url}/holdings", headers=headers)
        response.raise_for_status()
        data = response.json()
        assert "holdings" in data
        assert "total_portfolio_value" in data
        assert len(data['holdings']) > 0
        print(f"   ✅ Holdings endpoint passed")
        print(f"   Holdings: {len(data['holdings'])} position(s)")
        print(f"   Portfolio Value: ${data['total_portfolio_value']:,.2f}\n")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Holdings endpoint failed: {e}\n")
        tests_failed += 1

    # Test 6: Trade Endpoint (Sell)
    print("6. Testing /trade endpoint (SELL)...")
    try:
        trade_data = {"symbol": "AAPL", "side": "sell", "quantity": 1}
        response = requests.post(f"{base_url}/trade", json=trade_data, headers=headers)
        response.raise_for_status()
        data = response.json()
        assert data['status'] == 'success'
        print(f"   ✅ Sell trade passed")
        print(f"   Sold 1 share at ${data['trade']['price']:.2f}\n")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Sell trade failed: {e}\n")
        tests_failed += 1

    # Test 7: History Endpoint
    print("7. Testing /history endpoint...")
    try:
        params = {"symbol": "AAPL", "resolution": "1d", "limit": 5}
        response = requests.get(f"{base_url}/history", params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        assert "history" in data
        assert len(data['history']) > 0
        print(f"   ✅ History endpoint passed")
        print(f"   Retrieved {data['count']} candles\n")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ History endpoint failed: {e}\n")
        tests_failed += 1

    # Test 8: Market Status Endpoint
    print("8. Testing /market_status endpoint...")
    try:
        response = requests.get(f"{base_url}/market_status", params={"symbol": "AAPL"}, headers=headers)
        response.raise_for_status()
        data = response.json()
        assert "isOpen" in data
        print(f"   ✅ Market status passed")
        print(f"   Market Open: {data['isOpen']}\n")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Market status failed: {e}\n")
        tests_failed += 1

    # Summary
    print("=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests:  {tests_passed + tests_failed}")

    if tests_failed == 0:
        print("\n🎉 All tests passed! Your API is working correctly!")
        return True
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py YOUR_API_KEY [BASE_URL]")
        print("\nExample:")
        print("  python test_api.py abc123def456")
        print("  python test_api.py abc123def456 http://localhost:8000/api")
        sys.exit(1)

    api_key = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000/api"

    try:
        success = test_api(api_key, base_url)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
