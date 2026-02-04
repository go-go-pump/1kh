#!/usr/bin/env python3
"""
Standalone test for realistic metrics generation.
This tests the _generate_realistic_metrics logic directly without dependencies.
"""
import random

def generate_realistic_metrics(task: dict, hypothesis: dict = None) -> dict:
    """
    Generate realistic metrics for local/dev mode.

    These are NOT Claude's estimates - they're simulated results
    that represent what might happen if the task was actually executed.

    Uses small, realistic numbers that accumulate over many cycles.
    """
    # Base metrics - small, realistic increments
    # A typical early-stage business might see:
    # - 5-50 signups per successful marketing task
    # - $10-500 revenue per successful sales task

    task_type = task.get("task_type", "build")
    description = task.get("description", "").lower()

    # Determine likely impact based on task description
    if any(word in description for word in ["marketing", "campaign", "social", "content"]):
        # Marketing tasks: more signups, less direct revenue
        signups = random.randint(5, 30)
        revenue = random.randint(0, 50)
    elif any(word in description for word in ["pricing", "payment", "checkout", "premium"]):
        # Revenue-focused tasks: more revenue, fewer signups
        signups = random.randint(0, 10)
        revenue = random.randint(50, 300)
    elif any(word in description for word in ["referral", "viral", "partnership"]):
        # Growth tasks: balanced
        signups = random.randint(10, 50)
        revenue = random.randint(20, 150)
    elif any(word in description for word in ["onboarding", "retention", "engagement"]):
        # Retention tasks: indirect revenue through retention
        signups = random.randint(0, 5)
        revenue = random.randint(10, 100)
    else:
        # Default: small, safe increments
        signups = random.randint(2, 15)
        revenue = random.randint(10, 75)

    # Add some randomness - not every task succeeds equally
    # 20% chance of exceptional results, 20% chance of poor results
    roll = random.random()
    if roll > 0.8:
        # Exceptional - 2-3x results
        multiplier = random.uniform(2.0, 3.0)
    elif roll < 0.2:
        # Poor results - 0.2-0.5x
        multiplier = random.uniform(0.2, 0.5)
    else:
        # Normal - slight variance
        multiplier = random.uniform(0.8, 1.2)

    return {
        "signups": int(signups * multiplier),
        "revenue": int(revenue * multiplier),
    }


def test_realistic_metrics():
    """Test that metrics are realistic, not Claude's estimates."""
    print("Testing realistic metrics generation...")
    print("=" * 60)

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
            metrics = generate_realistic_metrics(task, {"id": "hyp-1"})

            signups = metrics.get("signups", 0)
            revenue = metrics.get("revenue", 0)

            total_signups += signups
            total_revenue += revenue

            print(f"  Run {i+1}: signups={signups}, revenue=${revenue}")

            # Verify metrics are realistic (not Claude's crazy estimates)
            if signups > 150:  # Max is ~50 * 3 = 150 with exceptional multiplier
                print(f"  ❌ FAIL: signups too high ({signups})")
                all_passed = False
            elif revenue > 900:  # Max is ~300 * 3 = 900 with exceptional multiplier
                print(f"  ❌ FAIL: revenue too high (${revenue})")
                all_passed = False
            else:
                print(f"  ✓ Realistic metrics")

    print("\n" + "=" * 60)
    print(f"Total across all runs: signups={total_signups}, revenue=${total_revenue}")
    print(f"Average per task: signups={total_signups/15:.1f}, revenue=${total_revenue/15:.1f}")

    # Calculate what this would mean over many cycles
    avg_revenue_per_task = total_revenue / 15
    tasks_to_1m = 1_000_000 / avg_revenue_per_task if avg_revenue_per_task > 0 else float('inf')

    print(f"\nAt this rate, reaching $1M would take ~{int(tasks_to_1m)} tasks")
    print(f"With ~15 tasks/cycle, that's ~{int(tasks_to_1m/15)} cycles")

    # Final check - should NOT be anywhere near $1M in one cycle
    if total_revenue > 50000:
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
    exit(test_realistic_metrics())
