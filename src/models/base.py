import uuid
import json
from datetime import datetime
import logging


class Model:
    """Base class for all data models in the system."""
    
    table_name = ""  # Override in subclasses
    related_tables = []  # Override in subclasses
    
    def __init__(self, id=None, created_at=None, updated_at=None):
        """Initialize a new model instance.
        
        Args:
            id (str, optional): Unique identifier. Defaults to None (will be generated).
            created_at (str, optional): Creation timestamp. Defaults to None.
            updated_at (str, optional): Last update timestamp. Defaults to None.
        """
        self.id = id or str(uuid.uuid4())
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
        self.errors = []
    
    def mark_created(self):
        """Mark the model as newly created with current timestamp."""
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def mark_updated(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.now().isoformat()
    
    def validate(self):
        """Validate the model data.
        
        Returns:
            bool: True if validation passes, False otherwise.
        """
        self.errors = []
        # Base validation (override in subclasses)
        return len(self.errors) == 0
    
    def to_dict(self):
        """Convert model to dictionary.
        
        Returns:
            dict: Dictionary representation of the model.
        """
        # Base implementation, override if needed in subclasses
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_') and key != 'errors':
                result[key] = value
        return result
    
    def to_json(self):
        """Convert model to JSON string.
        
        Returns:
            str: JSON string representation of the model.
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data):
        """Create model instance from dictionary.
        
        Args:
            data (dict): Dictionary containing model data.
            
        Returns:
            Model: New model instance.
        """
        instance = cls()
        # Handle special case for assignments (for Agent and Squadron)
        if 'assignment' in data and data['assignment'] and hasattr(instance, 'current_task'):
            try:
                logging.info(f"[FROM_DICT_DEBUG] Processing assignment JSON: {data['assignment']}")
                assignment_json = data['assignment']
                if isinstance(assignment_json, str):
                    instance.current_task = json.loads(assignment_json)
                    logging.info(f"[FROM_DICT_DEBUG] Parsed assignment: {instance.current_task}")
                else:
                    instance.current_task = assignment_json
                    logging.info(f"[FROM_DICT_DEBUG] Using non-string assignment: {instance.current_task}")
            except Exception as e:
                logging.error(f"[FROM_DICT_DEBUG] Error parsing assignment JSON: {str(e)}")
                instance.current_task = None
        
        # Set all other attributes
        for key, value in data.items():
            if key != 'assignment' and hasattr(instance, key):
                setattr(instance, key, value)
        
        if hasattr(instance, 'district_id') and hasattr(instance, 'current_task'):
            logging.info(f"[FROM_DICT_DEBUG] Created {cls.__name__} instance with district_id: {instance.district_id}, current_task: {instance.current_task}")
        
        return instance
    
    @classmethod
    def from_json(cls, json_str):
        """Create model instance from JSON string.
        
        Args:
            json_str (str): JSON string containing model data.
            
        Returns:
            Model: New model instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)