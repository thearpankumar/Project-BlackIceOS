# Task 8: Safety & Ethics Framework

## What This Task Is About
This task creates the "security guardian" for Kali AI-OS - a comprehensive safety system that prevents misuse:
- **Command Validation** - Blocks dangerous operations like system destruction, unauthorized access
- **Ethical Enforcement** - Ensures all activities comply with ethical hacking principles
- **Legal Compliance** - Validates activities comply with local laws and regulations
- **Emergency Controls** - Instant shutdown capabilities if malicious activity detected
- **Complete Audit Trail** - Forensic-grade logging of all system activities

## Why This Task Is Critical
- **Legal Protection**: Ensures users comply with cybersecurity laws and regulations
- **Ethical Responsibility**: Prevents misuse of powerful automation capabilities
- **Risk Mitigation**: Blocks dangerous operations that could damage systems
- **Accountability**: Maintains complete audit trails for legal and compliance purposes

## How to Complete This Task - Step by Step

### Phase 1: Setup Safety Environment (45 minutes)
```bash
# 1. Create audit and security directories (in VM)
sudo mkdir -p /var/log/kali-ai-os/{audit,security,compliance}
sudo chown -R kali:kali /var/log/kali-ai-os
sudo chmod -R 750 /var/log/kali-ai-os

# 2. Install safety dependencies
pip install cryptography jsonschema validators
pip install psutil netifaces ipaddress

# 3. Create safety directory structure
mkdir -p src/safety/{validation,compliance,monitoring,controls,audit,config}
mkdir -p data/safety/{rules,policies,evidence}
mkdir -p tests/safety/fixtures

# 4. Test security logging
touch /var/log/kali-ai-os/audit/test.log && rm /var/log/kali-ai-os/audit/test.log
echo "Safety environment ready!"
```

### Phase 2: Write Safety Tests First (1.5 hours)
```python
# tests/safety/test_safety_core.py
def test_dangerous_command_blocking():
    """Test blocking of system-destructive commands"""
    # Input: "rm -rf /", "dd if=/dev/zero of=/dev/sda"
    # Expected: Blocked with HIGH risk level

def test_authorized_scope_validation():
    """Test target scope authorization"""
    # Input: nmap command with target outside authorized scope
    # Expected: Blocked with unauthorized_target reason

def test_ethical_violation_detection():
    """Test detection of unethical activities"""
    # Input: data theft, unauthorized access attempts
    # Expected: Blocked with ethical_violation flag

def test_emergency_stop_functionality():
    """Test emergency shutdown works instantly"""
    # Input: Emergency stop trigger
    # Expected: All operations stopped within 1 second

def test_audit_trail_integrity():
    """Test audit logging cannot be tampered"""
    # Input: Log activities, attempt to modify logs
    # Expected: Integrity verification detects tampering
```

### Phase 3: Command Validation System (2.5 hours)
```python
# src/safety/validation/command_validator.py
import re
import ipaddress
from datetime import datetime
from typing import Dict, List, Any, Optional

class CommandValidator:
    def __init__(self):
        # Define dangerous command patterns
        self.dangerous_patterns = {
            'system_destruction': [
                r'rm\s+-rf\s+/',  # Delete root filesystem
                r'del\s+/.*',     # Windows delete
                r'format\s+c:',   # Format C drive
                r'dd\s+if=.*of=/dev/[sh]d[a-z]',  # Overwrite disk
                r'mkfs\.',        # Create filesystem (destroys data)
                r'>\s*/dev/[sh]d[a-z]'  # Write to raw disk
            ],
            'fork_bombs': [
                r':\(\)\{\s*:\|\:&\s*\};:',  # Bash fork bomb
                r'while\s+true.*do.*done',      # Infinite loop
                r'for\s*\(\s*;;\s*\)',          # C-style infinite loop
            ],
            'privilege_escalation': [
                r'sudo\s+su\s*-',               # Switch to root
                r'chmod\s+\+s\s+/bin/',         # Set SUID bit
                r'usermod.*-a.*-G.*sudo',        # Add to sudo group
                r'echo.*>>\s*/etc/sudoers',      # Modify sudoers
                r'passwd\s+root'                # Change root password
            ],
            'malware_download': [
                r'curl.*\|.*bash',              # Download and execute
                r'wget.*\|.*sh',                # Download and execute
                r'powershell.*-enc',             # Encoded PowerShell
                r'certutil.*-urlcache.*-split',  # Windows download utility
                r'bitsadmin\s+/transfer'         # Windows background transfer
            ],
            'network_attacks': [
                r'hping3.*--flood',             # Network flooding
                r'slowhttptest',                # Slow HTTP attacks
                r'nmap.*-sS.*0\.0\.0\.0/0',    # Scan entire internet
                r'masscan.*0\.0\.0\.0/0'       # Mass scan internet
            ]
        }

        # Security tools - allowed but monitored
        self.security_tools = {
            'nmap', 'nikto', 'dirb', 'gobuster', 'burpsuite',
            'wireshark', 'sqlmap', 'metasploit', 'hydra',
            'john', 'hashcat', 'aircrack-ng', 'recon-ng'
        }

        # High-risk operations requiring authorization
        self.high_risk_operations = {
            'network_scanning', 'vulnerability_testing',
            'password_cracking', 'traffic_analysis',
            'exploitation', 'privilege_escalation_testing'
        }

    def validate_command(self, command: str,
                        context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Comprehensive command validation with safety checks"""

        validation_start = datetime.now()

        try:
            # Normalize command for analysis
            normalized_cmd = command.strip().lower()

            # 1. Check for dangerous patterns
            danger_check = self._check_dangerous_patterns(command)
            if not danger_check['safe']:
                return self._create_block_result(
                    'dangerous_operation',
                    danger_check,
                    risk_level='CRITICAL'
                )

            # 2. Validate target authorization
            target_check = self._validate_target_authorization(command, context)
            if not target_check['authorized']:
                return self._create_block_result(
                    'unauthorized_target',
                    target_check,
                    risk_level='HIGH'
                )

            # 3. Check scope boundaries
            scope_check = self._check_scope_boundaries(command, context)
            if not scope_check['within_scope']:
                return self._create_block_result(
                    'scope_violation',
                    scope_check,
                    risk_level='HIGH'
                )

            # 4. Assess operation risk level
            risk_assessment = self._assess_operation_risk(command, context)

            # 5. Check rate limits
            rate_limit_check = self._check_rate_limits(command, context)
            if not rate_limit_check['allowed']:
                return self._create_block_result(
                    'rate_limit_exceeded',
                    rate_limit_check,
                    risk_level='MEDIUM'
                )

            validation_time = (datetime.now() - validation_start).total_seconds()

            return {
                'allowed': True,
                'validation_passed': True,
                'risk_level': risk_assessment['level'],
                'risk_score': risk_assessment['score'],
                'security_tool_detected': self._detect_security_tool(command),
                'target_analysis': target_check,
                'scope_analysis': scope_check,
                'validation_time_ms': validation_time * 1000,
                'recommended_monitoring': risk_assessment['monitoring_required'],
                'approval_required': risk_assessment['requires_approval']
            }

        except Exception as e:
            return {
                'allowed': False,
                'validation_error': True,
                'error': str(e),
                'risk_level': 'HIGH',
                'block_reason': 'validation_failure'
            }

    def _check_dangerous_patterns(self, command: str) -> Dict[str, Any]:
        """Check command against dangerous operation patterns"""
        dangerous_matches = []

        for category, patterns in self.dangerous_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    dangerous_matches.append({
                        'category': category,
                        'pattern': pattern,
                        'severity': 'CRITICAL' if category in ['system_destruction', 'malware_download'] else 'HIGH'
                    })

        if dangerous_matches:
            return {
                'safe': False,
                'dangerous_patterns': dangerous_matches,
                'highest_severity': max(match['severity'] for match in dangerous_matches)
            }

        return {'safe': True, 'dangerous_patterns': []}

    def _validate_target_authorization(self, command: str,
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate targets against authorized scope"""
        if not context or 'authorized_scope' not in context:
            return {
                'authorized': True,
                'reason': 'no_scope_restrictions',
                'targets_found': []
            }

        # Extract all potential targets from command
        targets = self._extract_all_targets(command)

        if not targets:
            return {
                'authorized': True,
                'reason': 'no_targets_detected',
                'targets_found': []
            }

        authorized_scope = context['authorized_scope']
        unauthorized_targets = []

        for target in targets:
            if not self._is_target_in_scope(target, authorized_scope):
                unauthorized_targets.append(target)

        if unauthorized_targets:
            return {
                'authorized': False,
                'unauthorized_targets': unauthorized_targets,
                'all_targets': targets,
                'authorized_scope': authorized_scope,
                'violation_type': 'scope_boundary'
            }

        return {
            'authorized': True,
            'targets_found': targets,
            'all_targets_authorized': True
        }

    def _extract_all_targets(self, command: str) -> List[Dict[str, str]]:
        """Extract IP addresses, domains, and URLs from command"""
        targets = []

        # IPv4 addresses (including CIDR)
        ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:/[0-9]{1,2})?\b'
        for match in re.finditer(ipv4_pattern, command):
            targets.append({
                'type': 'ipv4',
                'value': match.group(),
                'position': match.span()
            })

        # IPv6 addresses
        ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b::1\b|\b::ffff:[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b'
        for match in re.finditer(ipv6_pattern, command):
            targets.append({
                'type': 'ipv6',
                'value': match.group(),
                'position': match.span()
            })

        # Domain names and hostnames
        domain_pattern = r'\b[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+\b'
        for match in re.finditer(domain_pattern, command):
            domain = match.group()
            # Filter out obvious non-domains
            if '.' in domain and not domain.startswith('-') and not domain.endswith('-'):
                targets.append({
                    'type': 'domain',
                    'value': domain,
                    'position': match.span()
                })

        # URLs
        url_pattern = r'https?://[^\s<>"]+'
        for match in re.finditer(url_pattern, command):
            targets.append({
                'type': 'url',
                'value': match.group(),
                'position': match.span()
            })

        return targets

    def _is_target_in_scope(self, target: Dict[str, str],
                           authorized_scope: List[str]) -> bool:
        """Check if target is within authorized scope"""
        target_value = target['value']
        target_type = target['type']

        for scope_item in authorized_scope:
            if self._target_matches_scope(target_value, target_type, scope_item):
                return True

        return False

    def _target_matches_scope(self, target_value: str, target_type: str,
                            scope_item: str) -> bool:
        """Check if target matches a scope item"""
        try:
            # Handle CIDR ranges
            if '/' in scope_item and target_type in ['ipv4', 'ipv6']:
                network = ipaddress.ip_network(scope_item, strict=False)
                target_ip = ipaddress.ip_address(target_value.split('/')[0])
                return target_ip in network

            # Handle wildcard domains
            if scope_item.startswith('*.'):
                domain_pattern = scope_item[2:]  # Remove '*.'
                return target_value.endswith(domain_pattern)

            # Exact match
            if target_value == scope_item:
                return True

            # Handle domain matching
            if target_type == 'domain' and scope_item in target_value:
                return True

        except (ipaddress.AddressValueError, ValueError):
            pass

        return False
```

### Phase 4: Ethical Compliance System (2 hours)
```python
# src/safety/validation/ethical_checker.py
from datetime import datetime
from typing import Dict, List, Any, Optional

class EthicalChecker:
    def __init__(self):
        # Define ethical violation categories
        self.ethical_violations = {
            'unauthorized_access': {
                'severity': 'CRITICAL',
                'description': 'Accessing systems without explicit written authorization',
                'legal_implications': 'Criminal charges under computer fraud laws',
                'patterns': [
                    'accessing_without_permission',
                    'bypassing_authentication',
                    'unauthorized_system_entry'
                ]
            },
            'data_exfiltration': {
                'severity': 'CRITICAL',
                'description': 'Attempting to steal, copy, or exfiltrate sensitive data',
                'legal_implications': 'Data theft, privacy violations, GDPR violations',
                'patterns': [
                    'database_dumping',
                    'file_copying_unauthorized',
                    'credential_harvesting',
                    'personal_data_collection'
                ]
            },
            'service_disruption': {
                'severity': 'HIGH',
                'description': 'Causing intentional service disruption or denial of service',
                'legal_implications': 'Service disruption laws, economic damage',
                'patterns': [
                    'dos_attacks',
                    'resource_exhaustion',
                    'service_flooding',
                    'system_overload'
                ]
            },
            'privacy_violation': {
                'severity': 'HIGH',
                'description': 'Violating user privacy or accessing personal information',
                'legal_implications': 'GDPR, CCPA, privacy law violations',
                'patterns': [
                    'personal_data_access',
                    'privacy_invasion',
                    'unauthorized_monitoring',
                    'personal_information_collection'
                ]
            },
            'system_damage': {
                'severity': 'CRITICAL',
                'description': 'Causing intentional damage to systems or data',
                'legal_implications': 'Computer damage laws, destruction of property',
                'patterns': [
                    'file_deletion',
                    'system_corruption',
                    'data_destruction',
                    'malware_deployment'
                ]
            }
        }

    def check_action_ethics(self, action: Dict[str, Any],
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Comprehensive ethical analysis of proposed action"""

        analysis_start = datetime.now()
        violations_detected = []

        try:
            # 1. Check for direct ethical violations
            direct_violations = self._check_direct_violations(action)
            violations_detected.extend(direct_violations)

            # 2. Analyze action intent and purpose
            intent_analysis = self._analyze_action_intent(action, context)
            if intent_analysis['suspicious']:
                violations_detected.extend(intent_analysis['violations'])

            # 3. Check authorization and consent
            authorization_check = self._verify_authorization(action, context)
            if not authorization_check['authorized']:
                violations_detected.append({
                    'type': 'unauthorized_access',
                    'reason': authorization_check['reason'],
                    'severity': 'CRITICAL'
                })

            # 4. Assess proportionality (means vs. ends)
            proportionality = self._assess_proportionality(action, context)
            if not proportionality['proportional']:
                violations_detected.append({
                    'type': 'disproportionate_action',
                    'reason': proportionality['reason'],
                    'severity': 'MEDIUM'
                })

            # 5. Check for potential collateral damage
            collateral_assessment = self._assess_collateral_risk(action, context)
            if collateral_assessment['high_risk']:
                violations_detected.append({
                    'type': 'collateral_damage_risk',
                    'reason': collateral_assessment['reason'],
                    'severity': 'HIGH'
                })

            analysis_time = (datetime.now() - analysis_start).total_seconds()

            if violations_detected:
                # Determine highest severity
                severities = [v['severity'] for v in violations_detected]
                max_severity = self._get_max_severity(severities)

                return {
                    'ethical_violation': True,
                    'violations': violations_detected,
                    'severity': max_severity,
                    'recommendation': 'BLOCK_ACTION',
                    'requires_human_review': max_severity in ['CRITICAL', 'HIGH'],
                    'legal_risk_assessment': self._assess_legal_risk(violations_detected),
                    'analysis_time_ms': analysis_time * 1000
                }
            else:
                return {
                    'ethical_violation': False,
                    'assessment': 'APPROVED',
                    'confidence_score': intent_analysis.get('confidence', 0.9),
                    'ethical_guidelines_followed': True,
                    'analysis_time_ms': analysis_time * 1000
                }

        except Exception as e:
            return {
                'ethical_violation': True,
                'assessment_error': True,
                'error': str(e),
                'recommendation': 'BLOCK_ACTION',
                'severity': 'HIGH'
            }

    def _check_direct_violations(self, action: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for direct ethical violations in action"""
        violations = []

        action_type = action.get('action', '')
        description = action.get('description', '')
        command = action.get('command', '')

        # Check unauthorized access patterns
        if self._indicates_unauthorized_access(action):
            violations.append({
                'type': 'unauthorized_access',
                'evidence': 'Action indicates unauthorized system access',
                'severity': 'CRITICAL'
            })

        # Check data exfiltration patterns
        if self._indicates_data_exfiltration(action):
            violations.append({
                'type': 'data_exfiltration',
                'evidence': 'Action indicates unauthorized data collection/transfer',
                'severity': 'CRITICAL'
            })

        # Check service disruption patterns
        if self._indicates_service_disruption(action):
            violations.append({
                'type': 'service_disruption',
                'evidence': 'Action may cause service disruption',
                'severity': 'HIGH'
            })

        # Check privacy violations
        if self._indicates_privacy_violation(action):
            violations.append({
                'type': 'privacy_violation',
                'evidence': 'Action may violate user privacy',
                'severity': 'HIGH'
            })

        return violations

    def _indicates_unauthorized_access(self, action: Dict[str, Any]) -> bool:
        """Check if action indicates unauthorized access attempt"""
        unauthorized_patterns = [
            'password_cracking_without_authorization',
            'unauthorized_login_attempt',
            'bypassing_authentication',
            'privilege_escalation_unauthorized',
            'backdoor_creation',
            'unauthorized_shell_access'
        ]

        action_str = str(action).lower()
        return any(pattern.replace('_', ' ') in action_str for pattern in unauthorized_patterns)

    def _verify_authorization(self, action: Dict[str, Any],
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify proper authorization exists for action"""
        if not context:
            return {
                'authorized': False,
                'reason': 'no_context_provided',
                'required_authorization': 'written_consent_and_scope'
            }

        # Check for authorization documentation
        authorization = context.get('authorization', {})

        required_fields = ['assessment_id', 'client_consent', 'scope_definition', 'authorized_by']
        missing_fields = [field for field in required_fields if field not in authorization]

        if missing_fields:
            return {
                'authorized': False,
                'reason': 'incomplete_authorization',
                'missing_fields': missing_fields
            }

        # Verify scope alignment
        if not self._action_within_authorized_scope(action, authorization):
            return {
                'authorized': False,
                'reason': 'action_outside_authorized_scope'
            }

        return {
            'authorized': True,
            'authorization_verified': True,
            'assessment_id': authorization.get('assessment_id')
        }
```

### Phase 5: Emergency Control System (1.5 hours)
```python
# src/safety/controls/emergency_stop.py
import time
import threading
import signal
from datetime import datetime
from typing import Dict, List, Any, Optional

class EmergencyStop:
    def __init__(self):
        self.emergency_active = False
        self.stop_reason = None
        self.stop_timestamp = None
        self.triggered_by = None
        self.stopped_processes = []
        self.alert_sent = False
        self.lock = threading.Lock()

        # Initialize emergency procedures
        self.emergency_procedures = {
            'ai_operations': self._stop_ai_operations,
            'tool_execution': self._stop_tool_execution,
            'automation_engine': self._stop_automation,
            'network_operations': self._stop_network_operations,
            'file_operations': self._stop_file_operations
        }

    def trigger_emergency_stop(self, reason: str, triggered_by: str,
                              evidence: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger immediate emergency stop of all operations"""

        with self.lock:
            if self.emergency_active:
                return {
                    'success': False,
                    'reason': 'emergency_already_active',
                    'current_emergency': {
                        'reason': self.stop_reason,
                        'triggered_by': self.triggered_by,
                        'timestamp': self.stop_timestamp
                    }
                }

            emergency_start = time.time()

            # Set emergency state
            self.emergency_active = True
            self.stop_reason = reason
            self.stop_timestamp = datetime.now()
            self.triggered_by = triggered_by

            stop_results = []

            try:
                # Execute emergency procedures in priority order
                for system_name, stop_function in self.emergency_procedures.items():
                    try:
                        print(f"EMERGENCY: Stopping {system_name}...")
                        stop_result = stop_function()
                        stop_result['system'] = system_name
                        stop_results.append(stop_result)

                        if stop_result['success']:
                            self.stopped_processes.append(system_name)
                        else:
                            print(f"WARNING: Failed to stop {system_name}: {stop_result.get('error', 'Unknown error')}")

                    except Exception as e:
                        error_result = {
                            'system': system_name,
                            'success': False,
                            'error': str(e)
                        }
                        stop_results.append(error_result)
                        print(f"ERROR: Exception stopping {system_name}: {e}")

                # Create forensic evidence package
                evidence_package = self._create_evidence_package(reason, evidence)

                # Send emergency alerts
                alert_result = self._send_emergency_alerts(reason, triggered_by, evidence)

                # Log emergency stop
                self._log_emergency_stop(reason, triggered_by, evidence, stop_results)

                emergency_duration = time.time() - emergency_start

                return {
                    'success': True,
                    'emergency_active': True,
                    'emergency_id': self._generate_emergency_id(),
                    'reason': reason,
                    'triggered_by': triggered_by,
                    'timestamp': self.stop_timestamp.isoformat(),
                    'stopped_systems': stop_results,
                    'systems_stopped_count': len(self.stopped_processes),
                    'response_time_seconds': emergency_duration,
                    'evidence_package_id': evidence_package['id'],
                    'alert_sent': alert_result['success'],
                    'recovery_instructions': self._get_recovery_instructions()
                }

            except Exception as e:
                return {
                    'success': False,
                    'error': f'Emergency stop failed: {str(e)}',
                    'partial_stop': True,
                    'stopped_systems': stop_results
                }

    def _stop_ai_operations(self) -> Dict[str, Any]:
        """Stop all AI processing operations"""
        try:
            # Stop AI inference engines
            # Stop LLM processing
            # Stop decision making
            # Stop learning systems

            return {
                'success': True,
                'operations_stopped': [
                    'llm_processing',
                    'decision_engine',
                    'learning_system',
                    'inference_engine'
                ],
                'stop_method': 'graceful_shutdown'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _stop_tool_execution(self) -> Dict[str, Any]:
        """Stop all security tool execution"""
        try:
            # Kill running security tools
            # Stop command execution
            # Halt workflow execution
            # Stop automation

            return {
                'success': True,
                'operations_stopped': [
                    'security_tools',
                    'command_execution',
                    'workflow_engine',
                    'automation_system'
                ],
                'stop_method': 'forced_termination'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _stop_network_operations(self) -> Dict[str, Any]:
        """Stop all network operations"""
        try:
            # Stop network scanning
            # Close network connections
            # Stop traffic capture
            # Halt data transmission

            return {
                'success': True,
                'operations_stopped': [
                    'network_scanning',
                    'active_connections',
                    'traffic_capture',
                    'data_transmission'
                ],
                'stop_method': 'connection_termination'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def is_emergency_active(self) -> bool:
        """Check if emergency stop is currently active"""
        return self.emergency_active

    def get_emergency_status(self) -> Dict[str, Any]:
        """Get current emergency status"""
        if not self.emergency_active:
            return {
                'emergency_active': False,
                'system_status': 'normal_operations'
            }

        return {
            'emergency_active': True,
            'reason': self.stop_reason,
            'triggered_by': self.triggered_by,
            'timestamp': self.stop_timestamp.isoformat(),
            'stopped_systems': self.stopped_processes,
            'duration_seconds': (datetime.now() - self.stop_timestamp).total_seconds()
        }

    def reset_emergency_stop(self, authorized_by: str,
                           reset_reason: str) -> Dict[str, Any]:
        """Reset emergency stop (requires authorization)"""
        with self.lock:
            if not self.emergency_active:
                return {
                    'success': False,
                    'reason': 'no_emergency_active'
                }

            # Log reset action
            reset_log = {
                'action': 'emergency_reset',
                'authorized_by': authorized_by,
                'reset_reason': reset_reason,
                'timestamp': datetime.now(),
                'previous_emergency': {
                    'reason': self.stop_reason,
                    'triggered_by': self.triggered_by,
                    'duration': (datetime.now() - self.stop_timestamp).total_seconds()
                }
            }

            self._log_emergency_reset(reset_log)

            # Reset emergency state
            self.emergency_active = False
            self.stop_reason = None
            self.stop_timestamp = None
            self.triggered_by = None
            self.stopped_processes = []

            return {
                'success': True,
                'emergency_reset': True,
                'reset_by': authorized_by,
                'system_status': 'operations_resumed'
            }
```

### Phase 6: Audit Database Setup (1 hour)
```bash
# 1. Create audit database initialization scripts
mkdir -p src/safety/audit/database/migrations

# 2. Create comprehensive audit database schema
cat > src/safety/audit/database/migrations/001_audit_schema.sql << 'EOF'
-- Kali AI-OS Safety & Audit Database Schema
-- This creates a forensic-grade audit trail with tamper detection

-- Main audit log table - stores all system activities
CREATE TABLE IF NOT EXISTS audit_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL UNIQUE,      -- UUID for each audit entry
    timestamp TEXT NOT NULL,            -- ISO timestamp
    activity_type TEXT NOT NULL,        -- Type of activity
    activity_data TEXT NOT NULL,        -- JSON data about the activity
    user_context TEXT,                  -- JSON user information
    system_context TEXT,                -- JSON system information
    security_context TEXT,              -- JSON security information
    compliance_metadata TEXT,           -- JSON compliance information
    integrity_hash TEXT NOT NULL,       -- SHA-256 hash for tamper detection
    previous_hash TEXT,                  -- Hash of previous record (blockchain-style)
    hash_algorithm TEXT DEFAULT 'SHA-256',
    custody_id TEXT,                    -- Chain of custody reference
    log_level TEXT DEFAULT 'INFO',      -- INFO, WARN, ERROR, CRITICAL
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Security events table - specific security incidents
CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,      -- UUID for each security event
    audit_id TEXT NOT NULL,             -- Reference to audit_activities
    event_type TEXT NOT NULL,           -- Type of security event
    severity TEXT NOT NULL,             -- LOW, MEDIUM, HIGH, CRITICAL
    threat_indicators TEXT,             -- JSON array of threat indicators
    risk_assessment TEXT,               -- JSON risk assessment data
    incident_correlation TEXT,          -- JSON incident correlation data
    blocked BOOLEAN DEFAULT FALSE,      -- Whether action was blocked
    emergency_triggered BOOLEAN DEFAULT FALSE, -- Whether emergency stop was triggered
    evidence_collected BOOLEAN DEFAULT FALSE,  -- Whether forensic evidence was collected
    response_actions TEXT,              -- JSON array of response actions taken
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_id) REFERENCES audit_activities(audit_id)
);

-- Compliance events table - legal and regulatory compliance
CREATE TABLE IF NOT EXISTS compliance_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compliance_id TEXT NOT NULL UNIQUE, -- UUID for compliance event
    audit_id TEXT NOT NULL,             -- Reference to audit_activities
    legal_framework TEXT,               -- Applicable legal framework
    regulation TEXT,                    -- Specific regulation/law
    compliance_status TEXT NOT NULL,    -- COMPLIANT, NON_COMPLIANT, PENDING_REVIEW
    jurisdiction TEXT,                  -- Legal jurisdiction
    authorization_required BOOLEAN DEFAULT FALSE, -- Whether authorization is needed
    consent_verified BOOLEAN DEFAULT FALSE,       -- Whether user consent exists
    data_protection_impact TEXT,        -- GDPR/CCPA impact assessment
    retention_period INTEGER,           -- Data retention period in days
    legal_risk_level TEXT,              -- LOW, MEDIUM, HIGH, CRITICAL
    remediation_required BOOLEAN DEFAULT FALSE,   -- Whether remediation is needed
    remediation_actions TEXT,           -- JSON array of remediation actions
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_id) REFERENCES audit_activities(audit_id)
);

-- Forensic evidence table - digital evidence collection
CREATE TABLE IF NOT EXISTS forensic_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id TEXT NOT NULL UNIQUE,   -- UUID for evidence package
    incident_id TEXT,                   -- Related incident ID
    audit_id TEXT,                      -- Reference to audit_activities
    evidence_type TEXT NOT NULL,        -- SYSTEM_SNAPSHOT, PROCESS_DUMP, NETWORK_CAPTURE, etc.
    collection_timestamp TEXT NOT NULL, -- When evidence was collected
    evidence_data TEXT NOT NULL,        -- JSON evidence data
    evidence_hash TEXT NOT NULL,        -- SHA-256 hash of evidence
    collection_method TEXT,             -- How evidence was collected
    collector_info TEXT,                -- JSON info about collector (system/user)
    chain_of_custody TEXT,              -- JSON chain of custody record
    integrity_verified BOOLEAN DEFAULT TRUE,      -- Whether integrity check passed
    admissible BOOLEAN DEFAULT TRUE,    -- Whether evidence is legally admissible
    retention_period INTEGER DEFAULT 2555, -- 7 years default retention
    access_log TEXT,                    -- JSON log of who accessed evidence
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_id) REFERENCES audit_activities(audit_id)
);

-- Emergency actions table - emergency stop and response actions
CREATE TABLE IF NOT EXISTS emergency_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emergency_id TEXT NOT NULL UNIQUE, -- UUID for emergency action
    audit_id TEXT NOT NULL,            -- Reference to audit_activities
    trigger_reason TEXT NOT NULL,      -- Why emergency was triggered
    triggered_by TEXT NOT NULL,        -- Who/what triggered emergency
    emergency_type TEXT NOT NULL,      -- FULL_STOP, PARTIAL_STOP, CONTAINMENT
    systems_affected TEXT,             -- JSON array of affected systems
    stop_duration INTEGER,             -- Duration in seconds
    recovery_actions TEXT,             -- JSON array of recovery actions
    impact_assessment TEXT,            -- JSON impact assessment
    lessons_learned TEXT,              -- JSON lessons learned
    follow_up_required BOOLEAN DEFAULT TRUE,     -- Whether follow-up is needed
    incident_report_id TEXT,           -- Reference to incident report
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT,                  -- When emergency was resolved
    FOREIGN KEY (audit_id) REFERENCES audit_activities(audit_id)
);

-- Command validation results table - all command validation attempts
CREATE TABLE IF NOT EXISTS command_validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    validation_id TEXT NOT NULL UNIQUE, -- UUID for validation
    audit_id TEXT NOT NULL,             -- Reference to audit_activities
    command_text TEXT NOT NULL,         -- The command that was validated
    validation_result TEXT NOT NULL,    -- ALLOWED, BLOCKED, REQUIRES_APPROVAL
    risk_level TEXT NOT NULL,           -- LOW, MEDIUM, HIGH, CRITICAL
    risk_score REAL,                    -- Numerical risk score (0.0-1.0)
    threat_types TEXT,                  -- JSON array of detected threat types
    validation_reasons TEXT,            -- JSON array of validation reasons
    target_analysis TEXT,               -- JSON target analysis data
    scope_analysis TEXT,                -- JSON scope analysis data
    ethical_analysis TEXT,              -- JSON ethical analysis data
    compliance_analysis TEXT,           -- JSON compliance analysis data
    validation_time_ms INTEGER,         -- Time taken for validation in milliseconds
    approved_by TEXT,                   -- Who approved if manual approval required
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audit_id) REFERENCES audit_activities(audit_id)
);

-- Create comprehensive indexes for performance and forensic queries
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_activities(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_audit_hash ON audit_activities(integrity_hash);
CREATE INDEX IF NOT EXISTS idx_audit_custody ON audit_activities(custody_id);
CREATE INDEX IF NOT EXISTS idx_audit_level ON audit_activities(log_level);

CREATE INDEX IF NOT EXISTS idx_security_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_blocked ON security_events(blocked);
CREATE INDEX IF NOT EXISTS idx_security_emergency ON security_events(emergency_triggered);
CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_events(created_at);

CREATE INDEX IF NOT EXISTS idx_compliance_status ON compliance_events(compliance_status);
CREATE INDEX IF NOT EXISTS idx_compliance_framework ON compliance_events(legal_framework);
CREATE INDEX IF NOT EXISTS idx_compliance_jurisdiction ON compliance_events(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_compliance_risk ON compliance_events(legal_risk_level);

CREATE INDEX IF NOT EXISTS idx_evidence_type ON forensic_evidence(evidence_type);
CREATE INDEX IF NOT EXISTS idx_evidence_incident ON forensic_evidence(incident_id);
CREATE INDEX IF NOT EXISTS idx_evidence_timestamp ON forensic_evidence(collection_timestamp);
CREATE INDEX IF NOT EXISTS idx_evidence_hash ON forensic_evidence(evidence_hash);

CREATE INDEX IF NOT EXISTS idx_emergency_type ON emergency_actions(emergency_type);
CREATE INDEX IF NOT EXISTS idx_emergency_trigger ON emergency_actions(triggered_by);
CREATE INDEX IF NOT EXISTS idx_emergency_resolved ON emergency_actions(resolved_at);

CREATE INDEX IF NOT EXISTS idx_validation_result ON command_validations(validation_result);
CREATE INDEX IF NOT EXISTS idx_validation_risk ON command_validations(risk_level);
CREATE INDEX IF NOT EXISTS idx_validation_command ON command_validations(command_text);

-- Insert initial audit entry to validate setup
INSERT INTO audit_activities (
    audit_id, timestamp, activity_type, activity_data,
    system_context, integrity_hash
) VALUES (
    'init_' || datetime('now') || '_' || abs(random()),
    datetime('now'),
    'system_initialization',
    '{"action": "audit_database_initialized", "version": "1.0"}',
    '{"component": "audit_database", "status": "initialized"}',
    'initial_setup_hash'
);

-- Validate table creation
SELECT 'Audit database initialization complete. Tables created:' as status;
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
EOF

# 3. Create audit database manager with tamper protection
cat > src/safety/audit/database/audit_db_manager.py << 'EOF'
import sqlite3
import os
import json
import hashlib
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class AuditDatabaseManager:
    def __init__(self, audit_db_path: str = "/var/log/kali-ai-os/audit"):
        self.audit_db_path = Path(audit_db_path)
        self.db_path = self.audit_db_path / "audit.db"
        self.migration_path = Path(__file__).parent / "migrations"

        # Ensure audit directory exists with secure permissions
        self.audit_db_path.mkdir(parents=True, exist_ok=True)
        os.chmod(self.audit_db_path, 0o750)  # Owner and group only

        # Initialize database
        self.init_audit_database()

        # Track last hash for blockchain-style integrity
        self.last_hash = self._get_last_hash()

    def init_audit_database(self):
        """Initialize audit database with automatic migration"""
        try:
            # Check if database exists
            db_exists = self.db_path.exists()

            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign keys and secure settings
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
                conn.execute("PRAGMA synchronous = FULL")  # Ensure data integrity

                if not db_exists:
                    logging.info("Creating new audit database...")
                    self._run_migrations(conn)
                else:
                    logging.info("Audit database exists, verifying schema...")
                    self._verify_schema(conn)

                # Test database health
                self._test_database_health(conn)

                # Set secure permissions on database file
                if self.db_path.exists():
                    os.chmod(self.db_path, 0o640)  # Owner read/write, group read

            logging.info(f"Audit database initialized at: {self.db_path}")
            return True

        except Exception as e:
            logging.error(f"Failed to initialize audit database: {e}")
            return False

    def _run_migrations(self, conn: sqlite3.Connection):
        """Execute all audit migration files"""
        migration_files = sorted(self.migration_path.glob("*.sql"))

        for migration_file in migration_files:
            logging.info(f"Running audit migration: {migration_file.name}")

            with open(migration_file, 'r') as f:
                migration_sql = f.read()

            # Execute migration (handle multiple statements)
            conn.executescript(migration_sql)

        conn.commit()
        logging.info(f"Completed {len(migration_files)} audit migrations")

    def _verify_schema(self, conn: sqlite3.Connection):
        """Verify audit database schema is correct"""
        expected_tables = [
            'audit_activities', 'security_events', 'compliance_events',
            'forensic_evidence', 'emergency_actions', 'command_validations'
        ]

        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)

        existing_tables = [row[0] for row in cursor.fetchall()]

        for table in expected_tables:
            if table not in existing_tables:
                logging.warning(f"Audit table '{table}' missing, re-running migrations")
                self._run_migrations(conn)
                break

    def _test_database_health(self, conn: sqlite3.Connection):
        """Test audit database operations"""
        # Test each audit table
        for table in ['audit_activities', 'security_events', 'compliance_events']:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logging.info(f"Audit table '{table}': {count} records")

    def log_audit_activity(self, activity: Dict[str, Any]) -> str:
        """Log activity with full audit trail and tamper protection"""
        audit_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")

                # Prepare audit record
                audit_record = {
                    'audit_id': audit_id,
                    'timestamp': timestamp,
                    'activity_type': activity.get('type', 'unknown'),
                    'activity_data': json.dumps(activity),
                    'user_context': json.dumps(activity.get('user_context', {})),
                    'system_context': json.dumps(activity.get('system_context', {})),
                    'security_context': json.dumps(activity.get('security_context', {})),
                    'compliance_metadata': json.dumps(activity.get('compliance_metadata', {})),
                    'log_level': activity.get('log_level', 'INFO')
                }

                # Calculate integrity hash
                integrity_hash = self._calculate_integrity_hash(audit_record)
                audit_record['integrity_hash'] = integrity_hash
                audit_record['previous_hash'] = self.last_hash

                # Insert audit record
                conn.execute('''
                    INSERT INTO audit_activities
                    (audit_id, timestamp, activity_type, activity_data, user_context,
                     system_context, security_context, compliance_metadata,
                     integrity_hash, previous_hash, log_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    audit_record['audit_id'], audit_record['timestamp'],
                    audit_record['activity_type'], audit_record['activity_data'],
                    audit_record['user_context'], audit_record['system_context'],
                    audit_record['security_context'], audit_record['compliance_metadata'],
                    audit_record['integrity_hash'], audit_record['previous_hash'],
                    audit_record['log_level']
                ))

                # Update last hash for next record
                self.last_hash = integrity_hash

                conn.commit()
                return audit_id

        except Exception as e:
            logging.error(f"Failed to log audit activity: {e}")
            # Emergency fallback logging
            self._emergency_log_fallback(activity, audit_id, str(e))
            return audit_id

    def log_security_event(self, event: Dict[str, Any], audit_id: str = None) -> str:
        """Log security event with correlation to audit activity"""
        event_id = str(uuid.uuid4())

        # Create audit activity if not provided
        if not audit_id:
            audit_id = self.log_audit_activity({
                'type': 'security_event',
                'security_event': event
            })

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO security_events
                    (event_id, audit_id, event_type, severity, threat_indicators,
                     risk_assessment, blocked, emergency_triggered, evidence_collected,
                     response_actions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event_id, audit_id, event.get('type', 'unknown'),
                    event.get('severity', 'MEDIUM'),
                    json.dumps(event.get('threat_indicators', [])),
                    json.dumps(event.get('risk_assessment', {})),
                    event.get('blocked', False),
                    event.get('emergency_triggered', False),
                    event.get('evidence_collected', False),
                    json.dumps(event.get('response_actions', []))
                ))

                conn.commit()
                return event_id

        except Exception as e:
            logging.error(f"Failed to log security event: {e}")
            return event_id

    def log_command_validation(self, validation: Dict[str, Any], audit_id: str = None) -> str:
        """Log command validation result"""
        validation_id = str(uuid.uuid4())

        # Create audit activity if not provided
        if not audit_id:
            audit_id = self.log_audit_activity({
                'type': 'command_validation',
                'validation': validation
            })

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO command_validations
                    (validation_id, audit_id, command_text, validation_result,
                     risk_level, risk_score, threat_types, validation_reasons,
                     target_analysis, scope_analysis, ethical_analysis,
                     compliance_analysis, validation_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    validation_id, audit_id, validation.get('command', ''),
                    validation.get('result', 'UNKNOWN'),
                    validation.get('risk_level', 'MEDIUM'),
                    validation.get('risk_score', 0.0),
                    json.dumps(validation.get('threat_types', [])),
                    json.dumps(validation.get('reasons', [])),
                    json.dumps(validation.get('target_analysis', {})),
                    json.dumps(validation.get('scope_analysis', {})),
                    json.dumps(validation.get('ethical_analysis', {})),
                    json.dumps(validation.get('compliance_analysis', {})),
                    validation.get('validation_time_ms', 0)
                ))

                conn.commit()
                return validation_id

        except Exception as e:
            logging.error(f"Failed to log command validation: {e}")
            return validation_id

    def get_audit_trail(self, start_time: str = None, end_time: str = None,
                       activity_types: List[str] = None,
                       limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve audit trail with filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = "SELECT * FROM audit_activities WHERE 1=1"
                params = []

                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time)

                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time)

                if activity_types:
                    placeholders = ','.join(['?' for _ in activity_types])
                    query += f" AND activity_type IN ({placeholders})"
                    params.extend(activity_types)

                query += " ORDER BY timestamp DESC"

                if limit:
                    query += " LIMIT ?"
                    params.append(limit)

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                # Convert rows to dictionaries and verify integrity
                audit_records = []
                for row in rows:
                    record = dict(row)

                    # Verify record integrity
                    if self._verify_record_integrity(record):
                        audit_records.append(record)
                    else:
                        # Log integrity violation
                        logging.error(f"Audit integrity violation detected for record {record.get('audit_id')}")

                return audit_records

        except Exception as e:
            logging.error(f"Failed to retrieve audit trail: {e}")
            return []

    def _calculate_integrity_hash(self, record: Dict[str, Any]) -> str:
        """Calculate SHA-256 integrity hash for audit record"""
        # Remove hash fields for calculation
        record_copy = {k: v for k, v in record.items()
                      if k not in ['integrity_hash', 'previous_hash']}

        # Create deterministic string representation
        record_string = json.dumps(record_copy, sort_keys=True, default=str)

        # Calculate SHA-256 hash
        return hashlib.sha256(record_string.encode('utf-8')).hexdigest()

    def _verify_record_integrity(self, record: Dict[str, Any]) -> bool:
        """Verify integrity hash of audit record"""
        try:
            stored_hash = record.get('integrity_hash')
            if not stored_hash:
                return False

            calculated_hash = self._calculate_integrity_hash(record)
            return stored_hash == calculated_hash

        except Exception:
            return False

    def _get_last_hash(self) -> Optional[str]:
        """Get hash of most recent audit record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT integrity_hash FROM audit_activities ORDER BY id DESC LIMIT 1"
                )
                result = cursor.fetchone()
                return result[0] if result else None

        except Exception:
            return None

    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive audit database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}

                # Table counts
                tables = ['audit_activities', 'security_events', 'compliance_events',
                         'forensic_evidence', 'emergency_actions', 'command_validations']

                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]

                # Database size
                stats['database_size_bytes'] = self.db_path.stat().st_size
                stats['database_path'] = str(self.db_path)

                # Recent activity
                cursor = conn.execute("""
                    SELECT activity_type, COUNT(*) as count
                    FROM audit_activities
                    WHERE timestamp >= datetime('now', '-1 day')
                    GROUP BY activity_type
                """)
                stats['recent_activity'] = {row[0]: row[1] for row in cursor.fetchall()}

                return stats

        except Exception as e:
            return {'error': str(e)}
EOF

# 4. Create audit database connection manager
cat > src/safety/audit/database/connection.py << 'EOF'
import os
import logging
from pathlib import Path
from .audit_db_manager import AuditDatabaseManager

# Global audit database manager
_audit_db_manager = None

def get_audit_database_manager(audit_path: str = None) -> AuditDatabaseManager:
    """Get singleton audit database manager"""
    global _audit_db_manager

    if _audit_db_manager is None:
        if audit_path is None:
            # Auto-determine audit path
            if os.path.exists("/var/log/kali-ai-os"):
                audit_path = "/var/log/kali-ai-os/audit"
            else:
                audit_path = "/tmp/kali-ai-os-audit"

        _audit_db_manager = AuditDatabaseManager(audit_path)

    return _audit_db_manager

def initialize_audit_database(audit_path: str = None, force_reset: bool = False) -> bool:
    """Initialize audit database with comprehensive setup"""
    try:
        if force_reset and audit_path:
            # Remove existing audit database for fresh start
            db_path = Path(audit_path) / "audit.db"
            if db_path.exists():
                db_path.unlink()
                logging.info("Existing audit database removed for reset")

        audit_manager = get_audit_database_manager(audit_path)

        # Test audit database operations
        stats = audit_manager.get_database_stats()
        logging.info(f"Audit database ready: {stats}")

        return True

    except Exception as e:
        logging.error(f"Failed to initialize audit database: {e}")
        return False

def check_audit_database_health() -> Dict[str, Any]:
    """Check audit database connection and health"""
    try:
        audit_manager = get_audit_database_manager()
        stats = audit_manager.get_database_stats()

        return {
            'healthy': True,
            'statistics': stats,
            'message': 'Audit database is healthy and secure'
        }

    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'message': 'Audit database connection failed'
        }
EOF

echo "✅ Audit database auto-setup complete!"
```

### Phase 7: Audit & Compliance System with Database Integration (1.5 hours)
```python
# src/safety/audit/audit_logger.py
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .database.connection import get_audit_database_manager, initialize_audit_database

class AuditLogger:
    def __init__(self, audit_log_path: str = "/var/log/kali-ai-os/audit"):
        self.audit_log_path = Path(audit_log_path)

        # Initialize audit database automatically
        if not initialize_audit_database(str(self.audit_log_path)):
            raise Exception("Failed to initialize audit database")

        self.audit_db = get_audit_database_manager(str(self.audit_log_path))

        # Also maintain file-based logs for redundancy
        self.audit_log_path.mkdir(parents=True, exist_ok=True)
        self.activity_log = self.audit_log_path / "activity.log"
        self.security_log = self.audit_log_path / "security.log"
        self.compliance_log = self.audit_log_path / "compliance.log"
        self.forensic_log = self.audit_log_path / "forensic.log"

        # Audit configuration
        self.audit_config = {
            'integrity_protection': True,
            'real_time_logging': True,
            'compression_enabled': False,
            'retention_days': 365,
            'forensic_mode': True
        }

        # Chain of custody tracking
        self.custody_chain = []

    def log_activity(self, activity: Dict[str, Any],
                    log_type: str = 'activity') -> str:
        """Log activity with complete audit trail"""

        audit_id = self._generate_audit_id()
        timestamp = datetime.now()

        try:
            # Create comprehensive audit record
            audit_record = {
                'audit_id': audit_id,
                'timestamp': timestamp.isoformat(),
                'log_type': log_type,
                'activity_type': activity.get('type', 'unknown'),
                'activity_details': activity,
                'system_context': self._capture_system_context(),
                'user_context': self._capture_user_context(),
                'security_context': self._capture_security_context(),
                'compliance_metadata': self._generate_compliance_metadata(activity)
            }

            # Add integrity protection
            if self.audit_config['integrity_protection']:
                audit_record['integrity_hash'] = self._calculate_integrity_hash(audit_record)
                audit_record['previous_hash'] = self._get_previous_hash(log_type)
                audit_record['hash_algorithm'] = 'SHA-256'

            # Add chain of custody entry
            custody_entry = self._create_custody_entry(audit_record)
            self.custody_chain.append(custody_entry)
            audit_record['custody_id'] = custody_entry['custody_id']

            # Write to appropriate log file
            log_file = self._get_log_file(log_type)
            self._write_audit_record(log_file, audit_record)

            # Real-time alerting for critical events
            if self._is_critical_event(activity):
                self._send_real_time_alert(audit_record)

            return audit_id

        except Exception as e:
            # Emergency logging fallback
            fallback_record = {
                'audit_id': audit_id,
                'timestamp': timestamp.isoformat(),
                'error': 'audit_logging_failed',
                'exception': str(e),
                'activity_summary': str(activity)[:200]
            }

            self._emergency_log(fallback_record)
            return audit_id

    def log_security_event(self, event: Dict[str, Any]) -> str:
        """Log security-specific events"""
        enhanced_event = {
            **event,
            'event_category': 'security',
            'risk_assessment': self._assess_security_risk(event),
            'threat_indicators': self._extract_threat_indicators(event),
            'incident_correlation': self._correlate_with_incidents(event)
        }

        return self.log_activity(enhanced_event, 'security')

    def log_compliance_event(self, event: Dict[str, Any]) -> str:
        """Log compliance-related events"""
        enhanced_event = {
            **event,
            'event_category': 'compliance',
            'legal_framework': self._determine_legal_framework(event),
            'compliance_status': self._check_compliance_status(event),
            'regulatory_requirements': self._identify_regulatory_requirements(event)
        }

        return self.log_activity(enhanced_event, 'compliance')

    def collect_forensic_evidence(self, incident: Dict[str, Any]) -> str:
        """Collect forensic evidence for incidents"""
        evidence_id = self._generate_evidence_id()

        forensic_package = {
            'evidence_id': evidence_id,
            'incident_id': incident.get('incident_id'),
            'collection_timestamp': datetime.now().isoformat(),
            'incident_details': incident,
            'system_snapshot': self._capture_system_snapshot(),
            'process_information': self._capture_process_info(),
            'network_state': self._capture_network_state(),
            'file_system_state': self._capture_filesystem_state(),
            'memory_artifacts': self._capture_memory_artifacts(),
            'collector_information': {
                'tool': 'Kali AI-OS Forensic Collector',
                'version': '1.0',
                'collected_by': 'automated_system'
            }
        }

        # Calculate evidence integrity hash
        forensic_package['evidence_hash'] = self._calculate_evidence_hash(forensic_package)

        # Create chain of custody
        custody_record = {
            'evidence_id': evidence_id,
            'collected_at': datetime.now().isoformat(),
            'collected_by': 'kali_ai_os_system',
            'integrity_verified': True,
            'custody_transfers': []
        }

        forensic_package['chain_of_custody'] = custody_record

        # Store forensic evidence
        self.log_activity(forensic_package, 'forensic')

        return evidence_id

    def get_audit_trail(self, start_time: datetime = None,
                       end_time: datetime = None,
                       activity_types: List[str] = None,
                       limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve audit trail with filtering"""
        audit_records = []

        try:
            # Read from all log files
            for log_file in [self.activity_log, self.security_log,
                           self.compliance_log, self.forensic_log]:
                if log_file.exists():
                    records = self._read_log_file(log_file, start_time, end_time,
                                                activity_types, limit)
                    audit_records.extend(records)

            # Sort by timestamp
            audit_records.sort(key=lambda x: x.get('timestamp', ''))

            # Apply limit
            if limit:
                audit_records = audit_records[:limit]

            # Verify integrity of returned records
            verified_records = []
            for record in audit_records:
                if self._verify_record_integrity(record):
                    verified_records.append(record)
                else:
                    # Log integrity violation
                    self.log_security_event({
                        'type': 'audit_integrity_violation',
                        'record_id': record.get('audit_id'),
                        'violation_type': 'hash_mismatch'
                    })

            return verified_records

        except Exception as e:
            self.log_security_event({
                'type': 'audit_trail_access_error',
                'error': str(e)
            })
            return []

    def _calculate_integrity_hash(self, record: Dict[str, Any]) -> str:
        """Calculate SHA-256 integrity hash for audit record"""
        # Remove hash fields for calculation
        record_copy = {k: v for k, v in record.items()
                      if k not in ['integrity_hash', 'previous_hash']}

        # Create deterministic string representation
        record_string = json.dumps(record_copy, sort_keys=True, default=str)

        # Calculate SHA-256 hash
        return hashlib.sha256(record_string.encode('utf-8')).hexdigest()

    def _capture_system_context(self) -> Dict[str, Any]:
        """Capture comprehensive system context"""
        return {
            'hostname': self._get_hostname(),
            'operating_system': self._get_os_info(),
            'python_version': self._get_python_version(),
            'kali_ai_os_version': '1.0',
            'system_time': datetime.now().isoformat(),
            'timezone': str(datetime.now().astimezone().tzinfo),
            'process_id': os.getpid(),
            'user_id': os.getuid() if hasattr(os, 'getuid') else 'unknown',
            'working_directory': os.getcwd()
        }
```

### Phase 7: Real-time Monitoring (1 hour)
```python
# src/safety/monitoring/threat_detector.py
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class ThreatDetector:
    def __init__(self):
        self.threat_patterns = {
            'privilege_escalation': [
                r'sudo\s+su\s*-',
                r'chmod\s+\+s\s+/bin/',
                r'usermod.*-a.*-G.*sudo',
                r'echo.*>>\s*/etc/sudoers'
            ],
            'data_exfiltration': [
                r'scp.*\*.*@',
                r'rsync.*ssh.*\*',
                r'tar.*czf.*\|.*ssh',
                r'mysqldump.*\|.*gzip.*\|.*base64'
            ],
            'system_reconnaissance': [
                r'find\s+/.*-type\s+f.*-name\s+.*passwd',
                r'grep.*-r.*password.*/',
                r'locate.*\.key$',
                r'find.*-perm.*4000'
            ],
            'persistence_mechanisms': [
                r'crontab\s+-e',
                r'echo.*>>.*\.bashrc',
                r'systemctl.*enable.*malicious',
                r'chkconfig.*on'
            ]
        }

        self.behavioral_indicators = {
            'unusual_file_access': {
                'patterns': ['/etc/passwd', '/etc/shadow', '/.ssh/', '/home/*/.ssh/'],
                'threshold': 5,  # Access to 5+ sensitive files
                'time_window': 300  # Within 5 minutes
            },
            'rapid_scanning': {
                'command_pattern': r'nmap.*-p.*-T[4-5]',
                'threshold': 10,  # 10+ rapid scans
                'time_window': 600  # Within 10 minutes
            },
            'mass_execution': {
                'threshold': 50,  # 50+ commands
                'time_window': 300  # Within 5 minutes
            }
        }

        # Track activity for behavioral analysis
        self.activity_history = []
        self.threat_scores = {}

    def analyze_command_threat(self, command: str,
                              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze command for threat indicators"""

        threat_analysis = {
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'threat_detected': False,
            'threat_types': [],
            'risk_score': 0.0,
            'indicators': []
        }

        try:
            # Check against known threat patterns
            for threat_type, patterns in self.threat_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, command, re.IGNORECASE):
                        threat_analysis['threat_detected'] = True
                        threat_analysis['threat_types'].append(threat_type)
                        threat_analysis['indicators'].append({
                            'type': 'pattern_match',
                            'threat_category': threat_type,
                            'matched_pattern': pattern
                        })

            # Calculate risk score
            base_risk = len(threat_analysis['threat_types']) * 0.3

            # Add risk for specific threat types
            high_risk_threats = ['privilege_escalation', 'data_exfiltration']
            for threat_type in threat_analysis['threat_types']:
                if threat_type in high_risk_threats:
                    base_risk += 0.4

            threat_analysis['risk_score'] = min(1.0, base_risk)

            # Determine risk level
            if threat_analysis['risk_score'] >= 0.8:
                threat_analysis['risk_level'] = 'CRITICAL'
            elif threat_analysis['risk_score'] >= 0.6:
                threat_analysis['risk_level'] = 'HIGH'
            elif threat_analysis['risk_score'] >= 0.3:
                threat_analysis['risk_level'] = 'MEDIUM'
            else:
                threat_analysis['risk_level'] = 'LOW'

            # Add to activity history for behavioral analysis
            self.activity_history.append({
                'command': command,
                'timestamp': datetime.now(),
                'threat_score': threat_analysis['risk_score'],
                'threat_types': threat_analysis['threat_types']
            })

            # Behavioral analysis
            behavioral_threats = self._analyze_behavioral_patterns()
            if behavioral_threats:
                threat_analysis['behavioral_threats'] = behavioral_threats
                threat_analysis['threat_detected'] = True

            return threat_analysis

        except Exception as e:
            return {
                'command': command,
                'threat_detected': True,
                'error': str(e),
                'risk_level': 'HIGH',
                'analysis_failed': True
            }

    def _analyze_behavioral_patterns(self) -> List[Dict[str, Any]]:
        """Analyze behavioral patterns for threats"""
        behavioral_threats = []
        current_time = datetime.now()

        # Check for rapid command execution
        recent_commands = [
            activity for activity in self.activity_history
            if (current_time - activity['timestamp']).total_seconds() < 300
        ]

        if len(recent_commands) > 50:
            behavioral_threats.append({
                'type': 'rapid_execution',
                'description': 'Unusually high command execution rate',
                'command_count': len(recent_commands),
                'time_window': 300
            })

        # Check for escalating threat scores
        if len(recent_commands) >= 5:
            avg_threat_score = sum(cmd['threat_score'] for cmd in recent_commands) / len(recent_commands)
            if avg_threat_score > 0.5:
                behavioral_threats.append({
                    'type': 'escalating_threats',
                    'description': 'Increasing threat level in recent activities',
                    'average_threat_score': avg_threat_score
                })

        return behavioral_threats
```

### Phase 8: Integration & Testing (1 hour)
```python
# Test complete safety framework
async def test_complete_safety_framework():
    # 1. Initialize safety components
    validator = CommandValidator()
    ethical_checker = EthicalChecker()
    emergency_stop = EmergencyStop()
    audit_logger = AuditLogger()
    threat_detector = ThreatDetector()

    # 2. Test dangerous command blocking
    dangerous_cmd = "rm -rf /"
    validation_result = validator.validate_command(dangerous_cmd)
    assert validation_result['allowed'] == False
    assert validation_result['risk_level'] == 'CRITICAL'

    # 3. Test ethical violation detection
    unethical_action = {
        'action': 'unauthorized_data_exfiltration',
        'description': 'Steal customer database'
    }
    ethical_result = ethical_checker.check_action_ethics(unethical_action)
    assert ethical_result['ethical_violation'] == True

    # 4. Test emergency stop
    emergency_result = emergency_stop.trigger_emergency_stop(
        "Malicious activity detected",
        "threat_detector"
    )
    assert emergency_result['success'] == True
    assert emergency_stop.is_emergency_active() == True

    # 5. Test audit logging
    audit_id = audit_logger.log_security_event({
        'type': 'blocked_dangerous_command',
        'command': dangerous_cmd,
        'block_reason': 'system_destruction_attempt'
    })
    assert audit_id is not None

    # 6. Test threat detection
    threat_analysis = threat_detector.analyze_command_threat("sudo su -")
    assert threat_analysis['threat_detected'] == True
    assert 'privilege_escalation' in threat_analysis['threat_types']

    print("Safety framework working correctly!")

# Performance testing
def test_safety_performance():
    validator = CommandValidator()

    # Test validation speed
    commands = [
        "nmap -sS example.com",
        "nikto -h https://example.com",
        "rm -rf /tmp/test",
        "sudo apt update"
    ] * 100

    start_time = time.time()
    for cmd in commands:
        result = validator.validate_command(cmd)
    validation_time = time.time() - start_time

    print(f"Validated 400 commands in {validation_time:.2f}s")
    assert validation_time < 2.0  # Should validate 400 commands in under 2 seconds
```

## Overview
Build a comprehensive safety and ethics framework that validates all AI actions, ensures legal compliance, prevents malicious activities, and maintains complete audit trails. This system acts as the security guardian for all AI operations.

## Directory Structure
```
Samsung-AI-os/
├── kali-ai-os/
│   ├── src/
│   │   ├── safety/
│   │   │   ├── __init__.py
│   │   │   ├── validation/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── command_validator.py
│   │   │   │   ├── target_authorizer.py
│   │   │   │   ├── scope_verifier.py
│   │   │   │   ├── ethical_checker.py
│   │   │   │   └── risk_assessor.py
│   │   │   ├── compliance/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── legal_framework.py
│   │   │   │   ├── jurisdiction_checker.py
│   │   │   │   ├── authorization_manager.py
│   │   │   │   ├── consent_tracker.py
│   │   │   │   └── reporting_system.py
│   │   │   ├── monitoring/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── activity_monitor.py
│   │   │   │   ├── anomaly_detector.py
│   │   │   │   ├── threat_detector.py
│   │   │   │   ├── behavior_analyzer.py
│   │   │   │   └── alert_system.py
│   │   │   ├── controls/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── emergency_stop.py
│   │   │   │   ├── action_blocker.py
│   │   │   │   ├── rate_limiter.py
│   │   │   │   ├── session_manager.py
│   │   │   │   └── privilege_controller.py
│   │   │   ├── audit/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── audit_logger.py
│   │   │   │   ├── evidence_collector.py
│   │   │   │   ├── compliance_reporter.py
│   │   │   │   ├── forensic_recorder.py
│   │   │   │   └── chain_of_custody.py
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       ├── safety_config.py
│   │   │       ├── compliance_rules.py
│   │   │       ├── ethical_guidelines.py
│   │   │       └── emergency_procedures.py
│   │   └── tests/
│   │       ├── safety/
│   │       │   ├── test_command_validation.py
│   │       │   ├── test_ethical_checking.py
│   │       │   ├── test_compliance_system.py
│   │       │   ├── test_emergency_controls.py
│   │       │   ├── test_audit_logging.py
│   │       │   └── test_safety_integration.py
│   │       └── fixtures/
│   │           ├── test_scenarios/
│   │           ├── compliance_data/
│   │           └── audit_samples/
```

## Technology Stack
- **Validation**: regex, AST parsing, rule engines
- **Monitoring**: psutil, network monitoring, file system watchers
- **Logging**: structured logging, JSON format, log rotation
- **Compliance**: legal frameworks, jurisdiction databases
- **Security**: cryptographic signatures, integrity checking



## Testing Strategy

### Security Tests (95% coverage minimum)
```bash
cd kali-ai-os
python -m pytest tests/safety/ -v --cov=src.safety --cov-report=html

# Test categories:
# - Command validation and blocking
# - Ethical boundary enforcement
# - Legal compliance checking
# - Emergency stop functionality
# - Audit trail integrity
# - Anomaly detection
# - Privilege escalation prevention
```

### Penetration Testing
```bash
# Test safety framework against attacks
python scripts/test_safety_penetration.py

# Test emergency response times
python scripts/test_emergency_response.py

# Test audit trail tamper resistance
python scripts/test_audit_integrity.py
```

## Deployment & Validation

### Setup Commands
```bash
# 1. Create audit directories with proper permissions
sudo mkdir -p /var/log/kali-ai-os
sudo chown kali:kali /var/log/kali-ai-os
sudo chmod 750 /var/log/kali-ai-os

# 2. Install safety dependencies
pip install cryptography jsonschema

# 3. Initialize safety framework
python -c "
from src.safety.validation.command_validator import CommandValidator
validator = CommandValidator()
print('Safety framework initialized!')
"

# 4. Run comprehensive safety tests
python -m pytest tests/safety/ -v
```

### Success Metrics
- ✅ 100% dangerous command blocking
- ✅ Complete audit trail integrity
- ✅ Emergency stop response <1 second
- ✅ Ethical violation detection >99%
- ✅ Legal compliance validation working
- ✅ Ready for multi-modal interface integration

## Configuration Files

### safety_config.py
```python
SAFETY_CONFIG = {
    'validation': {
        'block_dangerous_commands': True,
        'require_target_authorization': True,
        'enable_ethical_checking': True,
        'risk_assessment_enabled': True
    },
    'monitoring': {
        'anomaly_detection': True,
        'behavior_analysis': True,
        'real_time_alerts': True,
        'threat_detection': True
    },
    'controls': {
        'emergency_stop_enabled': True,
        'rate_limiting_enabled': True,
        'privilege_controls': True,
        'session_timeouts': 3600
    },
    'audit': {
        'log_all_activities': True,
        'integrity_protection': True,
        'forensic_mode': True,
        'retention_days': 365
    }
}
```

## Audit Database Troubleshooting Guide

### Common Audit Database Problems and Solutions:

**1. Audit database not created automatically:**
```bash
# Check if audit directory exists
ls -la /var/log/kali-ai-os/audit/

# Check migration files exist
ls -la src/safety/audit/database/migrations/

# Manually create audit database if needed
cd /var/log/kali-ai-os/audit/
sqlite3 audit.db < /path/to/migrations/001_audit_schema.sql

# Verify audit tables created
sqlite3 audit.db ".tables"
```

**2. Permission errors on audit database:**
```bash
# Check audit directory permissions (should be 750)
ls -ld /var/log/kali-ai-os/audit/

# Check audit database permissions (should be 640)
ls -la /var/log/kali-ai-os/audit/audit.db

# Fix permissions if needed
sudo chmod 750 /var/log/kali-ai-os/audit/
sudo chmod 640 /var/log/kali-ai-os/audit/audit.db
sudo chown kali:kali /var/log/kali-ai-os/audit/audit.db
```

**3. Audit database corruption or integrity issues:**
```bash
# Check database integrity
sqlite3 /var/log/kali-ai-os/audit/audit.db "PRAGMA integrity_check;"

# Check for tampered records (this will show records with hash mismatches)
sqlite3 /var/log/kali-ai-os/audit/audit.db "
SELECT audit_id, timestamp, activity_type, 'INTEGRITY_VIOLATION' as status
FROM audit_activities
WHERE integrity_hash != 'recalculated_hash';
"

# Rebuild audit database if corrupted (WARNING: This removes audit history!)
sudo mv /var/log/kali-ai-os/audit/audit.db /var/log/kali-ai-os/audit/audit.db.corrupted
python -c "from src.safety.audit.database.connection import initialize_audit_database; initialize_audit_database('/var/log/kali-ai-os/audit', force_reset=True)"
```

**4. Application can't connect to audit database:**
```bash
# Test SQLite connection directly
sqlite3 /var/log/kali-ai-os/audit/audit.db "SELECT sqlite_version();"

# Test audit database manager
python -c "
from src.safety.audit.database.connection import check_audit_database_health
health = check_audit_database_health()
print(health)
"

# Check if audit database is locked
lsof /var/log/kali-ai-os/audit/audit.db
```

**5. Audit logging fails:**
```bash
# Check disk space for audit logs
df -h /var/log/

# Test manual audit insertion
sqlite3 /var/log/kali-ai-os/audit/audit.db "
INSERT INTO audit_activities (audit_id, timestamp, activity_type, activity_data, integrity_hash)
VALUES ('test-' || datetime('now'), datetime('now'), 'manual_test', '{\"test\": true}', 'test_hash');
"

# Check if record was inserted
sqlite3 /var/log/kali-ai-os/audit/audit.db "SELECT COUNT(*) FROM audit_activities WHERE activity_type='manual_test';"
```

**6. Security event logging not working:**
```bash
# Check security_events table exists
sqlite3 /var/log/kali-ai-os/audit/audit.db ".schema security_events"

# Test security event insertion
python -c "
from src.safety.audit.database.audit_db_manager import AuditDatabaseManager
db = AuditDatabaseManager('/var/log/kali-ai-os/audit')
event_id = db.log_security_event({
    'type': 'test_security_event',
    'severity': 'LOW',
    'blocked': True
})
print(f'Security event logged: {event_id}')
"
```

**7. Audit trail retrieval fails:**
```bash
# Check audit trail manually
sqlite3 /var/log/kali-ai-os/audit/audit.db "
SELECT audit_id, timestamp, activity_type, log_level
FROM audit_activities
ORDER BY timestamp DESC
LIMIT 10;
"

# Test Python audit trail retrieval
python -c "
from src.safety.audit.database.audit_db_manager import AuditDatabaseManager
db = AuditDatabaseManager('/var/log/kali-ai-os/audit')
trail = db.get_audit_trail(limit=5)
print(f'Retrieved {len(trail)} audit records')
for record in trail:
    print(f'- {record.get(\"timestamp\")}: {record.get(\"activity_type\")}')
"
```

**8. Forensic evidence collection fails:**
```bash
# Check forensic_evidence table
sqlite3 /var/log/kali-ai-os/audit/audit.db "SELECT COUNT(*) FROM forensic_evidence;"

# Test forensic evidence collection
python -c "
from src.safety.audit.audit_logger import AuditLogger
logger = AuditLogger('/var/log/kali-ai-os/audit')
evidence_id = logger.collect_forensic_evidence({
    'incident_id': 'test_incident',
    'type': 'test_evidence'
})
print(f'Forensic evidence collected: {evidence_id}')
"
```

**9. Emergency action logging not working:**
```bash
# Check emergency_actions table structure
sqlite3 /var/log/kali-ai-os/audit/audit.db ".schema emergency_actions"

# Test emergency action logging
sqlite3 /var/log/kali-ai-os/audit/audit.db "
INSERT INTO emergency_actions (emergency_id, audit_id, trigger_reason, triggered_by, emergency_type)
VALUES ('test-emergency', 'test-audit', 'test_trigger', 'manual_test', 'TEST_STOP');
"

# Verify emergency action was logged
sqlite3 /var/log/kali-ai-os/audit/audit.db "SELECT * FROM emergency_actions WHERE emergency_type='TEST_STOP';"
```

**10. Performance issues with audit queries:**
```bash
# Analyze audit query performance
sqlite3 /var/log/kali-ai-os/audit/audit.db "EXPLAIN QUERY PLAN SELECT * FROM audit_activities WHERE timestamp >= datetime('now', '-1 day');"

# Update table statistics
sqlite3 /var/log/kali-ai-os/audit/audit.db "ANALYZE;"

# Check index usage
sqlite3 /var/log/kali-ai-os/audit/audit.db "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';"

# Vacuum database to optimize
sqlite3 /var/log/kali-ai-os/audit/audit.db "VACUUM;"
```

### Comprehensive Audit Database Health Check Script:
```bash
# Create audit health check script
cat > check_audit_db_health.sh << 'EOF'
#!/bin/bash

AUDIT_DB_PATH="/var/log/kali-ai-os/audit/audit.db"

echo "🔍 Audit Database Health Check"
echo "=============================="

# Check if audit database exists
if [ -f "$AUDIT_DB_PATH" ]; then
    echo "✅ Audit database exists: $AUDIT_DB_PATH"
else
    echo "❌ Audit database missing: $AUDIT_DB_PATH"
    exit 1
fi

# Check file permissions (should be 640)
PERMS=$(stat -c "%a" "$AUDIT_DB_PATH")
echo "📋 File permissions: $PERMS"
if [ "$PERMS" = "640" ]; then
    echo "✅ Permissions are secure"
else
    echo "⚠️  Permissions should be 640 for security"
fi

# Check database size
SIZE=$(du -sh "$AUDIT_DB_PATH" | cut -f1)
echo "📊 Database size: $SIZE"

# Test database connection
if sqlite3 "$AUDIT_DB_PATH" "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Check database integrity
INTEGRITY=$(sqlite3 "$AUDIT_DB_PATH" "PRAGMA integrity_check;" | head -1)
if [ "$INTEGRITY" = "ok" ]; then
    echo "✅ Database integrity check passed"
else
    echo "❌ Database integrity check failed: $INTEGRITY"
fi

# Check table counts
echo "📈 Audit table statistics:"
sqlite3 "$AUDIT_DB_PATH" "
SELECT
    'audit_activities: ' || COUNT(*) FROM audit_activities
UNION ALL SELECT
    'security_events: ' || COUNT(*) FROM security_events
UNION ALL SELECT
    'compliance_events: ' || COUNT(*) FROM compliance_events
UNION ALL SELECT
    'forensic_evidence: ' || COUNT(*) FROM forensic_evidence
UNION ALL SELECT
    'emergency_actions: ' || COUNT(*) FROM emergency_actions
UNION ALL SELECT
    'command_validations: ' || COUNT(*) FROM command_validations;
"

# Check recent audit activity
echo "⏰ Recent audit activities:"
sqlite3 "$AUDIT_DB_PATH" "
SELECT
    datetime(timestamp, 'localtime') as local_time,
    activity_type,
    log_level
FROM audit_activities
ORDER BY timestamp DESC
LIMIT 5;
"

# Check for any integrity violations
VIOLATIONS=$(sqlite3 "$AUDIT_DB_PATH" "
SELECT COUNT(*) FROM audit_activities
WHERE integrity_hash = 'tampered' OR integrity_hash IS NULL;
")
if [ "$VIOLATIONS" -eq 0 ]; then
    echo "✅ No integrity violations detected"
else
    echo "⚠️  $VIOLATIONS potential integrity violations found"
fi

# Check WAL mode (for performance)
WAL_MODE=$(sqlite3 "$AUDIT_DB_PATH" "PRAGMA journal_mode;")
echo "📝 Journal mode: $WAL_MODE"

echo "🎉 Audit database health check complete!"
EOF

chmod +x check_audit_db_health.sh
./check_audit_db_health.sh
```

### Emergency Audit Recovery:
```bash
# If audit database is completely corrupted
cat > recover_audit_db.sh << 'EOF'
#!/bin/bash

AUDIT_DIR="/var/log/kali-ai-os/audit"
BACKUP_DIR="/var/log/kali-ai-os/audit/backups"

echo "🚨 Emergency Audit Database Recovery"
echo "===================================="

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup corrupted database
if [ -f "$AUDIT_DIR/audit.db" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    cp "$AUDIT_DIR/audit.db" "$BACKUP_DIR/audit_corrupted_$TIMESTAMP.db"
    echo "📦 Corrupted database backed up to: $BACKUP_DIR/audit_corrupted_$TIMESTAMP.db"
fi

# Try to extract any salvageable data
echo "💾 Attempting to salvage audit data..."
sqlite3 "$AUDIT_DIR/audit.db" .dump > "$BACKUP_DIR/audit_dump_$TIMESTAMP.sql" 2>/dev/null

# Remove corrupted database
rm -f "$AUDIT_DIR/audit.db"

# Reinitialize audit database
echo "🔧 Reinitializing audit database..."
python3 -c "
from src.safety.audit.database.connection import initialize_audit_database
success = initialize_audit_database('$AUDIT_DIR', force_reset=True)
print('✅ Audit database reinitialized' if success else '❌ Failed to reinitialize audit database')
"

# Try to restore salvaged data
if [ -f "$BACKUP_DIR/audit_dump_$TIMESTAMP.sql" ]; then
    echo "🔄 Attempting to restore salvaged data..."
    sqlite3 "$AUDIT_DIR/audit.db" < "$BACKUP_DIR/audit_dump_$TIMESTAMP.sql" 2>/dev/null && echo "✅ Salvaged data restored"
fi

echo "🎉 Emergency recovery complete!"
echo "⚠️  Please review the audit trail integrity after recovery"
EOF

chmod +x recover_audit_db.sh
```

## Next Steps
After completing this task:
1. Integrate safety checks into all system components
2. Create safety dashboard for monitoring
3. Establish incident response procedures
4. Proceed to Task 9: Multi-Modal Interface
