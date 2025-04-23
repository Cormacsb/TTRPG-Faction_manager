import sqlite3
import logging
import os
from datetime import datetime
import threading

from .repositories.district import DistrictRepository
from .repositories.faction import FactionRepository
from .repositories.agent import AgentRepository
from .repositories.squadron import SquadronRepository
from .repositories.rumor import RumorRepository


class DatabaseManager:
    """Manager class for database connection and operations."""
    
    def __init__(self, db_path=':memory:', is_memory=False):
        """Initialize the database manager.
        
        Args:
            db_path (str, optional): Path to SQLite database file. Defaults to ':memory:'.
            is_memory (bool, optional): Whether to use in-memory database. Defaults to False.
        """
        self.db_path = db_path if not is_memory else ":memory:"
        self.is_memory = is_memory
        self._local = threading.local()
        self.initialize_db()
    
    @property
    def connection(self):
        """Get the database connection, creating it if necessary.
        
        Returns:
            sqlite3.Connection: The SQLite connection object.
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path, 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False  # Allow use across threads - we'll manage thread safety
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection
    
    def initialize_db(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            with self.connection:
                # Create schema_migrations table first
                self.connection.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL
                    )
                """)
                
                # Check if we need to create tables or if they already exist
                cursor = self.connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='districts'"
                )
                if cursor.fetchone() is None:
                    # Create all tables
                    self._create_tables()
        except Exception as e:
            logging.error(f"Error initializing database: {str(e)}")
            raise
    
    def _create_tables(self):
        """Create all database tables."""
        with self.connection:
            # Districts
            self.connection.execute("""
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_districts_name ON districts(name)")
            
            # Factions
            self.connection.execute("""
                CREATE TABLE factions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    monitoring_bonus INTEGER NOT NULL DEFAULT 0,
                    color TEXT NOT NULL DEFAULT '#3498db',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_factions_name ON factions(name)")
            
            # District Influence
            self.connection.execute("""
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_district_influence_district ON district_influence(district_id)")
            self.connection.execute("CREATE INDEX idx_district_influence_faction ON district_influence(faction_id)")
            
            # District Likeability
            self.connection.execute("""
                CREATE TABLE district_likeability (
                    district_id TEXT NOT NULL,
                    faction_id TEXT NOT NULL,
                    likeability_value INTEGER NOT NULL CHECK (likeability_value BETWEEN -5 AND 5),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (district_id, faction_id),
                    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
                    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE
                )
            """)
            
            # Faction Relationships
            self.connection.execute("""
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_faction_relationships_faction ON faction_relationships(faction_id)")
            self.connection.execute("CREATE INDEX idx_faction_relationships_target ON faction_relationships(target_faction_id)")
            
            # Agents
            self.connection.execute("""
                CREATE TABLE agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    faction_id TEXT,
                    attunement INTEGER NOT NULL CHECK (attunement BETWEEN 0 AND 5),
                    intellect INTEGER NOT NULL CHECK (intellect BETWEEN 0 AND 5),
                    finesse INTEGER NOT NULL CHECK (finesse BETWEEN 0 AND 5),
                    might INTEGER NOT NULL CHECK (might BETWEEN 0 AND 5),
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_agents_faction ON agents(faction_id)")
            self.connection.execute("CREATE INDEX idx_agents_district ON agents(district_id)")
            self.connection.execute("CREATE INDEX idx_agents_name ON agents(name)")
            
            # Squadrons
            self.connection.execute("""
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_squadrons_faction ON squadrons(faction_id)")
            self.connection.execute("CREATE INDEX idx_squadrons_district ON squadrons(district_id)")
            self.connection.execute("CREATE INDEX idx_squadrons_name ON squadrons(name)")
            
            # District Rumors
            self.connection.execute("""
                CREATE TABLE district_rumors (
                    id TEXT PRIMARY KEY,
                    district_id TEXT NOT NULL,
                    rumor_text TEXT NOT NULL,
                    discovery_dc INTEGER NOT NULL,
                    is_discovered BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_district_rumors_district ON district_rumors(district_id)")
            self.connection.execute("CREATE INDEX idx_district_rumors_dc ON district_rumors(discovery_dc)")
            
            # Faction Known Rumors
            self.connection.execute("""
                CREATE TABLE faction_known_rumors (
                    faction_id TEXT NOT NULL,
                    rumor_id TEXT NOT NULL,
                    discovered_on TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (faction_id, rumor_id),
                    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE,
                    FOREIGN KEY (rumor_id) REFERENCES district_rumors(id) ON DELETE CASCADE
                )
            """)
            
            # District Adjacency
            self.connection.execute("""
                CREATE TABLE district_adjacency (
                    district_id TEXT NOT NULL,
                    adjacent_district_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (district_id, adjacent_district_id),
                    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
                    FOREIGN KEY (adjacent_district_id) REFERENCES districts(id) ON DELETE CASCADE,
                    CHECK (district_id != adjacent_district_id)
                )
            """)
            
            # District Modifiers
            self.connection.execute("""
                CREATE TABLE district_modifiers (
                    id TEXT PRIMARY KEY,
                    district_id TEXT NOT NULL,
                    modifier_type TEXT NOT NULL,
                    modifier_value INTEGER NOT NULL,
                    expires_on INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_district_modifiers_district ON district_modifiers(district_id)")
            
            # Faction Resources
            self.connection.execute("""
                CREATE TABLE faction_resources (
                    faction_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_value INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (faction_id, resource_type),
                    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE
                )
            """)
            
            # Game State
            self.connection.execute("""
                CREATE TABLE game_state (
                    id TEXT PRIMARY KEY DEFAULT 'current',
                    current_turn INTEGER NOT NULL DEFAULT 1,
                    current_phase TEXT NOT NULL DEFAULT 'preparation',
                    last_updated TEXT NOT NULL,
                    campaign_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Turn History
            self.connection.execute("""
                CREATE TABLE turn_history (
                    turn_number INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    action_description TEXT NOT NULL,
                    result_description TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (turn_number, phase, created_at)
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_turn_history_turn ON turn_history(turn_number)")
            
            # Faction Monitoring Reports
            self.connection.execute("""
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_reports_faction ON faction_monitoring_reports(faction_id)")
            self.connection.execute("CREATE INDEX idx_reports_turn ON faction_monitoring_reports(turn_number)")
            
            # Map Configuration
            self.connection.execute("""
                CREATE TABLE map_configuration (
                    id TEXT PRIMARY KEY DEFAULT 'current',
                    base_map_path TEXT,
                    map_width INTEGER,
                    map_height INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # District Shapes
            self.connection.execute("""
                CREATE TABLE district_shapes (
                    district_id TEXT NOT NULL,
                    shape_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (district_id),
                    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
                )
            """)
            
            # Newspaper Issues
            self.connection.execute("""
                CREATE TABLE newspaper_issues (
                    id TEXT PRIMARY KEY,
                    issue_number INTEGER NOT NULL,
                    publication_date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_newspaper_issue_number ON newspaper_issues(issue_number)")
            
            # Newspaper Articles
            self.connection.execute("""
                CREATE TABLE newspaper_articles (
                    id TEXT PRIMARY KEY,
                    issue_id TEXT NOT NULL,
                    section TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (issue_id) REFERENCES newspaper_issues(id) ON DELETE CASCADE
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_newspaper_articles_issue ON newspaper_articles(issue_id)")
            
            # Actions
            self.connection.execute("""
                CREATE TABLE actions (
                    id TEXT PRIMARY KEY,
                    turn_number INTEGER NOT NULL,
                    piece_id TEXT NOT NULL,
                    piece_type TEXT NOT NULL CHECK (piece_type IN ('agent', 'squadron')),
                    faction_id TEXT NOT NULL,
                    district_id TEXT NOT NULL,
                    action_type TEXT NOT NULL CHECK (action_type IN ('monitor', 'gain_influence', 'take_influence', 'freeform', 'initiate_conflict')),
                    action_description TEXT,
                    target_faction_id TEXT,
                    attribute_used TEXT,
                    skill_used TEXT,
                    aptitude_used TEXT,
                    dc INTEGER,
                    manual_modifier INTEGER NOT NULL DEFAULT 0 CHECK (manual_modifier BETWEEN -10 AND 10),
                    roll_result INTEGER,
                    outcome_tier TEXT,
                    influence_gained INTEGER DEFAULT 0,
                    influence_lost INTEGER DEFAULT 0,
                    target_influence_lost INTEGER DEFAULT 0,
                    target_influence_gained INTEGER DEFAULT 0,
                    monitoring_report_id TEXT,
                    conflict_id TEXT,
                    dm_notes TEXT,
                    in_conflict BOOLEAN NOT NULL DEFAULT 0,
                    conflict_penalty INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (faction_id) REFERENCES factions(id) ON DELETE CASCADE,
                    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_faction_id) REFERENCES factions(id) ON DELETE SET NULL,
                    FOREIGN KEY (monitoring_report_id) REFERENCES faction_monitoring_reports(id) ON DELETE SET NULL
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_actions_turn ON actions(turn_number)")
            self.connection.execute("CREATE INDEX idx_actions_faction ON actions(faction_id)")
            self.connection.execute("CREATE INDEX idx_actions_district ON actions(district_id)")
            self.connection.execute("CREATE INDEX idx_actions_piece_id ON actions(piece_id)")
            
            # Enemy Penalties
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS enemy_penalties (
                    id TEXT PRIMARY KEY,
                    turn_number INTEGER NOT NULL,
                    action_id TEXT NOT NULL,
                    total_penalty INTEGER NOT NULL,
                    penalty_breakdown TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (action_id) REFERENCES actions(id) ON DELETE CASCADE
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_enemy_penalties_turn ON enemy_penalties(turn_number)")
            self.connection.execute("CREATE INDEX idx_enemy_penalties_action ON enemy_penalties(action_id)")
            
            # Create decay_results table
            self.connection.execute("""
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
                )
            """)
            
            # Conflicts
            self.connection.execute("""
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_conflicts_turn ON conflicts(turn_number)")
            self.connection.execute("CREATE INDEX idx_conflicts_district ON conflicts(district_id)")
            self.connection.execute("CREATE INDEX idx_conflicts_status ON conflicts(resolution_status)")
            
            # Conflict Factions
            self.connection.execute("""
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_conflict_factions_conflict ON conflict_factions(conflict_id)")
            self.connection.execute("CREATE INDEX idx_conflict_factions_faction ON conflict_factions(faction_id)")
            
            # Conflict Pieces
            self.connection.execute("""
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_conflict_pieces_conflict ON conflict_pieces(conflict_id)")
            self.connection.execute("CREATE INDEX idx_conflict_pieces_piece ON conflict_pieces(piece_id)")
            self.connection.execute("CREATE INDEX idx_conflict_pieces_faction ON conflict_pieces(faction_id)")
            
            # Conflict Resolution
            self.connection.execute("""
                CREATE TABLE conflict_resolutions (
                    conflict_id TEXT PRIMARY KEY,
                    resolution_type TEXT NOT NULL CHECK (resolution_type IN ('win', 'loss', 'draw', 'special')),
                    resolution_notes TEXT,
                    resolved_by TEXT NOT NULL,
                    resolved_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (conflict_id) REFERENCES conflicts(id) ON DELETE CASCADE
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_conflict_resolutions_conflict ON conflict_resolutions(conflict_id)")
            
            # Faction Support Status
            self.connection.execute("""
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
                )
            """)
            
            self.connection.execute("CREATE INDEX idx_faction_support_turn ON faction_support_status(turn_number)")
            self.connection.execute("CREATE INDEX idx_faction_support_declaring ON faction_support_status(declaring_faction_id)")
            self.connection.execute("CREATE INDEX idx_faction_support_target ON faction_support_status(target_faction_id)")
            
            # Record schema migration
            self.connection.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (1, datetime.now().isoformat())
            )
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query and return the results.
        
        Args:
            query (str): SQL query to execute.
            params (dict or tuple, optional): Query parameters. Defaults to None.
            
        Returns:
            list: List of sqlite3.Row objects.
        """
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
        """Execute an UPDATE, INSERT, or DELETE query and return affected rows.
        
        Args:
            query (str): SQL query to execute.
            params (dict or tuple, optional): Query parameters. Defaults to None.
            
        Returns:
            int: Number of affected rows.
        """
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
        """Execute a multi-statement SQL script.
        
        Args:
            script (str): SQL script to execute.
        """
        try:
            self.connection.executescript(script)
        except Exception as e:
            logging.error(f"Script error: {str(e)}")
            raise
    
    def close(self):
        """Close the database connection for the current thread."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
    
    def get_repository(self, repository_name):
        """Get a repository instance by name.
        
        Args:
            repository_name (str): The name of the repository to get.
            
        Returns:
            Repository: The repository instance.
            
        Raises:
            ValueError: If repository_name is not valid.
        """
        repositories = {
            "district": DistrictRepository,
            "faction": FactionRepository,
            "agent": AgentRepository,
            "squadron": SquadronRepository,
            "rumor": RumorRepository
        }
        
        if repository_name not in repositories:
            raise ValueError(f"Unknown repository name: {repository_name}")
            
        return repositories[repository_name](self)