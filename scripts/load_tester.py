#!/usr/bin/env python3
"""
SmartCloudOps AI - Production Load Testing
==========================================

Comprehensive load testing to validate 10-50 user capacity.
Identifies performance bottlenecks before production deployment.
"""

import asyncio
import json
import logging
import os
import statistics
import time
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
import psutil


class LoadTester:
    """Production load testing for SmartCloudOps AI"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.api_key = os.getenv(
            "TEST_API_KEY", "sk-readonly-demo-key-12345678901234567890"
        )
        self.results = []
        self.setup_logging()

    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(
                    f'load_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    async def make_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str = "GET",
        data: Dict = None,
    ) -> Dict[str, Any]:
        """Make an async HTTP request and measure performance"""
        headers = {"X-API-Key": self.api_key}
        if data:
            headers["Content-Type"] = "application/json"

        start_time = time.time()
        try:
            if method.upper() == "GET":
                async with session.get(
                    f"{self.base_url}{endpoint}", headers=headers
                ) as response:
                    response_time = time.time() - start_time
                    content = await response.text()
                    return {
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status,
                        "response_time": response_time,
                        "success": 200 <= response.status < 300,
                        "content_length": len(content),
                        "timestamp": datetime.now().isoformat(),
                    }
            else:
                async with session.post(
                    f"{self.base_url}{endpoint}", headers=headers, json=data
                ) as response:
                    response_time = time.time() - start_time
                    content = await response.text()
                    return {
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status,
                        "response_time": response_time,
                        "success": 200 <= response.status < 300,
                        "content_length": len(content),
                        "timestamp": datetime.now().isoformat(),
                    }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time": response_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def simulate_user_session(
        self, session: aiohttp.ClientSession, user_id: int
    ) -> List[Dict[str, Any]]:
        """Simulate a realistic user session"""
        session_results = []

        # Typical user workflow
        workflows = [
            # Health check
            {"endpoint": "/health", "method": "GET"},
            # Check system status
            {"endpoint": "/status", "method": "GET"},
            # Get ML metrics
            {"endpoint": "/ml/health", "method": "GET"},
            # Make ML prediction
            {
                "endpoint": "/ml/predict",
                "method": "POST",
                "data": {
                    "metrics": {
                        "cpu_usage": 75.5,
                        "memory_usage": 60.2,
                        "disk_usage": 45.0,
                        "load_1m": 1.5,
                    }
                },
            },
            # Chat interaction (if available)
            {
                "endpoint": "/chat",
                "method": "POST",
                "data": {"message": "What is the current system status?"},
            },
        ]

        for step in workflows:
            result = await self.make_request(
                session, step["endpoint"], step.get("method", "GET"), step.get("data")
            )
            result["user_id"] = user_id
            result["step"] = step["endpoint"]
            session_results.append(result)

            # Small delay between requests (realistic user behavior)
            await asyncio.sleep(0.5)

        return session_results

    async def run_concurrent_users(self, num_users: int, duration_seconds: int = 60):
        """Run load test with concurrent users"""
        self.logger.info(
            f"Starting load test: {num_users} concurrent users for {duration_seconds}s"
        )

        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            start_time = time.time()
            all_tasks = []

            # Start monitoring system resources
            resource_monitor = asyncio.create_task(
                self.monitor_system_resources(duration_seconds)
            )

            while time.time() - start_time < duration_seconds:
                # Create batch of concurrent users
                batch_tasks = []
                for user_id in range(num_users):
                    task = asyncio.create_task(
                        self.simulate_user_session(session, user_id)
                    )
                    batch_tasks.append(task)

                # Wait for batch to complete
                batch_results = await asyncio.gather(
                    *batch_tasks, return_exceptions=True
                )

                # Process results
                for result in batch_results:
                    if isinstance(result, list):
                        self.results.extend(result)
                    elif isinstance(result, Exception):
                        self.logger.error(f"User session failed: {result}")

                # Small delay before next batch
                await asyncio.sleep(1)

            # Stop resource monitoring
            resource_monitor.cancel()

        self.logger.info(f"Load test completed. Total requests: {len(self.results)}")

    async def monitor_system_resources(self, duration_seconds: int):
        """Monitor system resources during load test"""
        resource_data = []
        start_time = time.time()

        try:
            while time.time() - start_time < duration_seconds:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                resource_data.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_available_gb": memory.available / (1024**3),
                    }
                )

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

        # Save resource data
        with open(
            f'resource_usage_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', "w"
        ) as f:
            json.dump(resource_data, f, indent=2)

        self.logger.info(
            f"Resource monitoring data saved ({len(resource_data)} samples)"
        )

    def analyze_results(self) -> Dict [str, Any]:
        """Analyze load test results"""
        if not self.results:
            return {}

        successful_requests = [r for r in self.results if r["success"]]
        failed_requests = [r for r in self.results if not r["success"]]

        response_times = [r["response_time"] for r in successful_requests]

        # Calculate statistics
        stats = {
            "total_requests": len(self.results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": len(successful_requests) / len(self.results) * 100,
            "response_times": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "mean": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0,
                "p95": (
                    statistics.quantiles(response_times, n=20)[18]
                    if len(response_times) > 20
                    else 0
                ),
                "p99": (
                    statistics.quantiles(response_times, n=100)[98]
                    if len(response_times) > 100
                    else 0
                ),
            },
            "requests_per_second": len(self.results)
            / (max([r["timestamp"] for r in self.results]) if self.results else 1),
            "endpoint_performance": {},
        }

        # Analyze by endpoint
        endpoints = set(r["endpoint"] for r in self.results)
        for endpoint in endpoints:
            endpoint_results = [r for r in self.results if r["endpoint"] == endpoint]
            endpoint_successful = [r for r in endpoint_results if r["success"]]
            endpoint_times = [r["response_time"] for r in endpoint_successful]

            stats["endpoint_performance"][endpoint] = {
                "total_requests": len(endpoint_results),
                "successful_requests": len(endpoint_successful),
                "success_rate": len(endpoint_successful) / len(endpoint_results) * 100,
                "avg_response_time": (
                    statistics.mean(endpoint_times) if endpoint_times else 0
                ),
                "max_response_time": max(endpoint_times) if endpoint_times else 0,
            }

        return stats

    def generate_report(self, stats: Dict[str, Any]):
        """Generate comprehensive load test report"""
        report = f"""
🚀 SmartCloudOps AI - Load Test Report
=====================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 OVERALL PERFORMANCE
----------------------
Total Requests: {stats['total_requests']:,}
Successful: {stats['successful_requests']:,} ({stats['success_rate']:.1f}%)
Failed: {stats['failed_requests']:,}

⏱️  RESPONSE TIMES
------------------
Average: {stats['response_times']['mean']*1000:.0f}ms
Median: {stats['response_times']['median']*1000:.0f}ms
95th Percentile: {stats['response_times']['p95']*1000:.0f}ms
99th Percentile: {stats['response_times']['p99']*1000:.0f}ms
Min: {stats['response_times']['min']*1000:.0f}ms
Max: {stats['response_times']['max']*1000:.0f}ms

📈 THROUGHPUT
-------------
Requests/Second: {stats['requests_per_second']:.1f}

🎯 ENDPOINT PERFORMANCE
-----------------------"""

        for endpoint, perf in stats["endpoint_performance"].items():
            report += f"""
{endpoint}:
  Requests: {perf['total_requests']:,}
  Success Rate: {perf['success_rate']:.1f}%
  Avg Response: {perf['avg_response_time']*1000:.0f}ms
  Max Response: {perf['max_response_time']*1000:.0f}ms"""

        # Performance recommendations
        report += "\n\n🔍 PERFORMANCE ANALYSIS\n"
        report += "-" * 23 + "\n"

        if stats["success_rate"] < 95:
            report += "⚠️  WARNING: Success rate below 95% - investigate error causes\n"

        if stats["response_times"]["p95"] > 5:
            report += (
                "⚠️  WARNING: 95th percentile response time > 5s - performance issue\n"
            )

        if stats["response_times"]["mean"] > 2:
            report += "⚠️  WARNING: Average response time > 2s - optimization needed\n"

        if stats["requests_per_second"] < 10:
            report += "⚠️  WARNING: Low throughput < 10 RPS - scalability concern\n"

        # Recommendations
        report += "\n💡 RECOMMENDATIONS\n"
        report += "------------------\n"

        if stats["response_times"]["mean"] > 1:
            report += "• Consider implementing response caching\n"
            report += "• Optimize database queries\n"
            report += "• Add connection pooling\n"

        if stats["requests_per_second"] < 50:
            report += "• Upgrade to larger instance types\n"
            report += "• Implement load balancing\n"
            report += "• Consider horizontal scaling\n"

        return report

    def save_detailed_results(self):
        """Save detailed results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"load_test_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)

        self.logger.info(f"Detailed results saved to {filename}")


async def main():
    """Main load testing function"""
    import sys

    # Configuration
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    num_users = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60

    print("🚀 Starting Load Test")
    print(f"Target: {base_url}")
    print(f"Concurrent Users: {num_users}")
    print(f"Duration: {duration}s")
    print("-" * 50)

    # Run load test
    tester = LoadTester(base_url)
    await tester.run_concurrent_users(num_users, duration)

    # Analyze results
    stats = tester.analyze_results()
    report = tester.generate_report(stats)

    # Display results
    print(report)

    # Save detailed results
    tester.save_detailed_results()

    # Return exit code based on performance
    if stats["success_rate"] < 95 or stats["response_times"]["p95"] > 5:
        print("\n❌ Load test FAILED - Performance issues detected")
        return 1
    else:
        print("\n✅ Load test PASSED - Performance acceptable")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
