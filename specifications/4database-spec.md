# Faction Management System Database Specification

## Core Database Architecture

### Database Technology Choice
- **SQLite**: Selected for its simplicity, zero-configuration, and file-based nature
  - **Pros**: Serverless, zero configuration, single file storage, cross-platform, lightweight
  - **Cons**: Limited concurrency, not suitable for high-volume network access
  - **Appropriateness**: Ideal for desktop application with single-user access pattern

### Transaction Management
- **Context Manager Pattern**: Required for all database operations
  ```python
  try:
      with self.db_manager.connection:  # Transaction automatically begins
          # Database operations here
          # Operations automatically committed if no exception occurs
      
      # Success handling outside the with block
      return True
  except Exception as e:
      # Error handling (transaction automatically rolled back)
      logging.error(f"Error: {str(e)}")
      return False
  ```
- **Implementation Timing**: Must be implemented before any repository classes
- **Consistency**: Use same pattern throughout entire codebase
- **No Explicit Statements**: Never use direct BEGIN/COMMIT/ROLLBACK statements

## Database Schema

### Core Tables and Relationships

#### 1. Districts
```sql
CREATE TABLE districts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    commerce_value INTEGER NOT NULL CHECK (commerce_value BETWEEN 0 AND 10),
    muster_value INTEGER NOT NULL CHECK (muster_value BETWEEN 0 AND 10),
    aristocratic_value INTEGER NOT NULL CHECK (aristocratic_value BETWEEN 0 AND 10),
    preferred_gain_attribute TEXT NOT NULL,
    preferred_gain_skill TEXT NOT NULL,
    preferred_gain_squadron_aptitude TEXT NOT NULL,
    preferred_monitor_attribute TEXT NOT NULL, 
    preferred_monitor_skill TEXT NOT NULL,
    preferred_monitor_squadron_aptitude TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_districts_name ON districts(name);
```

#### 2. Factions
```sql
CREATE TABLE factions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    monitoring_bonus INTEGER NOT NULL DEFAULT 0,
    color TEXT NOT NULL DEFAULT '#3498db', -- Hex color code for faction representation, defaults to blue
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_factions_name ON factions(name);
```

#### 3. District Influence
```sql
CREATE TABLE district_influence (
    district_id TEXT NOT NULL,
    faction_id TEXT NOT NULL,
    influence_value INTEGER NOT NULL CHECK (influence_value BETWEEN 0 AND 10),
    has_stronghold BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (district_id, faction_id),
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE
);

CREATE INDEX idx_district_influence_district ON district_influence(district_id);
CREATE INDEX idx_district_influence_faction ON district_influence(faction_id);
```

#### 4. District Likeability
```sql
CREATE TABLE district_likeability (
    district_id TEXT NOT NULL,
    faction_id TEXT NOT NULL,
    likeability_value INTEGER NOT NULL CHECK (likeability_value BETWEEN -5 AND 5),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (district_id, faction_id),
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE
);
```

#### 5. Faction Relationships
```sql
CREATE TABLE faction_relationships (
    faction_id TEXT NOT NULL,
    target_faction_id TEXT NOT NULL,
    relationship_value INTEGER NOT NULL CHECK (relationship_value BETWEEN -2 AND 2),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (faction_id, target_faction_id),
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE,
    FOREIGN KEY (target_faction_id) REFERENCES factions(id) ON DELETE CASCADE,
    CHECK (faction_id != target_faction_id)
);

CREATE INDEX idx_faction_relationships_faction ON faction_relationships(faction_id);
CREATE INDEX idx_faction_relationships_target ON faction_relationships(target_faction_id);
```

#### 6. Agents
```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    faction_id TEXT,
    attunement INTEGER NOT NULL CHECK (brawn BETWEEN 0 AND 5),
    intellect INTEGER NOT NULL CHECK (dexterity BETWEEN 0 AND 5),
    finesse INTEGER NOT NULL CHECK (intellect BETWEEN 0 AND 5),
    might INTEGER NOT NULL CHECK (cunning BETWEEN 0 AND 5),
    presence INTEGER NOT NULL CHECK (presence BETWEEN 0 AND 5),
    arcana INTEGER NOT NULL DEFAULT 0,
    artifice INTEGER NOT NULL DEFAULT 0,
    combat INTEGER NOT NULL DEFAULT 0,
    infiltration INTEGER NOT NULL DEFAULT 0,
    streetwise INTEGER NOT NULL DEFAULT 0,
    survival INTEGER NOT NULL DEFAULT 0,
    persuasion INTEGER NOT NULL DEFAULT 0,
    district_id TEXT,
    assignment TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE SET NULL,
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE SET NULL
);

CREATE INDEX idx_agents_faction ON agents(faction_id);
CREATE INDEX idx_agents_district ON agents(district_id);
CREATE INDEX idx_agents_name ON agents(name);
```

#### 7. Squadrons
```sql
CREATE TABLE squadrons (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    faction_id TEXT,
    type TEXT NOT NULL,
    mobility INTEGER NOT NULL,
    combat_aptitude INTEGER NOT NULL DEFAULT -1 CHECK (combat_aptitude BETWEEN -3 AND 5),
    underworld_aptitude INTEGER NOT NULL DEFAULT -1 CHECK (underworld_aptitude BETWEEN -3 AND 5),
    social_aptitude INTEGER NOT NULL DEFAULT -1 CHECK (social_aptitude BETWEEN -3 AND 5),
    technical_aptitude INTEGER NOT NULL DEFAULT -1 CHECK (technical_aptitude BETWEEN -3 AND 5),
    labor_aptitude INTEGER NOT NULL DEFAULT -1 CHECK (labor_aptitude BETWEEN -3 AND 5),
    arcane_aptitude INTEGER NOT NULL DEFAULT -1 CHECK (arcane_aptitude BETWEEN -3 AND 5),
    wilderness_aptitude INTEGER NOT NULL DEFAULT -1 CHECK (wilderness_aptitude BETWEEN -3 AND 5),
    monitoring_aptitude INTEGER NOT NULL DEFAULT -1 CHECK (monitoring_aptitude BETWEEN -3 AND 5),
    district_id TEXT,
    assignment TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE SET NULL,
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE SET NULL
);

CREATE INDEX idx_squadrons_faction ON squadrons(faction_id);
CREATE INDEX idx_squadrons_district ON squadrons(district_id);
CREATE INDEX idx_squadrons_name ON squadrons(name);
```

#### 8. District Rumors
```sql
CREATE TABLE district_rumors (
    id TEXT PRIMARY KEY,
    district_id TEXT NOT NULL,
    rumor_text TEXT NOT NULL,
    discovery_dc INTEGER NOT NULL,
    is_discovered BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
);

CREATE INDEX idx_district_rumors_district ON district_rumors(district_id);
CREATE INDEX idx_district_rumors_dc ON district_rumors(discovery_dc);
```

#### 9. Faction Known Rumors
```sql
CREATE TABLE faction_known_rumors (
    faction_id TEXT NOT NULL,
    rumor_id TEXT NOT NULL,
    discovered_on TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (faction_id, rumor_id),
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE,
    FOREIGN KEY (rumor_id) REFERENCES district_rumors(id) ON DELETE CASCADE
);
```

#### 10. District Adjacency
```sql
CREATE TABLE district_adjacency (
    district_id TEXT NOT NULL,
    adjacent_district_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (district_id, adjacent_district_id),
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
    FOREIGN KEY (adjacent_district_id) REFERENCES districts(id) ON DELETE CASCADE,
    CHECK (district_id != adjacent_district_id)
);
```

#### 11. District Modifiers
```sql
CREATE TABLE district_modifiers (
    id TEXT PRIMARY KEY,
    district_id TEXT NOT NULL,
    modifier_type TEXT NOT NULL,
    modifier_value INTEGER NOT NULL,
    expires_on INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
);

CREATE INDEX idx_district_modifiers_district ON district_modifiers(district_id);
```

#### 12. Faction Resources
```sql
CREATE TABLE faction_resources (
    faction_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_value INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (faction_id, resource_type),
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE
);
```

#### 13. Game State
```sql
CREATE TABLE game_state (
    id TEXT PRIMARY KEY DEFAULT 'current',
    current_turn INTEGER NOT NULL DEFAULT 1,
    current_phase TEXT NOT NULL DEFAULT 'preparation',
    last_updated TEXT NOT NULL,
    campaign_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 14. Turn History
```sql
CREATE TABLE turn_history (
    turn_number INTEGER NOT NULL,
    phase TEXT NOT NULL,
    action_description TEXT NOT NULL,
    result_description TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (turn_number, phase, created_at)
);

CREATE INDEX idx_turn_history_turn ON turn_history(turn_number);
```

#### 15. Faction Monitoring Reports
```sql
CREATE TABLE faction_monitoring_reports (
    id TEXT PRIMARY KEY,
    faction_id TEXT NOT NULL,
    district_id TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    report_json TEXT NOT NULL,
    confidence_rating INTEGER NOT NULL CHECK (confidence_rating BETWEEN 1 AND 10),
    created_at TEXT NOT NULL,
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE,
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
);

CREATE INDEX idx_reports_faction ON faction_monitoring_reports(faction_id);
CREATE INDEX idx_reports_turn ON faction_monitoring_reports(turn_number);
```

#### 16. Map Configuration
```sql
CREATE TABLE map_configuration (
    id TEXT PRIMARY KEY DEFAULT 'current',
    base_map_path TEXT,
    map_width INTEGER,
    map_height INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

#### 17. District Shapes
```sql
CREATE TABLE district_shapes (
    district_id TEXT NOT NULL,
    shape_data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (district_id),
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
);
```

#### 18. Newspaper Issues
```sql
CREATE TABLE newspaper_issues (
    id TEXT PRIMARY KEY,
    issue_number INTEGER NOT NULL,
    publication_date TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_newspaper_issue_number ON newspaper_issues(issue_number);
```

#### 19. Newspaper Articles
```sql
CREATE TABLE newspaper_articles (
    id TEXT PRIMARY KEY,
    issue_id TEXT NOT NULL,
    section TEXT NOT NULL,
    headline TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (issue_id) REFERENCES newspaper_issues(id) ON DELETE CASCADE
);

CREATE INDEX idx_newspaper_articles_issue ON newspaper_articles(issue_id);
```

#### 20. Actions
```sql
CREATE TABLE actions (
    id TEXT PRIMARY KEY,
    turn_number INTEGER NOT NULL,
    piece_id TEXT NOT NULL,
    piece_type TEXT NOT NULL,
    faction_id TEXT NOT NULL,
    district_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_faction_id TEXT,
    attribute_used TEXT,
    skill_used TEXT,
    aptitude_used TEXT,
    dc INTEGER,
    manual_modifier INTEGER,
    roll_result INTEGER,
    outcome_tier TEXT,
    in_conflict INTEGER DEFAULT 0,
    conflict_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (faction_id) REFERENCES factions (id),
    FOREIGN KEY (district_id) REFERENCES districts (id),
    FOREIGN KEY (target_faction_id) REFERENCES factions (id)
);

CREATE TABLE decay_results (
    id TEXT PRIMARY KEY,
    turn_number INTEGER NOT NULL,
    district_id TEXT NOT NULL,
    faction_id TEXT NOT NULL,
    influence_change INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (district_id) REFERENCES districts (id),
    FOREIGN KEY (faction_id) REFERENCES factions (id)
);

CREATE INDEX idx_actions_turn ON actions(turn_number);
CREATE INDEX idx_actions_faction ON actions(faction_id);
CREATE INDEX idx_actions_district ON actions(district_id);
CREATE INDEX idx_actions_piece_id ON actions(piece_id);
```

#### 21. Conflicts
```sql
CREATE TABLE conflicts (
    id TEXT PRIMARY KEY,
    turn_number INTEGER NOT NULL,
    district_id TEXT NOT NULL,
    conflict_type TEXT NOT NULL CHECK (conflict_type IN ('manual_initiate', 'relationship', 'target', 'adjacent')),
    detection_source TEXT NOT NULL,
    resolution_status TEXT NOT NULL DEFAULT 'pending' CHECK (resolution_status IN ('pending', 'resolved')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
);

CREATE INDEX idx_conflicts_turn ON conflicts(turn_number);
CREATE INDEX idx_conflicts_district ON conflicts(district_id);
CREATE INDEX idx_conflicts_status ON conflicts(resolution_status);
```

#### 22. Conflict Factions
```sql
CREATE TABLE conflict_factions (
    conflict_id TEXT NOT NULL,
    faction_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('initiator', 'target', 'ally', 'adjacent')),
    outcome TEXT CHECK (outcome IN ('win', 'loss', 'draw', NULL)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (conflict_id, faction_id),
    FOREIGN KEY (conflict_id) REFERENCES conflicts(id) ON DELETE CASCADE,
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE
);

CREATE INDEX idx_conflict_factions_conflict ON conflict_factions(conflict_id);
CREATE INDEX idx_conflict_factions_faction ON conflict_factions(faction_id);
```

#### 23. Conflict Pieces
```sql
CREATE TABLE conflict_pieces (
    conflict_id TEXT NOT NULL,
    piece_id TEXT NOT NULL,
    piece_type TEXT NOT NULL CHECK (piece_type IN ('agent', 'squadron')),
    faction_id TEXT NOT NULL,
    participation_type TEXT NOT NULL CHECK (participation_type IN ('direct', 'adjacent', 'ally_support')),
    original_action_type TEXT NOT NULL,
    original_action_id TEXT NOT NULL,
    roll_result INTEGER,
    outcome_tier TEXT,
    conflict_penalty INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (conflict_id, piece_id),
    FOREIGN KEY (conflict_id) REFERENCES conflicts(id) ON DELETE CASCADE,
    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE
);

CREATE INDEX idx_conflict_pieces_conflict ON conflict_pieces(conflict_id);
CREATE INDEX idx_conflict_pieces_piece ON conflict_pieces(piece_id);
CREATE INDEX idx_conflict_pieces_faction ON conflict_pieces(faction_id);
```

#### 24. Conflict Resolution
```sql
CREATE TABLE conflict_resolutions (
    conflict_id TEXT PRIMARY KEY,
    resolution_type TEXT NOT NULL CHECK (resolution_type IN ('win', 'loss', 'draw', 'special')),
    resolution_notes TEXT,
    resolved_by TEXT NOT NULL, -- User ID or system ID
    resolved_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (conflict_id) REFERENCES conflicts(id) ON DELETE CASCADE
);

CREATE INDEX idx_conflict_resolutions_conflict ON conflict_resolutions(conflict_id);
```

#### 25. Faction Support Status
```sql
CREATE TABLE faction_support_status (
    turn_number INTEGER NOT NULL,
    declaring_faction_id TEXT NOT NULL,
    target_faction_id TEXT NOT NULL,
    will_support BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (turn_number, declaring_faction_id, target_faction_id),
    FOREIGN KEY (declaring_faction_id) REFERENCES factions(id) ON DELETE CASCADE,
    FOREIGN KEY (target_faction_id) REFERENCES factions(id) ON DELETE CASCADE
);

CREATE INDEX idx_faction_support_turn ON faction_support_status(turn_number);
CREATE INDEX idx_faction_support_declaring ON faction_support_status(declaring_faction_id);
CREATE INDEX idx_faction_support_target ON faction_support_status(target_faction_id);
```

## Database Manager Implementation

### DatabaseManager Class
```python
class DatabaseManager:
    def __init__(self, db_path=':memory:'):
        """Initialize the database manager with the given database path."""
        self.db_path = db_path
        self._connection = None
        self.initialize_db()
    
    @property
    def connection(self):
        """Get the database connection, creating it if necessary."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection
    
    def initialize_db(self):
        """Initialize the database schema if it doesn't exist."""
        with self.connection:
            # Create tables here (using schema definitions above)
            pass
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query and return the results."""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Query error: {str(e)} - Query: {query}")
            raise
    
    def execute_update(self, query, params=None):
        """Execute an UPDATE, INSERT, or DELETE query and return affected rows."""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
        except Exception as e:
            logging.error(f"Update error: {str(e)} - Query: {query}")
            raise
    
    def execute_script(self, script):
        """Execute a multi-statement SQL script."""
        try:
            self.connection.executescript(script)
        except Exception as e:
            logging.error(f"Script error: {str(e)}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
```

## Repository Pattern Implementation

### Base Repository

```python
class Repository:
    def __init__(self, db_manager, model_class):
        """Initialize with database manager and model class."""
        self.db_manager = db_manager
        self.model_class = model_class
        self.table_name = model_class.table_name
    
    def find_by_id(self, id):
        """Find a record by its ID."""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = :id"
            results = self.db_manager.execute_query(query, {"id": id})
            
            if not results:
                return None
                
            return self.model_class.from_dict(dict(results[0]))
        except Exception as e:
            logging.error(f"Error finding {self.model_class.__name__} with ID {id}: {str(e)}")
            return None
    
    def find_all(self):
        """Find all records in the table."""
        try:
            query = f"SELECT * FROM {self.table_name}"
            results = self.db_manager.execute_query(query)
            
            return [self.model_class.from_dict(dict(row)) for row in results]
        except Exception as e:
            logging.error(f"Error finding all {self.model_class.__name__}: {str(e)}")
            return []
    
    def create(self, model):
        """Create a new record in the database."""
        try:
            # Generate ID if needed
            if not model.id:
                model.id = str(uuid.uuid4())
                
            # Set timestamps
            model.mark_created()
            
            # Validate the model
            if not model.validate():
                logging.error(f"Invalid model: {model.errors}")
                return False
                
            # Use context manager for transaction
            with self.db_manager.connection:
                # Prepare data for insertion
                data = model.to_dict()
                
                # Extract related collections for separate handling
                related_data = {}
                for key in list(data.keys()):
                    if isinstance(data[key], list):
                        related_data[key] = data.pop(key)
                
                # Insert main record
                columns = list(data.keys())
                placeholders = [f":{col}" for col in columns]
                
                query = f"""
                    INSERT INTO {self.table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                
                self.db_manager.execute_update(query, data)
                
                # Handle related records
                for key, items in related_data.items():
                    self._save_related_records(model.id, key, items)
                    
            # Transaction successful
            return True
            
        except Exception as e:
            logging.error(f"Error creating {self.model_class.__name__}: {str(e)}")
            return False
    
    def update(self, model):
        """Update an existing record in the database."""
        try:
            # Validate the model
            if not model.validate():
                logging.error(f"Invalid model: {model.errors}")
                return False
                
            # Mark as updated
            model.mark_updated()
            
            # Use context manager for transaction
            with self.db_manager.connection:
                # Prepare data for update
                data = model.to_dict()
                
                # Extract related collections for separate handling
                related_data = {}
                for key in list(data.keys()):
                    if isinstance(data[key], list):
                        related_data[key] = data.pop(key)
                
                # Update main record
                set_clauses = [f"{col} = :{col}" for col in data.keys() if col != 'id']
                
                query = f"""
                    UPDATE {self.table_name}
                    SET {', '.join(set_clauses)}
                    WHERE id = :id
                """
                
                result = self.db_manager.execute_update(query, data)
                
                if result <= 0:
                    # Record wasn't found
                    return False
                    
                # Handle related records
                for key, items in related_data.items():
                    self._delete_related_records(model.id, key)
                    self._save_related_records(model.id, key, items)
                    
            # Transaction successful
            return True
            
        except Exception as e:
            logging.error(f"Error updating {self.model_class.__name__} with ID {model.id}: {str(e)}")
            return False
    
    def delete(self, id):
        """Delete a record from the database."""
        try:
            # Use context manager for transaction
            with self.db_manager.connection:
                # Delete related records first
                for related_table in self.model_class.related_tables:
                    self._delete_related_records(id, related_table)
                
                # Delete the main record
                query = f"""
                    DELETE FROM {self.table_name}
                    WHERE id = :id
                """
                
                result = self.db_manager.execute_update(query, {"id": id})
                
                if result <= 0:
                    # Record wasn't found
                    return False
                    
            # Transaction successful
            return True
            
        except Exception as e:
            logging.error(f"Error deleting {self.model_class.__name__} with ID {id}: {str(e)}")
            return False
    
    # Helper methods for related records
    def _save_related_records(self, parent_id, relation_name, items):
        """Save related records to a junction table or child table."""
        # Implementation depends on the specific relationship type
        pass
    
    def _delete_related_records(self, parent_id, relation_name):
        """Delete related records from a junction table or child table."""
        # Implementation depends on the specific relationship type
        pass
```

## Database Migration and Management

### Schema Versioning

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
```

### Migration Manager

```python
class MigrationManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Ensure the schema_migrations table exists."""
        with self.db_manager.connection:
            query = """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            );
            """
            self.db_manager.execute_update(query)
    
    def get_current_version(self):
        """Get the current schema version."""
        query = "SELECT MAX(version) as current_version FROM schema_migrations"
        result = self.db_manager.execute_query(query)
        return result[0]['current_version'] if result and result[0]['current_version'] else 0
    
    def apply_migrations(self, target_version=None):
        """Apply all pending migrations up to target_version."""
        current_version = self.get_current_version()
        migrations = self._get_available_migrations()
        
        applicable_migrations = [m for m in migrations if m['version'] > current_version]
        if target_version:
            applicable_migrations = [m for m in applicable_migrations if m['version'] <= target_version]
        
        applicable_migrations.sort(key=lambda m: m['version'])
        
        for migration in applicable_migrations:
            self._apply_migration(migration)
    
    def _apply_migration(self, migration):
        """Apply a single migration."""
        try:
            with self.db_manager.connection:
                # Run the migration script
                self.db_manager.execute_script(migration['script'])
                
                # Record the migration
                query = """
                INSERT INTO schema_migrations (version, applied_at) 
                VALUES (:version, :applied_at)
                """
                self.db_manager.execute_update(query, {
                    'version': migration['version'],
                    'applied_at': datetime.datetime.now().isoformat()
                })
                
            logging.info(f"Applied migration {migration['version']}")
        except Exception as e:
            logging.error(f"Error applying migration {migration['version']}: {str(e)}")
            raise
```

## Data Backup and Recovery

### Backup Strategy

```python
class BackupManager:
    def __init__(self, db_manager, backup_dir='backups'):
        self.db_manager = db_manager
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, label=None):
        """Create a backup of the current database."""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        label_suffix = f"_{label}" if label else ""
        backup_filename = f"backup_{timestamp}{label_suffix}.sqlite"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Ensure we're using a disk-based database
            if self.db_manager.db_path == ':memory:':
                logging.warning("Cannot backup in-memory database")
                return None
            
            # Create backup using SQLite backup API
            source = sqlite3.connect(self.db_manager.db_path)
            dest = sqlite3.connect(backup_path)
            source.backup(dest)
            dest.close()
            source.close()
            
            logging.info(f"Created database backup: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            return None
    
    def restore_backup(self, backup_path):
        """Restore database from backup."""
        try:
            # Close existing connection
            self.db_manager.close()
            
            # Ensure we're using a disk-based database
            if self.db_manager.db_path == ':memory:':
                logging.warning("Cannot restore to in-memory database")
                return False
            
            # Create a backup of current before restore
            self.create_backup(label='pre_restore')
            
            # Copy backup to main database file
            shutil.copy2(backup_path, self.db_manager.db_path)
            
            # Reconnect
            _ = self.db_manager.connection
            
            logging.info(f"Restored database from: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Error restoring backup: {str(e)}")
            return False
```

## Performance Optimization

### Index Strategy
- Primary keys and foreign keys indexed by default
- Additional indices on frequently queried columns
- Compound indices for common query patterns
- Indices on name fields for text searches

### Query Optimization
- Use prepared statements for all queries
- Limit result sets where appropriate
- Use joins rather than separate queries where possible
- Consider denormalizing frequently accessed data if performance issues occur

## Transaction Handling Principles

### DO:
1. Use context managers for all transactions
2. Group related operations that need to succeed or fail together
3. Place try/except blocks outside context managers
4. Keep proper transaction scope (include all related operations in one transaction)

### DON'T:
1. Don't use explicit BEGIN/COMMIT/ROLLBACK statements
2. Don't mix transaction styles within the same repository
3. Avoid nested transactions
4. Don't return from within a context manager

## Testing and Verification

### Unit Tests for Database Layer
- Test DatabaseManager initialization and connection
- Test transaction behavior with rollback on exceptions
- Test repository CRUD operations
- Test complex queries and relationships

### Integration Tests
- Test data consistency across related tables
- Test concurrent operations
- Test backup and restore operations
- Test performance with realistic data volumes
