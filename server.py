#!/usr/bin/env python3
"""
ferretlog MCP server
Exposes ferretlog CLI commands as MCP tools.
"""

import subprocess
import sys
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("ferretlog")


def _run_ferretlog(*args: str) -> str:
    """Run a ferretlog command and return its output."""
    cmd = [sys.executable, "-m", "ferretlog"] + list(args)
    # Try direct ferretlog command first
    try:
        result = subprocess.run(
            ["ferretlog"] + list(args),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 or result.stdout:
            return result.stdout + (result.stderr if result.stderr else "")
    except FileNotFoundError:
        pass

    # Fallback: try python -m ferretlog
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ferretlog"] + list(args),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout + (result.stderr if result.stderr else "")
    except Exception as e:
        return f"Error running ferretlog: {e}"


@mcp.tool()
async def list_runs(
    limit: int = 20,
    no_color: bool = False,
) -> dict:
    """List recent Claude Code agent runs in git-log style.

    Use this to get an overview of all agent sessions, their tasks, costs,
    duration, and token usage. Shows run IDs needed for other commands.
    Use this as the starting point when the user wants to see their agent history.

    Args:
        limit: Maximum number of recent runs to display (default: 20)
        no_color: Disable colored output for plain text display (default: False)

    Returns:
        A dict with the list of recent runs as formatted text.
    """
    args = []
    if limit and limit != 20:
        args += ["--limit", str(limit)]
    if no_color:
        args += ["--no-color"]

    output = _run_ferretlog(*args)
    return {
        "output": output,
        "description": "Recent Claude Code agent runs",
    }


@mcp.tool()
async def show_run(run_id: str) -> dict:
    """Show a full tool-by-tool breakdown of a specific agent run.

    Use this when the user wants to understand exactly what an agent did during
    a session — which files it read/edited, what commands it ran, tokens used,
    and cost. Requires a run ID from list_runs.

    Args:
        run_id: The run ID (short hash) to inspect, e.g. 'a3f2b1c9'.
                Get this from list_runs.

    Returns:
        A dict with the full tool-by-tool breakdown of the run.
    """
    if not run_id:
        return {"error": "run_id is required"}

    output = _run_ferretlog("show", run_id)
    return {
        "run_id": run_id,
        "output": output,
        "description": f"Details of agent run {run_id}",
    }


@mcp.tool()
async def diff_runs(run_id_a: str, run_id_b: str) -> dict:
    """Compare two agent runs side-by-side.

    Use this when the user wants to understand why the same or similar prompt
    produced different results across two sessions, or to compare efficiency
    between runs. Shows differences in tool calls, files touched, and cost.

    Args:
        run_id_a: The first run ID to compare, e.g. 'a3f2b1c9'. Get this from list_runs.
        run_id_b: The second run ID to compare, e.g. '9c1b2d3e'. Get this from list_runs.

    Returns:
        A dict with the side-by-side comparison of the two runs.
    """
    if not run_id_a:
        return {"error": "run_id_a is required"}
    if not run_id_b:
        return {"error": "run_id_b is required"}

    output = _run_ferretlog("diff", run_id_a, run_id_b)
    return {
        "run_id_a": run_id_a,
        "run_id_b": run_id_b,
        "output": output,
        "description": f"Comparison between agent runs {run_id_a} and {run_id_b}",
    }


@mcp.tool()
async def get_stats(no_color: bool = False) -> dict:
    """Show aggregate statistics across all Claude Code agent sessions.

    Shows total cost, total tokens consumed, total time spent, number of runs,
    average run cost, and model usage breakdown. Use this when the user wants
    a high-level summary of their overall agent usage or wants to understand
    cumulative spending.

    Args:
        no_color: Disable colored output for plain text display (default: False)

    Returns:
        A dict with aggregate statistics across all agent sessions.
    """
    args = ["stats"]
    if no_color:
        args += ["--no-color"]

    output = _run_ferretlog(*args)
    return {
        "output": output,
        "description": "Aggregate statistics across all Claude Code agent sessions",
    }


if __name__ == "__main__":
    mcp.run()
