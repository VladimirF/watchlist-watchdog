# Episode Owl 🦉

A simple, lightweight command-line tool to track TV shows and anime episodes. Get notified about new episodes without the bloat of dedicated apps or browser extensions.

## Features

- **Track Multiple Shows**: Monitor as many TV shows and anime as you want
- **Fuzzy Search**: Find shows easily with partial names (e.g., "sunny" finds "It's Always Sunny in Philadelphia")
- **Timeline Format**: View all new episodes in a clean, chronological timeline
- **Desktop Notifications**: Get Windows toast notifications when new episodes are found (NEW!)
- **Mark as Watched**: Track which episodes you've seen, filter timeline to show only unwatched (NEW!)
- **Auto-Open Timeline**: Automatically opens timeline file after finding new episodes (NEW!)
- **Offline Storage**: All data stored locally in simple JSON/text files
- **Manual Execution**: Run when you want updates - no background processes or daemons
- **Windows Compatible**: Works seamlessly on Windows (and Linux/macOS)
- **No API Key Required**: Uses the free TVMaze API

## Installation

### Prerequisites

- Python 3.10 or higher
- Internet connection (for fetching episode data)

### Windows Installation

1. **Install Python** (if not already installed)
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Download Episode Owl**
   ```bash
   git clone https://github.com/yourusername/episode-owl.git
   cd episode-owl
   ```

3. **Create Virtual Environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Episode Owl**
   ```bash
   pip install -e .
   ```

### Linux/macOS Installation

```bash
git clone https://github.com/yourusername/episode-owl.git
cd episode-owl
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Usage

### Interactive Mode

Run without arguments to launch the interactive menu:

```bash
python -m episode_owl
```

Or on Windows, use the batch file:

```bash
episode-owl.bat
```

### Command-Line Mode

```bash
# Add a show
python -m episode_owl add

# Check for new episodes
python -m episode_owl check

# Check without auto-opening timeline
python -m episode_owl check --no-open

# List tracked shows
python -m episode_owl list

# View recent unwatched episodes (default)
python -m episode_owl timeline

# View ALL episodes (including watched)
python -m episode_owl timeline --all

# View more timeline entries
python -m episode_owl timeline 50

# Mark episodes as watched
python -m episode_owl mark
```

### Example Workflow

1. **Add a show:**
   ```
   > python -m episode_owl add
   Enter show name to search: breaking bad

   Found 3 matches:
   1. Breaking Bad (2008) [Ended] (Match: 100%)
   2. Breaking In (2011) [Ended] (Match: 75%)
   3. Breaking Borders (2017) [Ended] (Match: 65%)

   Enter number to add show (or 0 to cancel): 1

   ✓ Added 'Breaking Bad'
   Starting from: S05E16 - Felina
   ```

2. **Check for updates:**
   ```
   > python -m episode_owl check
   Checking 3 show(s) for updates...

   ✓ It's Always Sunny in Philadelphia: 1 new episode(s)
     The Office: No new episodes
   ✓ Attack on Titan: 2 new episode(s)

   ✓ Added 3 notification(s) to timeline
   ```

3. **View timeline:**
   ```
   > python -m episode_owl timeline

   Recent Episodes (showing 20):

   [2025-11-05] Attack on Titan - S04E29: The Final Chapter
   [2025-11-05] Attack on Titan - S04E28: The Dawn of Humanity
   [2025-11-05] It's Always Sunny in Philadelphia - S16E03: The Gang Gets Analyzed
   [2025-11-04] Breaking Bad - S05E16: Felina
   ```

## Configuration

Episode Owl can be configured by editing `data/config.json`:

```json
{
  "output_path": "data/notifications.txt",
  "date_format": "%Y-%m-%d",
  "max_notifications": 100,
  "api_timeout": 10,
  "retry_attempts": 1,
  "desktop_notifications": true,
  "auto_open_timeline": true,
  "notification_sound": false,
  "archive_watched_after_days": 30
}
```

### Configuration Options

- **output_path**: Where to save notifications (default: `data/notifications.txt`)
- **date_format**: Python date format string (default: `%Y-%m-%d`)
- **max_notifications**: Maximum notifications to keep (default: 100)
- **api_timeout**: API request timeout in seconds (default: 10)
- **retry_attempts**: Number of retries for failed requests (default: 1)
- **desktop_notifications**: Enable Windows toast notifications (default: true)
- **auto_open_timeline**: Auto-open timeline file after finding episodes (default: true)
- **notification_sound**: Play sound with desktop notifications (default: false)
- **archive_watched_after_days**: Days before archiving old watched episodes (default: 30)

## Data Files

All data is stored in the `data/` directory:

- **shows.json**: List of tracked shows and their last seen episodes
- **notifications.txt**: Timeline of new episodes (newest first)
- **watched.json**: Tracks which notifications have been marked as watched (NEW!)
- **config.json**: User configuration (created on first run)

### Example shows.json

```json
{
  "shows": [
    {
      "id": 169,
      "name": "Breaking Bad",
      "last_checked": "2025-11-05T10:30:00",
      "last_seen_season": 5,
      "last_seen_episode": 16
    }
  ]
}
```

### Example notifications.txt

```
2025-11-05 | Attack on Titan | S04E29 | The Final Chapter
2025-11-05 | It's Always Sunny in Philadelphia | S16E03 | The Gang Gets Analyzed
2025-11-04 | The Office | S09E23 | Finale
```

## Phase 2 Features

### Desktop Notifications

When new episodes are found, Episode Owl sends a Windows toast notification:
- Shows count of new episodes
- Lists top 3 show names
- Click notification to open timeline file (Windows only)
- Can be disabled in config: `"desktop_notifications": false`

### Mark as Watched

Track which episodes you've seen to keep your timeline clean:

```bash
python -m episode_owl mark
```

Interactive interface shows unwatched episodes:
```
Unwatched notifications:

[1] 2025-11-05 | Breaking Bad | S05E16 | Felina
[2] 2025-11-04 | The Wire | S05E10 | -30-

Mark as watched (comma-separated, 'all', or 'none'): 1,2
```

Supports various input formats:
- Single: `1`
- Multiple: `1,3,5`
- Range: `2-5`
- All: `all`
- None: `none`

By default, `timeline` command shows only unwatched episodes. Use `--all` flag to see everything.

### Auto-Open Timeline

After finding new episodes, the timeline file automatically opens in your default text editor:
- Windows: Notepad
- macOS: Default text editor
- Linux: xdg-open

Disable in config: `"auto_open_timeline": false`

Or use command-line flag: `python -m episode_owl check --no-open`

### Automatic Archiving

Old watched notifications are automatically archived to prevent file bloat:
- Default: 30 days
- Configure with `"archive_watched_after_days": 30`
- Unwatched notifications are never archived
- Runs automatically during `check` command

## Automation (Optional)

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 9:00 AM)
4. Action: Start a program
   - Program: `C:\Path\To\venv\Scripts\python.exe`
   - Arguments: `-m episode_owl check`
   - Start in: `C:\Path\To\episode-owl`

### Linux/macOS Cron

Add to crontab (`crontab -e`):

```cron
# Check for updates daily at 9 AM
0 9 * * * cd /path/to/episode-owl && /path/to/venv/bin/python -m episode_owl check
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=episode_owl --cov-report=html

# Run specific test file
pytest tests/test_tracker.py
```

### Project Structure

```
episode-owl/
├── src/episode_owl/
│   ├── api.py              # TVMaze API client
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration management
│   ├── notifications.py    # Notification formatting
│   ├── search.py           # Fuzzy search logic
│   ├── storage.py          # File I/O operations
│   └── tracker.py          # Episode tracking logic
├── tests/                  # Test suite
├── data/                   # User data files
├── requirements.txt        # Dependencies
└── pyproject.toml         # Package configuration
```

### Code Style

- Type hints on all functions
- Docstrings (Google style)
- PEP 8 compliant
- Pure functions where possible
- Side effects isolated to api.py, storage.py, cli.py

## Troubleshooting

### "No module named episode_owl"

Make sure you've installed the package:
```bash
pip install -e .
```

### "Network error" when checking updates

- Check your internet connection
- TVMaze API might be temporarily down
- Try increasing `api_timeout` in config.json

### Shows not appearing in search

- TVMaze might not have the show
- Try different search terms (e.g., English vs Japanese title)
- Check [tvmaze.com](https://www.tvmaze.com/) to verify the show exists

### Duplicate notifications

The app prevents duplicates on the same day. If you're seeing duplicates:
- Check if you ran `check` multiple times on different days
- This is expected behavior - notifications persist chronologically

### File permissions errors

Make sure the `data/` directory is writable:
```bash
# Linux/macOS
chmod -R u+w data/

# Windows: Right-click data folder -> Properties -> Security
```

## FAQ

**Q: Does this work with anime?**
A: Yes! TVMaze has many anime titles. Search for the English or Japanese title.

**Q: Can I track multiple shows?**
A: Yes, there's no limit on the number of shows you can track.

**Q: Will this send me push notifications?**
A: No. Episode Owl is a manual tool - you run it when you want to check for updates. The timeline persists, so you won't miss anything.

**Q: Do I need a TVMaze account?**
A: No, the TVMaze API is completely free and requires no authentication.

**Q: What if a show doesn't have season numbers?**
A: Some shows (especially anime) use absolute episode numbering. Episode Owl handles both formats.

**Q: Can I export my tracked shows?**
A: Your shows are stored in `data/shows.json` - this is a standard JSON file you can back up or share.

## API Information

Episode Owl uses the [TVMaze API](https://www.tvmaze.com/api):

- **Base URL**: https://api.tvmaze.com
- **Rate Limit**: ~20 requests per 10 seconds
- **Authentication**: None required
- **Documentation**: https://www.tvmaze.com/api

The app respects rate limits with built-in delays between requests.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [TVMaze](https://www.tvmaze.com/) for their excellent free API
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) for fuzzy string matching
- All the TV show fans who just want a simple tracker 📺

## Support

Having issues? Please:

1. Check the Troubleshooting section above
2. Search existing issues on GitHub
3. Create a new issue with:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce

---

**Episode Owl** - Because tracking TV shows shouldn't require a PhD in software engineering 🦉