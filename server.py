#!/usr/bin/env python3
"""ferretlog MCP server - git log for your Claude Code agent runs."""

import subprocess
import json
import os
from typing import Optional
from fastmcp import FastMCP

mcp = FastMCP("ferretlog")


def _run_ferretlog(*args) -> str:
    """Run ferretlog CLI with given arguments and return output."""
    cmd = ["ferretlog"] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        if result.returncode != 0 and result.stderr:
            output = output + "\nSTDERR: " + result.stderr
        return output if output.strip() else "No output returned."
    except FileNotFoundError:
        return "Error: ferretlog is not installed. Install with: pip install ferretlog"
    except subprocess.TimeoutExpired:
        return "Error: ferretlog command timed out."
    except Exception as e:
        return f"Error running ferretlog: {str(e)}"


@mcp.tool()
async def list_runs(
    limit: Optional[int] = 20,
    project_path: Optional[str] = None
) -> dict:
    """List recent Claude Code agent runs in git log style for the current or specified project.
    
    Use this to get an overview of past agent sessions, their tasks, costs,
    token usage, and duration. This is the default view and the starting point
    for exploring agent history.
    """
    args = []
    
    if project_path:
        args.extend(["--project", project_path])
    
    if limit is not None:
        args.extend(["--limit", str(limit)])
    
    # Run ferretlog with optional args (default command is list)
    if project_path:
        # Try with --project flag first
        output = _run_ferretlog(*args)
    elif limit and limit != 20:
        output = _run_ferretlog("--limit", str(limit))
    else:
        output = _run_ferretlog()
    
    return {
        "output": output,
        "command": "ferretlog " + " ".join(args) if args else "ferretlog",
        "limit": limit,
        "project_path": project_path
    }


@mcp.tool()
async def show_run(run_id: str) -> dict:
    """Show a full tool-by-tool breakdown of a specific agent run.
    
    Includes all tool calls (read, edit, bash), files touched, token counts,
    cost estimate, model used, and duration. Use this when you want to
    understand exactly what the agent did in a particular session.
    """
    if not run_id or not run_id.strip():
        return {
            "error": "run_id is required",
            "output": ""
        }
    
    output = _run_ferretlog("show", run_id.strip())
    
    return {
        "output": output,
        "command": f"ferretlog show {run_id}",
        "run_id": run_id
    }


@mcp.tool()
async def diff_runs(run_id_a: str, run_id_b: str) -> dict:
    """Compare two agent runs side by side.
    
    Shows how the agent approached the same or similar tasks differently.
    Useful for understanding why two runs had different outcomes, costs,
    or tool usage patterns.
    """
    if not run_id_a or not run_id_a.strip():
        return {
            "error": "run_id_a is required",
            "output": ""
        }
    
    if not run_id_b or not run_id_b.strip():
        return {
            "error": "run_id_b is required",
            "output": ""
        }
    
    output = _run_ferretlog("diff", run_id_a.strip(), run_id_b.strip())
    
    return {
        "output": output,
        "command": f"ferretlog diff {run_id_a} {run_id_b}",
        "run_id_a": run_id_a,
        "run_id_b": run_id_b
    }


@mcp.tool()
async def get_stats(project_path: Optional[str] = None) -> dict:
    """Show aggregate statistics across all Claude Code agent sessions.
    
    Includes total cost, total tokens consumed, total time spent, number
    of runs, and per-model breakdowns. Use this to understand overall
    agent usage and spending trends.
    """
    args = ["stats"]
    
    if project_path:
        args.extend(["--project", project_path])
    
    output = _run_ferretlog(*args)
    
    return {
        "output": output,
        "command": "ferretlog " + " ".join(args),
        "project_path": project_path
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
