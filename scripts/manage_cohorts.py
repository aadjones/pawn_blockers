#!/usr/bin/env python3
"""Cohort management script - replaces generate_demo_data.py with flexible cohort system."""

import argparse
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.cohorts import CohortConfig, CohortManager, CohortType


def main():
    parser = argparse.ArgumentParser(description="Manage cohort-based chess game analysis")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List cohorts
    list_parser = subparsers.add_parser("list", help="List available cohorts")
    list_parser.add_argument("--tag", help="Filter by tag")

    # Process cohorts
    process_parser = subparsers.add_parser("process", help="Process cohort data")
    process_parser.add_argument("cohorts", nargs="*", help="Cohort IDs to process (default: all)")
    process_parser.add_argument("--tag", help="Process cohorts with this tag")
    process_parser.add_argument("--force", action="store_true", help="Force refresh cached data")
    process_parser.add_argument("--token", "-t", help="Lichess API token for higher rate limits")

    # Compare cohorts
    compare_parser = subparsers.add_parser("compare", help="Compare two cohorts")
    compare_parser.add_argument("cohort1", help="First cohort ID")
    compare_parser.add_argument("cohort2", help="Second cohort ID")
    compare_parser.add_argument("--token", "-t", help="Lichess API token")

    # Status
    status_parser = subparsers.add_parser("status", help="Show cohort system status")

    # Create cohort
    create_parser = subparsers.add_parser("create", help="Create a new cohort")
    create_parser.add_argument("--id", required=True, help="Cohort ID")
    create_parser.add_argument("--name", required=True, help="Cohort name")
    create_parser.add_argument("--description", required=True, help="Description")
    create_parser.add_argument(
        "--type", choices=["lichess_user", "lichess_human_sample", "pgn_files"], default="lichess_user"
    )
    create_parser.add_argument("--username", help="Lichess username (for lichess_user type)")
    create_parser.add_argument("--rating-min", type=int, default=1800, help="Min rating for human_sample type")
    create_parser.add_argument("--rating-max", type=int, default=2200, help="Max rating for human_sample type")
    create_parser.add_argument("--players-count", type=int, default=15, help="Number of players to sample")
    create_parser.add_argument("--games", type=int, default=200, help="Target number of games")
    create_parser.add_argument("--tags", nargs="*", default=[], help="Tags for this cohort")

    # Delete cohort data
    delete_parser = subparsers.add_parser("delete", help="Delete cohort data")
    delete_parser.add_argument("cohort_id", help="Cohort ID to delete data for")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    # Initialize manager
    manager = CohortManager(lichess_token=getattr(args, "token", None))

    if args.command == "list":
        cohorts = manager.list_available_cohorts()
        if args.tag:
            cohorts = [c for c in cohorts if args.tag in c.tags]

        if not cohorts:
            print("No cohorts found")
            return 0

        print(f"{'ID':<20} {'Name':<30} {'Type':<15} {'Target':<8} {'Tags'}")
        print("-" * 80)
        for cohort in sorted(cohorts, key=lambda c: c.priority, reverse=True):
            tags_str = ", ".join(cohort.tags[:3])  # Show first 3 tags
            if len(cohort.tags) > 3:
                tags_str += "..."
            print(f"{cohort.id:<20} {cohort.name:<30} {cohort.type.value:<15} {cohort.target_games:<8} {tags_str}")

    elif args.command == "process":
        if args.cohorts:
            # Process specific cohorts
            for cohort_id in args.cohorts:
                print(f"\n{'='*60}")
                df = manager.process_cohort(cohort_id, args.force)
                if df is not None and not df.empty:
                    summary = manager.get_cohort_summary(cohort_id)
                    print_cohort_summary(cohort_id, summary)

        elif args.tag:
            # Process cohorts by tag
            results = manager.process_cohorts_by_tag(args.tag, args.force)
            for cohort_id in results:
                summary = manager.get_cohort_summary(cohort_id)
                print_cohort_summary(cohort_id, summary)
        else:
            # Process all cohorts
            results = manager.process_all_cohorts(args.force)
            print(f"\n🎯 Processed {len(results)} cohorts")
            for cohort_id in results:
                summary = manager.get_cohort_summary(cohort_id)
                print_cohort_summary(cohort_id, summary)

    elif args.command == "compare":
        comparison = manager.compare_cohorts(args.cohort1, args.cohort2)
        if "error" in comparison:
            print(f"❌ {comparison['error']}")
            return 1

        print(f"\n📊 Comparing {args.cohort1} vs {args.cohort2}")
        print(f"Total games: {comparison['n_games']}")
        print(f"{args.cohort1}: {comparison['group1_games']} games")
        print(f"{args.cohort2}: {comparison['group2_games']} games")

        if "spbts" in comparison["metrics"]:
            spbts = comparison["metrics"]["spbts"]
            print(f"\nSPBTS Comparison:")
            print(f"  {args.cohort1}: median={spbts['group1_median']:.3f}, mean={spbts['group1_mean']:.3f}")
            print(f"  {args.cohort2}: median={spbts['group2_median']:.3f}, mean={spbts['group2_mean']:.3f}")
            print(f"  Difference: {spbts['difference']:+.3f}")

    elif args.command == "status":
        status = manager.get_status()
        print(f"📊 Cohort System Status")
        print(f"Total cohorts: {status['total_cohorts']}")
        print(f"Active cohorts: {status['active_cohorts']}")
        print(f"Total games: {status['total_games']}")

        print(f"\nCohort Details:")
        for cohort in status["cohorts"]:
            progress = cohort["progress"]
            status_icon = "✅" if progress >= 80 else "🔄" if progress > 0 else "⏸️"
            print(
                f"  {status_icon} {cohort['id']}: {cohort['collected_games']}/{cohort['target_games']} games ({progress:.1f}%)"
            )

    elif args.command == "create":
        if args.type == "lichess_user" and not args.username:
            print("❌ --username required for lichess_user type")
            return 1

        data_sources = []
        if args.type == "lichess_user":
            data_sources.append({"type": "lichess_user", "username": args.username, "max_games": args.games})
        elif args.type == "lichess_human_sample":
            data_sources.append(
                {
                    "type": "lichess_human_sample",
                    "rating_min": args.rating_min,
                    "rating_max": args.rating_max,
                    "players_count": args.players_count,
                    "max_games": args.games,
                }
            )

        cohort = CohortConfig(
            id=args.id,
            name=args.name,
            description=args.description,
            type=CohortType(args.type),
            data_sources=data_sources,
            target_games=args.games,
            tags=args.tags,
        )

        manager.create_cohort(cohort)
        print(f"✅ Created cohort '{args.id}'")

    elif args.command == "delete":
        deleted_files = manager.delete_cohort_data(args.cohort_id)
        if deleted_files:
            print(f"✅ Deleted data for cohort '{args.cohort_id}':")
            for file_path in deleted_files:
                print(f"   - {file_path}")
        else:
            print(f"ℹ️  No data found for cohort '{args.cohort_id}'")

    return 0


def print_cohort_summary(cohort_id: str, summary: dict):
    """Print a formatted cohort summary."""
    if "error" in summary:
        print(f"❌ {cohort_id}: {summary['error']}")
        return

    print(f"\n📈 {cohort_id} Summary:")
    print(f"   Games: {summary['total_games']}")
    print(f"   Players: {summary['unique_players']}")
    print(f"   Avg plies: {summary['avg_plies_analyzed']:.1f}")

    spbts = summary["spbts_stats"]
    print(f"   SPBTS - White: {spbts['white_median']:.3f}, Black: {spbts['black_median']:.3f}")
    if spbts["f_file_mean"] is not None:
        print(f"   F-file blocking: {spbts['f_file_mean']:.3f}")


if __name__ == "__main__":
    exit(main())
