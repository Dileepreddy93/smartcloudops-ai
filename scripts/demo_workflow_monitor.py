#!/usr/bin/env python3
"""
🎯 SmartCloudOps AI - Workflow Monitor Demo
==========================================

This script demonstrates the workflow monitoring system capabilities
without requiring actual GitHub API access. It shows:

1. How the system analyzes failure patterns
2. How fixes are applied
3. How the monitoring loop works
4. How reports are generated

Usage:
    python3 scripts/demo_workflow_monitor.py
"""


import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))


def demo_failure_analysis():
    """Demonstrate failure pattern analysis"""
    print("🔍 Demo: Failure Pattern Analysis")
    print("=" * 50)

    # Import the WorkflowMonitor class
    from auto_workflow_fixer import WorkflowMonitor

    # Create a monitor instance (we won't use the API)
    monitor = WorkflowMonitor("demo_owner", "demo_repo", "demo_token")

    # Sample failure logs
    failure_logs = [
        {
            "name": "Dependency Failure",
            "logs": "ModuleNotFoundError: No module named 'requests'\npip install requests",
        },
        {
            "name": "Test Failure",
            "logs": "FAILED test_example.py::test_function\nAssertionError: expected 2, got 1",
        },
        {
            "name": "Linting Failure",
            "logs": "flake8 found 5 errors\nblack would reformat 3 files",
        },
        {
            "name": "Security Failure",
            "logs": "bandit found 2 security issues\nsafety check failed",
        },
        {
            "name": "Build Failure",
            "logs": "docker build failed\nBuild error in Dockerfile",
        },
    ]

    for failure in failure_logs:
        print(f"\n📋 Analyzing: {failure['name']}")
        issues = monitor.analyze_failure(failure["logs"])
        print(f"   Issues detected: {len(issues)}")
        for issue in issues:
            print(f"   • {issue}")

    print("\n✅ Failure analysis demo completed!")


def demo_fix_application():
    """Demonstrate fix application"""
    print("\n🔧 Demo: Fix Application")
    print("=" * 50)

    from auto_workflow_fixer import WorkflowMonitor

    monitor = WorkflowMonitor("demo_owner", "demo_repo", "demo_token")

    # Create a test file to demonstrate fixes
    test_file = "demo_test.py"
    with open(test_file, "w") as f:
        f.write("import os\nprint('hello world')\n")

    print("📝 Created test file for demonstration")

    # Demonstrate different fix types
    fix_types = [
        ("Dependency Issues", monitor.fix_dependency_issues),
        ("Test Issues", monitor.fix_test_issues),
        ("Linting Issues", monitor.fix_linting_issues),
        ("Security Issues", monitor.fix_security_issues),
    ]

    for fix_name, fix_function in fix_types:
        print(f"\n🔧 Applying {fix_name}...")
        try:
            result = fix_function()
            print(f"   ✅ {fix_name}: {'Success' if result else 'Failed'}")
        except Exception as e:
            print(f"   ❌ {fix_name}: Error - {e}")

    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)

    print(f"\n📊 Fixes applied: {monitor.fixes_applied}")
    print("✅ Fix application demo completed!")


def demo_monitoring_loop():
    """Demonstrate the monitoring loop"""
    print("\n🔄 Demo: Monitoring Loop")
    print("=" * 50)

    from auto_workflow_fixer import WorkflowMonitor

    monitor = WorkflowMonitor("demo_owner", "demo_repo", "demo_token")

    # Simulate monitoring statistics
    stats = {
        "checks": 0,
        "fixes_applied": 0,
        "workflows_fixed": 0,
        "start_time": datetime.now(),
    }

    print("🚀 Starting simulated monitoring loop...")
    print("   (This simulates 5 monitoring cycles)")

    for cycle in range(1, 6):
        stats["checks"] += 1
        print(f"\n🔄 Cycle {cycle}/5")
        print(f"   📊 Checks performed: {stats['checks']}")

        # Simulate different scenarios
        if cycle == 2:
            print("   ❌ Detected failed workflow")
            print("   🔧 Applying dependency fix...")
            stats["fixes_applied"] += 1
            stats["workflows_fixed"] += 1
            print("   ✅ Fix applied successfully")
        elif cycle == 4:
            print("   ❌ Detected linting issues")
            print("   🔧 Applying linting fix...")
            stats["fixes_applied"] += 1
            stats["workflows_fixed"] += 1
            print("   ✅ Fix applied successfully")
        else:
            print("   ✅ All workflows passing")

        # Simulate wait time
        time.sleep(1)

    runtime = datetime.now() - stats["start_time"]
    print("\n📊 Final Statistics:")
    print(f"   Runtime: {runtime}")
    print(f"   Checks performed: {stats['checks']}")
    print(f"   Fixes applied: {stats['fixes_applied']}")
    print(f"   Workflows fixed: {stats['workflows_fixed']}")

    print("✅ Monitoring loop demo completed!")


def demo_report_generation():
    """Demonstrate report generation"""
    print("\n📊 Demo: Report Generation")
    print("=" * 50)

    from auto_workflow_fixer import WorkflowMonitor

    monitor = WorkflowMonitor("demo_owner", "demo_repo", "demo_token")

    # Simulate some fixes being applied
    monitor.fixes_applied = ["dependency_issues", "test_issues", "linting_issues"]

    # Generate report
    report = monitor.generate_report()

    print("📋 Generated monitoring report:")
    print(json.dumps(report, indent=2))

    # Save report to file
    report_file = "demo_workflow_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Report saved to: {report_file}")
    print("✅ Report generation demo completed!")


def demo_continuous_monitor():
    """Demonstrate continuous monitoring setup"""
    print("\n🔄 Demo: Continuous Monitor Setup")
    print("=" * 50)

    try:
        from monitor_workflows import ContinuousWorkflowMonitor

        # Create continuous monitor
        monitor = ContinuousWorkflowMonitor(interval=5)  # 5 seconds for demo

        print("✅ ContinuousWorkflowMonitor initialized")
        print(f"   Monitoring interval: {monitor.interval} seconds")
        print(f"   Running status: {monitor.running}")
        print(f"   Statistics tracking: {len(monitor.stats)} metrics")

        print("\n📊 Available statistics:")
        for key, value in monitor.stats.items():
            print(f"   • {key}: {value}")

        print("\n💡 To run continuous monitoring:")
        print("   python3 scripts/monitor_workflows.py --continuous")
        print("   python3 scripts/monitor_workflows.py --continuous --interval 30")

    except ImportError as e:
        print(f"❌ Could not import ContinuousWorkflowMonitor: {e}")

    print("✅ Continuous monitor demo completed!")


def main():
    """Main demonstration function"""
    print("🎯 SmartCloudOps AI - Workflow Monitor Demo")
    print("=" * 60)
    print("This demo shows the capabilities of the workflow monitoring system")
    print("without requiring actual GitHub API access.")
    print("")

    # Run all demos
    demos = [
        ("Failure Analysis", demo_failure_analysis),
        ("Fix Application", demo_fix_application),
        ("Monitoring Loop", demo_monitoring_loop),
        ("Report Generation", demo_report_generation),
        ("Continuous Monitor", demo_continuous_monitor),
    ]

    for demo_name, demo_function in demos:
        try:
            demo_function()
        except Exception as e:
            print(f"❌ Demo '{demo_name}' failed: {e}")

    print("\n" + "=" * 60)
    print("🎉 All demos completed!")
    print("")
    print("📚 Next Steps:")
    print("   1. Set up your GitHub token: export GITHUB_TOKEN=your_token")
    print("   2. Run single check: python3 scripts/monitor_workflows.py")
    print("   3. Run continuous monitoring: python3 scripts/monitor_workflows.py --continuous")
    print("   4. View the full guide: WORKFLOW_MONITORING_GUIDE.md")
    print("")
    print("🚀 Your workflow monitoring system is ready to use!")


if __name__ == "__main__":
    main()
