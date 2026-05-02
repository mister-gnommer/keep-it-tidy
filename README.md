> **⚠ AI-generated code — not yet human-reviewed. Use at your own risk.**
> This project was scaffolded by an AI agent. The logic has not been audited by a human (in fact this is happening right now ;)).
> Do not run against important directories without first testing with `dry-run = true`.

---

# keep-it-tidy

A daily-running CLI script that keeps watched directories (e.g. `~/Downloads`) tidy by
staging and eventually removing old files and folders based on age and naming patterns.

Targets Linux (Fedora). Scheduled via a systemd user timer.

## How it works

Items in watched directories go through a three-stage pipeline on each run:

1. **Main sweep** — items matching `removable-pattern` that are older than
   `removable-main-sweep-ttl` days are moved to `_to-remove/YYYY-MM-DD_<name>`.
2. **Removal** — items that have sat in `_to-remove/` for longer than
   `removable-remove-after` days are deleted (or moved to `_safe-to-remove/` if
   `danger-enable-removing = false`).
3. **Auto-archive** — standard (non-removable) items older than `arch-main-sweep-ttl`
   days are moved to `_auto-arch/` when `enable-auto-arch = true`.

A `dry-run` mode makes no filesystem changes and writes a markdown report instead.

### Item age

The effective age of an item is determined by `max(mtime, birthtime)`. For directories,
the freshest date among all descendant files is used, capped by `dir-scan-file-limit`
to avoid scanning huge trees.

### Special folders

These folders inside watched directories are never processed as regular items:

| Folder | Purpose |
|---|---|
| `_to-remove/` | Staging area — items waiting for the removal TTL |
| `_auto-arch/` | Archive for old standard items |
| `_safe-to-remove/` | Destination when `danger-enable-removing = false` |

## Installation

Requires Python 3.11+.

```bash
git clone <repo>
cd keep-it-tidy
pip install -e .
```

For development (includes pytest and mypy):

```bash
pip install -e ".[dev]"
```

## Configuration

Copy the example config and edit it:

```bash
cp config/config.example.toml config/config.toml
vim config/config.toml
```

`config/config.toml` is gitignored. See `config/config.example.toml` for all fields
with descriptions.

**Required fields:**

```toml
directories = ["/home/user/Downloads"]
removable-main-sweep-ttl = 7
removable-remove-after = 14
arch-main-sweep-ttl = 60
```

## Usage

```bash
keep-it-tidy --config /path/to/config.toml
```

Always do a dry run first to see what would happen:

```bash
# Set dry-run = true in config.toml, then:
keep-it-tidy --config /path/to/config.toml
# A report is written to the first watched directory.
```

## Daily scheduling (Fedora / systemd)

```bash
bash scripts/setup-systemd.sh
```

This installs a systemd user timer that runs `keep-it-tidy` daily. The timer uses
`Persistent=true` so a missed run (machine was off) fires once on next boot.

Check status and logs:

```bash
systemctl --user status keep-it-tidy.timer
journalctl --user -u keep-it-tidy.service -n 50
```

## Running tests

```bash
pytest
```

The test suite includes a static analysis check (`test_single_deletion_point.py`) that
asserts filesystem deletion calls exist in exactly one place in the codebase (`fs_ops.py`),
directly gated on the `dry_run` flag.

## Project structure

```
src/keep_it_tidy/
├── __main__.py          # entry point
├── config/              # TOML loading and type definitions
├── platform/            # OS guard (Linux only)
├── scanner/             # directory walker
├── date/                # effective-date resolution
├── classifier/          # ignore / removable / standard classification
├── pipeline/            # orchestrator + three pipeline stages
├── fs/                  # sole module allowed to mutate the filesystem
└── report/              # dry-run markdown report generator
```

## TODOs

- human review remaining: unit tests
- per-directory TTLs
