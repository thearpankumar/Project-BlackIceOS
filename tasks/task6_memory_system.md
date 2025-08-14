# Task 6: Persistent Memory System

## What This Task Is About
This task creates the "brain" of Kali AI-OS - a sophisticated memory system that learns and remembers everything:
- **Workflow Memory** - Records and learns from every security assessment workflow
- **Vector Search** - AI-powered semantic search to find relevant past workflows
- **Dual Mode Storage** - Works in both persistent (saves forever) and session-only (temporary) modes
- **Smart Learning** - AI learns from user feedback and optimizes workflows over time
- **Export/Import** - Share workflows between systems and team members

## Why This Task Is Critical
- **Continuous Learning**: AI gets smarter with every use, building institutional knowledge
- **Workflow Reuse**: Never repeat work - find and reuse similar past assessments
- **Team Collaboration**: Share and learn from team member's workflows
- **Institutional Memory**: Preserve cybersecurity knowledge permanently

## How to Complete This Task - Step by Step

### Phase 1: Setup Memory Environment (45 minutes)
```bash
# 1. Install memory system dependencies (in VM)
sudo apt update
sudo apt install -y sqlite3 libsqlite3-dev

# 2. Setup Python environment with uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv add chromadb sentence-transformers sqlalchemy
uv add faiss-cpu numpy scikit-learn
uv add pytest pytest-asyncio --dev
uv sync --all-extras

# 2. Create memory directory structure
mkdir -p src/memory/{core,persistence,retrieval,learning,export,config}
mkdir -p data/{persistent,session}/{workflows,vectors,screenshots,backups}
mkdir -p tests/memory/fixtures

# 3. Test storage permissions
touch data/session/test.db && rm data/session/test.db
echo "Memory directories ready!"
```

### Phase 2: Write Memory Tests First (1.5 hours)
```python
# tests/memory/test_memory_core.py
def test_workflow_storage_and_retrieval():
    """Test basic workflow storage works"""
    # Input: workflow with steps, tools, context
    # Expected: Stored with ID, retrievable with same data

def test_semantic_search_accuracy():
    """Test AI can find relevant workflows"""
    # Input: "web application security testing"
    # Expected: Returns burpsuite, owasp-zap workflows first

def test_dual_mode_switching():
    """Test switching between persistent and session modes"""
    # Input: Mode switch from persistent to session
    # Expected: Data preserved, new storage in temp

def test_workflow_learning_improvement():
    """Test AI learns from user feedback"""
    # Input: User improves workflow, marks as successful
    # Expected: AI updates workflow with improvements

def test_export_import_functionality():
    """Test sharing workflows between systems"""
    # Input: Export workflows to file, import on new system
    # Expected: All workflows transferred with metadata
```

### Phase 3: Automatic SQLite Database Setup (1 hour)
```bash
# 1. Create database initialization scripts
mkdir -p src/memory/database/migrations

# 2. Create automatic SQLite migration script
cat > src/memory/database/migrations/001_memory_schema.sql << 'EOF'
-- Kali AI-OS Memory System Database Schema
-- This file creates the complete memory system structure in SQLite

-- Workflows table - stores all workflow data
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    steps TEXT NOT NULL,               -- JSON array of workflow steps
    tools_used TEXT,                  -- JSON array of tools used
    target_types TEXT,                -- JSON array of supported target types
    context_tags TEXT,                -- JSON array of context tags
    success_rate REAL DEFAULT 1.0,
    usage_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    last_used TEXT,
    version REAL DEFAULT 1.0,
    parent_id INTEGER,                -- Reference to parent workflow for versions
    metadata TEXT,                    -- JSON metadata
    mode TEXT DEFAULT 'session-only', -- persistent or session-only
    embedding_text TEXT,              -- Pre-computed text for embeddings
    FOREIGN KEY (parent_id) REFERENCES workflows(id)
);

-- Vector embeddings table - stores workflow embeddings for semantic search
CREATE TABLE IF NOT EXISTS workflow_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    embedding_vector TEXT NOT NULL,   -- JSON array of embedding values
    model_version TEXT DEFAULT 'all-MiniLM-L6-v2',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

-- Learning patterns table - stores AI learning data
CREATE TABLE IF NOT EXISTS learning_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    pattern_type TEXT NOT NULL,       -- 'improvement', 'optimization', 'user_feedback'
    pattern_data TEXT NOT NULL,       -- JSON data about the pattern
    confidence_score REAL DEFAULT 1.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

-- Memory sessions table - tracks usage sessions
CREATE TABLE IF NOT EXISTS memory_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_start TEXT NOT NULL,
    session_end TEXT,
    mode TEXT NOT NULL,               -- persistent or session-only
    workflows_used TEXT,              -- JSON array of workflow IDs used
    storage_path TEXT,
    metadata TEXT                     -- JSON session metadata
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name);
CREATE INDEX IF NOT EXISTS idx_workflows_tools ON workflows(tools_used);
CREATE INDEX IF NOT EXISTS idx_workflows_context ON workflows(context_tags);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at);
CREATE INDEX IF NOT EXISTS idx_workflows_mode ON workflows(mode);
CREATE INDEX IF NOT EXISTS idx_workflows_success_rate ON workflows(success_rate);

CREATE INDEX IF NOT EXISTS idx_embeddings_workflow_id ON workflow_embeddings(workflow_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON workflow_embeddings(model_version);

CREATE INDEX IF NOT EXISTS idx_patterns_workflow_id ON learning_patterns(workflow_id);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON learning_patterns(pattern_type);

CREATE INDEX IF NOT EXISTS idx_sessions_mode ON memory_sessions(mode);
CREATE INDEX IF NOT EXISTS idx_sessions_start ON memory_sessions(session_start);

-- Insert initial test data for validation
INSERT OR IGNORE INTO workflows (
    name, description, steps, tools_used, context_tags,
    created_at, embedding_text
) VALUES (
    'Basic Network Scan',
    'Simple network reconnaissance using nmap',
    '[{"action": "port_scan", "tool": "nmap", "params": {"type": "syn_scan"}}]',
    '["nmap"]',
    '["network", "reconnaissance", "scanning"]',
    datetime('now'),
    'Basic network scan reconnaissance nmap port scanning'
);

-- Validate table creation
SELECT 'Database initialization complete. Tables created:' as status;
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
EOF

# 3. Create SQLite database manager
cat > src/memory/database/sqlite_manager.py << 'EOF'
import sqlite3
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class SQLiteManager:
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.db_path = self.storage_path / "memory.db"
        self.migration_path = Path(__file__).parent / "migrations"

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.init_database()

    def init_database(self):
        """Initialize SQLite database with automatic migration"""
        try:
            # Check if database exists
            db_exists = self.db_path.exists()

            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                if not db_exists:
                    logging.info("Creating new memory database...")
                    self._run_migrations(conn)
                else:
                    logging.info("Memory database already exists")
                    self._verify_schema(conn)

                # Test database health
                self._test_database_health(conn)

            logging.info(f"Memory database initialized at: {self.db_path}")
            return True

        except Exception as e:
            logging.error(f"Failed to initialize memory database: {e}")
            return False

    def _run_migrations(self, conn: sqlite3.Connection):
        """Execute all migration files"""
        migration_files = sorted(self.migration_path.glob("*.sql"))

        for migration_file in migration_files:
            logging.info(f"Running migration: {migration_file.name}")

            with open(migration_file, 'r') as f:
                migration_sql = f.read()

            # Execute migration (handle multiple statements)
            conn.executescript(migration_sql)

        conn.commit()
        logging.info(f"Completed {len(migration_files)} migrations")

    def _verify_schema(self, conn: sqlite3.Connection):
        """Verify database schema is correct"""
        expected_tables = [
            'workflows', 'workflow_embeddings',
            'learning_patterns', 'memory_sessions'
        ]

        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)

        existing_tables = [row[0] for row in cursor.fetchall()]

        for table in expected_tables:
            if table not in existing_tables:
                logging.warning(f"Table '{table}' missing, re-running migrations")
                self._run_migrations(conn)
                break

    def _test_database_health(self, conn: sqlite3.Connection):
        """Test basic database operations"""
        # Test workflows table
        cursor = conn.execute("SELECT COUNT(*) FROM workflows")
        workflow_count = cursor.fetchone()[0]

        # Test embeddings table
        cursor = conn.execute("SELECT COUNT(*) FROM workflow_embeddings")
        embedding_count = cursor.fetchone()[0]

        logging.info(f"Database health: {workflow_count} workflows, {embedding_count} embeddings")

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute query and return results"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """Execute update query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            stats = {}

            # Table counts
            for table in ['workflows', 'workflow_embeddings', 'learning_patterns', 'memory_sessions']:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # Database size
            stats['database_size_bytes'] = self.db_path.stat().st_size
            stats['database_path'] = str(self.db_path)

            return stats
EOF

# 4. Create automated database connection module
cat > src/memory/database/connection.py << 'EOF'
import os
import logging
from pathlib import Path
from .sqlite_manager import SQLiteManager

# Global database manager instance
_db_manager = None

def get_database_manager(storage_path: str = None) -> SQLiteManager:
    """Get singleton database manager instance"""
    global _db_manager

    if _db_manager is None:
        if storage_path is None:
            # Auto-determine storage path
            if os.path.exists("/tmp"):
                storage_path = "/tmp/kali-ai-os-memory"
            else:
                storage_path = "./data/memory"

        _db_manager = SQLiteManager(storage_path)

    return _db_manager

def initialize_memory_database(storage_path: str = None, force_reset: bool = False) -> bool:
    """Initialize memory database with automatic setup"""
    try:
        if force_reset and storage_path:
            # Remove existing database for fresh start
            db_path = Path(storage_path) / "memory.db"
            if db_path.exists():
                db_path.unlink()
                logging.info("Existing database removed for reset")

        db_manager = get_database_manager(storage_path)

        # Test database operations
        stats = db_manager.get_database_stats()
        logging.info(f"Memory database ready: {stats}")

        return True

    except Exception as e:
        logging.error(f"Failed to initialize memory database: {e}")
        return False

def check_database_health() -> Dict[str, Any]:
    """Check database connection and health"""
    try:
        db_manager = get_database_manager()
        stats = db_manager.get_database_stats()

        return {
            'healthy': True,
            'statistics': stats,
            'message': 'Memory database is healthy'
        }

    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'message': 'Memory database connection failed'
        }
EOF

echo "✅ SQLite database auto-setup complete!"
```

### Phase 4: Core Memory Manager with Database Integration (2.5 hours)
```python
# src/memory/core/memory_manager.py
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..database.connection import get_database_manager, initialize_memory_database

class MemoryManager:
    def __init__(self, mode: str = "session-only", storage_path: str = None):
        self.mode = mode
        self.storage_path = self._determine_storage_path(mode, storage_path)

        # Initialize database automatically
        if not initialize_memory_database(self.storage_path):
            raise Exception("Failed to initialize memory database")

        self.db_manager = get_database_manager(self.storage_path)
        self.workflow_storage = WorkflowStorage(self.db_manager)
        self.vector_store = VectorStore(f"{self.storage_path}/vectors", self.db_manager)
        self.semantic_search = SemanticSearch(self.vector_store)
        self.learner = WorkflowLearner(self)

    def _determine_storage_path(self, mode: str, custom_path: str = None) -> str:
        """Choose storage location based on mode"""
        if custom_path:
            return custom_path

        if mode == "persistent":
            # Check if persistent storage is available
            persistent_path = "/persistent/kali-ai-os"
            if os.path.exists("/persistent"):
                os.makedirs(persistent_path, exist_ok=True)
                return persistent_path
            else:
                # Fall back to session mode if no persistent storage
                print("Warning: Persistent storage not available, using session mode")
                mode = "session-only"

        # Session-only mode (default)
        session_path = "/tmp/kali-ai-os-session"
        os.makedirs(session_path, exist_ok=True)
        return session_path

    def store_workflow(self, workflow: Dict[str, Any]) -> int:
        """Store a new workflow in memory system"""
        try:
            # Add system metadata
            workflow['id'] = None  # Will be assigned by database
            workflow['created_at'] = datetime.now().isoformat()
            workflow['usage_count'] = 0
            workflow['success_rate'] = 1.0
            workflow['last_used'] = datetime.now().isoformat()
            workflow['mode'] = self.mode

            # Store in database
            workflow_id = self.workflow_storage.save_workflow(workflow)
            workflow['id'] = workflow_id

            # Create searchable embedding
            embedding_text = self._create_embedding_text(workflow)
            self.vector_store.add_workflow_embedding(
                workflow_id, embedding_text, workflow
            )

            return workflow_id

        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to store workflow: {str(e)}"
            }

    def semantic_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search workflows using AI semantic understanding"""
        try:
            # Use vector search to find similar workflows
            similar_workflows = self.vector_store.search_similar(query, limit)

            # Enhance results with full workflow data
            enhanced_results = []
            for result in similar_workflows:
                workflow_id = result['id']
                full_workflow = self.workflow_storage.get_workflow(workflow_id)
                if full_workflow:
                    enhanced_result = {
                        **full_workflow,
                        'similarity_score': result['similarity_score'],
                        'match_reason': result.get('match_reason', '')
                    }
                    enhanced_results.append(enhanced_result)

            return enhanced_results

        except Exception as e:
            return []

    def get_contextual_workflows(self, context: Dict) -> List[Dict]:
        """Get workflows that match current context"""
        # Convert context to search query
        context_query = self._context_to_query(context)

        # Get semantic matches
        semantic_results = self.semantic_search(context_query, limit=10)

        # Filter by context tags and target types
        contextual_results = []
        for workflow in semantic_results:
            context_score = self._calculate_context_score(workflow, context)
            if context_score > 0.5:  # Threshold for relevance
                workflow['context_score'] = context_score
                contextual_results.append(workflow)

        # Sort by combined similarity and context scores
        contextual_results.sort(
            key=lambda w: (w['similarity_score'] + w['context_score']) / 2,
            reverse=True
        )

        return contextual_results

    def learn_workflow_improvement(self, workflow_id: int,
                                  improved_steps: List[Dict],
                                  success_feedback: bool = True) -> int:
        """Learn from user improvements to workflows"""
        return self.learner.improve_workflow(
            workflow_id, improved_steps, success_feedback
        )

    def _create_embedding_text(self, workflow: Dict) -> str:
        """Create text for vector embedding"""
        parts = []

        # Add workflow name and description
        parts.append(workflow.get('name', ''))
        parts.append(workflow.get('description', ''))

        # Add tools used
        tools = workflow.get('tools_used', [])
        if tools:
            parts.append(f"Tools: {', '.join(tools)}")

        # Add context tags
        tags = workflow.get('context_tags', [])
        if tags:
            parts.append(f"Context: {', '.join(tags)}")

        # Add step descriptions
        steps = workflow.get('steps', [])
        for step in steps:
            if 'action' in step:
                parts.append(f"Action: {step['action']}")
            if 'description' in step:
                parts.append(step['description'])

        return ' '.join(parts)
```

### Phase 4: Vector Search System (2 hours)
```python
# src/memory/core/vector_store.py
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any

class VectorStore:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

        # Initialize ChromaDB for vector storage
        self.client = chromadb.PersistentClient(path=storage_path)
        self.collection = self.client.get_or_create_collection(
            name="workflow_embeddings",
            metadata={"description": "Kali AI-OS Workflow Embeddings"}
        )

        # Initialize embedding model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def add_workflow_embedding(self, workflow_id: int, text: str,
                             metadata: Dict) -> bool:
        """Add workflow embedding to vector database"""
        try:
            # Generate embedding
            embedding = self.embedder.encode(text)

            # Prepare metadata for storage
            stored_metadata = {
                'workflow_id': workflow_id,
                'name': metadata.get('name', ''),
                'tools_used': json.dumps(metadata.get('tools_used', [])),
                'context_tags': json.dumps(metadata.get('context_tags', [])),
                'created_at': metadata.get('created_at', ''),
                'success_rate': metadata.get('success_rate', 1.0)
            }

            # Add to collection
            self.collection.add(
                embeddings=[embedding.tolist()],
                metadatas=[stored_metadata],
                ids=[str(workflow_id)]
            )

            return True

        except Exception as e:
            print(f"Failed to add embedding: {e}")
            return False

    def search_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for workflows similar to query"""
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode(query)

            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                include=['metadatas', 'distances']
            )

            # Format results
            formatted_results = []
            for i, metadata in enumerate(results['metadatas'][0]):
                # Convert distance to similarity score (0-1)
                distance = results['distances'][0][i]
                similarity_score = max(0, 1 - distance)  # Simple conversion

                result = {
                    'id': metadata['workflow_id'],
                    'name': metadata['name'],
                    'tools_used': json.loads(metadata['tools_used']),
                    'context_tags': json.loads(metadata['context_tags']),
                    'similarity_score': similarity_score,
                    'created_at': metadata['created_at']
                }
                formatted_results.append(result)

            return formatted_results

        except Exception as e:
            print(f"Search failed: {e}")
            return []
```

### Phase 5: Database Testing & Validation (1 hour)
```bash
# 1. Test SQLite database creation
mkdir -p /tmp/test_memory_system
cd /tmp/test_memory_system

# 2. Create database test script
cat > test_memory_db.py << 'EOF'
import sys
import os
import json
import logging
from pathlib import Path

# Add project path to imports
sys.path.insert(0, '/path/to/Samsung-AI-os/kali-ai-os/src')

from memory.database.connection import initialize_memory_database, check_database_health
from memory.database.sqlite_manager import SQLiteManager

def test_database_initialization():
    """Test automatic database setup"""
    print("🔧 Testing SQLite database initialization...")

    test_path = "/tmp/test_memory_db"

    # Initialize database
    result = initialize_memory_database(test_path, force_reset=True)
    assert result == True, "Database initialization failed"

    # Check database health
    health = check_database_health()
    assert health['healthy'] == True, f"Database unhealthy: {health.get('error')}"

    print(f"✅ Database initialized successfully at {test_path}")
    print(f"   Statistics: {health['statistics']}")

def test_database_operations():
    """Test basic database operations"""
    print("🔧 Testing database operations...")

    db_manager = SQLiteManager("/tmp/test_memory_db")

    # Test workflow insertion
    workflow_data = {
        'name': 'Test Workflow',
        'description': 'Test workflow for database validation',
        'steps': '[{"action": "test", "tool": "test_tool"}]',
        'tools_used': '["test_tool"]',
        'context_tags': '["test", "validation"]',
        'created_at': '2024-01-01T00:00:00',
        'embedding_text': 'test workflow validation database'
    }

    # Insert workflow
    result = db_manager.execute_update("""
        INSERT INTO workflows (name, description, steps, tools_used, context_tags, created_at, embedding_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        workflow_data['name'], workflow_data['description'], workflow_data['steps'],
        workflow_data['tools_used'], workflow_data['context_tags'],
        workflow_data['created_at'], workflow_data['embedding_text']
    ))

    assert result > 0, "Failed to insert workflow"

    # Query workflows
    workflows = db_manager.execute_query("SELECT * FROM workflows WHERE name = ?", ('Test Workflow',))
    assert len(workflows) > 0, "Failed to retrieve inserted workflow"

    workflow = workflows[0]
    assert workflow['name'] == 'Test Workflow', "Workflow data mismatch"

    print("✅ Database operations working correctly")
    print(f"   Retrieved workflow: {workflow['name']}")

def test_database_schema():
    """Test database schema is correct"""
    print("🔧 Testing database schema...")

    db_manager = SQLiteManager("/tmp/test_memory_db")

    # Check tables exist
    tables = db_manager.execute_query("""
        SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """)

    table_names = [table['name'] for table in tables]
    expected_tables = ['workflows', 'workflow_embeddings', 'learning_patterns', 'memory_sessions']

    for expected_table in expected_tables:
        assert expected_table in table_names, f"Missing table: {expected_table}"

    print("✅ Database schema is correct")
    print(f"   Tables found: {table_names}")

def test_database_indexes():
    """Test database indexes are created"""
    print("🔧 Testing database indexes...")

    db_manager = SQLiteManager("/tmp/test_memory_db")

    # Check indexes exist
    indexes = db_manager.execute_query("""
        SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'
    """)

    index_names = [index['name'] for index in indexes]
    expected_indexes = [
        'idx_workflows_name', 'idx_workflows_tools', 'idx_workflows_context',
        'idx_embeddings_workflow_id', 'idx_patterns_workflow_id'
    ]

    for expected_index in expected_indexes:
        assert expected_index in index_names, f"Missing index: {expected_index}"

    print("✅ Database indexes are correct")
    print(f"   Indexes found: {len(index_names)}")

def main():
    """Run all database tests"""
    print("🚀 Starting Memory Database Tests...")

    try:
        test_database_initialization()
        test_database_schema()
        test_database_indexes()
        test_database_operations()

        print("\n🎉 All memory database tests passed!")

    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

# 3. Run database tests
python test_memory_db.py

# 4. Test database persistence
echo "🔧 Testing database persistence..."

# Create workflow
sqlite3 /tmp/test_memory_db/memory.db "
INSERT INTO workflows (name, description, steps, tools_used, created_at)
VALUES ('Persistence Test', 'Test workflow persistence', '[{\"action\":\"test\"}]', '[\"test\"]', datetime('now'));
"

# Verify it persists
workflow_count=$(sqlite3 /tmp/test_memory_db/memory.db "SELECT COUNT(*) FROM workflows WHERE name='Persistence Test';")
if [ "$workflow_count" -eq 1 ]; then
    echo "✅ Database persistence working"
else
    echo "❌ Database persistence failed"
fi

echo "✅ Database testing complete!"
```

### Phase 6: Workflow Storage Engine with Database Integration (1.5 hours)
```python
# src/memory/persistence/workflow_storage.py
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

class WorkflowStorage:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def init_database(self):
        """Initialize SQLite database with workflow schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    steps TEXT NOT NULL,  -- JSON array of workflow steps
                    tools_used TEXT,      -- JSON array of tools
                    target_types TEXT,    -- JSON array of target types
                    context_tags TEXT,    -- JSON array of context tags
                    success_rate REAL DEFAULT 1.0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    version REAL DEFAULT 1.0,
                    parent_id INTEGER,    -- For workflow versions
                    metadata TEXT,        -- JSON metadata
                    mode TEXT DEFAULT 'session-only',
                    FOREIGN KEY (parent_id) REFERENCES workflows(id)
                )
            ''')

            # Create indexes for better search performance
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_workflows_name
                ON workflows(name)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_workflows_tools
                ON workflows(tools_used)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_workflows_created_at
                ON workflows(created_at)
            ''')

    def save_workflow(self, workflow: Dict[str, Any]) -> int:
        """Save workflow to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO workflows
                (name, description, steps, tools_used, target_types,
                 context_tags, success_rate, usage_count, created_at,
                 last_used, version, parent_id, metadata, mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                workflow['name'],
                workflow.get('description', ''),
                json.dumps(workflow.get('steps', [])),
                json.dumps(workflow.get('tools_used', [])),
                json.dumps(workflow.get('target_types', [])),
                json.dumps(workflow.get('context_tags', [])),
                workflow.get('success_rate', 1.0),
                workflow.get('usage_count', 0),
                workflow['created_at'],
                workflow.get('last_used', workflow['created_at']),
                workflow.get('version', 1.0),
                workflow.get('parent_id'),
                json.dumps(workflow.get('metadata', {})),
                workflow.get('mode', 'session-only')
            ))

            return cursor.lastrowid

    def get_workflow(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve workflow by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM workflows WHERE id = ?', (workflow_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_dict(row)
            return None

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to workflow dictionary"""
        return {
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'steps': json.loads(row['steps']),
            'tools_used': json.loads(row['tools_used']),
            'target_types': json.loads(row['target_types']),
            'context_tags': json.loads(row['context_tags']),
            'success_rate': row['success_rate'],
            'usage_count': row['usage_count'],
            'created_at': row['created_at'],
            'last_used': row['last_used'],
            'version': row['version'],
            'parent_id': row['parent_id'],
            'metadata': json.loads(row['metadata'] or '{}'),
            'mode': row['mode']
        }
```

### Phase 6: Learning System (1.5 hours)
```python
# src/memory/learning/workflow_learner.py
class WorkflowLearner:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.pattern_recognizer = PatternRecognizer()

    def improve_workflow(self, workflow_id: int, improved_steps: List[Dict],
                        success_feedback: bool = True) -> int:
        """Learn from user improvements"""
        try:
            # Get original workflow
            original = self.memory.workflow_storage.get_workflow(workflow_id)
            if not original:
                raise ValueError(f"Workflow {workflow_id} not found")

            # Analyze improvement patterns
            improvements = self._analyze_improvements(
                original['steps'], improved_steps
            )

            # Create improved version
            improved_workflow = {
                **original,
                'steps': improved_steps,
                'parent_id': workflow_id,
                'version': original['version'] + 0.1,
                'created_at': datetime.now().isoformat(),
                'improvements': improvements,
                'learned_from': 'user_feedback'
            }

            # Adjust success rate based on feedback
            if success_feedback:
                improved_workflow['success_rate'] = min(1.0, original['success_rate'] + 0.1)
            else:
                improved_workflow['success_rate'] = max(0.1, original['success_rate'] - 0.1)

            # Store improved version
            new_workflow_id = self.memory.store_workflow(improved_workflow)

            # Update original workflow's usage statistics
            self._update_workflow_stats(workflow_id, success_feedback)

            return new_workflow_id

        except Exception as e:
            print(f"Failed to improve workflow: {e}")
            return None

    def _analyze_improvements(self, original_steps: List[Dict],
                            improved_steps: List[Dict]) -> Dict[str, Any]:
        """Analyze what was improved in the workflow"""
        improvements = {
            'steps_added': [],
            'steps_removed': [],
            'steps_modified': [],
            'new_tools': [],
            'optimization_type': 'unknown'
        }

        # Find added steps
        if len(improved_steps) > len(original_steps):
            improvements['steps_added'] = improved_steps[len(original_steps):]
            improvements['optimization_type'] = 'expansion'

        # Find removed steps
        elif len(improved_steps) < len(original_steps):
            improvements['optimization_type'] = 'simplification'

        # Find modified steps
        for i, (orig, improved) in enumerate(zip(original_steps, improved_steps)):
            if orig != improved:
                improvements['steps_modified'].append({
                    'step_index': i,
                    'original': orig,
                    'improved': improved
                })

        return improvements
```

### Phase 7: Export/Import System (1 hour)
```python
# src/memory/export/workflow_exporter.py
class WorkflowExporter:
    def __init__(self, memory_manager):
        self.memory = memory_manager

    def export_workflows(self, export_path: str,
                        workflow_ids: List[int] = None) -> Dict[str, Any]:
        """Export workflows to portable JSON format"""
        try:
            # Get workflows to export
            if workflow_ids:
                workflows = []
                for wf_id in workflow_ids:
                    wf = self.memory.workflow_storage.get_workflow(wf_id)
                    if wf:
                        workflows.append(wf)
            else:
                workflows = self.memory.workflow_storage.get_all_workflows()

            # Create export package
            export_data = {
                'export_metadata': {
                    'version': '1.0',
                    'exported_at': datetime.now().isoformat(),
                    'total_workflows': len(workflows),
                    'kali_ai_os_version': '1.0',
                    'export_mode': self.memory.mode
                },
                'workflows': workflows,
                'statistics': self._generate_export_stats(workflows)
            }

            # Save to file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            return {
                'success': True,
                'exported_count': len(workflows),
                'file_path': export_path,
                'file_size': os.path.getsize(export_path)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def import_workflows(self, import_path: str) -> Dict[str, Any]:
        """Import workflows from backup file"""
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)

            workflows = import_data.get('workflows', [])
            imported_count = 0
            errors = []

            for workflow in workflows:
                try:
                    # Remove ID to avoid conflicts
                    workflow.pop('id', None)

                    # Update import metadata
                    workflow['imported_at'] = datetime.now().isoformat()
                    workflow['imported_from'] = import_path

                    # Store workflow
                    self.memory.store_workflow(workflow)
                    imported_count += 1

                except Exception as e:
                    errors.append(f"Failed to import '{workflow.get('name', 'Unknown')}': {e}")

            return {
                'success': True,
                'imported_count': imported_count,
                'total_available': len(workflows),
                'errors': errors
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

### Phase 8: Testing & Integration (1 hour)
```python
# Test complete memory system
async def test_complete_memory_system():
    # 1. Initialize memory manager
    memory = MemoryManager(mode="session-only")

    # 2. Store test workflows
    nmap_workflow = {
        'name': 'Comprehensive Nmap Scan',
        'description': 'Complete network reconnaissance with nmap',
        'steps': [
            {'action': 'port_scan', 'tool': 'nmap', 'params': {'type': 'syn'}},
            {'action': 'service_detection', 'tool': 'nmap', 'params': {'version': True}},
            {'action': 'os_detection', 'tool': 'nmap', 'params': {'os': True}}
        ],
        'tools_used': ['nmap'],
        'context_tags': ['network', 'reconnaissance', 'scanning'],
        'target_types': ['network', 'hosts']
    }

    workflow_id = memory.store_workflow(nmap_workflow)
    assert workflow_id is not None

    # 3. Test semantic search
    search_results = memory.semantic_search("network port scanning")
    assert len(search_results) > 0
    assert search_results[0]['name'] == 'Comprehensive Nmap Scan'

    # 4. Test workflow improvement
    improved_steps = nmap_workflow['steps'] + [
        {'action': 'vulnerability_scan', 'tool': 'nmap', 'params': {'scripts': True}}
    ]

    improved_id = memory.learn_workflow_improvement(
        workflow_id, improved_steps, success_feedback=True
    )
    assert improved_id is not None

    # 5. Test export/import
    exporter = WorkflowExporter(memory)
    export_result = exporter.export_workflows("/tmp/test_export.json")
    assert export_result['success'] == True

    print("Memory system working correctly!")

# Performance testing
def test_memory_performance():
    memory = MemoryManager()

    # Test storage speed
    start_time = time.time()
    for i in range(100):
        workflow = {
            'name': f'Test Workflow {i}',
            'steps': [{'action': 'test', 'id': i}],
            'tools_used': ['test_tool']
        }
        memory.store_workflow(workflow)
    storage_time = time.time() - start_time

    # Test search speed
    start_time = time.time()
    results = memory.semantic_search("test workflow")
    search_time = time.time() - start_time

    print(f"Storage time for 100 workflows: {storage_time:.2f}s")
    print(f"Search time: {search_time:.2f}s")

    assert storage_time < 10.0  # Should store 100 workflows in under 10 seconds
    assert search_time < 1.0    # Should search in under 1 second
```

## Overview
Build a sophisticated persistent memory system that enables AI to learn and remember security workflows permanently. This system provides both persistent and session-only modes, with vector search, workflow storage, and cross-session knowledge transfer.

## Directory Structure
```
Samsung-AI-os/
├── kali-ai-os/
│   ├── src/
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── memory_manager.py
│   │   │   │   ├── storage_engine.py
│   │   │   │   ├── vector_store.py
│   │   │   │   └── knowledge_base.py
│   │   │   ├── persistence/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── database_manager.py
│   │   │   │   ├── workflow_storage.py
│   │   │   │   ├── session_manager.py
│   │   │   │   └── backup_system.py
│   │   │   ├── retrieval/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── semantic_search.py
│   │   │   │   ├── workflow_matcher.py
│   │   │   │   ├── context_retriever.py
│   │   │   │   └── relevance_scorer.py
│   │   │   ├── learning/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── workflow_learner.py
│   │   │   │   ├── pattern_recognizer.py
│   │   │   │   ├── optimization_engine.py
│   │   │   │   └── feedback_processor.py
│   │   │   ├── export/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── workflow_exporter.py
│   │   │   │   ├── import_manager.py
│   │   │   │   ├── format_converter.py
│   │   │   │   └── portability_handler.py
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       ├── memory_config.py
│   │   │       ├── storage_config.py
│   │   │       └── boot_mode_selector.py
│   │   └── tests/
│   │       ├── memory/
│   │       │   ├── test_workflow_storage.py
│   │       │   ├── test_semantic_search.py
│   │       │   ├── test_learning_engine.py
│   │       │   ├── test_export_import.py
│   │       │   └── test_mode_switching.py
│   │       └── fixtures/
│   │           ├── test_workflows.json
│   │           └── sample_memories.db
│   ├── data/
│   │   ├── persistent/          # Created if persistent mode
│   │   │   ├── workflows.db
│   │   │   ├── vectors/
│   │   │   ├── screenshots/
│   │   │   └── backups/
│   │   └── session/            # Always available in /tmp
│   │       ├── temp_workflows.db
│   │       ├── temp_vectors/
│   │       └── session_data/
│   └── scripts/
│       ├── setup_persistent_storage.sh
│       └── export_session_data.sh
```

## Technology Stack
- **Database**: SQLite 3.40+, SQLAlchemy 2.0.23
- **Vector Search**: ChromaDB 0.4.15, sentence-transformers
- **Embeddings**: all-MiniLM-L6-v2, Google GenAI embeddings
- **Storage**: File system management, USB detection
- **Serialization**: JSON, pickle, msgpack

## Implementation Requirements

### Core Components

#### 1. Memory Manager
```python
# src/memory/core/memory_manager.py
from typing import Dict, List, Any, Optional
from src.memory.persistence.database_manager import DatabaseManager
from src.memory.retrieval.semantic_search import SemanticSearch

class MemoryManager:
    def __init__(self, mode: str = "persistent"):
        self.mode = mode
        self.storage_path = self._determine_storage_path()
        self.db_manager = DatabaseManager(self.storage_path)
        self.semantic_search = SemanticSearch()
        self.vector_store = None

    def _determine_storage_path(self) -> str:
        """Determine storage path based on mode"""
        if self.mode == "persistent":
            # Check for persistent partition
            if os.path.exists("/persistent"):
                return "/persistent/kali-ai-os"
            else:
                raise StorageError("Persistent mode requested but no persistent storage found")
        else:  # session-only
            return "/tmp/kali-ai-os-session"

    def store_workflow(self, workflow: Dict[str, Any]) -> int:
        """Store workflow in memory system"""
        # Add metadata
        workflow['created_at'] = datetime.now()
        workflow['usage_count'] = 0
        workflow['success_rate'] = 1.0

        # Store in database
        workflow_id = self.db_manager.insert_workflow(workflow)

        # Create vector embedding
        embedding_text = self._create_embedding_text(workflow)
        self.semantic_search.add_embedding(workflow_id, embedding_text)

        return workflow_id

    def semantic_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search workflows using semantic similarity"""
        return self.semantic_search.search(query, limit)

    def get_contextual_workflows(self, context: Dict) -> List[Dict]:
        """Get workflows relevant to current context"""
        # Combine semantic search with context filtering
        semantic_results = self.semantic_search.search(
            self._context_to_query(context)
        )

        # Filter by context tags and target types
        filtered_results = []
        for result in semantic_results:
            if self._matches_context(result, context):
                filtered_results.append(result)

        return filtered_results
```

#### 2. Vector Store
```python
# src/memory/core/vector_store.py
import chromadb
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.client = chromadb.PersistentClient(path=storage_path)
        self.collection = self.client.get_or_create_collection("workflows")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def add_workflow(self, workflow_id: int, text: str, metadata: Dict):
        """Add workflow to vector store"""
        embedding = self.embedder.encode(text)

        self.collection.add(
            embeddings=[embedding.tolist()],
            metadatas=[metadata],
            ids=[str(workflow_id)]
        )

    def search_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar workflows"""
        query_embedding = self.embedder.encode(query)

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )

        return self._format_results(results)
```

#### 3. Workflow Storage
```python
# src/memory/persistence/workflow_storage.py
import sqlite3
import json
from typing import Dict, List, Any, Optional

class WorkflowStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    steps TEXT NOT NULL,
                    tools_used TEXT,
                    target_types TEXT,
                    context_tags TEXT,
                    success_rate REAL DEFAULT 1.0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version REAL DEFAULT 1.0,
                    parent_id INTEGER,
                    metadata TEXT,
                    FOREIGN KEY (parent_id) REFERENCES workflows(id)
                )
            ''')

    def save_workflow(self, workflow: Dict[str, Any]) -> int:
        """Save workflow to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO workflows
                (name, description, steps, tools_used, target_types, context_tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                workflow['name'],
                workflow.get('description', ''),
                json.dumps(workflow['steps']),
                json.dumps(workflow.get('tools_used', [])),
                json.dumps(workflow.get('target_types', [])),
                json.dumps(workflow.get('context_tags', [])),
                json.dumps(workflow.get('metadata', {}))
            ))

            return cursor.lastrowid
```

### Learning System

#### 1. Workflow Learner
```python
# src/memory/learning/workflow_learner.py
class WorkflowLearner:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.pattern_recognizer = PatternRecognizer()

    def learn_from_demonstration(self, workflow_name: str,
                                recorded_actions: List[Dict]) -> int:
        """Learn workflow from user demonstration"""
        # Analyze actions for patterns
        patterns = self.pattern_recognizer.analyze_actions(recorded_actions)

        # Optimize action sequence
        optimized_steps = self._optimize_action_sequence(recorded_actions)

        # Create workflow
        workflow = {
            'name': workflow_name,
            'steps': optimized_steps,
            'learned_from': 'demonstration',
            'patterns': patterns,
            'created_at': datetime.now()
        }

        return self.memory.store_workflow(workflow)

    def improve_workflow(self, workflow_id: int,
                        feedback: Dict[str, Any]) -> int:
        """Improve existing workflow based on feedback"""
        existing_workflow = self.memory.get_workflow(workflow_id)

        # Analyze feedback
        improvements = self._analyze_feedback(feedback)

        # Create improved version
        improved_workflow = self._apply_improvements(existing_workflow, improvements)
        improved_workflow['parent_id'] = workflow_id
        improved_workflow['version'] = existing_workflow['version'] + 0.1

        return self.memory.store_workflow(improved_workflow)
```

### Export/Import System

#### 1. Workflow Exporter
```python
# src/memory/export/workflow_exporter.py
class WorkflowExporter:
    def __init__(self, memory_manager):
        self.memory = memory_manager

    def export_all_workflows(self, export_path: str) -> Dict[str, Any]:
        """Export all workflows to portable format"""
        all_workflows = self.memory.get_all_workflows()

        export_data = {
            'export_metadata': {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'total_workflows': len(all_workflows),
                'kali_ai_os_version': self._get_system_version()
            },
            'workflows': []
        }

        for workflow in all_workflows:
            # Include screenshots and metadata
            workflow_data = {
                'workflow': workflow,
                'screenshots': self._export_screenshots(workflow['id']),
                'usage_stats': self._get_usage_stats(workflow['id'])
            }
            export_data['workflows'].append(workflow_data)

        # Save to file
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        return {
            'success': True,
            'exported_count': len(all_workflows),
            'file_path': export_path
        }

    def import_workflows(self, import_path: str) -> Dict[str, Any]:
        """Import workflows from backup file"""
        with open(import_path, 'r') as f:
            import_data = json.load(f)

        imported_count = 0
        for workflow_data in import_data['workflows']:
            try:
                # Import workflow
                workflow_id = self.memory.store_workflow(workflow_data['workflow'])

                # Import screenshots
                self._import_screenshots(workflow_id, workflow_data['screenshots'])

                imported_count += 1
            except Exception as e:
                print(f"Failed to import workflow: {e}")

        return {
            'success': True,
            'imported_count': imported_count,
            'total_available': len(import_data['workflows'])
        }
```

## Testing Strategy

### Unit Tests (85% coverage minimum)
```bash
cd kali-ai-os
python -m pytest tests/memory/ -v --cov=src.memory --cov-report=html

# Test categories:
# - Workflow storage and retrieval
# - Semantic search accuracy
# - Mode switching (persistent/session)
# - Export/import functionality
# - Learning and optimization
# - Vector embeddings
```

### Performance Tests
```python
def test_large_scale_storage():
    """Test storage of many workflows"""
    memory_manager = MemoryManager()

    # Store 10,000 workflows
    for i in range(10000):
        workflow = {
            'name': f'Workflow {i}',
            'steps': [{'action': 'test', 'id': i}] * 5
        }
        memory_manager.store_workflow(workflow)

    # Search should still be fast
    start_time = time.time()
    results = memory_manager.semantic_search("test workflow")
    search_time = time.time() - start_time

    assert search_time < 1.0  # Under 1 second
    assert len(results) > 0

def test_memory_persistence():
    """Test data persistence across restarts"""
    # Store workflows
    memory_manager = MemoryManager(mode="persistent")
    workflow_id = memory_manager.store_workflow({
        'name': 'Persistent Test',
        'steps': [{'action': 'test'}]
    })

    # Simulate restart
    del memory_manager

    # Create new instance
    new_memory_manager = MemoryManager(mode="persistent")

    # Should retrieve stored workflow
    retrieved = new_memory_manager.get_workflow(workflow_id)
    assert retrieved['name'] == 'Persistent Test'
```

## Deployment & Validation

### Setup Commands
```bash
# 1. Install dependencies
pip install chromadb sentence-transformers sqlalchemy

# 2. Setup storage directories
mkdir -p data/persistent/{vectors,screenshots,backups}
mkdir -p data/session

# 3. Initialize memory system
python -c "
from src.memory.core.memory_manager import MemoryManager
memory = MemoryManager(mode='session-only')
print('Memory system initialized!')
"

# 4. Run memory tests
python -m pytest tests/memory/ -v
```

### Success Metrics
- ✅ Workflow storage and retrieval working
- ✅ Semantic search accuracy >80%
- ✅ Export/import functionality operational
- ✅ Learning system functional
- ✅ Both persistent and session modes working
- ✅ Ready for teaching mode integration

## Configuration Files

### memory_config.py
```python
MEMORY_CONFIG = {
    'storage': {
        'persistent_path': '/persistent/kali-ai-os',
        'session_path': '/tmp/kali-ai-os-session',
        'backup_interval': 3600,  # 1 hour
        'max_workflows': 10000
    },
    'search': {
        'embedding_model': 'all-MiniLM-L6-v2',
        'similarity_threshold': 0.7,
        'max_results': 10
    },
    'optimization': {
        'auto_optimize_interval': 86400,  # 24 hours
        'memory_limit_mb': 512,
        'compression_enabled': True
    }
}
```

## SQLite Database Troubleshooting Guide

### Common Database Problems and Solutions:

**1. Database file not created automatically:**
```bash
# Check if directory exists
ls -la /tmp/kali-ai-os-memory/

# Check migration files exist
ls -la src/memory/database/migrations/

# Manually create database if needed
cd /tmp/kali-ai-os-memory/
sqlite3 memory.db < /path/to/migrations/001_memory_schema.sql

# Verify tables created
sqlite3 memory.db ".tables"
```

**2. Permission errors on database file:**
```bash
# Check file permissions
ls -la /tmp/kali-ai-os-memory/memory.db

# Fix permissions if needed
chmod 664 /tmp/kali-ai-os-memory/memory.db
chown $USER:$USER /tmp/kali-ai-os-memory/memory.db

# Check directory permissions
chmod 755 /tmp/kali-ai-os-memory/
```

**3. Database corruption or schema errors:**
```bash
# Check database integrity
sqlite3 /tmp/kali-ai-os-memory/memory.db "PRAGMA integrity_check;"

# Check schema version
sqlite3 /tmp/kali-ai-os-memory/memory.db "SELECT name FROM sqlite_master WHERE type='table';"

# Rebuild database if corrupted
mv memory.db memory.db.backup
python -c "from src.memory.database.connection import initialize_memory_database; initialize_memory_database('/tmp/kali-ai-os-memory', force_reset=True)"
```

**4. Application can't connect to SQLite database:**
```bash
# Test SQLite connection directly
sqlite3 /tmp/kali-ai-os-memory/memory.db "SELECT sqlite_version();"

# Check Python SQLite module
python -c "import sqlite3; print(sqlite3.sqlite_version)"

# Test database manager
python -c "
from src.memory.database.connection import check_database_health
health = check_database_health()
print(health)
"
```

**5. Workflow insertion/retrieval fails:**
```bash
# Check table structure
sqlite3 /tmp/kali-ai-os-memory/memory.db ".schema workflows"

# Test manual insertion
sqlite3 /tmp/kali-ai-os-memory/memory.db "
INSERT INTO workflows (name, steps, tools_used, created_at)
VALUES ('Test', '[{}]', '[\"test\"]', datetime('now'));
"

# Check data exists
sqlite3 /tmp/kali-ai-os-memory/memory.db "SELECT COUNT(*) FROM workflows;"
```

**6. Vector embeddings not working:**
```bash
# Check embeddings table
sqlite3 /tmp/kali-ai-os-memory/memory.db "SELECT COUNT(*) FROM workflow_embeddings;"

# Test embedding insertion
python -c "
import json
from src.memory.database.sqlite_manager import SQLiteManager
db = SQLiteManager('/tmp/kali-ai-os-memory')
db.execute_update('INSERT INTO workflow_embeddings (workflow_id, embedding_vector) VALUES (1, ?)', (json.dumps([0.1, 0.2, 0.3]),))
"
```

**7. Database locks or concurrent access issues:**
```bash
# Check for database locks
lsof | grep memory.db

# Enable WAL mode for better concurrency
sqlite3 /tmp/kali-ai-os-memory/memory.db "PRAGMA journal_mode=WAL;"

# Check WAL files
ls -la /tmp/kali-ai-os-memory/memory.db*
```

**8. Storage space issues:**
```bash
# Check disk space
df -h /tmp

# Check database size
du -sh /tmp/kali-ai-os-memory/

# Vacuum database to reclaim space
sqlite3 /tmp/kali-ai-os-memory/memory.db "VACUUM;"
```

**9. Migration files not executing:**
```bash
# Check migration files have correct format
head -20 src/memory/database/migrations/001_memory_schema.sql

# Test migration manually
sqlite3 /tmp/kali-ai-os-memory/memory.db < src/memory/database/migrations/001_memory_schema.sql

# Check migration log
python -c "
import logging
logging.basicConfig(level=logging.INFO)
from src.memory.database.sqlite_manager import SQLiteManager
db = SQLiteManager('/tmp/kali-ai-os-memory')
"
```

**10. Performance issues with large datasets:**
```bash
# Analyze query performance
sqlite3 /tmp/kali-ai-os-memory/memory.db "EXPLAIN QUERY PLAN SELECT * FROM workflows WHERE name LIKE '%test%';"

# Update table statistics
sqlite3 /tmp/kali-ai-os-memory/memory.db "ANALYZE;"

# Check index usage
sqlite3 /tmp/kali-ai-os-memory/memory.db "SELECT name FROM sqlite_master WHERE type='index';"
```

### Database Health Check Script:
```bash
# Create comprehensive health check
cat > check_memory_db_health.sh << 'EOF'
#!/bin/bash

DB_PATH="/tmp/kali-ai-os-memory/memory.db"

echo "🔍 Memory Database Health Check"
echo "================================"

# Check if database exists
if [ -f "$DB_PATH" ]; then
    echo "✅ Database file exists: $DB_PATH"
else
    echo "❌ Database file missing: $DB_PATH"
    exit 1
fi

# Check file permissions
PERMS=$(stat -c "%a" "$DB_PATH")
echo "📋 File permissions: $PERMS"

# Check database size
SIZE=$(du -sh "$DB_PATH" | cut -f1)
echo "📊 Database size: $SIZE"

# Test database connection
if sqlite3 "$DB_PATH" "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Check table counts
echo "📈 Table statistics:"
sqlite3 "$DB_PATH" "
SELECT
    'workflows: ' || COUNT(*) FROM workflows
UNION ALL SELECT
    'embeddings: ' || COUNT(*) FROM workflow_embeddings
UNION ALL SELECT
    'patterns: ' || COUNT(*) FROM learning_patterns
UNION ALL SELECT
    'sessions: ' || COUNT(*) FROM memory_sessions;
"

# Check recent activity
echo "⏰ Recent workflows:"
sqlite3 "$DB_PATH" "SELECT name, created_at FROM workflows ORDER BY created_at DESC LIMIT 3;"

echo "🎉 Database health check complete!"
EOF

chmod +x check_memory_db_health.sh
./check_memory_db_health.sh
```

## Next Steps
After completing this task:
1. Integrate with AI processing layer
2. Connect to teaching mode system
3. Optimize for large-scale storage
4. Proceed to Task 7: Teaching Mode & Learning
