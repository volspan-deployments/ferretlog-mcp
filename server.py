#!/usr/bin/env python3
"""FerretLog MCP Server - git log for your Claude Code agent runs."""

from fastmcp import FastMCP
import os
import subprocess
import sys
from typing import Optional

mcp = FastMCP("ferretlog")


def _run_ferretlog(*args) -> str:
    """Run ferretlog CLI command and return output."""
    cmd = [sys.executable, "-m", "ferretlog"] + list(args)
    # Try 'ferretlog' directly first, fall back to module
    try:
        result = subprocess.run(
            ["ferretlog"] + list(args),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 or result.stdout:
            return result.stdout or result.stderr
    except FileNotFoundError:
        pass

    # Try as python module
    result = subprocess.run(
        [sys.executable, "-c",
         f"import ferretlog; import sys; sys.argv = ['ferretlog'] + {list(args)!r}; ferretlog.main()"],
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout or result.stderr or "No output returned."


def _run_ferretlog_in_dir(project_path: Optional[str], *args) -> str:
    """Run ferretlog CLI command optionally in a specific directory."""
    cmd_args = list(args)
    env = os.environ.copy()

    cwd = project_path if project_path else None

    # Try 'ferretlog' directly
    try:
        result = subprocess.run(
            ["ferretlog"] + cmd_args,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
            env=env
        )
        if result.returncode == 0 or result.stdout:
            return result.stdout or result.stderr
    except FileNotFoundError:
        pass

    # Try as python module
    result = subprocess.run(
        [sys.executable, "-c",
         f"import ferretlog; import sys; sys.argv = ['ferretlog'] + {cmd_args!r}; ferretlog.main()"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd,
        env=env
    )
    return result.stdout or result.stderr or "No output returned."


@mcp.tool()
def list_runs(
    limit: int = 20,
    project_path: Optional[str] = None
) -> dict:
    """List recent Claude Code agent runs in git-log style for the current project.
    
    Use this as the default starting point to get an overview of all agent sessions,
    their tasks, costs, duration, and file counts. Shows commit-style short IDs you
    can use with other commands.
    """
    args = ["--limit", str(limit)] if limit != 20 else []
    
    try:
        output = _run_ferretlog_in_dir(project_path, *args)
        return {
            "success": True,
            "output": output,
            "limit": limit,
            "project_path": project_path or "(current directory)"
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 30 seconds."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def show_run(run_id: str) -> dict:
    """Show a full tool-by-tool breakdown of a specific agent run.
    
    Includes every file read/edited, every bash command executed, token usage,
    cost, model, and duration. Use this when you need to understand exactly what
    the agent did in a particular session.
    """
    if not run_id or not run_id.strip():
        return {
            "success": False,
            "error": "run_id is required. Obtain a run ID from list_runs first."
        }

    try:
        output = _run_ferretlog("show", run_id.strip())
        return {
            "success": True,
            "output": output,
            "run_id": run_id.strip()
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 30 seconds."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def diff_runs(run_id_a: str, run_id_b: str) -> dict:
    """Compare two agent runs side-by-side.
    
    Shows differences in tool calls, files touched, token usage, and duration
    between the two sessions. Use this when debugging inconsistent agent behavior
    or understanding why the same/similar prompts produced different outcomes.
    """
    if not run_id_a or not run_id_a.strip():
        return {
            "success": False,
            "error": "run_id_a is required. Obtain run IDs from list_runs first."
        }
    if not run_id_b or not run_id_b.strip():
        return {
            "success": False,
            "error": "run_id_b is required. Obtain run IDs from list_runs first."
        }

    try:
        output = _run_ferretlog("diff", run_id_a.strip(), run_id_b.strip())
        return {
            "success": True,
            "output": output,
            "run_id_a": run_id_a.strip(),
            "run_id_b": run_id_b.strip()
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 30 seconds."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_stats(project_path: Optional[str] = None) -> dict:
    """Show aggregate statistics across all agent runs for the current project.
    
    Includes total cost, total tokens consumed, total time spent, average run
    duration, and most-used models. Use this to understand overall AI usage
    and spending patterns.
    """
    try:
        output = _run_ferretlog_in_dir(project_path, "stats")
        return {
            "success": True,
            "output": output,
            "project_path": project_path or "(current directory)"
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 30 seconds."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))))
