#!/usr/bin/env python3
"""
Standalone test for ClaudeExecutor realistic metrics.
Tests that metrics are small and realistic, not Claude's estimates.
"""
import sys
import random

# Add project to path
sys.path.insert(0, '/sessions/amazing-happy-einstein/mnt/1KH')

from core.executor import ClaudeExecutor

# Create a minimal mock dashboard
class MockDashboard:
    def log(self, *args, **kwargs): pass
    def add_event(self, *args, **kwargs): pass

# Create minimal mock conversation manager
class MockConversationManager:
    pass

# Create mock Claude client that returns planning response
class MockClaudeClient:
    class MockContent:
        def __init__(self):
            self.text = """PLAN:
1. Create marketing campaign landing page
2. Set up email capture form
3. Launch social media ads

RESOURCES NEEDED:
- Web hosting
- Email service

BLOCKERS: None

ESTIMATED TIME: 2 days

Note: This could generate $500,000 in revenue if successful!
"""

    class MockResponse:
        def __init__(self):
            self.content = [MockClaudeClient.MockContent()]

    class messages:
        @staticmethod
        def create(**kwargs):
            return MockClaudeClient.MockResponse()


def test_realistic_metrics():
    """Test that metrics are realistic, not Claude's estimates."""
    print("Testing ClaudeExecutor realistic metrics...")
    print("=" * 60)

    # Create executor with mock dependencies
    executor = ClaudeExecutor(
        project_path="/tmp",
        dashboard=MockDashboard(),
        conversation_manager=MockConversationManager(),
        claude_client=MockClaudeClient(),
        simulate_metrics=True,  # Use realistic mock metrics
    )

    # Test different task types
    test_cases = [
        {"description": "Create marketing campaign for product launch", "task_type": "build"},
        {"description": "Implement pricing page with premium tier", "task_type": "build"},
        {"description": "Launch referral program for viral growth", "task_type": "build"},
        {"description": "Improve onboarding retention flow", "task_type": "build"},
        {"description": "Generic task without keywords", "task_type": "build"},
    ]

    all_passed = True
    total_signups = 0
    total_revenue = 0

    for task in test_cases:
        print(f"\nTask: {task['description'][:50]}...")

        # Run multiple times to test variance
        for i in range(3):
            result = executor.execute(task, {"id": "hyp-1", "description": "Test hypothesis"})

            signups = result.metrics_delta.get("signups", 0)
            revenue = result.metrics_delta.get("revenue", 0)

            total_signups += signups
            total_revenue += revenue

            print(f"  Run {i+1}: signups={signups}, revenue=${revenue}")

            # Verify metrics are realistic (not Claude's crazy estimates)
            if signups > 100:
                print(f"  ❌ FAIL: signups too high ({signups})")
                all_passed = False
            elif revenue > 1000:
                print(f"  ❌ FAIL: revenue too high (${revenue})")
                all_passed = False
            else:
                print(f"  ✓ Realistic metrics")

    print("\n" + "=" * 60)
    print(f"Total across all runs: signups={total_signups}, revenue=${total_revenue}")
    print(f"Average per task: signups={total_signups/15:.1f}, revenue=${total_revenue/15:.1f}")

    # Final check - should NOT be anywhere near $1M
    if total_revenue > 10000:
        print(f"\n❌ FAIL: Total revenue too high - would hit $1M too fast")
        all_passed = False
    else:
        print(f"\n✓ Total revenue reasonable - won't hit $1M in one cycle")

    if all_passed:
        print("\n✅ ALL TESTS PASSED - Metrics are realistic!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(test_realistic_metrics())
