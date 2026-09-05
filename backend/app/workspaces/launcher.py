"""
Isolated Windows Native OS Launchers for Study Pilot.
Provides secure, path-validated process spawning for VS Code, File Explorer, and Terminal.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

from ..config import WORKSPACES_DIR


def validate_workspace_path(path: Path) -> Path:
    """Ensure target path is strictly within WORKSPACES_DIR to prevent path traversal."""
    resolved_target = path.resolve()
    resolved_root = WORKSPACES_DIR.resolve()

    try:
        resolved_target.relative_to(resolved_root)
    except ValueError:
        raise ValueError(f"Security error: Path {resolved_target} is outside allowed workspaces root {resolved_root}")

    if not resolved_target.exists():
        raise FileNotFoundError(f"Workspace directory does not exist: {resolved_target}")

    return resolved_target


class WindowsLauncher:
    @staticmethod
    def open_in_vscode(workspace_path: Path) -> Dict[str, Any]:
        """Launch VS Code rooted in the workspace directory."""
        target = validate_workspace_path(workspace_path)
        code_bin = shutil.which("code") or shutil.which("code.cmd")
        
        # Launch using shell on Windows to respect PATH resolution
        try:
            subprocess.Popen(["code", str(target)], shell=True)
            return {
                "success": True,
                "tool": "vscode",
                "message": f"Launched VS Code in {target.name}",
                "path": str(target),
            }
        except Exception as e:
            return {
                "success": False,
                "tool": "vscode",
                "error": str(e),
                "message": "Failed to launch VS Code. Ensure 'code' is installed and added to PATH.",
            }

    @staticmethod
    def open_in_explorer(workspace_path: Path) -> Dict[str, Any]:
        """Open Windows File Explorer at the workspace directory."""
        target = validate_workspace_path(workspace_path)
        try:
            if hasattr(os, "startfile"):
                os.startfile(str(target))
            else:
                subprocess.Popen(["explorer.exe", str(target)])
            return {
                "success": True,
                "tool": "explorer",
                "message": f"Opened File Explorer in {target.name}",
                "path": str(target),
            }
        except Exception as e:
            return {
                "success": False,
                "tool": "explorer",
                "error": str(e),
                "message": "Failed to open File Explorer.",
            }

    @staticmethod
    def open_in_terminal(workspace_path: Path) -> Dict[str, Any]:
        """Launch Windows Terminal (wt.exe) or fallback to PowerShell."""
        target = validate_workspace_path(workspace_path)
        wt_bin = shutil.which("wt") or shutil.which("wt.exe")

        try:
            if wt_bin:
                subprocess.Popen([wt_bin, "-d", str(target)])
            else:
                # Fallback to standard PowerShell
                subprocess.Popen(
                    ["powershell.exe", "-NoExit", "-Command", f"Set-Location -LiteralPath '{str(target)}'"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, "CREATE_NEW_CONSOLE") else 0
                )
            return {
                "success": True,
                "tool": "terminal",
                "message": f"Launched Terminal in {target.name}",
                "path": str(target),
            }
        except Exception as e:
            return {
                "success": False,
                "tool": "terminal",
                "error": str(e),
                "message": "Failed to launch terminal.",
            }

    @classmethod
    def launch(cls, workspace_path: Path, tool: str) -> Dict[str, Any]:
        """Dispatch launcher request by tool name."""
        tool_lower = tool.lower()
        if tool_lower in ["vscode", "code"]:
            return cls.open_in_vscode(workspace_path)
        elif tool_lower in ["explorer", "folder"]:
            return cls.open_in_explorer(workspace_path)
        elif tool_lower in ["terminal", "powershell", "cmd", "wt"]:
            return cls.open_in_terminal(workspace_path)
        else:
            raise ValueError(f"Unsupported launcher tool: '{tool}'. Supported: vscode, explorer, terminal")
