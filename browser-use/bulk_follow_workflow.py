#!/usr/bin/env python3
"""
Bulk Follow Workflow
Orchestrates bulk following operations with different strategies
"""

import argparse
import asyncio
import json


class BulkFollowWorkflow:
    """Workflow for managing bulk following operations"""

    def __init__(self):
        self.follower = TwitterFollower()

    async def follow_by_priority(self, priority: str, max_accounts: int = None):
        """Follow accounts by priority level"""
        print(f"Following accounts with priority: {priority}")
        if max_accounts:
            print(f"Limited to {max_accounts} accounts")

        results = await self.follower.follow_accounts_bulk(
            filter_by_priority=priority, max_accounts=max_accounts
        )
        return results

    async def follow_by_category(self, category: str, max_accounts: int = None):
        """Follow accounts by category"""
        print(f"Following accounts in category: {category}")
        if max_accounts:
            print(f"Limited to {max_accounts} accounts")

        results = await self.follower.follow_accounts_bulk(
            filter_by_category=category, max_accounts=max_accounts
        )
        return results

    async def follow_all_pending(self, max_accounts: int = None):
        """Follow all pending accounts"""
        print("Following all pending accounts")
        if max_accounts:
            print(f"Limited to {max_accounts} accounts")

        results = await self.follower.follow_accounts_bulk(max_accounts=max_accounts)
        return results

    def show_status(self):
        """Show current following status"""
        status = self.follower.get_follow_status()
        print("\n=== Current Following Status ===")
        print(json.dumps(status, indent=2))
        return status

    async def smart_follow(self, max_accounts: int = 10):
        """
        Smart following strategy:
        1. Follow high priority accounts first
        2. Then medium priority
        3. Finally low priority
        """
        print("Starting smart follow strategy...")

        total_results = {"followed": 0, "failed": 0, "skipped": 0, "details": []}

        remaining_accounts = max_accounts

        # Follow high priority first
        if remaining_accounts > 0:
            print("\n--- Following HIGH priority accounts ---")
            results = await self.follow_by_priority("high", remaining_accounts)
            total_results["followed"] += results["followed"]
            total_results["failed"] += results["failed"]
            total_results["skipped"] += results["skipped"]
            total_results["details"].extend(results["details"])
            remaining_accounts -= results["followed"]

        # Follow medium priority next
        if remaining_accounts > 0:
            print("\n--- Following MEDIUM priority accounts ---")
            results = await self.follow_by_priority("medium", remaining_accounts)
            total_results["followed"] += results["followed"]
            total_results["failed"] += results["failed"]
            total_results["skipped"] += results["skipped"]
            total_results["details"].extend(results["details"])
            remaining_accounts -= results["followed"]

        # Follow low priority last
        if remaining_accounts > 0:
            print("\n--- Following LOW priority accounts ---")
            results = await self.follow_by_priority("low", remaining_accounts)
            total_results["followed"] += results["followed"]
            total_results["failed"] += results["failed"]
            total_results["skipped"] += results["skipped"]
            total_results["details"].extend(results["details"])

        print("\n=== Smart Follow Complete ===")
        print(f"Total followed: {total_results['followed']}")
        print(f"Total failed: {total_results['failed']}")
        print(f"Total skipped: {total_results['skipped']}")

        return total_results


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Bulk Twitter Following Tool")
    parser.add_argument(
        "--strategy",
        choices=["priority", "category", "all", "smart", "status"],
        default="status",
        help="Following strategy",
    )
    parser.add_argument(
        "--filter", type=str, help="Priority level (high/medium/low) or category name"
    )
    parser.add_argument("--max", type=int, help="Maximum accounts to follow")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually following",
    )

    args = parser.parse_args()

    workflow = BulkFollowWorkflow()

    if args.strategy == "status":
        workflow.show_status()
        return

    if args.dry_run:
        print("DRY RUN MODE - No accounts will actually be followed")
        status = workflow.show_status()
        return

    try:
        if args.strategy == "priority":
            if not args.filter:
                print(
                    "Error: --filter required for priority strategy (high/medium/low)"
                )
                return
            results = await workflow.follow_by_priority(args.filter, args.max)

        elif args.strategy == "category":
            if not args.filter:
                print("Error: --filter required for category strategy")
                return
            results = await workflow.follow_by_category(args.filter, args.max)

        elif args.strategy == "all":
            results = await workflow.follow_all_pending(args.max)

        elif args.strategy == "smart":
            max_accounts = args.max or 10
            results = await workflow.smart_follow(max_accounts)

        print(
            f"\nFinal Results: {results['followed']} followed, {results['failed']} failed, {results['skipped']} skipped"
        )

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
