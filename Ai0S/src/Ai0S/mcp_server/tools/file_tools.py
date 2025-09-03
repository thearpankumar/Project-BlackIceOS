"""
File Tools - Cross-platform file system operations
Safe file management with security controls and monitoring.
"""

import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil

from ...utils.platform_detector import get_system_environment
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


class FileTools:
    """Cross-platform file system management tools."""
    
    def __init__(self):
        self.system_env = get_system_environment()
        self.settings = get_settings()
        
        # File operation history
        self.operation_history: List[Dict[str, Any]] = []
        
        # File manager executables per OS
        self.file_managers = self._get_file_managers()
        
        # Operation statistics
        self.stats = {
            "operations_performed": 0,
            "operations_blocked": 0,
            "files_accessed": 0,
            "directories_accessed": 0
        }
    
    def _get_file_managers(self) -> Dict[str, str]:
        """Get file manager executables for different OS."""
        
        managers = {
            "Windows": "explorer",
            "Darwin": "open",  # macOS Finder
            "Linux": self._detect_linux_file_manager()
        }
        
        return managers
    
    def _detect_linux_file_manager(self) -> str:
        """Detect available file manager on Linux."""
        
        # Common Linux file managers in order of preference
        managers = [
            "nautilus",      # GNOME Files
            "dolphin",       # KDE Dolphin  
            "thunar",        # XFCE Thunar
            "pcmanfm",       # LXDE/LXQt
            "nemo",          # Cinnamon Nemo
            "caja",          # MATE Caja
            "ranger",        # Terminal file manager
            "mc",            # Midnight Commander
            "xdg-open"       # Fallback
        ]
        
        for manager in managers:
            if shutil.which(manager):
                return manager
        
        return "ls"  # Ultimate fallback
    
    async def open_file_manager(self, path: str = ".") -> str:
        """
        Open file manager at specified path.
        
        Args:
            path: Path to open (default: current directory)
            
        Returns:
            Success message or error
        """
        try:
            logger.info(f"Opening file manager at path: {path}")
            
            # Resolve and validate path
            resolved_path = Path(path).resolve()
            
            if not resolved_path.exists():
                return f"Path does not exist: {resolved_path}"
            
            # Get appropriate file manager command
            file_manager = self.file_managers.get(self.system_env.os, "xdg-open")
            
            # Build command based on OS
            if self.system_env.os == "Windows":
                if resolved_path.is_file():
                    # Select file in explorer
                    command = f'explorer /select,"{resolved_path}"'
                else:
                    # Open directory
                    command = f'explorer "{resolved_path}"'
            
            elif self.system_env.os == "Darwin":  # macOS
                if resolved_path.is_file():
                    # Reveal file in Finder
                    command = f'open -R "{resolved_path}"'
                else:
                    # Open directory in Finder
                    command = f'open "{resolved_path}"'
            
            else:  # Linux
                command = f'{file_manager} "{resolved_path}" &'
            
            # Execute command
            logger.debug(f"Executing file manager command: {command}")
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            # Record operation
            self._record_operation("open_file_manager", {
                "path": str(resolved_path),
                "file_manager": file_manager,
                "success": result.returncode == 0
            })
            
            self.stats["operations_performed"] += 1
            self.stats["directories_accessed"] += 1
            
            if result.returncode == 0:
                return f"Successfully opened file manager at {resolved_path}"
            else:
                return f"Failed to open file manager: {result.stderr or 'Unknown error'}"
                
        except Exception as e:
            error_msg = f"Failed to open file manager at '{path}': {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def list_files(self, path: str = ".", show_hidden: bool = False) -> str:
        """
        List files in directory.
        
        Args:
            path: Directory path to list
            show_hidden: Show hidden files and directories
            
        Returns:
            Directory listing or error message
        """
        try:
            logger.info(f"Listing files in: {path}, show_hidden: {show_hidden}")
            
            # Resolve and validate path
            dir_path = Path(path).resolve()
            
            if not dir_path.exists():
                return f"Directory does not exist: {dir_path}"
            
            if not dir_path.is_dir():
                return f"Path is not a directory: {dir_path}"
            
            # Get directory listing
            items = []
            
            try:
                for item in dir_path.iterdir():
                    # Skip hidden files if not requested
                    if not show_hidden and item.name.startswith('.'):
                        continue
                    
                    # Get item info
                    stat = item.stat()
                    
                    item_info = {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size_bytes": stat.st_size if item.is_file() else 0,
                        "size_human": self._format_file_size(stat.st_size) if item.is_file() else "",
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "permissions": oct(stat.st_mode)[-3:],
                        "path": str(item)
                    }
                    
                    # Add file extension for files
                    if item.is_file():
                        item_info["extension"] = item.suffix.lower()
                    
                    items.append(item_info)
                
                # Sort items (directories first, then by name)
                items.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
                
                # Record operation
                self._record_operation("list_files", {
                    "path": str(dir_path),
                    "items_count": len(items),
                    "show_hidden": show_hidden
                })
                
                self.stats["operations_performed"] += 1
                self.stats["directories_accessed"] += 1
                
                # Create summary
                file_count = len([item for item in items if item["type"] == "file"])
                dir_count = len([item for item in items if item["type"] == "directory"])
                
                result = {
                    "path": str(dir_path),
                    "summary": {
                        "total_items": len(items),
                        "files": file_count,
                        "directories": dir_count
                    },
                    "items": items[:100]  # Limit to first 100 items
                }
                
                if len(items) > 100:
                    result["note"] = f"Showing first 100 items out of {len(items)} total"
                
                return str(result)
                
            except PermissionError:
                return f"Permission denied accessing directory: {dir_path}"
                
        except Exception as e:
            error_msg = f"Failed to list files in '{path}': {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    async def get_file_info(self, file_path: str) -> str:
        """
        Get detailed information about a file or directory.
        
        Args:
            file_path: Path to file or directory
            
        Returns:
            File information or error message
        """
        try:
            logger.info(f"Getting file info for: {file_path}")
            
            path = Path(file_path).resolve()
            
            if not path.exists():
                return f"File or directory does not exist: {path}"
            
            # Get file statistics
            stat = path.stat()
            
            info = {
                "path": str(path),
                "name": path.name,
                "type": "directory" if path.is_dir() else "file",
                "size_bytes": stat.st_size,
                "size_human": self._format_file_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
                "owner": stat.st_uid,
                "group": stat.st_gid
            }
            
            # Add file-specific info
            if path.is_file():
                info.update({
                    "extension": path.suffix.lower(),
                    "stem": path.stem,
                    "is_executable": os.access(path, os.X_OK),
                    "is_readable": os.access(path, os.R_OK),
                    "is_writable": os.access(path, os.W_OK)
                })
                
                # Try to detect file type
                try:
                    import mimetypes
                    mime_type, encoding = mimetypes.guess_type(str(path))
                    if mime_type:
                        info["mime_type"] = mime_type
                    if encoding:
                        info["encoding"] = encoding
                except:
                    pass
            
            # Add directory-specific info
            elif path.is_dir():
                try:
                    # Count items in directory
                    items = list(path.iterdir())
                    files = [item for item in items if item.is_file()]
                    dirs = [item for item in items if item.is_dir()]
                    
                    info.update({
                        "total_items": len(items),
                        "files_count": len(files),
                        "directories_count": len(dirs),
                        "total_size_bytes": sum(f.stat().st_size for f in files),
                    })
                    
                    info["total_size_human"] = self._format_file_size(info["total_size_bytes"])
                    
                except PermissionError:
                    info["note"] = "Permission denied to read directory contents"
            
            # Record operation
            self._record_operation("get_file_info", {
                "path": str(path),
                "type": info["type"]
            })
            
            self.stats["operations_performed"] += 1
            if path.is_file():
                self.stats["files_accessed"] += 1
            else:
                self.stats["directories_accessed"] += 1
            
            return str(info)
            
        except Exception as e:
            error_msg = f"Failed to get file info for '{file_path}': {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def find_files(
        self, 
        search_path: str = ".", 
        pattern: str = "*", 
        file_type: str = "all",
        max_results: int = 50
    ) -> str:
        """
        Find files matching criteria.
        
        Args:
            search_path: Directory to search in
            pattern: File name pattern (supports wildcards)
            file_type: Type of files to find (all, files, directories)
            max_results: Maximum number of results to return
            
        Returns:
            Search results or error message
        """
        try:
            logger.info(f"Finding files: path={search_path}, pattern={pattern}, type={file_type}")
            
            search_dir = Path(search_path).resolve()
            
            if not search_dir.exists():
                return f"Search directory does not exist: {search_dir}"
            
            if not search_dir.is_dir():
                return f"Search path is not a directory: {search_dir}"
            
            # Find matching files
            matches = []
            
            try:
                if pattern == "*":
                    # List all items
                    items = list(search_dir.rglob("*"))
                else:
                    # Use glob pattern
                    items = list(search_dir.rglob(pattern))
                
                for item in items:
                    if len(matches) >= max_results:
                        break
                    
                    # Filter by type
                    if file_type == "files" and not item.is_file():
                        continue
                    elif file_type == "directories" and not item.is_dir():
                        continue
                    
                    # Get item info
                    stat = item.stat()
                    
                    match_info = {
                        "name": item.name,
                        "path": str(item),
                        "relative_path": str(item.relative_to(search_dir)),
                        "type": "directory" if item.is_dir() else "file",
                        "size_bytes": stat.st_size if item.is_file() else 0,
                        "size_human": self._format_file_size(stat.st_size) if item.is_file() else "",
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                    
                    matches.append(match_info)
                
                # Sort by name
                matches.sort(key=lambda x: x["name"].lower())
                
                # Record operation
                self._record_operation("find_files", {
                    "search_path": str(search_dir),
                    "pattern": pattern,
                    "file_type": file_type,
                    "results_count": len(matches)
                })
                
                self.stats["operations_performed"] += 1
                
                result = {
                    "search_path": str(search_dir),
                    "pattern": pattern,
                    "file_type": file_type,
                    "results_count": len(matches),
                    "max_results": max_results,
                    "matches": matches
                }
                
                if len(items) > max_results:
                    result["note"] = f"Limited to first {max_results} results out of {len(items)} total matches"
                
                return str(result)
                
            except PermissionError:
                return f"Permission denied searching in directory: {search_dir}"
                
        except Exception as e:
            error_msg = f"Failed to find files: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def get_directory_size(self, dir_path: str) -> str:
        """
        Calculate total size of directory and its contents.
        
        Args:
            dir_path: Directory path to analyze
            
        Returns:
            Directory size information or error message
        """
        try:
            logger.info(f"Calculating directory size: {dir_path}")
            
            directory = Path(dir_path).resolve()
            
            if not directory.exists():
                return f"Directory does not exist: {directory}"
            
            if not directory.is_dir():
                return f"Path is not a directory: {directory}"
            
            # Calculate size recursively
            total_size = 0
            file_count = 0
            dir_count = 0
            
            try:
                for item in directory.rglob("*"):
                    if item.is_file():
                        total_size += item.stat().st_size
                        file_count += 1
                    elif item.is_dir():
                        dir_count += 1
                
                # Record operation
                self._record_operation("get_directory_size", {
                    "path": str(directory),
                    "total_size_bytes": total_size,
                    "file_count": file_count,
                    "dir_count": dir_count
                })
                
                self.stats["operations_performed"] += 1
                
                result = {
                    "path": str(directory),
                    "total_size_bytes": total_size,
                    "total_size_human": self._format_file_size(total_size),
                    "file_count": file_count,
                    "directory_count": dir_count,
                    "total_items": file_count + dir_count
                }
                
                return str(result)
                
            except PermissionError:
                return f"Permission denied accessing some files in directory: {directory}"
                
        except Exception as e:
            error_msg = f"Failed to calculate directory size: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _record_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Record file operation for history."""
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details,
            "system": {
                "os": self.system_env.os,
                "working_directory": str(Path.cwd())
            }
        }
        
        self.operation_history.append(record)
        
        # Limit history size
        if len(self.operation_history) > 200:
            self.operation_history = self.operation_history[-100:]
    
    def get_operation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent file operation history."""
        return self.operation_history[-limit:] if self.operation_history else []
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get file operation statistics."""
        return {
            "stats": self.stats.copy(),
            "operation_history_count": len(self.operation_history),
            "file_managers": self.file_managers,
            "current_directory": str(Path.cwd())
        }