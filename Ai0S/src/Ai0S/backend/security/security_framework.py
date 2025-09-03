"""
Security Framework - Comprehensive security controls and safety checks
Advanced security system with permissions, sandboxing, and threat detection.
"""

import asyncio
import hashlib
import hmac
import json
import os
import re
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import subprocess

from ...utils.platform_detector import get_system_environment
from ...config.settings import get_settings


logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    UNRESTRICTED = "unrestricted"  # No restrictions (development only)
    PERMISSIVE = "permissive"      # Basic safety checks
    STANDARD = "standard"          # Standard security controls
    STRICT = "strict"              # Strict security enforcement
    PARANOID = "paranoid"          # Maximum security (limited functionality)


class ThreatLevel(Enum):
    BENIGN = "benign"        # Safe operation
    SUSPICIOUS = "suspicious" # Potentially risky
    DANGEROUS = "dangerous"   # High risk operation
    MALICIOUS = "malicious"   # Definitely malicious


class PermissionType(Enum):
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_EXECUTE = "file_execute"
    NETWORK_ACCESS = "network_access"
    SYSTEM_COMMAND = "system_command"
    PROCESS_CONTROL = "process_control"
    REGISTRY_ACCESS = "registry_access"
    HARDWARE_ACCESS = "hardware_access"
    ADMIN_PRIVILEGES = "admin_privileges"


@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    policy_id: str
    name: str
    description: str
    security_level: SecurityLevel
    allowed_permissions: Set[PermissionType]
    blocked_patterns: List[str]
    allowed_paths: List[str]
    blocked_paths: List[str]
    max_execution_time: int
    require_confirmation: bool
    enable_sandboxing: bool
    log_all_actions: bool


@dataclass
class SecurityViolation:
    """Security violation record."""
    violation_id: str
    timestamp: datetime
    violation_type: str
    threat_level: ThreatLevel
    description: str
    context: Dict[str, Any]
    action_taken: str
    user_notified: bool


@dataclass
class PermissionRequest:
    """Permission request from a component."""
    request_id: str
    requester: str
    permission_type: PermissionType
    resource: str
    justification: str
    timestamp: datetime
    approved: Optional[bool] = None
    approver: Optional[str] = None


class SecurityFramework:
    """Comprehensive security framework for the AI OS."""
    
    def __init__(self):
        self.settings = get_settings()
        self.system_env = get_system_environment()
        
        # Security configuration
        self.current_policy: Optional[SecurityPolicy] = None
        self.security_level = SecurityLevel.STANDARD
        
        # Threat detection
        self.threat_patterns = self._load_threat_patterns()
        self.security_violations: List[SecurityViolation] = []
        
        # Permission management
        self.granted_permissions: Dict[str, Set[PermissionType]] = {}
        self.permission_requests: List[PermissionRequest] = []
        
        # Sandboxing and isolation
        self.sandbox_enabled = True
        self.sandbox_paths = []
        
        # Audit and monitoring
        self.audit_log: List[Dict[str, Any]] = []
        self.monitoring_active = False
        
        # Statistics
        self.stats = {
            "security_checks": 0,
            "violations_detected": 0,
            "permissions_granted": 0,
            "permissions_denied": 0,
            "threats_blocked": 0,
            "safe_operations": 0
        }
        
        # Initialize security system
        self._initialize_security()
    
    def _initialize_security(self) -> None:
        """Initialize the security framework."""
        
        # Load default security policies
        self._load_default_policies()
        
        # Set up default permissions
        self._setup_default_permissions()
        
        # Initialize sandboxing
        self._initialize_sandboxing()
        
        logger.info(f"Security framework initialized with {self.security_level.value} security level")
    
    def _load_default_policies(self) -> None:
        """Load default security policies."""
        
        # Standard policy for normal operations
        standard_policy = SecurityPolicy(
            policy_id="standard",
            name="Standard Security Policy",
            description="Balanced security for normal operations",
            security_level=SecurityLevel.STANDARD,
            allowed_permissions={
                PermissionType.FILE_READ,
                PermissionType.FILE_WRITE,
                PermissionType.NETWORK_ACCESS,
                PermissionType.SYSTEM_COMMAND
            },
            blocked_patterns=[
                "rm -rf", "del /f", "format", "mkfs", "dd if=",
                "shutdown", "reboot", "halt", "poweroff",
                "chmod 777", "chown root", "su -", "sudo su",
                "> /dev/", "curl.*sh", "wget.*sh", "nc -e",
                "eval", "exec", "__import__", "compile"
            ],
            allowed_paths=[
                str(Path.home()),
                "/tmp", "/var/tmp",
                str(Path.cwd())
            ],
            blocked_paths=[
                "/bin", "/sbin", "/usr/bin", "/usr/sbin",
                "/etc", "/boot", "/sys", "/proc", "/dev",
                "C:\\Windows\\System32", "C:\\Windows\\SysWOW64",
                "C:\\Program Files", "C:\\Program Files (x86)"
            ],
            max_execution_time=300,  # 5 minutes
            require_confirmation=True,
            enable_sandboxing=True,
            log_all_actions=True
        )
        
        self.current_policy = standard_policy
    
    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load threat detection patterns."""
        
        return {
            "command_injection": [
                r";\s*(rm|del|format|shutdown)",
                r"\|\s*(nc|netcat|curl|wget)",
                r"&\s*(echo|cat|grep).*>",
                r"`[^`]*`",  # Command substitution
                r"\$\([^)]*\)"  # Command substitution
            ],
            
            "path_traversal": [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e%5c"
            ],
            
            "privilege_escalation": [
                r"sudo\s+su",
                r"su\s+-",
                r"chmod\s+777",
                r"chown\s+root",
                r"setuid",
                r"setgid"
            ],
            
            "data_exfiltration": [
                r"curl.*-d\s+@",
                r"wget.*--post-file",
                r"nc.*<",
                r"cat.*\|.*nc",
                r"base64.*\|.*curl"
            ],
            
            "system_manipulation": [
                r"crontab\s+-e",
                r"/etc/passwd",
                r"/etc/shadow",
                r"registry\s+add",
                r"reg\s+add"
            ]
        }
    
    def _setup_default_permissions(self) -> None:
        """Setup default permissions for system components."""
        
        # AI models - restricted permissions
        self.granted_permissions["ai_models"] = {
            PermissionType.NETWORK_ACCESS
        }
        
        # MCP server - broader permissions
        self.granted_permissions["mcp_server"] = {
            PermissionType.FILE_READ,
            PermissionType.FILE_WRITE,
            PermissionType.SYSTEM_COMMAND,
            PermissionType.NETWORK_ACCESS
        }
        
        # Execution controller - controlled permissions
        self.granted_permissions["execution_controller"] = {
            PermissionType.FILE_READ,
            PermissionType.FILE_WRITE,
            PermissionType.SYSTEM_COMMAND,
            PermissionType.PROCESS_CONTROL
        }
        
        # Desktop app - UI permissions only
        self.granted_permissions["desktop_app"] = {
            PermissionType.FILE_READ
        }
    
    def _initialize_sandboxing(self) -> None:
        """Initialize sandboxing environment."""
        
        if not self.sandbox_enabled:
            return
        
        # Create sandbox directories
        sandbox_root = Path.home() / ".ai_os_sandbox"
        sandbox_root.mkdir(exist_ok=True)
        
        self.sandbox_paths = [
            str(sandbox_root / "temp"),
            str(sandbox_root / "data"),
            str(sandbox_root / "logs")
        ]
        
        # Create sandbox directories
        for path in self.sandbox_paths:
            Path(path).mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Sandbox initialized: {sandbox_root}")
    
    async def check_security(self, 
                           operation: str, 
                           context: Dict[str, Any],
                           requester: str = "unknown") -> Tuple[bool, str, ThreatLevel]:
        """
        Comprehensive security check for an operation.
        
        Returns:
            Tuple of (allowed, reason, threat_level)
        """
        
        try:
            self.stats["security_checks"] += 1
            
            # Basic security level check
            if self.security_level == SecurityLevel.UNRESTRICTED:
                self.stats["safe_operations"] += 1
                return True, "Unrestricted mode - all operations allowed", ThreatLevel.BENIGN
            
            # Analyze operation for threats
            threat_level = await self._analyze_threat_level(operation, context)
            
            # Check against current policy
            policy_check = await self._check_policy_compliance(operation, context, requester)
            
            # Permission check
            permission_check = await self._check_permissions(operation, context, requester)
            
            # Path safety check
            path_check = await self._check_path_safety(operation, context)
            
            # Pattern matching check
            pattern_check = await self._check_threat_patterns(operation, context)
            
            # Combine all checks
            overall_allowed = (
                policy_check["allowed"] and 
                permission_check["allowed"] and 
                path_check["allowed"] and 
                pattern_check["allowed"]
            )
            
            # Determine reason for denial
            reasons = []
            if not policy_check["allowed"]:
                reasons.append(policy_check["reason"])
            if not permission_check["allowed"]:
                reasons.append(permission_check["reason"])
            if not path_check["allowed"]:
                reasons.append(path_check["reason"])
            if not pattern_check["allowed"]:
                reasons.append(pattern_check["reason"])
            
            final_reason = "; ".join(reasons) if reasons else "Operation approved"
            
            # Log security decision
            await self._log_security_decision(
                operation, context, requester, overall_allowed, final_reason, threat_level
            )
            
            # Handle security violations
            if not overall_allowed:
                await self._handle_security_violation(
                    operation, context, requester, final_reason, threat_level
                )
                self.stats["threats_blocked"] += 1
            else:
                self.stats["safe_operations"] += 1
            
            return overall_allowed, final_reason, threat_level
            
        except Exception as e:
            logger.error(f"Security check error: {e}")
            # Fail secure - deny on error
            return False, f"Security system error: {e}", ThreatLevel.SUSPICIOUS
    
    async def _analyze_threat_level(self, operation: str, context: Dict[str, Any]) -> ThreatLevel:
        """Analyze operation to determine threat level."""
        
        try:
            # Check for obviously malicious patterns
            malicious_indicators = [
                "rm -rf /", "del /f /q C:\\", "format C:",
                "echo '' > /etc/passwd", "shutdown -h now",
                "curl.*evil", "wget.*malware"
            ]
            
            operation_lower = operation.lower()
            
            for indicator in malicious_indicators:
                if re.search(indicator.lower(), operation_lower):
                    return ThreatLevel.MALICIOUS
            
            # Check for dangerous operations
            dangerous_patterns = [
                "chmod 777", "chown root", "sudo su", "su -",
                "crontab -e", "/etc/", "registry add", "reg add",
                "nc -e", "netcat -e", "> /dev/"
            ]
            
            for pattern in dangerous_patterns:
                if pattern.lower() in operation_lower:
                    return ThreatLevel.DANGEROUS
            
            # Check for suspicious operations
            suspicious_patterns = [
                "curl", "wget", "nc ", "netcat", "base64",
                "eval", "exec", "__import__", "compile",
                "system(", "popen(", "subprocess"
            ]
            
            for pattern in suspicious_patterns:
                if pattern.lower() in operation_lower:
                    return ThreatLevel.SUSPICIOUS
            
            return ThreatLevel.BENIGN
            
        except Exception as e:
            logger.error(f"Threat analysis error: {e}")
            return ThreatLevel.SUSPICIOUS
    
    async def _check_policy_compliance(self, operation: str, context: Dict[str, Any], requester: str) -> Dict[str, Any]:
        """Check operation against current security policy."""
        
        if not self.current_policy:
            return {"allowed": True, "reason": "No policy defined"}
        
        # Check blocked patterns
        operation_lower = operation.lower()
        
        for pattern in self.current_policy.blocked_patterns:
            if re.search(pattern.lower(), operation_lower):
                return {"allowed": False, "reason": f"Blocked pattern detected: {pattern}"}
        
        # Check execution time limits
        estimated_time = context.get("estimated_execution_time", 0)
        if estimated_time > self.current_policy.max_execution_time:
            return {
                "allowed": False, 
                "reason": f"Operation exceeds time limit: {estimated_time}s > {self.current_policy.max_execution_time}s"
            }
        
        return {"allowed": True, "reason": "Policy compliance check passed"}
    
    async def _check_permissions(self, operation: str, context: Dict[str, Any], requester: str) -> Dict[str, Any]:
        """Check if requester has necessary permissions."""
        
        # Determine required permission type
        required_permission = self._determine_required_permission(operation, context)
        
        if not required_permission:
            return {"allowed": True, "reason": "No specific permission required"}
        
        # Check if requester has permission
        requester_permissions = self.granted_permissions.get(requester, set())
        
        if required_permission in requester_permissions:
            return {"allowed": True, "reason": f"Permission {required_permission.value} granted"}
        else:
            return {
                "allowed": False, 
                "reason": f"Permission {required_permission.value} not granted to {requester}"
            }
    
    def _determine_required_permission(self, operation: str, context: Dict[str, Any]) -> Optional[PermissionType]:
        """Determine what permission is required for an operation."""
        
        operation_lower = operation.lower()
        tool_name = context.get("tool_name", "").lower()
        
        # File operations
        if any(keyword in operation_lower for keyword in ["read", "cat", "type", "get"]):
            return PermissionType.FILE_READ
        
        if any(keyword in operation_lower for keyword in ["write", "create", "modify", "delete", "rm", "del"]):
            return PermissionType.FILE_WRITE
        
        if any(keyword in operation_lower for keyword in ["execute", "run", "launch", "start"]):
            return PermissionType.FILE_EXECUTE
        
        # Network operations
        if any(keyword in operation_lower for keyword in ["curl", "wget", "http", "download", "upload"]):
            return PermissionType.NETWORK_ACCESS
        
        # System operations
        if any(keyword in operation_lower for keyword in ["command", "system", "shell", "cmd", "bash"]):
            return PermissionType.SYSTEM_COMMAND
        
        # Process operations
        if any(keyword in operation_lower for keyword in ["kill", "process", "service", "daemon"]):
            return PermissionType.PROCESS_CONTROL
        
        # Tool-based permissions
        if "system" in tool_name:
            return PermissionType.SYSTEM_COMMAND
        elif "file" in tool_name:
            return PermissionType.FILE_WRITE
        elif "network" in tool_name or "browser" in tool_name:
            return PermissionType.NETWORK_ACCESS
        
        return None
    
    async def _check_path_safety(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if operation involves safe file paths."""
        
        if not self.current_policy:
            return {"allowed": True, "reason": "No policy defined"}
        
        # Extract file paths from operation and context
        paths = self._extract_paths(operation, context)
        
        if not paths:
            return {"allowed": True, "reason": "No file paths detected"}
        
        # Check each path
        for path in paths:
            # Check against blocked paths
            for blocked_path in self.current_policy.blocked_paths:
                if str(path).startswith(blocked_path):
                    return {"allowed": False, "reason": f"Access to blocked path: {path}"}
            
            # Check if path is in allowed paths (if sandboxing enabled)
            if self.sandbox_enabled and self.current_policy.enable_sandboxing:
                allowed = False
                
                for allowed_path in self.current_policy.allowed_paths + self.sandbox_paths:
                    if str(path).startswith(allowed_path):
                        allowed = True
                        break
                
                if not allowed:
                    return {"allowed": False, "reason": f"Path not in sandbox: {path}"}
        
        return {"allowed": True, "reason": "Path safety check passed"}
    
    def _extract_paths(self, operation: str, context: Dict[str, Any]) -> List[Path]:
        """Extract file paths from operation and context."""
        
        paths = []
        
        # Extract from context
        for key, value in context.items():
            if "path" in key.lower() or "file" in key.lower():
                if isinstance(value, str):
                    try:
                        paths.append(Path(value).resolve())
                    except:
                        pass
        
        # Extract from operation string using regex
        path_patterns = [
            r'["\']([/\\]?[\w\-_.~/\\]+)["\']',  # Quoted paths
            r'\s([/\\][\w\-_.~/\\]+)',           # Unquoted absolute paths
            r'\s([\w\-_.~]+[/\\][\w\-_.~/\\]*)', # Relative paths with separators
        ]
        
        for pattern in path_patterns:
            matches = re.findall(pattern, operation)
            for match in matches:
                try:
                    paths.append(Path(match).resolve())
                except:
                    pass
        
        return paths
    
    async def _check_threat_patterns(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check operation against known threat patterns."""
        
        operation_lower = operation.lower()
        
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, operation_lower, re.IGNORECASE):
                    return {
                        "allowed": False, 
                        "reason": f"Threat pattern detected: {threat_type} - {pattern}"
                    }
        
        return {"allowed": True, "reason": "No threat patterns detected"}
    
    async def _log_security_decision(self, 
                                   operation: str, 
                                   context: Dict[str, Any], 
                                   requester: str,
                                   allowed: bool, 
                                   reason: str, 
                                   threat_level: ThreatLevel) -> None:
        """Log security decision for audit trail."""
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation[:200],  # Limit size
            "requester": requester,
            "allowed": allowed,
            "reason": reason,
            "threat_level": threat_level.value,
            "security_level": self.security_level.value,
            "context": {k: str(v)[:100] for k, v in context.items()}  # Limit context size
        }
        
        self.audit_log.append(audit_entry)
        
        # Limit audit log size
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
        
        logger.debug(f"Security decision logged: {allowed} - {reason}")
    
    async def _handle_security_violation(self, 
                                       operation: str,
                                       context: Dict[str, Any], 
                                       requester: str,
                                       reason: str, 
                                       threat_level: ThreatLevel) -> None:
        """Handle detected security violation."""
        
        violation = SecurityViolation(
            violation_id=f"violation_{int(time.time() * 1000)}",
            timestamp=datetime.now(),
            violation_type="security_policy_violation",
            threat_level=threat_level,
            description=f"{requester} attempted: {operation[:200]} - {reason}",
            context=context.copy(),
            action_taken="blocked",
            user_notified=False
        )
        
        self.security_violations.append(violation)
        self.stats["violations_detected"] += 1
        
        # Log violation
        logger.warning(f"Security violation: {violation.description}")
        
        # Notify user for high-threat violations
        if threat_level in [ThreatLevel.DANGEROUS, ThreatLevel.MALICIOUS]:
            # This would trigger UI notification in a real implementation
            violation.user_notified = True
            logger.critical(f"HIGH THREAT VIOLATION: {violation.description}")
    
    async def request_permission(self, 
                               requester: str, 
                               permission_type: PermissionType,
                               resource: str, 
                               justification: str) -> bool:
        """Request permission for an operation."""
        
        request = PermissionRequest(
            request_id=f"req_{int(time.time() * 1000)}",
            requester=requester,
            permission_type=permission_type,
            resource=resource,
            justification=justification,
            timestamp=datetime.now()
        )
        
        self.permission_requests.append(request)
        
        # Auto-approve safe requests in permissive mode
        if self.security_level == SecurityLevel.PERMISSIVE:
            if permission_type in [PermissionType.FILE_READ, PermissionType.NETWORK_ACCESS]:
                return await self._approve_permission(request.request_id, "system_auto")
        
        # For now, auto-deny in this implementation
        # In a real system, this would trigger user approval dialog
        request.approved = False
        request.approver = "system_auto"
        
        self.stats["permissions_denied"] += 1
        
        logger.info(f"Permission request denied: {requester} requested {permission_type.value} for {resource}")
        
        return False
    
    async def _approve_permission(self, request_id: str, approver: str) -> bool:
        """Approve a permission request."""
        
        for request in self.permission_requests:
            if request.request_id == request_id:
                request.approved = True
                request.approver = approver
                
                # Grant permission to requester
                if request.requester not in self.granted_permissions:
                    self.granted_permissions[request.requester] = set()
                
                self.granted_permissions[request.requester].add(request.permission_type)
                
                self.stats["permissions_granted"] += 1
                
                logger.info(f"Permission granted: {request.requester} can now {request.permission_type.value}")
                
                return True
        
        return False
    
    def set_security_level(self, level: SecurityLevel) -> None:
        """Set system security level."""
        
        old_level = self.security_level
        self.security_level = level
        
        logger.info(f"Security level changed: {old_level.value} -> {level.value}")
        
        # Adjust policies based on level
        if level == SecurityLevel.UNRESTRICTED:
            logger.warning("SECURITY WARNING: System running in unrestricted mode")
        elif level == SecurityLevel.PARANOID:
            # Revoke all permissions in paranoid mode
            self.granted_permissions.clear()
            logger.info("All permissions revoked due to paranoid security level")
    
    def create_sandbox_path(self, relative_path: str) -> str:
        """Create a path within the sandbox."""
        
        if not self.sandbox_paths:
            raise Exception("Sandboxing not initialized")
        
        sandbox_root = Path(self.sandbox_paths[0]).parent
        full_path = sandbox_root / "temp" / relative_path
        
        # Ensure path is within sandbox
        try:
            full_path.resolve().relative_to(sandbox_root.resolve())
        except ValueError:
            raise Exception(f"Path escape attempt detected: {relative_path}")
        
        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        return str(full_path)
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status."""
        
        return {
            "security_level": self.security_level.value,
            "sandbox_enabled": self.sandbox_enabled,
            "policy_active": self.current_policy is not None,
            "violations_count": len(self.security_violations),
            "recent_violations": [
                asdict(v) for v in self.security_violations[-5:]
            ],
            "granted_permissions": {
                requester: [p.value for p in perms] 
                for requester, perms in self.granted_permissions.items()
            },
            "statistics": self.stats.copy(),
            "audit_log_size": len(self.audit_log)
        }
    
    def get_security_violations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent security violations."""
        
        recent_violations = self.security_violations[-limit:]
        return [asdict(v) for v in recent_violations]
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        
        return self.audit_log[-limit:]
    
    def clear_security_data(self) -> None:
        """Clear security data (for maintenance)."""
        
        self.security_violations.clear()
        self.audit_log.clear()
        self.permission_requests.clear()
        
        # Reset statistics
        for key in self.stats:
            self.stats[key] = 0
        
        logger.info("Security data cleared")
    
    def export_security_report(self) -> str:
        """Export comprehensive security report."""
        
        report_data = {
            "report_timestamp": datetime.now().isoformat(),
            "security_configuration": {
                "security_level": self.security_level.value,
                "sandbox_enabled": self.sandbox_enabled,
                "current_policy": asdict(self.current_policy) if self.current_policy else None
            },
            "statistics": self.stats.copy(),
            "violations_summary": {
                "total_violations": len(self.security_violations),
                "by_threat_level": {
                    level.value: len([v for v in self.security_violations if v.threat_level == level])
                    for level in ThreatLevel
                },
                "recent_violations": [asdict(v) for v in self.security_violations[-10:]]
            },
            "permissions_summary": {
                "total_requesters": len(self.granted_permissions),
                "granted_permissions": {
                    requester: [p.value for p in perms]
                    for requester, perms in self.granted_permissions.items()
                },
                "recent_requests": [asdict(r) for r in self.permission_requests[-10:]]
            }
        }
        
        return json.dumps(report_data, indent=2, default=str)