import os
import sys
import logging
import tkinter as tk
from tkinter import messagebox

# Add src directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database and models
from src.db.db_manager import DatabaseManager
from src.db.repositories.district import DistrictRepository
from src.db.repositories.faction import FactionRepository
from src.db.repositories.agent import AgentRepository
from src.db.repositories.squadron import SquadronRepository
from src.db.repositories.rumor import RumorRepository

# Import logic managers
from src.logic.turn import TurnManager
from src.logic.turn_resolution import TurnResolutionManager

# Import UI
from src.ui.main_window import MainWindow


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("faction_manager.log"),
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers to different levels as needed
    logging.getLogger("PIL").setLevel(logging.WARNING)  # Pillow can be verbose
    logging.getLogger("matplotlib").setLevel(logging.WARNING)  # Same for matplotlib


def main():
    """Main entry point for the application."""
    # Setup logging
    setup_logging()
    
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Create database
        db_path = os.path.join(data_dir, "faction_manager.db")
        db_manager = DatabaseManager(db_path)
        
        # Create repositories
        district_repository = DistrictRepository(db_manager)
        faction_repository = FactionRepository(db_manager)
        agent_repository = AgentRepository(db_manager)
        squadron_repository = SquadronRepository(db_manager)
        rumor_repository = RumorRepository(db_manager)
        
        # Create managers
        turn_manager = TurnManager(
            db_manager,
            district_repository,
            faction_repository,
            agent_repository,
            squadron_repository,
            rumor_repository
        )
        turn_resolution_manager = TurnResolutionManager(
            db_manager, 
            district_repository, 
            faction_repository, 
            agent_repository, 
            squadron_repository, 
            rumor_repository,
            turn_manager
        )
        
        # Create main window
        main_window = MainWindow(
            db_manager,
            district_repository,
            faction_repository,
            agent_repository,
            squadron_repository,
            rumor_repository,
            turn_manager,
            turn_resolution_manager
        )
        
        # Run the application
        main_window.run()
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Error starting application: {str(e)}\n{error_details}")
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()