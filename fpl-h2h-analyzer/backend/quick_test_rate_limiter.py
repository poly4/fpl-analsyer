#!/usr/bin/env python3
"""Quick test to verify rate limiter is integrated."""
import asyncio
import aiohttp
import time

async def quick_test():
    """Quick test of rate limiter."""
    print("🚀 Quick Rate Limiter Test")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Make 20 rapid requests
        print("\n📊 Making 20 rapid requests...")
        results = []
        
        for i in range(20):
            start = time.time()
            try:
                async with session.get("http://localhost:8000/api/gameweek/current") as resp:
                    status = resp.status
                    results.append({
                        "request": i + 1,
                        "status": status,
                        "time": time.time() - start
                    })
            except Exception as e:
                results.append({
                    "request": i + 1,
                    "status": "error",
                    "error": str(e)
                })
        
        # Show results
        success = sum(1 for r in results if r.get("status") == 200)
        rate_limited = sum(1 for r in results if r.get("status") == 429)
        errors = sum(1 for r in results if r.get("status") not in [200, 429])
        
        print(f"\nResults:")
        print(f"✅ Successful: {success}")
        print(f"⏳ Rate limited (429): {rate_limited}")
        print(f"❌ Errors: {errors}")
        
        # Test 2: Check metrics endpoint
        print("\n📊 Checking rate limiter metrics...")
        try:
            async with session.get("http://localhost:8000/api/rate-limiter/metrics") as resp:
                if resp.status == 200:
                    metrics = await resp.json()
                    print(f"✅ Metrics endpoint working!")
                    print(f"   Available tokens: {metrics.get('available_tokens', 'N/A')}")
                    print(f"   Total requests: {metrics.get('total_requests', 'N/A')}")
                else:
                    print(f"❌ Metrics endpoint returned: {resp.status}")
        except Exception as e:
            print(f"❌ Error accessing metrics: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())