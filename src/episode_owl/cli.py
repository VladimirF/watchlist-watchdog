"""Command-line interface for Episode Owl."""

import sys
from pathlib import Path

from . import api, config, notifications, search, storage, tracker


def print_header():
    """Print the application header."""
    print("\n" + "="*60)
    print("  Episode Owl - TV Show & Anime Tracker")
    print("="*60 + "\n")


def add_show_interactive(paths: dict[str, Path], cfg: config.Config) -> None:
    """Add a show through interactive search.

    Args:
        paths: Dictionary of file paths
        cfg: Configuration object
    """
    query = input("Enter show name to search: ").strip()

    if not query:
        print("Error: Search query cannot be empty")
        return

    print(f"\nSearching for '{query}'...")

    try:
        # Search TVMaze API
        results = api.search_shows(query, timeout=cfg.api_timeout)

        if not results:
            print("No shows found. Try a different search term.")
            return

        # Rank and display results
        ranked = search.rank_search_results(query, results, limit=5)

        print(f"\nFound {len(ranked)} matches:\n")
        for i, result in enumerate(ranked, 1):
            print(search.format_search_result(result, i))

        # Get user selection
        print("\nEnter number to add show (or 0 to cancel): ", end="")
        try:
            choice = int(input().strip())
        except ValueError:
            print("Invalid input. Cancelled.")
            return

        if choice < 1 or choice > len(ranked):
            print("Cancelled.")
            return

        selected = ranked[choice - 1]

        # Fetch episodes to set initial state
        print(f"\nFetching episodes for '{selected.name}'...")
        episodes_data = api.get_show_episodes(
            selected.show_id,
            timeout=cfg.api_timeout,
            retry_attempts=cfg.retry_attempts
        )

        # Parse and filter episodes
        episodes = [tracker.parse_episode_from_api(ep) for ep in episodes_data]
        aired_episodes = tracker.filter_aired_episodes(episodes)

        # Get latest episode for initial state
        latest = tracker.get_latest_episode(aired_episodes)

        # Create show dictionary
        show_dict = tracker.create_show_dict(
            selected.show_id,
            selected.name,
            latest
        )

        # Save to storage
        storage.add_show(show_dict, paths["shows"])

        if latest:
            episode_code = notifications.format_episode_code(latest)
            print(f"\n✓ Added '{selected.name}'")
            print(f"  Starting from: {episode_code} - {latest.title}")
        else:
            print(f"\n✓ Added '{selected.name}' (no episodes aired yet)")

    except api.NetworkError as e:
        print(f"\nNetwork error: {e}")
        print("Please check your internet connection and try again.")
    except api.TVMazeAPIError as e:
        print(f"\nAPI error: {e}")
    except storage.StorageError as e:
        print(f"\nStorage error: {e}")


def remove_show_interactive(paths: dict[str, Path]) -> None:
    """Remove a show through interactive selection.

    Args:
        paths: Dictionary of file paths
    """
    try:
        shows = storage.load_shows(paths["shows"])

        if not shows:
            print("No shows are currently being tracked.")
            return

        print("\nCurrently tracked shows:\n")
        for i, show in enumerate(shows, 1):
            print(f"{i}. {show['name']}")

        print("\nEnter number to remove (or 0 to cancel): ", end="")
        try:
            choice = int(input().strip())
        except ValueError:
            print("Invalid input. Cancelled.")
            return

        if choice < 1 or choice > len(shows):
            print("Cancelled.")
            return

        show = shows[choice - 1]

        # Confirm removal
        confirm = input(f"\nRemove '{show['name']}'? (y/n): ").strip().lower()

        if confirm == 'y':
            storage.remove_show(show["id"], paths["shows"])
            print(f"✓ Removed '{show['name']}'")
        else:
            print("Cancelled.")

    except storage.StorageError as e:
        print(f"\nStorage error: {e}")


def check_updates(paths: dict[str, Path], cfg: config.Config) -> None:
    """Check for new episodes for all tracked shows.

    Args:
        paths: Dictionary of file paths
        cfg: Configuration object
    """
    try:
        shows = storage.load_shows(paths["shows"])

        if not shows:
            print("No shows are currently being tracked.")
            print("Add shows first using the 'Add show' option.")
            return

        print(f"Checking {len(shows)} show(s) for updates...\n")

        all_updates = []
        errors = []

        for show in shows:
            show_name = show["name"]
            show_id = show["id"]
            last_season = show.get("last_seen_season")
            last_episode = show.get("last_seen_episode", 0)

            try:
                # Fetch episodes from API
                episodes_data = api.get_show_episodes(
                    show_id,
                    timeout=cfg.api_timeout,
                    retry_attempts=cfg.retry_attempts
                )

                # Parse and filter episodes
                episodes = [tracker.parse_episode_from_api(ep) for ep in episodes_data]
                aired_episodes = tracker.filter_aired_episodes(episodes)

                # Find new episodes
                new_episodes = tracker.find_new_episodes(
                    aired_episodes,
                    (last_season, last_episode)
                )

                if new_episodes:
                    print(f"✓ {show_name}: {len(new_episodes)} new episode(s)")

                    # Create updates for each new episode
                    for episode in new_episodes:
                        update = tracker.ShowUpdate(
                            show_id=show_id,
                            show_name=show_name,
                            episode=episode
                        )
                        all_updates.append(update)

                    # Update show state to latest episode
                    latest = new_episodes[-1]
                    storage.update_show(
                        show_id,
                        tracker.update_show_state(show, latest),
                        paths["shows"]
                    )
                else:
                    print(f"  {show_name}: No new episodes")

            except (api.NetworkError, api.TVMazeAPIError) as e:
                error_msg = f"  {show_name}: Error - {e}"
                print(error_msg)
                errors.append(error_msg)
                continue

        # Save notifications
        if all_updates:
            notification_lines = notifications.format_multiple_notifications(
                all_updates,
                cfg.date_format
            )
            storage.append_notifications(notification_lines, paths["notifications"])

            print(f"\n✓ Added {len(all_updates)} notification(s) to timeline")
        else:
            print("\nNo new episodes found.")

        if errors:
            print(f"\nWarning: {len(errors)} show(s) had errors during check")

    except storage.StorageError as e:
        print(f"\nStorage error: {e}")


def list_shows(paths: dict[str, Path]) -> None:
    """List all tracked shows.

    Args:
        paths: Dictionary of file paths
    """
    try:
        shows = storage.load_shows(paths["shows"])

        if not shows:
            print("No shows are currently being tracked.")
            return

        print(f"\nTracked Shows ({len(shows)}):\n")

        for show in shows:
            print(notifications.format_show_list_entry(show))
            print()

    except storage.StorageError as e:
        print(f"\nStorage error: {e}")


def view_timeline(paths: dict[str, Path], limit: int = 20) -> None:
    """View recent notifications from timeline.

    Args:
        paths: Dictionary of file paths
        limit: Maximum number of entries to display
    """
    try:
        lines = storage.load_notifications(paths["notifications"], limit=limit)

        if not lines:
            print("No notifications yet.")
            print("Check for updates to start tracking episodes.")
            return

        print(f"\nRecent Episodes (showing {len(lines)}):\n")

        for line in lines:
            print(notifications.format_timeline_entry(line))

    except storage.StorageError as e:
        print(f"\nStorage error: {e}")


def interactive_menu(paths: dict[str, Path], cfg: config.Config) -> None:
    """Run the interactive menu.

    Args:
        paths: Dictionary of file paths
        cfg: Configuration object
    """
    while True:
        print_header()
        print("1. Add show")
        print("2. Remove show")
        print("3. Check for updates")
        print("4. List tracked shows")
        print("5. View timeline")
        print("6. Exit")
        print()

        choice = input("Choose an option (1-6): ").strip()

        if choice == '1':
            add_show_interactive(paths, cfg)
        elif choice == '2':
            remove_show_interactive(paths)
        elif choice == '3':
            check_updates(paths, cfg)
        elif choice == '4':
            list_shows(paths)
        elif choice == '5':
            view_timeline(paths)
        elif choice == '6':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid option. Please choose 1-6.")

        input("\nPress Enter to continue...")


def main():
    """Main entry point for the CLI."""
    # Get paths and config
    paths = config.get_default_paths()
    cfg = config.load_config(paths["config"])

    # If command-line arguments provided, use them
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "add":
            if len(sys.argv) > 2:
                # Non-interactive mode not implemented yet
                print("Use interactive mode for now")
            else:
                add_show_interactive(paths, cfg)

        elif command == "remove":
            remove_show_interactive(paths)

        elif command == "check":
            check_updates(paths, cfg)

        elif command == "list":
            list_shows(paths)

        elif command == "timeline":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            view_timeline(paths, limit)

        else:
            print(f"Unknown command: {command}")
            print("Available commands: add, remove, check, list, timeline")
            sys.exit(1)
    else:
        # Run interactive menu
        interactive_menu(paths, cfg)


if __name__ == "__main__":
    main()
