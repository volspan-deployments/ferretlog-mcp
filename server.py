#!/usr/bin/env python3
"""
ferretlog MCP Server
Provides tools to interact with ferretlog CLI for Claude Code agent run analysis.
"""

from fastmcp import FastMCP
import subprocess
import os
import sys
from typing import Optional

mcp = FastMCP("ferretlog")


def _run_ferretlog(*args, no_color: bool = False) -> str:
    """Run the ferretlog CLI with given arguments and return output."""
    cmd = [sys.executable, "-m", "ferretlog"] if False else ["ferretlog"]
    
    # Try ferretlog as a command first, fall back to python -c invocation
    full_cmd = list(cmd) + list(args)
    if no_color:
        # Pass --no-color if supported, or set NO_COLOR env var
        env = os.environ.copy()
        env["NO_COLOR"] = "1"
    else:
        env = os.environ.copy()

    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        output = result.stdout
        if result.returncode != 0 and result.stderr:
            if not output:
                output = result.stderr
            else:
                output = output + "\nSTDERR: " + result.stderr
        return output if output else "(no output)"
    except FileNotFoundError:
        # ferretlog not found as a command, try as python module
        try:
            full_cmd2 = [sys.executable, "-m", "ferretlog"] + list(args)
            result2 = subprocess.run(
                full_cmd2,
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            output = result2.stdout
            if result2.returncode != 0 and result2.stderr:
                if not output:
                    output = result2.stderr
                else:
                    output = output + "\nSTDERR: " + result2.stderr
            return output if output else "(no output)"
        except FileNotFoundError:
            return "Error: ferretlog is not installed. Install it with: pip install ferretlog"
    except subprocess.TimeoutExpired:
        return "Error: ferretlog command timed out after 30 seconds"
    except Exception as e:
        return f"Error running ferretlog: {str(e)}"


@mcp.tool()
async def list_runs(
    limit: Optional[int] = 20,
    no_color: Optional[bool] = False
) -> dict:
    """
    List recent Claude Code agent runs in git log style.
    
    Use this as the default starting point to get an overview of all agent sessions,
    their tasks, costs, token usage, and duration. Shows runs for the current
    working directory's project.
    
    Returns a formatted list of runs with run IDs, dates, tasks, costs, and token usage.
    Use the run IDs returned here with show_run or diff_runs for detailed analysis.
    """
    args = []
    
    if limit is not None and limit != 20:
        args.extend(["--limit", str(limit)])
    
    if no_color:
        args.append("--no-color")
    
    output = _run_ferretlog(*args, no_color=bool(no_color))
    
    return {
        "output": output,
        "limit": limit,
        "no_color": no_color
    }


@mcp.tool()
async def show_run(
    run_id: str,
    no_color: Optional[bool] = False
) -> dict:
    """
    Show a full tool-by-tool breakdown of a specific agent run.
    
    Use this when you need to understand exactly what an agent did - every file read,
    bash command executed, and edit made. Requires a run ID (short hash) from list_runs.
    
    Returns detailed information including:
    - Run metadata (date, duration, model, branch)
    - Token usage and cost breakdown
    - Files touched during the run
    - Complete ordered list of tool calls (reads, edits, bash commands)
    """
    if not run_id:
        return {"error": "run_id is required. Get run IDs from list_runs first."}
    
    args = ["show", run_id]
    
    if no_color:
        args.append("--no-color")
    
    output = _run_ferretlog(*args, no_color=bool(no_color))
    
    return {
        "output": output,
        "run_id": run_id,
        "no_color": no_color
    }


@mcp.tool()
async def diff_runs(
    run_id_a: str,
    run_id_b: str,
    no_color: Optional[bool] = False
) -> dict:
    """
    Compare two agent runs side-by-side.
    
    Use this to understand why the same or similar prompt produced different behavior,
    tool usage, or results. Helpful for debugging inconsistent agent behavior or
    comparing different approaches across runs.
    
    Shows a visual diff of:
    - Tool call sequences (what steps each run took)
    - Files touched by each run
    - Differences in timing, call counts, and approach
    
    Symbols used: = (same in both), - (only in run A), + (only in run B), ~ (similar but different)
    """
    if not run_id_a:
        return {"error": "run_id_a is required. Get run IDs from list_runs first."}
    if not run_id_b:
        return {"error": "run_id_b is required. Get run IDs from list_runs first."}
    
    args = ["diff", run_id_a, run_id_b]
    
    if no_color:
        args.append("--no-color")
    
    output = _run_ferretlog(*args, no_color=bool(no_color))
    
    return {
        "output": output,
        "run_id_a": run_id_a,
        "run_id_b": run_id_b,
        "no_color": no_color
    }


@mcp.tool()
async def get_stats(
    no_color: Optional[bool] = False
) -> dict:
    """
    Show aggregate statistics across all Claude Code agent runs.
    
    Use this to understand overall agent usage patterns or estimate cumulative spend.
    
    Returns aggregate data including:
    - Total cost across all sessions
    - Total tokens consumed (input, output, cache)
    - Total time spent in agent sessions
    - Number of sessions and runs
    - Usage trends and patterns
    """
    args = ["stats"]
    
    if no_color:
        args.append("--no-color")
    
    output = _run_ferretlog(*args, no_color=bool(no_color))
    
    return {
        "output": output,
        "no_color": no_color
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))))
