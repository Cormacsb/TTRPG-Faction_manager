import uuid
import logging
from datetime import datetime


class Repository:
    """Base repository class for database operations on models."""
    
    def __init__(self, db_manager, model_class):
        """Initialize the repository.
        
        Args:
            db_manager: Database manager instance.
            model_class: Model class this repository handles.
        """
        self.db_manager = db_manager
        self.model_class = model_class
        self.table_name = model_class.table_name
    
    def find_by_id(self, id):
        """Find model by ID.
        
        Args:
            id (str): ID to find.
            
        Returns:
            object: Model instance if found, None otherwise.
        """
        try:
            query = f"SELECT * FROM {self.model_class.table_name} WHERE id = :id"
            results = self.db_manager.execute_query(query, {"id": id})
            
            if results:
                # Convert to dict for model instantiation
                row_dict = dict(results[0])
                logging.info(f"[FIND_DEBUG] Raw DB result for {self.model_class.__name__} {id}: {row_dict}")
                
                if 'assignment' in row_dict and row_dict['assignment']:
                    logging.info(f"[FIND_DEBUG] Assignment JSON: {row_dict['assignment']}")
                
                # Create and return model instance
                model = self.model_class.from_dict(row_dict)
                logging.info(f"[FIND_DEBUG] Loaded model: {model.__class__.__name__} {model.id}")
                return model
            
            return None
        except Exception as e:
            logging.error(f"Error finding {self.model_class.__name__} with ID {id}: {str(e)}")
            return None
    
    def find_all(self):
        """Find all records for this model.
        
        Returns:
            list: List of model instances.
        """
        try:
            query = f"SELECT * FROM {self.table_name}"
            results = self.db_manager.execute_query(query)
            
            return [self.model_class.from_dict(dict(row)) for row in results]
        except Exception as e:
            logging.error(f"Error finding all {self.model_class.__name__}: {str(e)}")
            return []
    
    def create(self, model):
        """Create a new record in the database.
        
        Args:
            model: Model instance to create.
            
        Returns:
            bool: True if successful, False otherwise.
        """
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
                    if isinstance(data[key], list) or isinstance(data[key], dict):
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
        """Update an existing record in the database.
        
        Args:
            model: Model instance to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Check if model exists
            existing = self.find_by_id(model.id)
            if not existing:
                logging.error(f"{self.model_class.__name__} with ID {model.id} not found for update")
                return False
            
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
                    if isinstance(data[key], list) or isinstance(data[key], dict):
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
        """Delete a record from the database.
        
        Args:
            id (str): ID of record to delete.
            
        Returns:
            bool: True if successful, False otherwise.
        """
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
    
    def find_by(self, criteria, limit=None, offset=None, order_by=None):
        """Find records matching specific criteria.
        
        Args:
            criteria (dict): Dictionary of field:value pairs to filter by.
            limit (int, optional): Maximum records to return. Defaults to None.
            offset (int, optional): Number of records to skip. Defaults to None.
            order_by (str, optional): Field to order by. Defaults to None.
            
        Returns:
            list: List of matching model instances.
        """
        try:
            # Build WHERE clause from criteria
            where_clauses = []
            params = {}
            
            for key, value in criteria.items():
                where_clauses.append(f"{key} = :{key}")
                params[key] = value
            
            # Construct the query
            query = f"SELECT * FROM {self.table_name}"
            
            if where_clauses:
                query += f" WHERE {' AND '.join(where_clauses)}"
                
            if order_by:
                query += f" ORDER BY {order_by}"
                
            if limit:
                query += f" LIMIT {limit}"
                
            if offset:
                query += f" OFFSET {offset}"
            
            # Execute the query
            results = self.db_manager.execute_query(query, params)
            
            return [self.model_class.from_dict(dict(row)) for row in results]
            
        except Exception as e:
            logging.error(f"Error finding {self.model_class.__name__} by criteria: {str(e)}")
            return []
    
    def count(self, criteria=None):
        """Count records, optionally matching specific criteria.
        
        Args:
            criteria (dict, optional): Dictionary of field:value pairs to filter by. Defaults to None.
            
        Returns:
            int: Count of matching records.
        """
        try:
            # Construct the query
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            params = {}
            
            # Add WHERE clause if criteria specified
            if criteria:
                where_clauses = []
                for key, value in criteria.items():
                    where_clauses.append(f"{key} = :{key}")
                    params[key] = value
                
                if where_clauses:
                    query += f" WHERE {' AND '.join(where_clauses)}"
            
            # Execute the query
            result = self.db_manager.execute_query(query, params)
            
            return result[0]['count'] if result else 0
            
        except Exception as e:
            logging.error(f"Error counting {self.model_class.__name__}: {str(e)}")
            return 0
    
    # Helper methods for related records
    def _save_related_records(self, parent_id, relation_name, items):
        """Save related records to a junction table or child table.
        
        This is a stub method that should be overridden in subclasses.
        
        Args:
            parent_id (str): ID of the parent record.
            relation_name (str): Name of the relation.
            items: Collection of related items to save.
        """
        pass
    
    def _delete_related_records(self, parent_id, relation_table):
        """Delete related records from a junction table or child table.
        
        Args:
            parent_id (str): ID of the parent record.
            relation_table (str): Name of the relation table.
        """
        # Get parent field name from relation table
        parent_field = f"{self.table_name[:-1]}_id"  # Assumes singular form by removing 's'
        
        # For junction tables, delete by parent ID
        try:
            query = f"""
                DELETE FROM {relation_table}
                WHERE {parent_field} = :parent_id
            """
            
            self.db_manager.execute_update(query, {"parent_id": parent_id})
        except Exception as e:
            logging.error(f"Error deleting related records in {relation_table}: {str(e)}")