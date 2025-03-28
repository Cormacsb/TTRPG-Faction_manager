import tkinter as tk
from tkinter import ttk
import logging
import os

# Import panels
from .dashboard import DashboardPanel
from .district_panel import DistrictPanel
from .faction_panel import FactionPanel
from .map_panel import MapPanel
from .turn_panel import TurnPanel
from .newspaper_panel import NewspaperPanel
from .reports_panel import ReportsPanel
from .piece_panel import PiecePanel
from .assignment_panel import AssignmentPanel
class MainWindow:
    """Main window for the Faction Management System application."""
    
    def __init__(self, db_manager, district_repository, faction_repository, 
                 agent_repository, squadron_repository, rumor_repository,
                 turn_manager, turn_resolution_manager):
        """Initialize the main window.
        
        Args:
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            agent_repository: Repository for agent operations.
            squadron_repository: Repository for squadron operations.
            rumor_repository: Repository for rumor operations.
            turn_manager: Turn manager instance.
            turn_resolution_manager: Turn resolution manager instance.
        """
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.agent_repository = agent_repository
        self.squadron_repository = squadron_repository
        self.rumor_repository = rumor_repository
        self.turn_manager = turn_manager
        self.turn_resolution_manager = turn_resolution_manager
        
        # Get the action manager from the turn resolution manager
        self.action_manager = self.turn_resolution_manager.action_manager
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Faction Management System")
        self.root.geometry("1280x720")
        
        # Setup styles
        self.setup_styles()
        
        # Create menu
        self.create_menu()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create status bar
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Create panels
        self.create_panels()
    
    def setup_styles(self):
        """Setup ttk styles."""
        self.style = ttk.Style()
        
        # Configure tab appearance
        self.style.configure("TNotebook", borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=[10, 5])
        
        # Configure other common elements
        self.style.configure("TButton", padding=5)
        self.style.configure("TLabel", padding=2)
        self.style.configure("TFrame", background="#f0f0f0")
    
    def create_menu(self):
        """Create the application menu."""
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New Game", command=self.new_game)
        file_menu.add_command(label="Open Game", command=self.open_game)
        file_menu.add_command(label="Save Game", command=self.save_game)
        file_menu.add_command(label="Save Game As...", command=self.save_game_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Preferences", command=self.show_preferences)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # Tools menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        tools_menu.add_command(label="Game Setup", command=self.show_game_setup)
        tools_menu.add_command(label="Map Editor", command=self.show_map_editor)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        # Set menu bar
        self.root.config(menu=self.menu_bar)
    
    def create_panels(self):
        """Create and add all panels to the notebook."""
        # Dashboard panel
        self.dashboard_panel = DashboardPanel(
            self.notebook, self.db_manager, self.district_repository, 
            self.faction_repository, self.agent_repository, self.squadron_repository
        )
        self.notebook.add(self.dashboard_panel.frame, text="Dashboard")
        
        # District management panel
        self.district_panel = DistrictPanel(
            self.notebook, self.db_manager, self.district_repository
        )
        self.notebook.add(self.district_panel.frame, text="Districts")
        
        # Faction management panel
        self.faction_panel = FactionPanel(
            self.notebook, self.db_manager, self.faction_repository
        )
        self.notebook.add(self.faction_panel.frame, text="Factions")

        # Piece management panel
        self.piece_panel = PiecePanel(
            self.notebook, self.db_manager, self.agent_repository,
            self.squadron_repository, self.faction_repository, self.district_repository
        )
        self.notebook.add(self.piece_panel, text="Pieces")

        # Assignment panel
        self.assignment_panel = AssignmentPanel(
            self.notebook, self.db_manager, self.agent_repository,
            self.squadron_repository, self.faction_repository, self.district_repository
        )
        self.notebook.add(self.assignment_panel, text="Assignments")
        
        # Map visualization panel
        self.map_panel = MapPanel(
            self.notebook, self.db_manager, self.district_repository, 
            self.faction_repository
        )
        self.notebook.add(self.map_panel, text="Map")
        
        # Turn resolution panel
        self.turn_panel = TurnPanel(
            self.notebook, self.db_manager, self.district_repository, 
            self.faction_repository, self.agent_repository, self.squadron_repository, 
            self.rumor_repository, self.turn_manager, self.turn_resolution_manager, self.action_manager
        )
        self.notebook.add(self.turn_panel, text="Turn Resolution")
        
        # Newspaper editor panel
        self.newspaper_panel = NewspaperPanel(
            self.notebook, self.db_manager, self.district_repository,
            self.faction_repository, self.rumor_repository
        )
        self.notebook.add(self.newspaper_panel, text="Newspaper")
        
        # Reports panel
        self.report_panel = ReportsPanel(
            self.notebook, self.db_manager, self.district_repository,
            self.faction_repository, self.rumor_repository, None  # Monitoring manager not available
        )
        self.notebook.add(self.report_panel, text="Reports")
    
    def run(self):
        """Run the main application loop."""
        self.root.mainloop()
    
    def update_status(self, message):
        """Update the status bar message.
        
        Args:
            message (str): Status message to display.
        """
        self.status_label.config(text=message)
    
    # Menu command methods
    def new_game(self):
        """Create a new game."""
        # Implement new game dialog
        self.update_status("Creating new game...")
    
    def open_game(self):
        """Open an existing game."""
        # Implement open game dialog
        self.update_status("Opening game...")
    
    def save_game(self):
        """Save the current game."""
        # Implement save game functionality
        self.update_status("Saving game...")
    
    def save_game_as(self):
        """Save the current game with a new name."""
        # Implement save as dialog
        self.update_status("Saving game as...")
    
    def show_preferences(self):
        """Show preferences dialog."""
        # Implement preferences dialog
        self.update_status("Showing preferences...")
    
    def show_game_setup(self):
        """Show game setup dialog."""
        # Implement game setup dialog
        self.update_status("Showing game setup...")
    
    def show_map_editor(self):
        """Show map editor dialog."""
        # Implement map editor dialog
        self.update_status("Showing map editor...")
    
    def show_help(self):
        """Show help dialog."""
        # Implement help dialog
        self.update_status("Showing help...")
    
    def show_about(self):
        """Show about dialog."""
        # Create simple about dialog
        about_window = tk.Toplevel(self.root)
        about_window.title("About Faction Management System")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        
        # Center the window
        about_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + (self.root.winfo_width() / 2) - 200,
            self.root.winfo_rooty() + (self.root.winfo_height() / 2) - 150
        ))
        
        # Add content
        ttk.Label(
            about_window, 
            text="Faction Management System", 
            font=("", 14, "bold")
        ).pack(pady=10)
        
        ttk.Label(
            about_window, 
            text="Version 1.0"
        ).pack()
        
        ttk.Label(
            about_window, 
            text="A system for managing factions, territories, and conflict resolution."
        ).pack(pady=10)
        
        ttk.Button(
            about_window, 
            text="Close", 
            command=about_window.destroy
        ).pack(pady=20)
        
        self.update_status("Showing about dialog...")