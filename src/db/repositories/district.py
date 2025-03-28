import logging
import json
import uuid
from datetime import datetime

from .base import Repository
from ...models.district import District


class DistrictRepository(Repository):
    """Repository for District model operations."""
    
    def __init__(self, db_manager):
        """Initialize the repository.
        
        Args:
            db_manager: Database manager instance.
        """
        super().__init__(db_manager, District)
    
    def find_by_id(self, id):
        """Find a district by its ID.
        
        Args:
            id (str): District ID to find.
            
        Returns:
            District: District instance if found, None otherwise.
        """
        district = super().find_by_id(id)
        if district:
            self._load_related_data(district)
        return district
    
    def find_all(self):
        """Find all districts.
        
        Returns:
            list: List of District instances.
        """
        districts = super().find_all()
        for district in districts:
            self._load_related_data(district)
        return districts
    
    def _load_related_data(self, district):
        """Load related data for a district.
        
        Args:
            district (District): District instance to load data for.
        """
        try:
            # Load faction influence
            query = """
                SELECT faction_id, influence_value, has_stronghold
                FROM district_influence
                WHERE district_id = :district_id
            """
            results = self.db_manager.execute_query(query, {"district_id": district.id})
            
            district.faction_influence = {}
            district.strongholds = {}
            
            for row in results:
                district.faction_influence[row['faction_id']] = row['influence_value']
                district.strongholds[row['faction_id']] = bool(row['has_stronghold'])
            
            # Calculate influence pool
            district.influence_pool = 10 - sum(district.faction_influence.values())
            
            # Load faction likeability
            query = """
                SELECT faction_id, likeability_value
                FROM district_likeability
                WHERE district_id = :district_id
            """
            results = self.db_manager.execute_query(query, {"district_id": district.id})
            
            district.faction_likeability = {}
            
            for row in results:
                district.faction_likeability[row['faction_id']] = row['likeability_value']
            
            # Load adjacent districts
            query = """
                SELECT adjacent_district_id
                FROM district_adjacency
                WHERE district_id = :district_id
            """
            results = self.db_manager.execute_query(query, {"district_id": district.id})
            
            district.adjacent_districts = [row['adjacent_district_id'] for row in results]
            
            # Load weekly DC modifier history
            query = """
                SELECT modifier_value
                FROM district_modifiers
                WHERE district_id = :district_id AND modifier_type = 'weekly_dc'
                ORDER BY created_at DESC
                LIMIT 10
            """
            results = self.db_manager.execute_query(query, {"district_id": district.id})
            
            district.weekly_dc_modifier_history = [row['modifier_value'] for row in results]
            
            # Set weekly DC modifier (most recent history entry or 0)
            district.weekly_dc_modifier = district.weekly_dc_modifier_history[0] if district.weekly_dc_modifier_history else 0
            
            # Load shape data if available
            query = """
                SELECT shape_data
                FROM district_shapes
                WHERE district_id = :district_id
            """
            results = self.db_manager.execute_query(query, {"district_id": district.id})
            
            if results:
                district.shape_data = json.loads(results[0]['shape_data'])
            
        except Exception as e:
            logging.error(f"Error loading related data for district {district.id}: {str(e)}")
    
    def create(self, district):
        """Create a new district in the database.
        
        Args:
            district (District): District instance to create.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Save main district record
                main_data = {
                    'id': district.id,
                    'name': district.name,
                    'description': district.description,
                    'commerce_value': district.commerce_value,
                    'muster_value': district.muster_value,
                    'aristocratic_value': district.aristocratic_value,
                    'preferred_gain_attribute': district.preferred_gain_attribute,
                    'preferred_gain_skill': district.preferred_gain_skill,
                    'preferred_gain_squadron_aptitude': district.preferred_gain_squadron_aptitude,
                    'preferred_monitor_attribute': district.preferred_monitor_attribute,
                    'preferred_monitor_skill': district.preferred_monitor_skill,
                    'preferred_monitor_squadron_aptitude': district.preferred_monitor_squadron_aptitude,
                    'created_at': district.created_at,
                    'updated_at': district.updated_at
                }
                
                query = """
                    INSERT INTO districts (
                        id, name, description, commerce_value, muster_value, aristocratic_value,
                        preferred_gain_attribute, preferred_gain_skill, preferred_gain_squadron_aptitude,
                        preferred_monitor_attribute, preferred_monitor_skill, preferred_monitor_squadron_aptitude,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :name, :description, :commerce_value, :muster_value, :aristocratic_value,
                        :preferred_gain_attribute, :preferred_gain_skill, :preferred_gain_squadron_aptitude,
                        :preferred_monitor_attribute, :preferred_monitor_skill, :preferred_monitor_squadron_aptitude,
                        :created_at, :updated_at
                    )
                """
                
                self.db_manager.execute_update(query, main_data)
                
                # Save faction influence
                for faction_id, influence_value in district.faction_influence.items():
                    if influence_value > 0:
                        query = """
                            INSERT INTO district_influence (
                                district_id, faction_id, influence_value, has_stronghold, created_at, updated_at
                            )
                            VALUES (
                                :district_id, :faction_id, :influence_value, :has_stronghold, :created_at, :updated_at
                            )
                        """
                        
                        params = {
                            'district_id': district.id,
                            'faction_id': faction_id,
                            'influence_value': influence_value,
                            'has_stronghold': district.strongholds.get(faction_id, False),
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        self.db_manager.execute_update(query, params)
                
                # Save faction likeability
                for faction_id, likeability_value in district.faction_likeability.items():
                    query = """
                        INSERT INTO district_likeability (
                            district_id, faction_id, likeability_value, created_at, updated_at
                        )
                        VALUES (
                            :district_id, :faction_id, :likeability_value, :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'district_id': district.id,
                        'faction_id': faction_id,
                        'likeability_value': likeability_value,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
                # Save adjacent districts
                for adjacent_id in district.adjacent_districts:
                    query = """
                        INSERT INTO district_adjacency (
                            district_id, adjacent_district_id, created_at, updated_at
                        )
                        VALUES (
                            :district_id, :adjacent_district_id, :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'district_id': district.id,
                        'adjacent_district_id': adjacent_id,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
                # Save weekly DC modifier
                if district.weekly_dc_modifier != 0:
                    query = """
                        INSERT INTO district_modifiers (
                            id, district_id, modifier_type, modifier_value, created_at, updated_at
                        )
                        VALUES (
                            :id, :district_id, :modifier_type, :modifier_value, :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'id': str(uuid.uuid4()),
                        'district_id': district.id,
                        'modifier_type': 'weekly_dc',
                        'modifier_value': district.weekly_dc_modifier,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
                # Save shape data if available
                if district.shape_data:
                    query = """
                        INSERT INTO district_shapes (
                            district_id, shape_data, created_at, updated_at
                        )
                        VALUES (
                            :district_id, :shape_data, :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'district_id': district.id,
                        'shape_data': json.dumps(district.shape_data),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
            return True
        except Exception as e:
            logging.error(f"Error creating district: {str(e)}")
            return False
    
    def update(self, district):
        """Update an existing district in the database.
        
        Args:
            district (District): District instance to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Update main district record
                main_data = {
                    'id': district.id,
                    'name': district.name,
                    'description': district.description,
                    'commerce_value': district.commerce_value,
                    'muster_value': district.muster_value,
                    'aristocratic_value': district.aristocratic_value,
                    'preferred_gain_attribute': district.preferred_gain_attribute,
                    'preferred_gain_skill': district.preferred_gain_skill,
                    'preferred_gain_squadron_aptitude': district.preferred_gain_squadron_aptitude,
                    'preferred_monitor_attribute': district.preferred_monitor_attribute,
                    'preferred_monitor_skill': district.preferred_monitor_skill,
                    'preferred_monitor_squadron_aptitude': district.preferred_monitor_squadron_aptitude,
                    'updated_at': datetime.now().isoformat()
                }
                
                query = """
                    UPDATE districts SET
                        name = :name,
                        description = :description,
                        commerce_value = :commerce_value,
                        muster_value = :muster_value,
                        aristocratic_value = :aristocratic_value,
                        preferred_gain_attribute = :preferred_gain_attribute,
                        preferred_gain_skill = :preferred_gain_skill,
                        preferred_gain_squadron_aptitude = :preferred_gain_squadron_aptitude,
                        preferred_monitor_attribute = :preferred_monitor_attribute,
                        preferred_monitor_skill = :preferred_monitor_skill,
                        preferred_monitor_squadron_aptitude = :preferred_monitor_squadron_aptitude,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                
                self.db_manager.execute_update(query, main_data)
                
                # Update faction influence (delete existing and re-insert)
                self.db_manager.execute_update(
                    "DELETE FROM district_influence WHERE district_id = :district_id",
                    {"district_id": district.id}
                )
                
                for faction_id, influence_value in district.faction_influence.items():
                    if influence_value > 0:
                        query = """
                            INSERT INTO district_influence (
                                district_id, faction_id, influence_value, has_stronghold, created_at, updated_at
                            )
                            VALUES (
                                :district_id, :faction_id, :influence_value, :has_stronghold, :created_at, :updated_at
                            )
                        """
                        
                        params = {
                            'district_id': district.id,
                            'faction_id': faction_id,
                            'influence_value': influence_value,
                            'has_stronghold': district.strongholds.get(faction_id, False),
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        self.db_manager.execute_update(query, params)
                
                # Update faction likeability (delete existing and re-insert)
                self.db_manager.execute_update(
                    "DELETE FROM district_likeability WHERE district_id = :district_id",
                    {"district_id": district.id}
                )
                
                for faction_id, likeability_value in district.faction_likeability.items():
                    query = """
                        INSERT INTO district_likeability (
                            district_id, faction_id, likeability_value, created_at, updated_at
                        )
                        VALUES (
                            :district_id, :faction_id, :likeability_value, :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'district_id': district.id,
                        'faction_id': faction_id,
                        'likeability_value': likeability_value,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
                # Update adjacent districts (delete existing and re-insert)
                self.db_manager.execute_update(
                    "DELETE FROM district_adjacency WHERE district_id = :district_id",
                    {"district_id": district.id}
                )
                
                for adjacent_id in district.adjacent_districts:
                    query = """
                        INSERT INTO district_adjacency (
                            district_id, adjacent_district_id, created_at, updated_at
                        )
                        VALUES (
                            :district_id, :adjacent_district_id, :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'district_id': district.id,
                        'adjacent_district_id': adjacent_id,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
                # Update weekly DC modifier
                if district.weekly_dc_modifier != 0:
                    # Check if modifier exists
                    exists_query = """
                        SELECT id FROM district_modifiers
                        WHERE district_id = :district_id AND modifier_type = 'weekly_dc'
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    
                    exists_result = self.db_manager.execute_query(
                        exists_query, {"district_id": district.id}
                    )
                    
                    if exists_result:
                        # Update existing modifier
                        query = """
                            UPDATE district_modifiers SET
                                modifier_value = :modifier_value,
                                updated_at = :updated_at
                            WHERE id = :id
                        """
                        
                        params = {
                            'id': exists_result[0]['id'],
                            'modifier_value': district.weekly_dc_modifier,
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        self.db_manager.execute_update(query, params)
                    else:
                        # Insert new modifier
                        query = """
                            INSERT INTO district_modifiers (
                                id, district_id, modifier_type, modifier_value, created_at, updated_at
                            )
                            VALUES (
                                :id, :district_id, :modifier_type, :modifier_value, :created_at, :updated_at
                            )
                        """
                        
                        params = {
                            'id': str(uuid.uuid4()),
                            'district_id': district.id,
                            'modifier_type': 'weekly_dc',
                            'modifier_value': district.weekly_dc_modifier,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        self.db_manager.execute_update(query, params)
                
                # Update shape data if available
                if district.shape_data:
                    # Check if shape data exists
                    exists_query = """
                        SELECT district_id FROM district_shapes
                        WHERE district_id = :district_id
                    """
                    
                    exists_result = self.db_manager.execute_query(
                        exists_query, {"district_id": district.id}
                    )
                    
                    if exists_result:
                        # Update existing shape data
                        query = """
                            UPDATE district_shapes SET
                                shape_data = :shape_data,
                                updated_at = :updated_at
                            WHERE district_id = :district_id
                        """
                        
                        params = {
                            'district_id': district.id,
                            'shape_data': json.dumps(district.shape_data),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        self.db_manager.execute_update(query, params)
                    else:
                        # Insert new shape data
                        query = """
                            INSERT INTO district_shapes (
                                district_id, shape_data, created_at, updated_at
                            )
                            VALUES (
                                :district_id, :shape_data, :created_at, :updated_at
                            )
                        """
                        
                        params = {
                            'district_id': district.id,
                            'shape_data': json.dumps(district.shape_data),
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        self.db_manager.execute_update(query, params)
                
            return True
        except Exception as e:
            logging.error(f"Error updating district: {str(e)}")
            return False
    
    def set_faction_influence(self, district_id, faction_id, value):
        """Set a faction's influence in a district.
        
        Args:
            district_id (str): District ID.
            faction_id (str): Faction ID.
            value (int): Influence value (0-10).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            district = self.find_by_id(district_id)
            if not district:
                return False
                
            # Check if setting would exceed 10 total influence
            current = district.get_faction_influence(faction_id)
            other_total = district.calculate_total_influence() - current
            
            if other_total + value > 10:
                return False
                
            with self.db_manager.connection:
                if value <= 0:
                    # Delete record if value is 0 or negative
                    self.db_manager.execute_update(
                        """
                        DELETE FROM district_influence
                        WHERE district_id = :district_id AND faction_id = :faction_id
                        """,
                        {"district_id": district_id, "faction_id": faction_id}
                    )
                    
                    # Update district model for consistency
                    if faction_id in district.faction_influence:
                        del district.faction_influence[faction_id]
                else:
                    # Check if record exists
                    exists = self.db_manager.execute_query(
                        """
                        SELECT 1 FROM district_influence
                        WHERE district_id = :district_id AND faction_id = :faction_id
                        """,
                        {"district_id": district_id, "faction_id": faction_id}
                    )
                    
                    if exists:
                        # Update existing record
                        self.db_manager.execute_update(
                            """
                            UPDATE district_influence SET
                                influence_value = :value,
                                updated_at = :updated_at
                            WHERE district_id = :district_id AND faction_id = :faction_id
                            """,
                            {
                                "district_id": district_id,
                                "faction_id": faction_id,
                                "value": value,
                                "updated_at": datetime.now().isoformat()
                            }
                        )
                    else:
                        # Insert new record
                        self.db_manager.execute_update(
                            """
                            INSERT INTO district_influence (
                                district_id, faction_id, influence_value, has_stronghold,
                                created_at, updated_at
                            )
                            VALUES (
                                :district_id, :faction_id, :value, :has_stronghold,
                                :created_at, :updated_at
                            )
                            """,
                            {
                                "district_id": district_id,
                                "faction_id": faction_id,
                                "value": value,
                                "has_stronghold": district.has_stronghold(faction_id),
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat()
                            }
                        )
                    
                    # Update district model for consistency
                    district.faction_influence[faction_id] = value
                
                # Update influence pool
                district.influence_pool = 10 - district.calculate_total_influence()
                
            return True
        except Exception as e:
            logging.error(f"Error setting faction influence: {str(e)}")
            return False
    
    def set_stronghold(self, district_id, faction_id, value):
        """Set a faction's stronghold status in a district.
        
        Args:
            district_id (str): District ID.
            faction_id (str): Faction ID.
            value (bool): Stronghold status.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            district = self.find_by_id(district_id)
            if not district:
                return False
                
            # Check if faction has influence in district
            if faction_id not in district.faction_influence:
                return False
                
            with self.db_manager.connection:
                # Update the record
                result = self.db_manager.execute_update(
                    """
                    UPDATE district_influence SET
                        has_stronghold = :has_stronghold,
                        updated_at = :updated_at
                    WHERE district_id = :district_id AND faction_id = :faction_id
                    """,
                    {
                        "district_id": district_id,
                        "faction_id": faction_id,
                        "has_stronghold": value,
                        "updated_at": datetime.now().isoformat()
                    }
                )
                
                # Update district model for consistency
                district.strongholds[faction_id] = value
                
            return result > 0
        except Exception as e:
            logging.error(f"Error setting stronghold: {str(e)}")
            return False
    
    def set_faction_likeability(self, district_id, faction_id, value):
        """Set a faction's likeability in a district.
        
        Args:
            district_id (str): District ID.
            faction_id (str): Faction ID.
            value (int): Likeability value (-5 to +5).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not -5 <= value <= 5:
                return False
                
            district = self.find_by_id(district_id)
            if not district:
                return False
                
            with self.db_manager.connection:
                # Check if record exists
                exists = self.db_manager.execute_query(
                    """
                    SELECT 1 FROM district_likeability
                    WHERE district_id = :district_id AND faction_id = :faction_id
                    """,
                    {"district_id": district_id, "faction_id": faction_id}
                )
                
                if exists:
                    # Update existing record
                    self.db_manager.execute_update(
                        """
                        UPDATE district_likeability SET
                            likeability_value = :value,
                            updated_at = :updated_at
                        WHERE district_id = :district_id AND faction_id = :faction_id
                        """,
                        {
                            "district_id": district_id,
                            "faction_id": faction_id,
                            "value": value,
                            "updated_at": datetime.now().isoformat()
                        }
                    )
                else:
                    # Insert new record
                    self.db_manager.execute_update(
                        """
                        INSERT INTO district_likeability (
                            district_id, faction_id, likeability_value,
                            created_at, updated_at
                        )
                        VALUES (
                            :district_id, :faction_id, :value,
                            :created_at, :updated_at
                        )
                        """,
                        {
                            "district_id": district_id,
                            "faction_id": faction_id,
                            "value": value,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        }
                    )
                
                # Update district model for consistency
                district.faction_likeability[faction_id] = value
                
            return True
        except Exception as e:
            logging.error(f"Error setting faction likeability: {str(e)}")
            return False
    
    def set_weekly_dc_modifier(self, district_id, value):
        """Set a district's weekly DC modifier.
        
        Args:
            district_id (str): District ID.
            value (int): Modifier value (-2 to +2).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not -2 <= value <= 2:
                return False
                
            district = self.find_by_id(district_id)
            if not district:
                return False
                
            with self.db_manager.connection:
                # Insert new modifier
                self.db_manager.execute_update(
                    """
                    INSERT INTO district_modifiers (
                        id, district_id, modifier_type, modifier_value,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :district_id, :modifier_type, :modifier_value,
                        :created_at, :updated_at
                    )
                    """,
                    {
                        "id": str(uuid.uuid4()),
                        "district_id": district_id,
                        "modifier_type": "weekly_dc",
                        "modifier_value": value,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                )
                
                # Update district model for consistency
                district.weekly_dc_modifier = value
                if not district.weekly_dc_modifier_history:
                    district.weekly_dc_modifier_history = []
                district.weekly_dc_modifier_history.insert(0, value)
                
            return True
        except Exception as e:
            logging.error(f"Error setting weekly DC modifier: {str(e)}")
            return False
    
    def add_adjacent_district(self, district_id, adjacent_id):
        """Add an adjacent district relationship.
        
        Args:
            district_id (str): District ID.
            adjacent_id (str): Adjacent district ID.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            district = self.find_by_id(district_id)
            if not district:
                return False
                
            # Check if adjacency already exists
            if adjacent_id in district.adjacent_districts:
                return True  # Already adjacent
                
            with self.db_manager.connection:
                # Insert bidirectional adjacency (both directions)
                for src, dest in [(district_id, adjacent_id), (adjacent_id, district_id)]:
                    self.db_manager.execute_update(
                        """
                        INSERT INTO district_adjacency (
                            district_id, adjacent_district_id, 
                            created_at, updated_at
                        )
                        VALUES (
                            :district_id, :adjacent_district_id,
                            :created_at, :updated_at
                        )
                        """,
                        {
                            "district_id": src,
                            "adjacent_district_id": dest,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        }
                    )
                
                # Update district model for consistency
                district.adjacent_districts.append(adjacent_id)
                
            return True
        except Exception as e:
            logging.error(f"Error adding adjacent district: {str(e)}")
            return False