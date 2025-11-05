"""Command-line interface for Episode Owl."""

import sys
from pathlib import Path

from . import api, config, notifications, notifier, search, storage, tracker, utils, watched


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


def check_updates(paths: dict[str, Path], cfg: config.Config, no_open: bool = False) -> None:
    """Check for new episodes for all tracked shows.

    Args:
        paths: Dictionary of file paths
        cfg: Configuration object
        no_open: If True, don't auto-open timeline (overrides config)
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

        # Phase 2 features: desktop notifications and auto-open
        if all_updates:
            # Send desktop notification
            if cfg.desktop_notifications:
                try:
                    notifier.send_desktop_notification(
                        all_updates,
                        paths["notifications"],
                        cfg.notification_sound
                    )
                except Exception as e:
                    # Don't crash if notification fails
                    print(f"Note: Desktop notification failed: {e}")

            # Auto-open timeline file
            if utils.should_auto_open(cfg.auto_open_timeline, no_open):
                utils.open_timeline_file(paths["notifications"])

        # Archive old watched notifications
        try:
            watched_state = watched.WatchedState(paths["watched"])
            archived = watched_state.archive_old_watched(cfg.archive_watched_after_days)
            if archived > 0:
                print(f"\nArchived {archived} old watched notification(s)")
        except Exception as e:
            # Don't crash if archiving fails
            print(f"Note: Could not archive old notifications: {e}")

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


def view_timeline(paths: dict[str, Path], limit: int = 20, show_all: bool = False) -> None:
    """View recent notifications from timeline.

    Args:
        paths: Dictionary of file paths
        limit: Maximum number of entries to display
        show_all: If True, show all notifications; if False, show only unwatched
    """
    try:
        lines = storage.load_notifications(paths["notifications"], limit=limit)

        if not lines:
            print("No notifications yet.")
            print("Check for updates to start tracking episodes.")
            return

        # Filter by watched status if needed
        if not show_all:
            watched_state = watched.WatchedState(paths["watched"])
            lines = watched.filter_unwatched_notifications(lines, watched_state)

            if not lines:
                print("No unwatched notifications.")
                print("Use --all flag to show all notifications.")
                return

        status = "All" if show_all else "Unwatched"
        print(f"\n{status} Episodes (showing {len(lines)}):\n")

        for line in lines:
            print(notifications.format_timeline_entry(line))

    except storage.StorageError as e:
        print(f"\nStorage error: {e}")


def mark_watched_interactive(paths: dict[str, Path]) -> None:
    """Interactive interface to mark notifications as watched.

    Args:
        paths: Dictionary of file paths
    """
    try:
        # Load unwatched notifications
        all_lines = storage.load_notifications(paths["notifications"])

        if not all_lines:
            print("No notifications yet.")
            print("Check for updates to start tracking episodes.")
            return

        watched_state = watched.WatchedState(paths["watched"])
        unwatched_lines = watched.filter_unwatched_notifications(all_lines, watched_state)

        if not unwatched_lines:
            print("No unwatched notifications.")
            return

        # Display unwatched notifications
        print(f"\nUnwatched notifications:\n")
        for i, line in enumerate(unwatched_lines, 1):
            print(f"[{i}] {line}")

        # Get user input
        print("\nMark as watched (comma-separated, 'all', or 'none'): ", end="")
        user_input = input().strip()

        if not user_input or user_input.lower() == "none":
            print("Cancelled.")
            return

        # Parse indices
        try:
            indices = watched.parse_notification_indices(user_input, len(unwatched_lines))

            if not indices:
                print("No notifications marked.")
                return

            # Create notification keys from selected lines
            keys_to_mark = []
            for idx in indices:
                line = unwatched_lines[idx]
                try:
                    key = watched.NotificationKey.from_notification_line(line)
                    keys_to_mark.append(key)
                except ValueError:
                    print(f"Warning: Could not parse line {idx + 1}")

            # Mark as watched
            if keys_to_mark:
                count = watched_state.mark_watched(keys_to_mark)
                print(f"\nMarked {len(keys_to_mark)} notification(s) as watched.")
            else:
                print("No valid notifications to mark.")

        except ValueError as e:
            print(f"\nError: {e}")

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
        print("6. Mark as watched")
        print("7. Exit")
        print()

        choice = input("Choose an option (1-7): ").strip()

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
            mark_watched_interactive(paths)
        elif choice == '7':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid option. Please choose 1-7.")

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
            # Check for --no-open flag
            no_open = "--no-open" in sys.argv
            check_updates(paths, cfg, no_open=no_open)

        elif command == "list":
            list_shows(paths)

        elif command == "timeline":
            # Parse flags and arguments
            show_all = "--all" in sys.argv
            # Get limit (number) if provided
            limit = 20
            for arg in sys.argv[2:]:
                if arg.isdigit():
                    limit = int(arg)
                    break

            view_timeline(paths, limit, show_all=show_all)

        elif command == "mark":
            mark_watched_interactive(paths)

        else:
            print(f"Unknown command: {command}")
            print("Available commands: add, remove, check [--no-open], list, timeline [--all], mark")
            sys.exit(1)
    else:
        # Run interactive menu
        interactive_menu(paths, cfg)


if __name__ == "__main__":
    main()
