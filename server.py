#!/usr/bin/env python3
"""
FerretLog MCP Server
Exposes ferretlog CLI tools as MCP tools via HTTP transport.
"""

import os
import subprocess
import sys
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("ferretlog")


def _run_ferretlog(*args: str) -> str:
    """
    Run ferretlog CLI with the given arguments.
    Returns combined stdout+stderr as a string.
    """
    cmd = [sys.executable, "-m", "ferretlog"] if False else ["ferretlog"]
    # Try 'ferretlog' directly first; fall back to 'python -m ferretlog'
    full_cmd = ["ferretlog"] + list(args)
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.returncode != 0 and result.stderr:
            output += "\n" + result.stderr
        return output.strip()
    except FileNotFoundError:
        # ferretlog not found on PATH, try via python -m ferretlog
        full_cmd2 = [sys.executable, "-m", "ferretlog"] + list(args)
        try:
            result2 = subprocess.run(
                full_cmd2,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result2.stdout
            if result2.returncode != 0 and result2.stderr:
                output += "\n" + result2.stderr
            return output.strip()
        except Exception as e2:
            return f"Error running ferretlog: {e2}"
    except subprocess.TimeoutExpired:
        return "Error: ferretlog command timed out after 30 seconds."
    except Exception as e:
        return f"Error running ferretlog: {e}"


@mcp.tool()
async def list_runs(
    limit: Optional[int] = 20,
    no_color: Optional[bool] = False,
) -> dict:
    """
    List recent Claude Code agent runs in git-log style.
    Use this when the user wants to see their agent history, recent sessions,
    or an overview of what the AI agent has done.
    Shows run IDs, tasks, file counts, duration, tokens, and cost.
    """
    args = []
    if limit and limit != 20:
        args += ["--limit", str(limit)]
    if no_color:
        args += ["--no-color"]
    output = _run_ferretlog(*args)
    return {"output": output, "limit": limit, "no_color": no_color}


@mcp.tool()
async def show_run(
    run_id: str,
    no_color: Optional[bool] = False,
) -> dict:
    """
    Display a full tool-by-tool breakdown of a specific agent run.
    Use this when the user wants to inspect exactly what the agent did in a
    session: which files it read, what bash commands it ran, what edits it made,
    and the token/cost breakdown.
    Requires a run ID from list_runs.
    """
    args = ["show", run_id]
    if no_color:
        args += ["--no-color"]
    output = _run_ferretlog(*args)
    return {"output": output, "run_id": run_id, "no_color": no_color}


@mcp.tool()
async def diff_runs(
    run_id_a: str,
    run_id_b: str,
    no_color: Optional[bool] = False,
) -> dict:
    """
    Compare two agent runs side-by-side to see how they differed.
    Use this when the user wants to understand why the same task went differently
    in two sessions, compare tool call sequences, file changes, or costs between
    two runs. Requires two run IDs from list_runs.
    """
    args = ["diff", run_id_a, run_id_b]
    if no_color:
        args += ["--no-color"]
    output = _run_ferretlog(*args)
    return {
        "output": output,
        "run_id_a": run_id_a,
        "run_id_b": run_id_b,
        "no_color": no_color,
    }


@mcp.tool()
async def get_stats(
    no_color: Optional[bool] = False,
) -> dict:
    """
    Show aggregate statistics across all Claude Code agent runs.
    Reports total cost, total tokens, total time, number of sessions, and
    per-model breakdowns.
    Use this when the user wants a summary of overall agent usage, spending,
    or productivity trends.
    """
    args = ["stats"]
    if no_color:
        args += ["--no-color"]
    output = _run_ferretlog(*args)
    return {"output": output, "no_color": no_color}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))))
