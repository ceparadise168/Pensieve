"""
Data Repository — version control for personal KB data (raw/ + wiki/).

Uses a bare git repo at .data-repo/ that coexists with the public project repo.
All operations go through the kb CLI; users never touch .data-repo/ directly.
"""
import subprocess
import click
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_REPO = PROJECT_ROOT / ".data-repo"

# Directories tracked by the data repo
TRACKED_DIRS = ["raw", "wiki"]


def _data_git(*args, check=False) -> subprocess.CompletedProcess:
    """Run a git command against the data repo."""
    cmd = [
        "git",
        f"--git-dir={DATA_REPO}",
        f"--work-tree={PROJECT_ROOT}",
    ] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def is_initialized() -> bool:
    return (DATA_REPO / "HEAD").exists()


def init():
    """Initialize the bare data repo. Returns True if newly created."""
    if is_initialized():
        click.echo("Data repo already initialized.")
        return False

    subprocess.run(["git", "init", "--bare", str(DATA_REPO)], capture_output=True, check=True)
    # Don't honor the parent project's .gitignore — we want to track raw/ and wiki/
    _data_git("config", "core.excludesFile", "/dev/null")
    click.echo(f"Initialized data repo at {DATA_REPO.relative_to(PROJECT_ROOT)}/")

    # Take an initial snapshot if there's data
    has_data = any((PROJECT_ROOT / d).exists() and any((PROJECT_ROOT / d).rglob("*")) for d in TRACKED_DIRS)
    if has_data:
        snapshot("Initial snapshot")

    return True


def _ensure_init():
    if not is_initialized():
        click.echo("Data repo not initialized. Run: kb snapshot  (auto-initializes)")
        init()


def snapshot(message: str) -> bool:
    """Stage raw/ + wiki/ and commit. Returns True if a commit was created."""
    _ensure_init()

    # Force-add to bypass the parent repo's .gitignore
    for d in TRACKED_DIRS:
        dir_path = PROJECT_ROOT / d
        if dir_path.exists():
            _data_git("add", "-f", str(dir_path))

    # Check if there's anything to commit
    diff = _data_git("diff", "--cached", "--quiet")
    if diff.returncode == 0:
        click.echo("No changes to snapshot.")
        return False

    _data_git("commit", "-m", message, check=True)
    click.echo(f"Snapshot created: {message}")
    return True


def history(n: int = 20) -> str:
    """Show recent data snapshots."""
    _ensure_init()
    result = _data_git("log", f"-{n}", "--format=%C(yellow)%h%C(reset) %s %C(dim)(%ar)%C(reset)")
    if result.returncode != 0 or not result.stdout.strip():
        return "No snapshots yet."
    return result.stdout.strip()


def undo() -> bool:
    """Revert the last data commit, restoring files to previous state."""
    _ensure_init()

    # Check there's a commit to revert
    log = _data_git("log", "--oneline", "-1")
    if log.returncode != 0 or not log.stdout.strip():
        click.echo("Nothing to undo.")
        return False

    last_msg = log.stdout.strip()
    click.echo(f"Undoing: {last_msg}")

    result = _data_git("revert", "--no-edit", "HEAD")
    if result.returncode != 0:
        click.echo(f"Revert failed: {result.stderr.strip()}")
        click.echo("You can use 'kb restore <hash>' to go back to a specific snapshot.")
        return False

    click.echo("Undo complete. Files restored to previous state.")
    return True


def restore(commit_hash: str) -> bool:
    """Restore raw/ and wiki/ to the state at a given commit."""
    _ensure_init()

    # Verify the commit exists
    verify = _data_git("cat-file", "-t", commit_hash)
    if verify.returncode != 0:
        click.echo(f"Commit not found: {commit_hash}")
        click.echo("Run 'kb history' to see available snapshots.")
        return False

    # Checkout files from that commit
    for d in TRACKED_DIRS:
        _data_git("checkout", commit_hash, "--", f"{d}/")

    # Commit the restoration
    _data_git("add", "-f", "raw/", "wiki/")
    diff = _data_git("diff", "--cached", "--quiet")
    if diff.returncode != 0:
        _data_git("commit", "-m", f"restore: reverted to {commit_hash}")
        click.echo(f"Restored to snapshot {commit_hash}.")
    else:
        click.echo("Already at that state.")

    return True


@click.group()
def cli():
    """Data repo — version control for KB data."""
    pass


@cli.command("snapshot")
@click.argument("message")
def cmd_snapshot(message):
    """Create a named snapshot of the current KB state."""
    snapshot(message)


@cli.command("history")
@click.option("-n", default=20, help="Number of entries to show")
def cmd_history(n):
    """Show snapshot history."""
    click.echo(history(n))


@cli.command("undo")
def cmd_undo():
    """Undo the last snapshot (revert)."""
    undo()


@cli.command("restore")
@click.argument("commit_hash")
def cmd_restore(commit_hash):
    """Restore KB to a specific snapshot."""
    restore(commit_hash)


if __name__ == "__main__":
    cli()
