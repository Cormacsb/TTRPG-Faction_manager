import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import json
from datetime import datetime
import queue
import os
from PIL import Image, ImageTk
from src.logic.action import ActionManager
from src.logic.influence import InfluenceManager


class TurnPanel(ttk.Frame):
    """Panel for managing turn progression and resolution."""
    
    def __init__(self, parent, db_manager, district_repository, faction_repository, 
                 agent_repository, squadron_repository, rumor_repository, turn_manager, turn_resolution_manager, action_manager):
        """Initialize the turn panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            agent_repository: Repository for agent operations.
            squadron_repository: Repository for squadron operations.
            rumor_repository: Repository for rumor operations.
            turn_manager: Turn manager instance.
            turn_resolution_manager: Turn resolution manager instance.
            action_manager: Action manager instance.
        """
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.agent_repository = agent_repository
        self.squadron_repository = squadron_repository
        self.rumor_repository = rumor_repository
        self.turn_manager = turn_manager
        self.turn_resolution_manager = turn_resolution_manager
        self.action_manager = action_manager
        
        # Create processing queue
        self.processing_queue = queue.Queue()
        self.processing_active = False
        
        # Get current turn info
        self.turn_info = self.turn_manager.get_current_turn()
        
        # Initialize UI elements
        self._create_widgets()
        
        # Set initial state
        self._update_ui_state()
        
        # Start queue processor
        self._process_queue()
    
    def _create_widgets(self):
        """Create the panel widgets."""
        # Main layout - split into sections
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Turn info section
        self.rowconfigure(1, weight=0)  # Phase controls section
        self.rowconfigure(2, weight=1)  # Current phase display
        self.rowconfigure(3, weight=1)  # Results display
        
        # Turn info section
        self._create_turn_info_section()
        
        # Phase controls section
        self._create_phase_controls_section()
        
        # Current phase display
        self._create_current_phase_display()
        
        # Results display
        self._create_results_display()
    
    def _create_turn_info_section(self):
        """Create the turn information section."""
        turn_frame = ttk.LabelFrame(self, text="Turn Information")
        turn_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # Turn number and phase display
        self.turn_label = ttk.Label(turn_frame, text=f"Turn: {self.turn_info['current_turn']}")
        self.turn_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.phase_label = ttk.Label(turn_frame, text=f"Phase: {self.turn_info['current_phase']}")
        self.phase_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Turn part indicator
        self.turn_part_label = ttk.Label(turn_frame, text="Turn Part: 1 (Pre-Conflict)")
        self.turn_part_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Add campaign name
        campaign_label = ttk.Label(turn_frame, text="Campaign:")
        campaign_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        
        # Use dictionary access instead of .get() method
        campaign_name = self.turn_info.get('campaign_name', 'New Campaign') if isinstance(self.turn_info, dict) else self.turn_info['campaign_name'] if 'campaign_name' in self.turn_info else 'New Campaign'
        
        self.campaign_label = ttk.Label(turn_frame, text=campaign_name)
        self.campaign_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
    
    def _create_phase_controls_section(self):
        """Create the phase controls section."""
        controls_frame = ttk.LabelFrame(self, text="Phase Controls")
        controls_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Process turn buttons
        self.process_turn_part1_button = ttk.Button(
            controls_frame, text="Process Turn Part 1", 
            command=self._process_turn_part1
        )
        self.process_turn_part1_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.process_turn_part2_button = ttk.Button(
            controls_frame, text="Process Turn Part 2", 
            command=self._process_turn_part2
        )
        self.process_turn_part2_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.process_turn_part2_button.config(state="disabled")  # Initially disabled
        
        # Reset button
        self.reset_button = ttk.Button(
            controls_frame, text="Reset Turn Processing",
            command=self._reset_turn_processing
        )
        self.reset_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Spacer
        ttk.Label(controls_frame, text="").grid(row=0, column=3, padx=20, pady=5)
        
        # Status indicator
        self.status_label = ttk.Label(controls_frame, text="Status: Ready")
        self.status_label.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        # Progress indicator
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            controls_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
        
        # Emergency stop button
        self.stop_button = ttk.Button(
            controls_frame, text="Stop Processing", 
            command=self._stop_processing
        )
        self.stop_button.grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.stop_button.config(state="disabled")  # Initially disabled
        
        # Configure grid weights
        controls_frame.columnconfigure(5, weight=1)  # Make progress bar expandable
    
    def _create_current_phase_display(self):
        """Create the current phase display section."""
        phase_frame = ttk.LabelFrame(self, text="Current Phase")
        phase_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        # Create notebook for different phase UIs
        self.phase_notebook = ttk.Notebook(phase_frame)
        self.phase_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create tabs for different phases
        self.influence_decay_frame = ttk.Frame(self.phase_notebook)
        self.phase_notebook.add(self.influence_decay_frame, text="Influence Decay")
        
        self.assignment_frame = ttk.Frame(self.phase_notebook)
        self.phase_notebook.add(self.assignment_frame, text="Assignment")
        
        self.conflict_detection_frame = ttk.Frame(self.phase_notebook)
        self.phase_notebook.add(self.conflict_detection_frame, text="Conflict Detection")
        
        self.action_roll_frame = ttk.Frame(self.phase_notebook)
        self.phase_notebook.add(self.action_roll_frame, text="Action Roll")
        
        self.conflict_resolution_frame = ttk.Frame(self.phase_notebook)
        self.phase_notebook.add(self.conflict_resolution_frame, text="Conflict Resolution")
        
        self.action_resolution_frame = ttk.Frame(self.phase_notebook)
        self.phase_notebook.add(self.action_resolution_frame, text="Action Resolution")
        
        self.influence_changes_frame = ttk.Frame(self.phase_notebook)
        self.phase_notebook.add(self.influence_changes_frame, text="Influence Changes")
        
        self.map_update_frame = ttk.Frame(self.phase_notebook)
        self.phase_notebook.add(self.map_update_frame, text="Map Update")
        # Initialize phase-specific UI components
        self._initialize_phase_uis()
    
    def _initialize_phase_uis(self):
        """Initialize UI components for each phase."""
        # Influence decay phase UI
        influence_decay_frame = ttk.Frame(self.influence_decay_frame)
        influence_decay_frame.pack(fill="both", expand=True)
        
        # Decay results table
        ttk.Label(influence_decay_frame, text="Influence Decay Results:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.decay_tree = ttk.Treeview(
            influence_decay_frame,
            columns=("district", "faction", "old_value", "change", "new_value"),
            show="headings"
        )
        
        self.decay_tree.heading("district", text="District")
        self.decay_tree.heading("faction", text="Faction")
        self.decay_tree.heading("old_value", text="Old Value")
        self.decay_tree.heading("change", text="Change")
        self.decay_tree.heading("new_value", text="New Value")
        
        self.decay_tree.column("district", width=120)
        self.decay_tree.column("faction", width=120)
        self.decay_tree.column("old_value", width=80)
        self.decay_tree.column("change", width=80)
        self.decay_tree.column("new_value", width=80)
        
        self.decay_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add scrollbar
        decay_scrollbar = ttk.Scrollbar(influence_decay_frame, orient="vertical", command=self.decay_tree.yview)
        self.decay_tree.configure(yscrollcommand=decay_scrollbar.set)
        decay_scrollbar.grid(row=1, column=1, sticky="ns")
        
        influence_decay_frame.columnconfigure(0, weight=1)
        influence_decay_frame.rowconfigure(1, weight=1)
        
        # Action roll phase UI
        action_roll_frame = ttk.Frame(self.action_roll_frame)
        action_roll_frame.pack(fill="both", expand=True)
        
        # Action roll results table
        ttk.Label(action_roll_frame, text="Action Roll Results:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.action_roll_tree = ttk.Treeview(
            action_roll_frame,
            columns=("id", "faction", "piece", "district", "action_type", "roll", "outcome"),
            show="headings"
        )
        
        self.action_roll_tree.heading("id", text="ID")
        self.action_roll_tree.heading("faction", text="Faction")
        self.action_roll_tree.heading("piece", text="Piece")
        self.action_roll_tree.heading("district", text="District")
        self.action_roll_tree.heading("action_type", text="Action Type")
        self.action_roll_tree.heading("roll", text="Roll Details")
        self.action_roll_tree.heading("outcome", text="Outcome")
        
        self.action_roll_tree.column("id", width=80)
        self.action_roll_tree.column("faction", width=120)
        self.action_roll_tree.column("piece", width=120)
        self.action_roll_tree.column("district", width=120)
        self.action_roll_tree.column("action_type", width=120)
        self.action_roll_tree.column("roll", width=200)
        self.action_roll_tree.column("outcome", width=100)
        
        self.action_roll_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add scrollbar
        action_scrollbar = ttk.Scrollbar(action_roll_frame, orient="vertical", command=self.action_roll_tree.yview)
        self.action_roll_tree.configure(yscrollcommand=action_scrollbar.set)
        action_scrollbar.grid(row=1, column=1, sticky="ns")
        
        # Connect event handler
        self.action_roll_tree.bind("<<TreeviewSelect>>", self._on_action_roll_selected)
        
        action_roll_frame.columnconfigure(0, weight=1)
        action_roll_frame.rowconfigure(1, weight=1)
        
        # Enemy Penalty UI
        enemy_penalty_frame = ttk.Frame(self.action_roll_frame)
        enemy_penalty_frame.pack(fill="both", expand=True, pady=10)
        
        # Enemy penalty results table
        ttk.Label(enemy_penalty_frame, text="Enemy Penalties:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.enemy_penalty_tree = ttk.Treeview(
            enemy_penalty_frame,
            columns=("id", "faction", "piece", "district", "penalty", "sources"),
            show="headings"
        )
        
        self.enemy_penalty_tree.heading("id", text="Action ID")
        self.enemy_penalty_tree.heading("faction", text="Faction")
        self.enemy_penalty_tree.heading("piece", text="Piece")
        self.enemy_penalty_tree.heading("district", text="District")
        self.enemy_penalty_tree.heading("penalty", text="Penalty")
        self.enemy_penalty_tree.heading("sources", text="Sources")
        
        self.enemy_penalty_tree.column("id", width=80)
        self.enemy_penalty_tree.column("faction", width=120)
        self.enemy_penalty_tree.column("piece", width=120)
        self.enemy_penalty_tree.column("district", width=120)
        self.enemy_penalty_tree.column("penalty", width=60)
        self.enemy_penalty_tree.column("sources", width=60)
        
        self.enemy_penalty_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add scrollbar
        penalty_scrollbar = ttk.Scrollbar(enemy_penalty_frame, orient="vertical", command=self.enemy_penalty_tree.yview)
        self.enemy_penalty_tree.configure(yscrollcommand=penalty_scrollbar.set)
        penalty_scrollbar.grid(row=1, column=1, sticky="ns")
        
        # Penalty details
        ttk.Label(enemy_penalty_frame, text="Penalty Details:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        self.penalty_details_text = tk.Text(enemy_penalty_frame, height=6, width=40)
        self.penalty_details_text.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Connect event handler
        self.enemy_penalty_tree.bind("<<TreeviewSelect>>", self._on_penalty_selected)
        
        enemy_penalty_frame.columnconfigure(0, weight=1)
        enemy_penalty_frame.rowconfigure(1, weight=1)
        enemy_penalty_frame.rowconfigure(3, weight=1)
        
        # Conflict detection and resolution UI
        self._create_conflict_resolution_ui()
        
        # Action resolution phase UI
        action_resolution_frame = ttk.Frame(self.action_resolution_frame)
        action_resolution_frame.pack(fill="both", expand=True)
        
        # Create filter controls
        filter_frame = ttk.Frame(action_resolution_frame)
        filter_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter by Faction:").pack(side="left", padx=5)
        self.faction_filter_var = tk.StringVar(value="All Factions")
        self.faction_filter_combo = ttk.Combobox(filter_frame, textvariable=self.faction_filter_var, width=25)
        self.faction_filter_combo.pack(side="left", padx=5)
        self.faction_filter_combo.bind("<<ComboboxSelected>>", self._apply_faction_filter)
        
        # Action results list
        ttk.Label(action_resolution_frame, text="Action Results:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.action_result_tree = ttk.Treeview(
            action_resolution_frame, 
            columns=("id", "faction", "piece", "district", "action_type", "result"),
            show="headings"
        )
        
        self.action_result_tree.heading("id", text="ID")
        self.action_result_tree.heading("faction", text="Faction")
        self.action_result_tree.heading("piece", text="Piece")
        self.action_result_tree.heading("district", text="District")
        self.action_result_tree.heading("action_type", text="Action")
        self.action_result_tree.heading("result", text="Result")
        
        self.action_result_tree.column("id", width=50)
        self.action_result_tree.column("faction", width=100)
        self.action_result_tree.column("piece", width=100)
        self.action_result_tree.column("district", width=100)
        self.action_result_tree.column("action_type", width=100)
        self.action_result_tree.column("result", width=150)
        
        self.action_result_tree.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add scrollbar
        action_result_scrollbar = ttk.Scrollbar(action_resolution_frame, orient="vertical", command=self.action_result_tree.yview)
        self.action_result_tree.configure(yscrollcommand=action_result_scrollbar.set)
        action_result_scrollbar.grid(row=2, column=1, sticky="ns")
        
        # Bind selection event
        self.action_result_tree.bind("<<TreeviewSelect>>", self._on_action_result_selected)
        
        # Action details panel
        details_frame = ttk.LabelFrame(action_resolution_frame, text="Action Details")
        details_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        self.action_details_text = tk.Text(details_frame, height=20, wrap="word")
        self.action_details_text.pack(fill="both", expand=True, padx=5, pady=5)
        details_scrollbar = ttk.Scrollbar(self.action_details_text, orient="vertical", command=self.action_details_text.yview)
        self.action_details_text.configure(yscrollcommand=details_scrollbar.set)
        details_scrollbar.pack(side="right", fill="y")
        
        # Set grid weights to make panels resizable
        action_resolution_frame.rowconfigure(2, weight=2)  # Action results gets more space
        action_resolution_frame.rowconfigure(3, weight=3)  # Details panel gets more space
        action_resolution_frame.columnconfigure(0, weight=1)

        # Influence changes tab
        influence_changes_frame = ttk.Frame(self.influence_changes_frame)
        influence_changes_frame.pack(fill="both", expand=True)
        
        # Influence changes section
        influence_frame = ttk.LabelFrame(influence_changes_frame, text="Influence Changes")
        influence_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.influence_tree = ttk.Treeview(
            influence_frame, 
            columns=("district", "faction", "change", "new_value"),
            show="headings"
        )
        
        self.influence_tree.heading("district", text="District")
        self.influence_tree.heading("faction", text="Faction")
        self.influence_tree.heading("change", text="Change")
        self.influence_tree.heading("new_value", text="New Value")
        
        self.influence_tree.column("district", width=120)
        self.influence_tree.column("faction", width=120)
        self.influence_tree.column("change", width=80)
        self.influence_tree.column("new_value", width=80)
        
        self.influence_tree.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Map update phase UI
        self._create_map_update_ui()
    
    def _create_conflict_resolution_ui(self):
        """Create the conflict resolution UI."""
        # Main frame
        conflict_resolution_frame = ttk.Frame(self.conflict_resolution_frame)
        conflict_resolution_frame.pack(fill="both", expand=True)
        
        # Split into two columns
        conflict_resolution_frame.columnconfigure(0, weight=1)
        conflict_resolution_frame.columnconfigure(1, weight=1)
        conflict_resolution_frame.rowconfigure(0, weight=1)
        
        # Left side - conflict list
        conflict_list_frame = ttk.LabelFrame(conflict_resolution_frame, text="Pending Conflicts")
        conflict_list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.pending_conflict_tree = ttk.Treeview(
            conflict_list_frame, 
            columns=("id", "district", "type", "factions"),
            show="headings"
        )
        
        self.pending_conflict_tree.heading("id", text="ID")
        self.pending_conflict_tree.heading("district", text="District")
        self.pending_conflict_tree.heading("type", text="Type")
        self.pending_conflict_tree.heading("factions", text="Factions")
        
        self.pending_conflict_tree.column("id", width=50)
        self.pending_conflict_tree.column("district", width=120)
        self.pending_conflict_tree.column("type", width=100)
        self.pending_conflict_tree.column("factions", width=200)
        
        self.pending_conflict_tree.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Connect selection event
        self.pending_conflict_tree.bind("<<TreeviewSelect>>", self._on_pending_conflict_selected)
        
        # Right side - conflict resolution form
        resolution_form_frame = ttk.LabelFrame(conflict_resolution_frame, text="Conflict Resolution")
        resolution_form_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Conflict details
        ttk.Label(resolution_form_frame, text="Conflict Details:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.resolution_details_text = tk.Text(resolution_form_frame, height=6, width=40)
        self.resolution_details_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.resolution_details_text.config(state="disabled")
        
        # Faction involved
        ttk.Label(resolution_form_frame, text="Factions Involved:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        self.factions_tree = ttk.Treeview(
            resolution_form_frame, 
            columns=("faction", "role"),
            show="headings",
            height=4
        )
        
        self.factions_tree.heading("faction", text="Faction")
        self.factions_tree.heading("role", text="Role")
        
        self.factions_tree.column("faction", width=150)
        self.factions_tree.column("role", width=100)
        
        self.factions_tree.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Resolution type
        ttk.Label(resolution_form_frame, text="Resolution Type:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        
        self.resolution_type = tk.StringVar(value="win")
        resolution_types = [
            ("One faction wins", "win"),
            ("Draw between factions", "draw"),
            ("Special ruling", "special")
        ]
        
        for i, (text, value) in enumerate(resolution_types):
            ttk.Radiobutton(
                resolution_form_frame, 
                text=text, 
                variable=self.resolution_type, 
                value=value,
                command=self._update_resolution_form
            ).grid(row=5+i, column=0, sticky="w", padx=5, pady=2)
        
        # Winning faction selection (only for "win" type)
        self.winning_faction_frame = ttk.Frame(resolution_form_frame)
        self.winning_faction_frame.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(self.winning_faction_frame, text="Winning Faction:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.winning_faction = tk.StringVar()
        self.winning_faction_combobox = ttk.Combobox(self.winning_faction_frame, textvariable=self.winning_faction)
        self.winning_faction_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        # Draw factions selection (only for "draw" type)
        self.draw_factions_frame = ttk.Frame(resolution_form_frame)
        self.draw_factions_frame.grid(row=9, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(self.draw_factions_frame, text="Select factions that are in a draw:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.draw_factions_listbox = tk.Listbox(self.draw_factions_frame, selectmode="multiple", height=4)
        self.draw_factions_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
        
        # Resolution notes
        ttk.Label(resolution_form_frame, text="Resolution Notes:").grid(row=10, column=0, sticky="w", padx=5, pady=5)
        
        self.resolution_notes = tk.Text(resolution_form_frame, height=4, width=40)
        self.resolution_notes.grid(row=11, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Apply resolution button
        self.apply_resolution_button = ttk.Button(
            resolution_form_frame, 
            text="Apply Resolution", 
            command=self._apply_conflict_resolution
        )
        self.apply_resolution_button.grid(row=12, column=0, columnspan=2, sticky="nsew", padx=5, pady=10)
        
        # Configure weights
        resolution_form_frame.columnconfigure(1, weight=1)
        resolution_form_frame.rowconfigure(11, weight=1)
        
        # Hide frames initially
        self.draw_factions_frame.grid_remove()
        
        # Initially disabled
        self.apply_resolution_button.config(state="disabled")
        
    def _create_results_display(self):
        """Create the results display section."""
        results_frame = ttk.LabelFrame(self, text="Results Log")
        results_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        
        # Create a horizontal frame for the buttons
        buttons_frame = ttk.Frame(results_frame)
        buttons_frame.pack(fill="x", padx=5, pady=2)
        
        # Add buttons to view different phase results
        ttk.Label(buttons_frame, text="View Results:").pack(side="left", padx=5)
        
        # Create buttons for each important phase
        self.view_decay_button = ttk.Button(
            buttons_frame, text="Influence Decay", 
            command=lambda: self.phase_notebook.select(0)
        )
        self.view_decay_button.pack(side="left", padx=2)
        
        self.view_rolls_button = ttk.Button(
            buttons_frame, text="Action Rolls", 
            command=lambda: self.phase_notebook.select(3)
        )
        self.view_rolls_button.pack(side="left", padx=2)
        
        self.view_resolution_button = ttk.Button(
            buttons_frame, text="Action Resolution", 
            command=lambda: self.phase_notebook.select(5)
        )
        self.view_resolution_button.pack(side="left", padx=2)
        
        self.view_monitoring_button = ttk.Button(
            buttons_frame, text="Monitoring", 
            command=lambda: self.phase_notebook.select(6)
        )
        self.view_monitoring_button.pack(side="left", padx=2)
        
        self.return_button = ttk.Button(
            buttons_frame, text="Return to Current Phase", 
            command=self._return_to_current_phase
        )
        self.return_button.pack(side="left", padx=2)
        
        # Results text widget
        self.results_text = tk.Text(results_frame, wrap="word", height=10)
        self.results_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.results_text, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Add timestamp to text
        self._log_message("Turn panel initialized")
    
    def _return_to_current_phase(self):
        """Return to the currently active phase tab."""
        phase = self.turn_info['current_phase']
        
        # Add debug logging to show all available tabs
        tab_names = [self.phase_notebook.tab(i, "text") for i in range(self.phase_notebook.index("end"))]
        logging.info(f"[UI_DEBUG] Available tabs: {', '.join(tab_names)}")
        
        # Use the same phase_to_tab mapping as in _update_ui_state
        phase_to_tab = {
            'preparation': 0,
            'influence_decay': 0,  # Changed from 1 to 0 to match the actual tabs
            'assignment': 1,       # Changed from 2 to 1
            'conflict_detection': 2, # Changed from 3 to 2
            'enemy_penalty': 3,      # Not used, but kept for consistency
            'action_roll': 3,         # Changed from 5 to 3
            'manual_conflict_resolution': 4, # Changed from 6 to 4
            'action_resolution': 5,     # Changed from 7 to 5
            'influence_changes': 6,
            'map_update': 7,
            'monitoring': 7  # Not used, but kept for consistency
        }
        
        if phase in phase_to_tab:
            tab_index = phase_to_tab[phase]
            if tab_index < len(tab_names):
                logging.info(f"[UI_DEBUG] Selecting tab index {tab_index} ({tab_names[tab_index]}) for phase: {phase}")
                self.phase_notebook.select(tab_index)
            else:
                logging.error(f"[UI_DEBUG] Tab index {tab_index} out of range (max: {len(tab_names)-1})")
            logging.info(f"[UI_DEBUG] Returning to current phase tab: {phase}")
        else:
            logging.error(f"[UI_DEBUG] No tab mapping found for phase: {phase}")
    
    def _update_ui_state(self):
        """Update the UI state based on current phase."""
        # Get fresh turn info
        logging.info("[UI_DEBUG] Starting _update_ui_state")
        old_phase = self.turn_info.get('current_phase', 'unknown')
        
        self.turn_info = self.turn_manager.get_current_turn()
        new_phase = self.turn_info['current_phase']
        
        logging.info(f"[UI_DEBUG] Phase change: {old_phase} -> {new_phase}")
        
        # Update labels
        self.turn_label.config(text=f"Turn: {self.turn_info['current_turn']}")
        self.phase_label.config(text=f"Phase: {self.turn_info['current_phase']}")
        
        # Update turn part indicator
        phase = self.turn_info['current_phase']
        if phase in ['preparation', 'influence_decay', 'assignment', 'conflict_detection', 'action_roll']:
            self.turn_part_label.config(text="Turn Part: 1 (Pre-Conflict)")
        elif phase == 'manual_conflict_resolution':
            self.turn_part_label.config(text="Turn Part: Manual Conflict Resolution")
        else:
            self.turn_part_label.config(text="Turn Part: 2 (Post-Conflict)")
        
        # Set active notebook tab based on phase
        phase_to_tab = {
            'preparation': 0,
            'influence_decay': 0,  # Matching actual tab index
            'assignment': 1,
            'conflict_detection': 2,
            'enemy_penalty': 3,    # Not used, but kept for reference
            'action_roll': 3,
            'manual_conflict_resolution': 4,
            'action_resolution': 5,
            'influence_changes': 6,
            'map_update': 7,
            'monitoring': 7        # Not used, but kept for reference
        }
        
        if phase in phase_to_tab:
            tab_index = phase_to_tab[phase]
            current_tab = self.phase_notebook.select()
            current_tab_idx = self.phase_notebook.index(current_tab)
            logging.info(f"[UI_DEBUG] Switching tab: {current_tab_idx} -> {tab_index} for phase {phase}")
            
            try:
                self.phase_notebook.select(tab_index)
                logging.info(f"[UI_DEBUG] Tab selection successful")
                
                # Verify the tab was actually selected
                current_tab = self.phase_notebook.select()
                current_tab_idx = self.phase_notebook.index(current_tab)
                logging.info(f"[UI_DEBUG] Current tab after selection: {current_tab_idx}")
                
                # Get tab name to confirm
                tab_name = self.phase_notebook.tab(current_tab, "text")
                logging.info(f"[UI_DEBUG] Current tab name: {tab_name}")
            except Exception as e:
                logging.error(f"[UI_DEBUG] Error selecting tab: {str(e)}")
        else:
            logging.warning(f"[UI_DEBUG] No tab mapping for phase: {phase}")
        
        # Update process buttons
        if phase in ['preparation', 'influence_decay', 'assignment', 'conflict_detection', 'action_roll']:
            self.process_turn_part1_button.config(state="normal")
            self.process_turn_part2_button.config(state="disabled")
        elif phase == 'manual_conflict_resolution':
            self.process_turn_part1_button.config(state="disabled")
            
            # Check if conflicts are all resolved
            if self._check_conflicts_resolved():
                self.process_turn_part2_button.config(state="normal")
            else:
                self.process_turn_part2_button.config(state="disabled")
        else:
            self.process_turn_part1_button.config(state="disabled")
            self.process_turn_part2_button.config(state="disabled")
        
        # Load phase-specific data
        logging.info("[UI_DEBUG] About to call _load_phase_data from _update_ui_state")
        self._load_phase_data()
        logging.info("[UI_DEBUG] Completed _update_ui_state")
    
    def _handle_part1_results(self, results):
        """Handle the results from turn part 1 processing."""
        # Check for errors
        if "error" in results:
            messagebox.showerror("Error", f"Error processing turn part 1: {results['error']}")
            self.status_label.config(text="Status: Error")
            self.stop_button.config(state="disabled")
            self.process_turn_part1_button.config(state="normal")
            return
        
        # Log detailed results for debugging
        logging.info("[TURN_DEBUG] Processing part 1 results:")
        logging.info(f"[TURN_DEBUG] Decay results: {json.dumps(results.get('decay_results', {}))}")
        logging.info(f"[TURN_DEBUG] Roll results: {json.dumps(results.get('roll_results', {}))}")
        
        # Additional detailed logging
        logging.info(f"[UI_DEBUG] Current phase before UI update: {self.turn_info.get('current_phase', 'unknown')}")
        
        # Check if the expected data is present
        if 'decay_results' not in results:
            logging.error("[UI_DEBUG] No decay_results found in part 1 results!")
        elif not results['decay_results']:
            logging.info("[UI_DEBUG] decay_results is empty or null")
        
        if 'roll_results' not in results:
            logging.error("[UI_DEBUG] No roll_results found in part 1 results!")
        elif not results['roll_results']:
            logging.info("[UI_DEBUG] roll_results is empty or null")
        
        # Log results
        self._log_message(f"Turn {results['turn_number']} part 1 processing complete")
        
        # Update progress and status
        self.progress_var.set(100)
        self.status_label.config(text="Status: Part 1 Complete")
        self.stop_button.config(state="disabled")
        
        # Store results for UI updates
        self.current_results = results
        logging.info(f"[UI_DEBUG] Stored results in self.current_results: {sorted(list(results.keys()))}")
        
        # First update the influence decay and action roll tabs with the results
        self._load_data_for_phase('influence_decay')
        self._load_data_for_phase('action_roll')
        
        # Then update the UI state to show the conflict resolution tab
        self._update_ui_state()
        logging.info(f"[UI_DEBUG] Called _update_ui_state, current phase after update: {self.turn_info.get('current_phase', 'unknown')}")
        
        # Debug why we might not be showing the right data
        current_tab = self.phase_notebook.select()
        current_tab_idx = self.phase_notebook.index(current_tab)
        tab_names = [self.phase_notebook.tab(i, "text") for i in range(self.phase_notebook.index("end"))]
        
        logging.info(f"[UI_DEBUG] Current notebook tab: {tab_names[current_tab_idx]} (index {current_tab_idx})")
        logging.info("[UI_DEBUG] Available tabs: " + ", ".join(tab_names))
        
        # Add a message to inform user they can view the results
        self._log_message("Use the 'View Results' buttons to see detailed Influence Decay and Action Roll results")
        
        # Show results summary
        summary = (
            f"Turn {results['turn_number']} Part 1 Processing Complete\n\n"
            f"Influence Decay: {len(results['decay_results'].get('affected_factions', []))} factions affected\n"
            f"Conflicts Detected: {len(results.get('conflicts', []))}\n"
            f"Actions Processed: {results['roll_results'].get('processed_actions', 0)}\n\n"
            f"Use the 'View Results' buttons above to see details."
        )
        
        messagebox.showinfo("Processing Complete", summary)
    
    def _load_data_for_phase(self, phase_name):
        """Load data for a specific phase without changing the current phase.
        
        Args:
            phase_name (str): Name of the phase to load data for.
        """
        logging.info(f"[UI_DEBUG] Loading data specifically for phase: {phase_name}")
        
        original_phase = self.turn_info.get('current_phase')
        saved_turn_info = self.turn_info.copy()
        
        # Temporarily modify turn_info to load data for the specified phase
        self.turn_info['current_phase'] = phase_name
        
        # Load the data for the specified phase
        self._load_phase_data()
        
        # Restore original turn_info
        self.turn_info = saved_turn_info
        
        logging.info(f"[UI_DEBUG] Completed loading data for specific phase: {phase_name}, restored to {original_phase}")
    
    def _load_phase_data(self):
        """Load data specific to the current phase."""
        phase = self.turn_info['current_phase']
        logging.info(f"[UI_DEBUG] Loading data for phase: {phase}")
        
        if phase == 'influence_decay':
            logging.info("[UI_DEBUG] Loading influence decay data")
            try:
                # Get decay results for current turn
                turn_number = self.turn_info['current_turn']
                
                # First check if we have decay results in memory
                if hasattr(self, 'current_results') and 'decay_results' in self.current_results:
                    logging.info("[UI_DEBUG] Found decay results in memory")
                    decay_results = self.current_results['decay_results']
                    logging.info(f"[UI_DEBUG] Memory decay results: {json.dumps(decay_results)}")
                    
                    # Add detailed logging about the structure
                    logging.info(f"[UI_DEBUG] Decay results type: {type(decay_results)}")
                    if isinstance(decay_results, dict):
                        for key, value in decay_results.items():
                            logging.info(f"[UI_DEBUG] Decay results key: {key}, value type: {type(value)}")
                            if isinstance(value, list) and key == 'affected_factions':
                                logging.info(f"[UI_DEBUG] Affected factions count: {len(value)}")
                
                # Clear existing items
                for item in self.decay_tree.get_children():
                    self.decay_tree.delete(item)
                
                # First, check if the decay_results table exists
                check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='decay_results';"
                table_check = self.db_manager.execute_query(check_query)
                
                if not table_check:
                    logging.info("[UI_DEBUG] decay_results table does not exist. Creating a message in the tree.")
                    self.decay_tree.insert(
                        "", "end", 
                        values=("No decay results table exists", "", "", "", "")
                    )
                    
                    # If we have memory results, display a summary
                    if hasattr(self, 'current_results') and 'decay_results' in self.current_results:
                        decay_results = self.current_results['decay_results']
                        if isinstance(decay_results, dict) and 'affected_factions' in decay_results:
                            self.decay_tree.insert(
                                "", "end",
                                values=(
                                    f"Summary from memory:", 
                                    f"{len(decay_results.get('affected_factions', []))} factions affected",
                                    f"{decay_results.get('total_influence_lost', 0)} influence lost",
                                    f"across {decay_results.get('processed_districts', 0)} districts",
                                    ""
                                )
                            )
                    return
                
                # Query the database
                try:
                    query = """
                        WITH old_values AS (
                            SELECT dr.district_id, dr.faction_id, 
                                   (di.influence_value + ABS(dr.influence_change)) as old_value
                            FROM decay_results dr
                            JOIN district_influence di ON dr.district_id = di.district_id 
                                AND dr.faction_id = di.faction_id
                            WHERE dr.turn_number = :turn_number
                        )
                        SELECT d.name as district_name, f.name as faction_name,
                               ov.old_value as old_value, dr.influence_change,
                               di.influence_value as new_value
                        FROM decay_results dr
                        JOIN districts d ON dr.district_id = d.id
                        JOIN factions f ON dr.faction_id = f.id
                        JOIN district_influence di ON dr.district_id = di.district_id 
                            AND dr.faction_id = di.faction_id
                        JOIN old_values ov ON dr.district_id = ov.district_id
                            AND dr.faction_id = ov.faction_id
                        WHERE dr.turn_number = :turn_number
                    """
                    results = self.db_manager.execute_query(query, {"turn_number": turn_number})
                    logging.info(f"[UI_DEBUG] Found {len(results)} decay results in database")
                    
                    # If no results are found, show a message
                    if not results:
                        self.decay_tree.insert(
                            "", "end", 
                            values=("No decay results for this turn", "", "", "", "")
                        )
                        
                        # If we have memory results, display a summary
                        if hasattr(self, 'current_results') and 'decay_results' in self.current_results:
                            decay_results = self.current_results['decay_results']
                            if isinstance(decay_results, dict) and 'affected_factions' in decay_results:
                                self.decay_tree.insert(
                                    "", "end",
                                    values=(
                                        f"Summary from memory:", 
                                        f"{len(decay_results.get('affected_factions', []))} factions affected",
                                        f"{decay_results.get('total_influence_lost', 0)} influence lost",
                                        f"across {decay_results.get('processed_districts', 0)} districts",
                                        ""
                                    )
                                )
                        return
                    
                    # Log the actual results for debugging
                    for result in results:
                        logging.info(f"[UI_DEBUG] Decay result: {json.dumps(dict(result))}")
                    
                    # Add results to tree
                    for row in results:
                        result = dict(row)
                        self.decay_tree.insert(
                            "", "end",
                            values=(
                                result['district_name'],
                                result['faction_name'],
                                result['old_value'],
                                result['influence_change'],
                                result['new_value']
                            )
                        )
                        logging.info(f"[UI_DEBUG] Added decay row to tree: {result['district_name']}, {result['faction_name']}")
                    
                    # Log final count of items in the tree 
                    logging.info(f"[UI_DEBUG] Decay tree now has {len(self.decay_tree.get_children())} items")
                except Exception as e:
                    logging.error(f"[UI_DEBUG] Error querying decay results: {str(e)}")
                    self.decay_tree.insert(
                        "", "end", 
                        values=(f"Error loading decay results: {str(e)}", "", "", "", "")
                    )
            
            except Exception as e:
                logging.error(f"[UI_DEBUG] Error loading influence decay data: {str(e)}")
                logging.exception("[UI_DEBUG] Full traceback:")
        
        elif phase == 'action_roll':
            logging.info("[UI_DEBUG] Loading action roll data")
            try:
                # Get all actions with rolls for current turn
                turn_number = self.turn_info['current_turn']
                
                # First check if we have roll results in memory
                if hasattr(self, 'current_results') and 'roll_results' in self.current_results:
                    logging.info("[UI_DEBUG] Found roll results in memory")
                    roll_results = self.current_results['roll_results']
                    logging.info(f"[UI_DEBUG] Memory roll results: {json.dumps(roll_results)}")
                    
                    # Add detailed logging about the structure
                    logging.info(f"[UI_DEBUG] Roll results type: {type(roll_results)}")
                    if isinstance(roll_results, dict):
                        for key, value in roll_results.items():
                            logging.info(f"[UI_DEBUG] Roll results key: {key}, value type: {type(value)}")
                            if key == 'results' and isinstance(value, list):
                                logging.info(f"[UI_DEBUG] Results count: {len(value)}")
                
                query = """
                    SELECT a.id, f.name as faction_name, 
                           CASE 
                               WHEN a.piece_type = 'agent' THEN ag.name
                               WHEN a.piece_type = 'squadron' THEN sq.name
                           END as piece_name,
                           d.name as district_name,
                           a.action_type, a.roll_result, a.outcome_tier,
                           a.dc, a.manual_modifier,
                           CASE 
                               WHEN a.piece_type = 'agent' THEN 
                                   COALESCE(a.attribute_used, '') || 
                                   CASE WHEN a.attribute_used IS NOT NULL AND a.skill_used IS NOT NULL THEN ' + ' ELSE '' END ||
                                   COALESCE(a.skill_used, '')
                               WHEN a.piece_type = 'squadron' THEN 
                                   COALESCE(a.aptitude_used, '')
                           END as used_skills
                    FROM actions a
                    JOIN factions f ON a.faction_id = f.id
                    JOIN districts d ON a.district_id = d.id
                    LEFT JOIN agents ag ON a.piece_id = ag.id AND a.piece_type = 'agent'
                    LEFT JOIN squadrons sq ON a.piece_id = sq.id AND a.piece_type = 'squadron'
                    WHERE a.turn_number = :turn_number
                    AND a.roll_result IS NOT NULL
                """
                results = self.db_manager.execute_query(query, {"turn_number": turn_number})
                logging.info(f"[UI_DEBUG] Found {len(results)} action roll results in database")
                
                # Log the actual results for debugging
                for result in results:
                    logging.info(f"[UI_DEBUG] Action roll result: {json.dumps(dict(result))}")
                
                # Clear existing items
                for item in self.action_roll_tree.get_children():
                    self.action_roll_tree.delete(item)
                
                # Add results to tree
                for row in results:
                    action = dict(row)
                    
                    # Format roll details
                    roll_details = f"{action['roll_result']}"
                    if action['dc']:
                        roll_details += f" vs DC {action['dc']}"
                    if action['manual_modifier']:
                        roll_details += f" (mod: {action['manual_modifier']:+d})"
                    if action['used_skills']:
                        roll_details += f" [{action['used_skills']}]"
                    
                    self.action_roll_tree.insert(
                        "", "end",
                        values=(
                            action['id'][:8],
                            action['faction_name'],
                            action['piece_name'],
                            action['district_name'],
                            action['action_type'].replace('_', ' ').title(),
                            roll_details,
                            action['outcome_tier'].replace('_', ' ').title() if action['outcome_tier'] else 'Pending'
                        )
                    )
                    logging.info(f"[UI_DEBUG] Added action roll row to tree: {action['faction_name']}, {action['action_type']}")
                
                # Log final count of items in the tree
                logging.info(f"[UI_DEBUG] Action roll tree now has {len(self.action_roll_tree.get_children())} items")
            
            except Exception as e:
                logging.error(f"[UI_DEBUG] Error loading action roll data: {str(e)}")
                logging.exception("[UI_DEBUG] Full traceback:")
        
        elif phase == 'enemy_penalty':
            logging.info("[UI_DEBUG] Loading enemy penalty data")
            try:
                # Get current turn
                turn_number = self.turn_info['current_turn']
                
                # Clear existing items
                for item in self.enemy_penalty_tree.get_children():
                    self.enemy_penalty_tree.delete(item)
                
                # Check if enemy_penalties table exists
                check_query = """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='enemy_penalties';
                """
                
                table_exists = self.db_manager.execute_query(check_query)
                
                if not table_exists:
                    self.enemy_penalty_tree.insert(
                        "", "end", 
                        values=("No enemy penalties table exists", "", "", "", "", "")
                    )
                    return
                
                # Get penalties for this turn
                query = """
                    SELECT ep.action_id, ep.total_penalty, ep.penalty_breakdown,
                           a.piece_id, a.piece_type, a.faction_id, a.district_id
                    FROM enemy_penalties ep
                    JOIN actions a ON ep.action_id = a.id
                    WHERE ep.turn_number = :turn_number
                """
                
                results = self.db_manager.execute_query(query, {"turn_number": turn_number})
                
                if not results:
                    self.enemy_penalty_tree.insert(
                        "", "end", 
                        values=("No penalties found", "", "", "", "", "")
                    )
                    return
                    
                # Add penalties to tree
                for row in results:
                    penalty = dict(row)
                    
                    # Get faction name
                    faction = self.faction_repository.find_by_id(penalty["faction_id"])
                    faction_name = faction.name if faction else "Unknown"
                    
                    # Get piece name
                    piece_name = "Unknown"
                    if penalty["piece_type"] == "agent":
                        agent = self.agent_repository.find_by_id(penalty["piece_id"])
                        piece_name = agent.name if agent else "Unknown"
                    elif penalty["piece_type"] == "squadron":
                        squadron = self.squadron_repository.find_by_id(penalty["piece_id"])
                        piece_name = squadron.name if squadron else "Unknown"
                    
                    # Get district name
                    district = self.district_repository.find_by_id(penalty["district_id"])
                    district_name = district.name if district else "Unknown"
                    
                    # Parse penalty breakdown to count sources
                    try:
                        breakdown = json.loads(penalty["penalty_breakdown"])
                        source_count = len(breakdown)
                    except:
                        source_count = 0
                    
                    # Add to tree
                    self.enemy_penalty_tree.insert(
                        "", "end",
                        values=(
                            penalty["action_id"][:8],
                            faction_name,
                            f"{penalty['piece_type'].title()}: {piece_name}",
                            district_name,
                            penalty["total_penalty"],
                            source_count
                        )
                    )
                
            except Exception as e:
                logging.error(f"[UI_DEBUG] Error loading enemy penalty data: {str(e)}")
                logging.exception("[UI_DEBUG] Full traceback:")


        elif phase == 'conflict_detection':
            logging.info("[UI_DEBUG] Loading conflict data")
            self._load_conflict_data()
        
        elif phase == 'manual_conflict_resolution':
            logging.info("[UI_DEBUG] Loading pending conflicts")
            self._load_pending_conflicts()
        
        logging.info(f"[UI_DEBUG] Completed loading data for phase: {phase}")
    
    def _load_conflict_data(self):
        """Load conflict data for the conflict detection phase."""
        # Clear existing data
        for item in self.conflict_tree.get_children():
            self.conflict_tree.delete(item)
        
        # Get conflicts for the current turn
        turn_number = self.turn_info['current_turn']
        
        query = """
            SELECT c.id, c.district_id, c.conflict_type, c.resolution_status
            FROM conflicts c
            WHERE c.turn_number = :turn_number
        """
        
        conflicts = self.db_manager.execute_query(query, {"turn_number": turn_number})
        
        # Add conflicts to treeview
        for row in conflicts:
            conflict = dict(row)
            
            # Get district name
            district = self.district_repository.find_by_id(conflict["district_id"])
            district_name = district.name if district else "Unknown"
            
            # Get factions involved
            query = """
                SELECT cf.faction_id, cf.role
                FROM conflict_factions cf
                WHERE cf.conflict_id = :conflict_id
            """
            
            faction_results = self.db_manager.execute_query(query, {"conflict_id": conflict["id"]})
            
            # Format faction text
            faction_texts = []
            for f_row in faction_results:
                f_data = dict(f_row)
                faction = self.faction_repository.find_by_id(f_data["faction_id"])
                faction_name = faction.name if faction else "Unknown"
                faction_texts.append(f"{faction_name} ({f_data['role']})")
            
            factions_text = ", ".join(faction_texts)
            
            # Format conflict type
            conflict_type = conflict["conflict_type"].replace("_", " ").title()
            
            # Add to treeview
            self.conflict_tree.insert(
                "", "end", values=(
                    conflict["id"][:8],
                    district_name,
                    conflict_type,
                    factions_text,
                    conflict["resolution_status"].title()
                )
            )
    
    def _load_pending_conflicts(self):
        """Load pending conflicts for the conflict resolution phase."""
        # Clear existing data
        for item in self.pending_conflict_tree.get_children():
            self.pending_conflict_tree.delete(item)
        
        # Get pending conflicts for the current turn
        turn_number = self.turn_info['current_turn']
        
        query = """
            SELECT c.id, c.district_id, c.conflict_type
            FROM conflicts c
            WHERE c.turn_number = :turn_number
            AND c.resolution_status = 'pending'
        """
        
        conflicts = self.db_manager.execute_query(query, {"turn_number": turn_number})
        
        # Add conflicts to treeview
        for row in conflicts:
            conflict = dict(row)
            
            # Get district name
            district = self.district_repository.find_by_id(conflict["district_id"])
            district_name = district.name if district else "Unknown"
            
            # Get factions involved
            query = """
                SELECT cf.faction_id, cf.role
                FROM conflict_factions cf
                WHERE cf.conflict_id = :conflict_id
            """
            
            faction_results = self.db_manager.execute_query(query, {"conflict_id": conflict["id"]})
            
            # Format faction text
            faction_texts = []
            for f_row in faction_results:
                f_data = dict(f_row)
                faction = self.faction_repository.find_by_id(f_data["faction_id"])
                faction_name = faction.name if faction else "Unknown"
                faction_texts.append(f"{faction_name}")
            
            factions_text = ", ".join(faction_texts)
            
            # Format conflict type
            conflict_type = conflict["conflict_type"].replace("_", " ").title()
            
            # Add to treeview
            self.pending_conflict_tree.insert(
                "", "end", values=(
                    conflict["id"][:8],
                    district_name,
                    conflict_type,
                    factions_text
                )
            )
    
    def _on_conflict_selected(self, event):
        """Handle conflict selection in the conflict tree."""
        selection = self.conflict_tree.selection()
        if not selection:
            return
        
        # Get selected conflict ID
        conflict_id_short = self.conflict_tree.item(selection[0])["values"][0]
        
        # Find full conflict ID (since we only display the first 8 chars)
        query = """
            SELECT id
            FROM conflicts 
            WHERE id LIKE :prefix
        """
        
        result = self.db_manager.execute_query(query, {"prefix": f"{conflict_id_short}%"})
        if not result:
            return
            
        conflict_id = result[0]["id"]
        
        # Get conflict details
        query = """
            SELECT c.*, d.name as district_name
            FROM conflicts c
            JOIN districts d ON c.district_id = d.id
            WHERE c.id = :conflict_id
        """
        
        result = self.db_manager.execute_query(query, {"conflict_id": conflict_id})
        if not result:
            return
            
        conflict = dict(result[0])
        
        # Get involved factions
        query = """
            SELECT cf.faction_id, cf.role, f.name as faction_name
            FROM conflict_factions cf
            JOIN factions f ON cf.faction_id = f.id
            WHERE cf.conflict_id = :conflict_id
        """
        
        factions = self.db_manager.execute_query(query, {"conflict_id": conflict_id})
        
        # Get involved pieces
        query = """
            SELECT cp.piece_id, cp.piece_type, cp.faction_id, 
                   cp.participation_type, cp.original_action_type
            FROM conflict_pieces cp
            WHERE cp.conflict_id = :conflict_id
        """
        
        pieces = self.db_manager.execute_query(query, {"conflict_id": conflict_id})
        
        # Format piece information
        piece_texts = []
        for piece in pieces:
            piece_data = dict(piece)
            
            # Get piece name
            piece_name = "Unknown"
            if piece_data["piece_type"] == "agent":
                agent = self.agent_repository.find_by_id(piece_data["piece_id"])
                piece_name = agent.name if agent else "Unknown"
            elif piece_data["piece_type"] == "squadron":
                squadron = self.squadron_repository.find_by_id(piece_data["piece_id"])
                piece_name = squadron.name if squadron else "Unknown"
            
            # Get faction name
            faction = self.faction_repository.find_by_id(piece_data["faction_id"])
            faction_name = faction.name if faction else "Unknown"
            
            # Format piece text
            piece_texts.append(
                f"{piece_data['piece_type'].title()}: {piece_name} ({faction_name}, "
                f"{piece_data['participation_type']} participation, "
                f"{piece_data['original_action_type']} action)"
            )
        
        # Format conflict details
        details = (
            f"Conflict ID: {conflict_id}\n"
            f"District: {conflict['district_name']}\n"
            f"Type: {conflict['conflict_type'].replace('_', ' ').title()}\n"
            f"Status: {conflict['resolution_status'].title()}\n"
            f"Detection Source: {conflict['detection_source']}\n\n"
            f"Involved Pieces:\n"
            f"{chr(10).join('- ' + text for text in piece_texts)}"
        )
        
        # Update details text
        self.conflict_details_text.delete("1.0", "end")
        self.conflict_details_text.insert("1.0", details)
    
    def _on_action_roll_selected(self, event):
        """Handle action roll selection in the action roll tree."""
        selection = self.action_roll_tree.selection()
        if not selection:
            return
        
        # Get selected action ID
        action_id_short = self.action_roll_tree.item(selection[0])["values"][0]
        
        # Find full action ID (since we only display the first 8 chars)
        query = """
            SELECT id
            FROM actions 
            WHERE id LIKE :prefix
        """
        
        result = self.db_manager.execute_query(query, {"prefix": f"{action_id_short}%"})
        if not result:
            return
            
        action_id = result[0]["id"]
        
        # Get action details
        query = """
            SELECT a.*, f.name as faction_name, d.name as district_name
            FROM actions a
            JOIN factions f ON a.faction_id = f.id
            JOIN districts d ON a.district_id = d.id
            WHERE a.id = :action_id
        """
        
        result = self.db_manager.execute_query(query, {"action_id": action_id})
        if not result:
            return
            
        action = dict(result[0])
        
        # Get piece details
        piece_name = "Unknown"
        piece_details = "No details available"
        
        if action["piece_type"] == "agent":
            agent = self.agent_repository.find_by_id(action["piece_id"])
            if agent:
                piece_name = agent.name
                piece_details = (
                    f"Attributes: ATN:{agent.attunement} INT:{agent.intellect} "
                    f"FIN:{agent.finesse} MIG:{agent.might} PRE:{agent.presence}\n"
                    f"Skills: INF:{agent.infiltration} PER:{agent.persuasion} "
                    f"COM:{agent.combat} STR:{agent.streetwise} SUR:{agent.survival} "
                    f"ART:{agent.artifice} ARC:{agent.arcana}"
                )
        elif action["piece_type"] == "squadron":
            squadron = self.squadron_repository.find_by_id(action["piece_id"])
            if squadron:
                piece_name = squadron.name
                piece_details = (
                    f"Mobility: {squadron.mobility}\n"
                    f"Aptitudes: COM:{squadron.combat_aptitude} UND:{squadron.underworld_aptitude} "
                    f"SOC:{squadron.social_aptitude} TEC:{squadron.technical_aptitude}\n"
                    f"LAB:{squadron.labor_aptitude} ARC:{squadron.arcane_aptitude} "
                    f"WIL:{squadron.wilderness_aptitude} MON:{squadron.monitoring_aptitude}"
                )
        
        # Get target faction name if applicable
        target_faction_name = "None"
        if action["target_faction_id"]:
            target_faction = self.faction_repository.find_by_id(action["target_faction_id"])
            target_faction_name = target_faction.name if target_faction else "Unknown"
        
        # Get roll breakdown information - reconstruct from piece stats since we don't store it in DB
        roll_breakdown = self._reconstruct_roll_breakdown(action)
        
        # Format additional DC information for influence actions
        dc_details = ""
        if action["action_type"] in ["gain_influence", "take_influence"] and action["dc"]:
            influence_manager = InfluenceManager(self.district_repository, self.faction_repository)
            
            try:
                # Get all the factors that contribute to the DC
                district = self.district_repository.find_by_id(action["district_id"])
                faction = self.faction_repository.find_by_id(action["faction_id"])
                target_faction = self.faction_repository.find_by_id(action["target_faction_id"]) if action["target_faction_id"] else None
                
                factors = []
                
                # Base DC
                factors.append("Base DC: 15")
                
                # District preference modifiers
                if district and action["action_type"] == "gain_influence":
                    pref_attr = district.preferred_attr
                    pref_skill = district.preferred_skill
                    
                    if pref_attr and action["attribute_used"] == pref_attr:
                        factors.append(f"District prefers {pref_attr}: -2")
                    elif pref_attr:
                        factors.append(f"Not using preferred attribute ({pref_attr}): +2")
                        
                    if pref_skill and action["skill_used"] == pref_skill:
                        factors.append(f"District prefers {pref_skill}: -2")
                    elif pref_skill:
                        factors.append(f"Not using preferred skill ({pref_skill}): +2")
                
                # Relationship modifiers
                if target_faction and faction:
                    relationship = faction.get_relationship(target_faction.id)
                    if relationship > 0:
                        factors.append(f"Positive relationship (+{relationship}): {-relationship}")
                    elif relationship < 0:
                        factors.append(f"Negative relationship ({relationship}): {abs(relationship)}")
                
                # District control modifiers
                if district and faction:
                    likeability = district.faction_likeability.get(faction.id, 0)
                    if likeability > 0:
                        factors.append(f"District likes faction (+{likeability}): {-likeability}")
                    elif likeability < 0:
                        factors.append(f"District dislikes faction ({likeability}): {abs(likeability)}")
                
                dc_details = "\n".join(factors)
            except Exception as e:
                logging.error(f"Error calculating DC factors: {str(e)}")
                dc_details = "Error calculating DC details"
        
        # Format roll details
        details = (
            f"Action ID: {action_id}\n"
            f"Type: {action['action_type'].replace('_', ' ').title()}\n"
            f"Piece: {action['piece_type'].title()} - {piece_name}\n"
            f"Faction: {action['faction_name']}\n"
            f"District: {action['district_name']}\n"
            f"Target Faction: {target_faction_name}\n\n"
            f"------- ROLL CALCULATION -------\n"
            f"{roll_breakdown}\n"
        )
        
        # Add DC calculation for influence actions
        if dc_details:
            details += f"\n------- DC CALCULATION -------\n{dc_details}\n"
        
        # Add piece details
        details += f"\n------- PIECE DETAILS -------\n{piece_details if 'piece_details' in locals() else 'No details available'}"
        
        # Update details text
        self.action_roll_details_text.delete("1.0", "end")
        self.action_roll_details_text.insert("1.0", details)
    
    def _reconstruct_roll_breakdown(self, action):
        """Reconstruct the roll breakdown from an action and its associated piece.
        
        Args:
            action (dict): The action data
            
        Returns:
            str: Formatted roll breakdown
        """
        # For debugging - log the action details
        logging.info(f"Reconstructing roll breakdown for action {action['id']} - {action['action_type']}")
        
        # Start with base roll estimation (we need to back-calculate this)
        base_roll = 0
        
        # Get the piece bonuses
        attribute_bonus = 0
        skill_bonus = 0
        aptitude_bonus = 0
        manual_modifier = action["manual_modifier"] or 0
        conflict_penalty = action["conflict_penalty"] or 0
        
        # Create an action manager instance to get enemy penalties
        action_manager = ActionManager(
            self.db_manager,
            self.district_repository,
            self.faction_repository,
            self.agent_repository,
            self.squadron_repository
        )
        
        # Get enemy penalty information using the new method
        try:
            # Use the new method to get enemy penalties
            enemy_penalty, penalty_breakdown = action_manager._get_enemy_penalties(action["id"])
            logging.info(f"Action {action['id']} enemy penalties: {enemy_penalty}, breakdown: {json.dumps(penalty_breakdown)}")
        except Exception as e:
            logging.error(f"Error getting enemy penalties for action {action['id']}: {str(e)}")
            logging.exception(f"Full traceback for enemy penalties error in action {action['id']}:")
            enemy_penalty = 0
            penalty_breakdown = {}
        
        if action["piece_type"] == "agent":
            agent = self.agent_repository.find_by_id(action["piece_id"])
            if agent:
                if action["attribute_used"]:
                    attribute_bonus = agent.get_attribute(action["attribute_used"])
                if action["skill_used"]:
                    skill_bonus = agent.get_skill(action["skill_used"])
        elif action["piece_type"] == "squadron":
            squadron = self.squadron_repository.find_by_id(action["piece_id"])
            if squadron and action["aptitude_used"]:
                aptitude_bonus = squadron.get_aptitude(action["aptitude_used"])
        
        # Calculate estimated base roll by subtracting all modifiers from final result
        total_modifiers = attribute_bonus + skill_bonus + aptitude_bonus + manual_modifier - conflict_penalty - enemy_penalty
        base_roll = action["roll_result"] - total_modifiers
        
        # Log the roll calculation breakdown
        logging.info(f"Roll calculation for action {action['id']}: total={action['roll_result']}, base={base_roll}, " +
                f"attribute={attribute_bonus}, skill={skill_bonus}, aptitude={aptitude_bonus}, " +
                f"manual={manual_modifier}, conflict={-conflict_penalty}, enemy={-enemy_penalty}")
        
        # Format breakdown
        lines = []
        lines.append(f"Base d20 Roll: {base_roll}")
        
        if attribute_bonus != 0:
            lines.append(f"{action['attribute_used']} Attribute: {attribute_bonus:+d}")
        
        if skill_bonus != 0:
            lines.append(f"{action['skill_used']} Skill: {skill_bonus:+d}")
        
        if aptitude_bonus != 0:
            lines.append(f"{action['aptitude_used']} Aptitude: {aptitude_bonus:+d}")
        
        if manual_modifier != 0:
            lines.append(f"Manual Modifier: {manual_modifier:+d}")
        
        if conflict_penalty != 0:
            lines.append(f"Conflict Penalty: {-conflict_penalty:+d}")
        
        # Always include the enemy penalty line, even if zero, for clarity
        lines.append(f"Enemy Penalty: {-enemy_penalty:+d}")
        
        # Add breakdown of enemy penalties if available
        if penalty_breakdown:
            for source_key, penalty_value in penalty_breakdown.items():
                parts = source_key.split('_')
                source_type = parts[0]
                source_id = '_'.join(parts[1:])
                
                source_name = "unknown"
                if source_type == "agent":
                    agent = self.agent_repository.find_by_id(source_id)
                    if agent:
                        source_name = agent.name
                elif source_type == "squadron":
                    squadron = self.squadron_repository.find_by_id(source_id)
                    if squadron:
                        source_name = squadron.name
                        
                lines.append(f"  - {source_type.title()} {source_name}: {-penalty_value:+d}")
        else:
            # If no enemy penalties, explain why
            lines.append("  (No enemy penalties applied)")
        
        # Add total
        lines.append(f"\nTotal Roll: {action['roll_result']}")
        
        # Add DC for comparison if available
        if action.get("dc") is not None:
            lines.append(f"DC: {action['dc']}")
            diff = action['roll_result'] - action['dc']
            if diff >= 0:
                lines.append(f"Result: Success by {diff}")
            else:
                lines.append(f"Result: Failure by {abs(diff)}")
        
        return "\n".join(lines)
    
    def _on_pending_conflict_selected(self, event):
        """Handle pending conflict selection in the pending conflict tree."""
        selection = self.pending_conflict_tree.selection()
        if not selection:
            self.apply_resolution_button.config(state="disabled")
            return
        
        # Get selected conflict ID
        conflict_id_short = self.pending_conflict_tree.item(selection[0])["values"][0]
        
        # Find full conflict ID (since we only display the first 8 chars)
        query = """
            SELECT id
            FROM conflicts 
            WHERE id LIKE :prefix
        """
        
        result = self.db_manager.execute_query(query, {"prefix": f"{conflict_id_short}%"})
        if not result:
            self.apply_resolution_button.config(state="disabled")
            return
            
        self.current_conflict_id = result[0]["id"]
        
        # Get conflict details
        query = """
            SELECT c.*, d.name as district_name
            FROM conflicts c
            JOIN districts d ON c.district_id = d.id
            WHERE c.id = :conflict_id
        """
        
        result = self.db_manager.execute_query(query, {"conflict_id": self.current_conflict_id})
        if not result:
            self.apply_resolution_button.config(state="disabled")
            return
            
        conflict = dict(result[0])
        
        # Get involved factions
        query = """
            SELECT cf.faction_id, cf.role, f.name as faction_name
            FROM conflict_factions cf
            JOIN factions f ON cf.faction_id = f.id
            WHERE cf.conflict_id = :conflict_id
        """
        
        factions = self.db_manager.execute_query(query, {"conflict_id": self.current_conflict_id})
        
        # Get involved pieces
        query = """
            SELECT cp.piece_id, cp.piece_type, cp.faction_id, 
                   cp.participation_type, cp.original_action_type,
                   f.name as faction_name
            FROM conflict_pieces cp
            JOIN factions f ON cp.faction_id = f.id
            WHERE cp.conflict_id = :conflict_id
        """
        
        pieces = self.db_manager.execute_query(query, {"conflict_id": self.current_conflict_id})
        
        # Store faction data for resolution
        self.conflict_factions = []
        
        # Clear and populate factions treeview
        for item in self.factions_tree.get_children():
            self.factions_tree.delete(item)
        
        for f_row in factions:
            f_data = dict(f_row)
            
            # Add to treeview
            self.factions_tree.insert(
                "", "end", values=(
                    f_data["faction_name"],
                    f_data["role"].title()
                )
            )
            
            # Add to faction data
            self.conflict_factions.append(f_data)
        
        # Format piece information
        piece_texts = []
        for piece in pieces:
            piece_data = dict(piece)
            
            # Get piece name
            piece_name = "Unknown"
            if piece_data["piece_type"] == "agent":
                agent = self.agent_repository.find_by_id(piece_data["piece_id"])
                piece_name = agent.name if agent else "Unknown"
            elif piece_data["piece_type"] == "squadron":
                squadron = self.squadron_repository.find_by_id(piece_data["piece_id"])
                piece_name = squadron.name if squadron else "Unknown"
            
            # Format piece text
            piece_texts.append(
                f"{piece_data['piece_type'].title()}: {piece_name} ({piece_data['faction_name']}, "
                f"{piece_data['participation_type']} participation)"
            )
        
        # Format conflict details
        details = (
            f"District: {conflict['district_name']}\n"
            f"Type: {conflict['conflict_type'].replace('_', ' ').title()}\n"
            f"Detection Source: {conflict['detection_source']}\n\n"
            f"Involved Pieces:\n"
            f"{chr(10).join('- ' + text for text in piece_texts)}"
        )
        
        # Update details text
        self.resolution_details_text.config(state="normal")
        self.resolution_details_text.delete("1.0", "end")
        self.resolution_details_text.insert("1.0", details)
        self.resolution_details_text.config(state="disabled")
        
        # Update faction comboboxes
        faction_names = [f["faction_name"] for f in self.conflict_factions]
        faction_ids = [f["faction_id"] for f in self.conflict_factions]
        
        self.winning_faction_combobox["values"] = faction_names
        if faction_names:
            self.winning_faction.set(faction_names[0])
        
        # Update draw factions listbox
        self.draw_factions_listbox.delete(0, "end")
        for name in faction_names:
            self.draw_factions_listbox.insert("end", name)
        
        # Store faction mapping for resolution
        self.faction_map = dict(zip(faction_names, faction_ids))
        
        # Update resolution form
        self._update_resolution_form()
        
        # Enable apply button
        self.apply_resolution_button.config(state="normal")
    
    def _update_resolution_form(self):
        """Update the resolution form based on selected resolution type."""
        resolution_type = self.resolution_type.get()
        
        if resolution_type == "win":
            self.winning_faction_frame.grid()
            self.draw_factions_frame.grid_remove()
        elif resolution_type == "draw":
            self.winning_faction_frame.grid_remove()
            self.draw_factions_frame.grid_remove()  # Hide draw factions frame since we auto-select all
        elif resolution_type == "special":
            self.winning_faction_frame.grid_remove()
            self.draw_factions_frame.grid_remove()
    
    def _apply_conflict_resolution(self):
        """Apply the conflict resolution."""
        if not hasattr(self, "current_conflict_id"):
            messagebox.showerror("Error", "No conflict selected")
            return
        
        resolution_type = self.resolution_type.get()
        resolution_notes = self.resolution_notes.get("1.0", "end-1c")
        
        # Get winning/losing/draw factions
        winning_factions = []
        losing_factions = []
        draw_factions = []
        
        if resolution_type == "win":
            winning_faction_name = self.winning_faction.get()
            if not winning_faction_name:
                messagebox.showerror("Error", "No winning faction selected")
                return
                
            if winning_faction_name not in self.faction_map:
                messagebox.showerror("Error", "Invalid winning faction")
                return
                
            winning_faction_id = self.faction_map[winning_faction_name]
            winning_factions = [winning_faction_id]
            
            # All other factions are losers
            for faction in self.conflict_factions:
                if faction["faction_id"] != winning_faction_id:
                    losing_factions.append(faction["faction_id"])
        
        elif resolution_type == "draw":
            # Automatic selection of all factions for draw
            for faction in self.conflict_factions:
                draw_factions.append(faction["faction_id"])
        
        elif resolution_type == "special":
            # All factions are in a draw for special rulings
            for faction in self.conflict_factions:
                draw_factions.append(faction["faction_id"])
        
        # Apply resolution
        try:
            result = self.action_manager.resolve_conflict(
                self.current_conflict_id, 
                resolution_type, 
                winning_factions, 
                losing_factions, 
                draw_factions, 
                resolution_notes
            )
            
            if result:
                messagebox.showinfo("Success", "Conflict resolution applied successfully")
                
                # Refresh conflict list
                self._load_pending_conflicts()
                
                # Check if all conflicts resolved
                if self._check_conflicts_resolved():
                    self.process_turn_part2_button.config(state="normal")
                    messagebox.showinfo(
                        "All Conflicts Resolved", 
                        "All conflicts have been resolved. You can now proceed to Part 2 of turn processing."
                    )
                
                # Clear form
                self.resolution_notes.delete("1.0", "end")
                self.resolution_details_text.config(state="normal")
                self.resolution_details_text.delete("1.0", "end")
                self.resolution_details_text.config(state="disabled")
                
                for item in self.factions_tree.get_children():
                    self.factions_tree.delete(item)
                
                self.apply_resolution_button.config(state="disabled")
                
                # Log resolution
                self._log_message(f"Resolved conflict {self.current_conflict_id[:8]} with {resolution_type} outcome")
            else:
                messagebox.showerror("Error", "Failed to apply conflict resolution")
        except Exception as e:
            messagebox.showerror("Error", f"Error applying conflict resolution: {str(e)}")
    
    def _check_conflicts_resolved(self):
        """Check if all conflicts have been resolved.
        
        Returns:
            bool: True if all conflicts resolved, False otherwise.
        """
        turn_number = self.turn_info['current_turn']
        
        # Check for pending conflicts
        query = """
            SELECT COUNT(*) as pending_count
            FROM conflicts
            WHERE turn_number = :turn_number
            AND resolution_status = 'pending'
        """
        
        result = self.db_manager.execute_query(query, {"turn_number": turn_number})
        
        if result and result[0]["pending_count"] == 0:
            return True
        
        return False
    
    def _process_queue(self):
        """Process items in the queue."""
        try:
            # Check if we have items to process
            if not self.processing_queue.empty() and self.processing_active:
                # Get next item
                item = self.processing_queue.get_nowait()
                
                # Process based on type
                if item["type"] == "part1":
                    logging.info("Processing turn part 1 from queue")
                    
                    # Create a new thread for processing
                    def process_part1():
                        try:
                            # This will run in a separate thread
                            logging.info("THREADING: Starting turn part 1 processing in thread")
                            results = self.turn_resolution_manager.process_turn_part1()
                            logging.info(f"THREADING: Turn part 1 processing complete, results: {type(results)}")
                            
                            # Use after() to update UI from the main thread
                            self.after(100, lambda: self._handle_part1_results(results))
                        except Exception as e:
                            logging.error(f"THREADING: Error in turn part 1 thread: {str(e)}")
                            # Use after() to update UI from the main thread
                            self.after(100, lambda: self._handle_processing_error("part1", str(e)))
                    
                    # Execute the turn processing directly in the main thread
                    # This avoids the SQLite threading issues
                    try:
                        logging.info("THREADING: Executing turn part 1 directly in main thread")
                        results = self.turn_resolution_manager.process_turn_part1()
                        logging.info(f"THREADING: Direct execution complete, results: {type(results)}")
                        self.after(100, lambda: self._handle_part1_results(results))
                    except Exception as e:
                        logging.error(f"THREADING: Error in direct execution: {str(e)}")
                        self.after(100, lambda: self._handle_processing_error("part1", str(e)))
                
                elif item["type"] == "part2":
                    logging.info("Processing turn part 2 from queue")
                    
                    # Execute directly in the main thread
                    try:
                        logging.info("THREADING: Executing turn part 2 directly in main thread")
                        results = self.turn_resolution_manager.process_turn_part2()
                        logging.info(f"THREADING: Direct execution complete, results: {type(results)}")
                        self.after(100, lambda: self._handle_part2_results(results))
                    except Exception as e:
                        logging.error(f"THREADING: Error in direct execution: {str(e)}")
                        self.after(100, lambda: self._handle_processing_error("part2", str(e)))
                
                # Mark item as done
                self.processing_queue.task_done()
            
            # Schedule next check
            self.after(100, self._process_queue)
        except queue.Empty:
            # No items to process, just reschedule
            self.after(100, self._process_queue)
        except Exception as e:
            logging.error(f"Error in queue processor: {str(e)}")
            self.after(100, self._process_queue)
    
    def _handle_part2_results(self, results):
        """Handle the results from turn part 2 processing.
        
        Args:
            results (dict): Results of part 2 processing.
        """
        # Check for errors
        if "error" in results:
            messagebox.showerror("Error", f"Error processing turn part 2: {results['error']}")
            self.status_label.config(text="Status: Error")
            self.stop_button.config(state="disabled")
            self.process_turn_part2_button.config(state="normal")
            return
        
        # Check for conflicts not resolved
        if results.get("status") == "conflicts_pending":
            messagebox.showerror("Error", "Not all conflicts have been resolved")
            self.status_label.config(text="Status: Conflicts Pending")
            self.stop_button.config(state="disabled")
            self.process_turn_part2_button.config(state="normal")
            return
        
        # Log results
        self._log_message(f"Turn {results['turn_number']} part 2 processing complete")
        
        # Display action results
        self._display_action_results(results.get('action_results', {}))
        
        # Update progress and status
        self.progress_var.set(100)
        self.status_label.config(text="Status: Turn Complete")
        self.stop_button.config(state="disabled")
        
        # After completing turn, advance to next turn and reset to preparation phase
        try:
            # This will advance to the next turn and set the phase to preparation
            self.turn_manager.advance_turn()
            self._log_message(f"Advanced to next turn")
            
            # Update UI state - this will enable Process Turn Part 1 button 
            self._update_ui_state()
            
            # Enable Process Turn Part 1 explicitly to ensure it's available
            self.process_turn_part1_button.config(state="normal")
            self.process_turn_part2_button.config(state="disabled")
        except Exception as e:
            logging.error(f"Error advancing turn: {str(e)}")
            self._log_message(f"Error advancing turn: {str(e)}")

        # Check for map results
        if "map_results" in results:
            map_results = results["map_results"]
            
            # Log map generation results
            if "generated_maps" in map_results:
                num_maps = len(map_results["generated_maps"])
                self._log_message(f"Generated {num_maps} faction maps")
                
                # Add information about maps to the results message
                map_info = "Generated maps for each faction. "
                if "dm_map" in map_results:
                    map_info += "Created DM master map."
                
                self._log_message(map_info)
                
                # Switch to the map update tab
                self.phase_notebook.select(self.map_update_frame)
                
                # Refresh map list
                self._refresh_map_list()
            
            # Log any errors
            if "errors" in map_results and map_results["errors"]:
                for error in map_results["errors"]:
                    self._log_message(f"Map error: {error}")
            
        # Show results summary
        next_turn = results['turn_number'] + 1
        summary = (
            f"Turn {results['turn_number']} Processing Complete\n\n"
            f"Actions Resolved: {results['action_results'].get('processed_actions', 0)}\n"
            f"Monitoring Reports Generated\n"
            f"Random Walk Updates Applied\n"
            f"Rumor DCs Decreased\n\n"
            f"Turn {next_turn} is ready to begin."
        )
        
        messagebox.showinfo("Processing Complete", summary)
    
    def _display_action_results(self, action_results):
        """Display action results in the action resolution tab.
        
        Args:
            action_results (dict): Action resolution results.
        """
        # Clear existing data
        for item in self.action_result_tree.get_children():
            self.action_result_tree.delete(item)
        
        # Clear influence tree
        for item in self.influence_tree.get_children():
            self.influence_tree.delete(item)
        
        # Clear details text
        if hasattr(self, 'action_details_text'):
            self.action_details_text.delete("1.0", "end")
        
        # Check if results exist
        if not action_results or "results" not in action_results:
            return
        
        # Debug logging
        logging.info(f"DEBUG - Received action_results: {len(action_results.get('results', []))} results")
        
        # Get results
        results = action_results.get("results", [])
        
        # Log sample for debugging
        if results:
            sample = results[0]
            logging.info(f"DEBUG - Sample result keys: {list(sample.keys())}")
            if "action_description" in sample:
                logging.info(f"DEBUG - Sample action_description: '{sample['action_description']}'")
            else:
                logging.info("DEBUG - action_description NOT FOUND in result")
        
        # Store all results for filtering
        self._all_action_results = []
        
        # Gather faction names for the filter dropdown
        all_factions = set(["All Factions"])
        
        # Add results to treeview
        for result in results:
            # Get faction name
            faction = self.faction_repository.find_by_id(result["faction_id"])
            faction_name = faction.name if faction else "Unknown"
            all_factions.add(faction_name)
            
            # Get district name
            district = self.district_repository.find_by_id(result["district_id"])
            district_name = district.name if district else "Unknown"
            
            # Get piece name
            piece_name = "Unknown"
            if result["piece_type"] == "agent":
                agent = self.agent_repository.find_by_id(result["piece_id"])
                piece_name = agent.name if agent else "Unknown"
            elif result["piece_type"] == "squadron":
                squadron = self.squadron_repository.find_by_id(result["piece_id"])
                piece_name = squadron.name if squadron else "Unknown"
            
            # Format action type
            action_type = result["action_type"].replace("_", " ").title()
            
            # Store complete result for filtering
            self._all_action_results.append({
                "action_id": result["action_id"],
                "faction_id": result["faction_id"],
                "piece_id": result["piece_id"],
                "piece_type": result["piece_type"],
                "district_id": result["district_id"],
                "action_type": result["action_type"],
                "result": result["result"],
                "action_description": result.get("action_description", None)
            })
            
            # Add to treeview
            self.action_result_tree.insert(
                "", "end", values=(
                    result["action_id"][:8],
                    faction_name,
                    f"{result['piece_type'].title()}: {piece_name}",
                    district_name,
                    action_type,
                    result["result"]
                )
            )
        
        # Update faction filter dropdown
        faction_list = sorted(list(all_factions))
        if hasattr(self, 'faction_filter_combo'):
            self.faction_filter_combo['values'] = faction_list
            self.faction_filter_var.set("All Factions")
        
        # Display influence changes
        influence_changes = action_results.get("influence_changes", [])
        
        for change in influence_changes:
            # Get district name
            district = self.district_repository.find_by_id(change["district_id"])
            district_name = district.name if district else "Unknown"
            
            # Get faction name
            faction = self.faction_repository.find_by_id(change["faction_id"])
            faction_name = faction.name if faction else "Unknown"
            
            # Format change
            change_text = f"+{change['change']}" if change['change'] > 0 else str(change['change'])
            
            # Add to treeview
            self.influence_tree.insert(
                "", "end", values=(
                    district_name,
                    faction_name,
                    change_text,
                    change["new_value"]
                )
            )
    
    def _process_turn_part1(self):
        """Process turn part 1."""
        # Confirm action
        if not messagebox.askyesno("Confirm", "Process turn part 1?"):
            return
        
        # Check for action assignments first
        turn_number = self.turn_info['current_turn']
        logging.info(f"DEBUGGING ACTIONS: Checking actions for turn {turn_number}")
        
        try:
            # Check the database directly for assigned actions
            query = """
                SELECT COUNT(*) as action_count FROM actions
                WHERE turn_number = :turn_number
            """
            result = self.db_manager.execute_query(query, {"turn_number": turn_number})
            action_count = result[0]["action_count"] if result else 0
            
            logging.info(f"DEBUGGING ACTIONS: Found {action_count} actions in database for turn {turn_number}")
            
            if action_count > 0:
                # Get details of some actions for debugging
                detail_query = """
                    SELECT id, piece_id, piece_type, faction_id, district_id, 
                           action_type, target_faction_id, in_conflict
                    FROM actions
                    WHERE turn_number = :turn_number
                    LIMIT 5
                """
                detail_result = self.db_manager.execute_query(detail_query, {"turn_number": turn_number})
                for idx, action in enumerate(detail_result):
                    logging.info(f"DEBUGGING ACTIONS: Sample action {idx+1}: {json.dumps(dict(action))}")
        except Exception as e:
            logging.error(f"DEBUGGING ACTIONS: Error checking actions: {str(e)}")
        
        # Update status
        self.status_label.config(text="Status: Processing Part 1...")
        self.progress_var.set(0)
        self.stop_button.config(state="normal")
        self.process_turn_part1_button.config(state="disabled")
        
        # Clear results text
        self.results_text.delete("1.0", "end")
        
        # Log start
        self._log_message("Starting turn part 1 processing...")
        
        # Add to processing queue
        self.processing_active = True
        self.processing_queue.put({"type": "part1"})
    
    def _process_turn_part2(self):
        """Process turn part 2."""
        # Confirm action
        if not messagebox.askyesno("Confirm", "Process turn part 2?"):
            return
        
        # Update status
        self.status_label.config(text="Status: Processing Part 2...")
        self.progress_var.set(0)
        self.stop_button.config(state="normal")
        self.process_turn_part2_button.config(state="disabled")
        
        # Clear results text
        self.results_text.delete("1.0", "end")
        
        # Log start
        self._log_message("Starting turn part 2 processing...")
        
        # Add to processing queue
        self.processing_active = True
        self.processing_queue.put({"type": "part2"})
    
    def _stop_processing(self):
        """Stop the current processing."""
        self.processing_active = False
        self.status_label.config(text="Status: Stopping...")
        self._log_message("Processing stop requested. Please wait...")
        
        def check_queue():
            if not self.processing_queue.empty():
                # Still has items, check again later
                self.after(100, check_queue)
            else:
                # Queue is empty, update UI
                self.status_label.config(text="Status: Stopped")
                self.stop_button.config(state="disabled")
                self.process_turn_part1_button.config(state="normal")
                self.process_turn_part2_button.config(state="normal")
                self._log_message("Processing stopped")
        
        # Start checking
        self.after(100, check_queue)
    
    def _log_message(self, message):
        """Log a message to the results text.
        
        Args:
            message (str): Message to log.
        """
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format message
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to text widget
        self.results_text.insert("end", formatted_message)
        
        # Scroll to end
        self.results_text.see("end")

    def _handle_processing_error(self, part_type, error_message):
        """Handle processing errors.
        
        Args:
            part_type (str): The part that had an error (part1 or part2)
            error_message (str): The error message
        """
        messagebox.showerror("Error", f"Error processing turn {part_type}: {error_message}")
        self.status_label.config(text="Status: Error")
        self.stop_button.config(state="disabled")
        
        if part_type == "part1":
            self.process_turn_part1_button.config(state="normal")
        else:
            self.process_turn_part2_button.config(state="normal")
        
        self._log_message(f"Error in turn processing: {error_message}")
    
    # Create a new method for the map update UI
    def _create_map_update_ui(self):
        """Create the map update UI."""
        map_update_frame = ttk.Frame(self.map_update_frame)
        map_update_frame.pack(fill="both", expand=True)
        
        # Split into two sections - top for controls, bottom for image display
        map_update_frame.rowconfigure(0, weight=0)  # Controls section
        map_update_frame.rowconfigure(1, weight=1)  # Image section
        map_update_frame.columnconfigure(0, weight=1)
        
        # Controls section
        controls_frame = ttk.Frame(map_update_frame)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Label(controls_frame, text="Map Selection:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Map selector dropdown
        self.map_selection = tk.StringVar()
        self.map_selector = ttk.Combobox(controls_frame, textvariable=self.map_selection, state="readonly")
        self.map_selector.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.map_selector.bind("<<ComboboxSelected>>", self._on_map_selected)
        
        # Refresh button
        ttk.Button(controls_frame, text="Refresh Maps", command=self._refresh_map_list).grid(
            row=0, column=2, padx=5, pady=5
        )
        
        # Open in viewer button
        ttk.Button(controls_frame, text="Open in External Viewer", command=self._open_map_external).grid(
            row=0, column=3, padx=5, pady=5
        )
        
        # Image display section
        image_frame = ttk.LabelFrame(map_update_frame, text="Map View")
        image_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create a canvas for the image
        self.map_canvas = tk.Canvas(image_frame, bg="white")
        self.map_canvas.pack(fill="both", expand=True)
        
        # Message when no map is selected
        self.map_message = ttk.Label(
            self.map_canvas, 
            text="Select a map from the dropdown above to view it.\n\nMaps are generated automatically at the end of each turn.",
            anchor="center",
            justify="center"
        )
        self.map_canvas.create_window(
            400, 300, 
            window=self.map_message
        )
        
        # Initialize with empty map list
        self.map_selector["values"] = ["No maps available"]
        self.map_selection.set("No maps available")
        
        # Store the current image
        self.current_map_image = None
        self.current_map_photo = None

    # Add method to handle map selection
    def _on_map_selected(self, event):
        """Handle map selection."""
        selected_map = self.map_selection.get()
        
        # Check if a valid map is selected
        if selected_map == "No maps available":
            return
        
        # Get map path
        map_path = self.map_paths.get(selected_map)
        if not map_path or not os.path.exists(map_path):
            messagebox.showerror("Error", f"Map file not found: {map_path}")
            return
        
        try:
            # Load the image
            self.current_map_image = Image.open(map_path)
            
            # Resize to fit canvas
            self._display_map_image()
        except Exception as e:
            messagebox.showerror("Error", f"Error loading map: {str(e)}")

    # Add method to refresh map list
    def _refresh_map_list(self):
        """Refresh the list of available maps."""
        try:
            # Get current turn
            turn_info = self.turn_manager.get_current_turn()
            turn_number = turn_info["current_turn"]
            
            # Check for maps directory
            maps_dir = os.path.join(os.getcwd(), "maps")
            if not os.path.exists(maps_dir):
                self.map_selector["values"] = ["No maps available"]
                self.map_selection.set("No maps available")
                return
            
            # Check for current turn directory
            turn_dir = os.path.join(maps_dir, f"turn_{turn_number}")
            if not os.path.exists(turn_dir):
                # Check for previous turn
                prev_turn_dir = os.path.join(maps_dir, f"turn_{turn_number-1}")
                if os.path.exists(prev_turn_dir):
                    turn_dir = prev_turn_dir
                else:
                    self.map_selector["values"] = ["No maps available"]
                    self.map_selection.set("No maps available")
                    return
            
            # Get map files
            map_files = [f for f in os.listdir(turn_dir) if f.endswith('.png')]
            
            if not map_files:
                self.map_selector["values"] = ["No maps available"]
                self.map_selection.set("No maps available")
                return
            
            # Format display names and store paths
            display_names = []
            self.map_paths = {}
            
            for map_file in map_files:
                # Parse name for display
                if map_file.startswith("DM_map"):
                    display_name = "DM View"
                else:
                    # Extract faction name
                    parts = map_file.split('_map_')
                    if len(parts) > 1:
                        faction_name = parts[0].replace('_', ' ')
                        display_name = f"{faction_name}'s View"
                    else:
                        display_name = map_file
                
                display_names.append(display_name)
                self.map_paths[display_name] = os.path.join(turn_dir, map_file)
            
            # Sort with DM first
            display_names.sort(key=lambda x: (0 if x == "DM View" else 1, x))
            
            # Update combobox
            self.map_selector["values"] = display_names
            if display_names:
                self.map_selection.set(display_names[0])
                self._on_map_selected(None)
        except Exception as e:
            logging.error(f"Error refreshing map list: {str(e)}")
            messagebox.showerror("Error", f"Error refreshing map list: {str(e)}")

    # Add method to display the map image
    def _display_map_image(self):
        """Display the current map image."""
        if not self.current_map_image:
            return
        
        # Clear canvas
        self.map_canvas.delete("all")
        
        # Get canvas size
        canvas_width = self.map_canvas.winfo_width()
        canvas_height = self.map_canvas.winfo_height()
        
        # If canvas doesn't have a size yet, use a reasonable default
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600
        
        # Calculate scaling factor to fit image to canvas
        img_width, img_height = self.current_map_image.size
        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height
        scale = min(scale_w, scale_h)
        
        # Resize image
        if scale < 1:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            resized_img = self.current_map_image.resize((new_width, new_height), Image.LANCZOS)
        else:
            resized_img = self.current_map_image
        
        # Convert to PhotoImage
        self.current_map_photo = ImageTk.PhotoImage(resized_img)
        
        # Display on canvas
        self.map_canvas.create_image(
            canvas_width/2, canvas_height/2,
            image=self.current_map_photo,
            anchor="center"
        )

    # Add method to handle canvas resize
    def _on_map_canvas_resize(self, event):
        """Handle map canvas resize."""
        if self.current_map_image:
            self._display_map_image()

    # Add method to open map in external viewer
    def _open_map_external(self):
        """Open the selected map in an external viewer."""
        selected_map = self.map_selection.get()
        
        # Check if a valid map is selected
        if selected_map == "No maps available":
            return
        
        # Get map path
        map_path = self.map_paths.get(selected_map)
        if not map_path or not os.path.exists(map_path):
            messagebox.showerror("Error", f"Map file not found: {map_path}")
            return
        
        # Open with system default viewer
        try:
            import platform
            import subprocess
            
            if platform.system() == 'Windows':
                os.startfile(map_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', map_path])
            else:  # Linux
                subprocess.call(['xdg-open', map_path])
        except Exception as e:
            messagebox.showerror("Error", f"Error opening map: {str(e)}")

    def _on_penalty_selected(self, event):
        """Handle enemy penalty selection in the penalty tree."""
        selection = self.enemy_penalty_tree.selection()
        if not selection:
            return
        
        # Get selected penalty action ID
        action_id_short = self.enemy_penalty_tree.item(selection[0])["values"][0]
        
        # Find full action ID (since we only display the first 8 chars)
        query = """
            SELECT id
            FROM actions 
            WHERE id LIKE :prefix
        """
        
        result = self.db_manager.execute_query(query, {"prefix": f"{action_id_short}%"})
        if not result:
            return
            
        action_id = result[0]["id"]
        
        # Get penalty details
        query = """
            SELECT ep.total_penalty, ep.penalty_breakdown,
                a.piece_id, a.piece_type, a.faction_id, a.district_id
            FROM enemy_penalties ep
            JOIN actions a ON ep.action_id = a.id
            WHERE ep.action_id = :action_id
        """
        
        result = self.db_manager.execute_query(query, {"action_id": action_id})
        if not result:
            return
            
        penalty_data = dict(result[0])
        
        # Parse penalty breakdown
        try:
            breakdown = json.loads(penalty_data["penalty_breakdown"])
        except:
            breakdown = {}
        
        # Get piece details
        piece_name = "Unknown"
        piece_details = ""
        
        if penalty_data["piece_type"] == "agent":
            agent = self.agent_repository.find_by_id(penalty_data["piece_id"])
            if agent:
                piece_name = agent.name
                piece_details = f"Agent: {agent.name}"
        elif penalty_data["piece_type"] == "squadron":
            squadron = self.squadron_repository.find_by_id(penalty_data["piece_id"])
            if squadron:
                piece_name = squadron.name
                piece_details = f"Squadron: {squadron.name}"
        
        # Get faction name
        faction = self.faction_repository.find_by_id(penalty_data["faction_id"])
        faction_name = faction.name if faction else "Unknown"
        
        # Get district name
        district = self.district_repository.find_by_id(penalty_data["district_id"])
        district_name = district.name if district else "Unknown"
        
        # Format penalty sources
        source_details = []
        for source_key, penalty_value in breakdown.items():
            parts = source_key.split('_')
            source_type = parts[0]
            source_id = '_'.join(parts[1:])
            
            source_name = "Unknown"
            if source_type == "agent":
                agent = self.agent_repository.find_by_id(source_id)
                source_name = agent.name if agent else "Unknown Agent"
            elif source_type == "squadron":
                squadron = self.squadron_repository.find_by_id(source_id)
                source_name = squadron.name if squadron else "Unknown Squadron"
            
            # Get source faction
            if source_type == "agent":
                agent = self.agent_repository.find_by_id(source_id)
                source_faction_id = agent.faction_id if agent else None
            else:
                squadron = self.squadron_repository.find_by_id(source_id)
                source_faction_id = squadron.faction_id if squadron else None
                
            source_faction = self.faction_repository.find_by_id(source_faction_id) if source_faction_id else None
            source_faction_name = source_faction.name if source_faction else "Unknown"
            
            # Add relationship info between factions
            relationship = "Unknown"
            if faction and source_faction:
                rel_value = faction.get_relationship(source_faction_id)
                if rel_value == -2:
                    relationship = "Hot War (-2)"
                elif rel_value == -1:
                    relationship = "Cold War (-1)"
                else:
                    relationship = f"Relationship: {rel_value}"
            
            source_details.append(f"{source_type.title()} {source_name} ({source_faction_name}): -{penalty_value} ({relationship})")
        
        # Format details
        details = (
            f"Action ID: {action_id}\n"
            f"Piece: {piece_details}\n"
            f"Faction: {faction_name}\n"
            f"District: {district_name}\n"
            f"Total Penalty: -{penalty_data['total_penalty']}\n\n"
            f"Penalty Sources:\n"
            f"{chr(10).join('- ' + source for source in source_details)}"
        )
        
        # Update details text
        self.penalty_details_text.delete("1.0", "end")
        self.penalty_details_text.insert("1.0", details)

    def _reset_turn_processing(self):
        """Reset the turn processing to the beginning."""
        # Show confirmation dialog
        if not messagebox.askyesno("Confirm Reset", "This will reset the turn processing to the beginning. Any progress in the current turn will be lost. Continue?"):
            return
        
        try:
            # Get current turn information
            turn_info = self.turn_manager.get_current_turn()
            turn_number = turn_info["current_turn"]
            
            # Log the reset action
            self._log_message(f"Resetting turn {turn_number} processing to the beginning")
            
            # Stop any ongoing processing
            self.processing_active = False
            
            # Wait for queue to clear
            while not self.processing_queue.empty():
                try:
                    self.processing_queue.get_nowait()
                    self.processing_queue.task_done()
                except:
                    pass
            
            # Reset the turn phase to preparation
            self.turn_manager.set_current_phase("preparation")
            
            # Reset the action manager's penalty tracker
            self.action_manager.reset_penalty_tracker()
            
            # Clear any temporary state
            if hasattr(self, 'current_results'):
                delattr(self, 'current_results')
            
            # Reset progress indicators
            self.progress_var.set(0)
            self.status_label.config(text="Status: Reset Complete")
            
            # Reset button states
            self.process_turn_part1_button.config(state="normal")
            self.process_turn_part2_button.config(state="disabled")
            self.stop_button.config(state="disabled")
            
            # Delete conflicts that may be in progress
            with self.db_manager.connection:
                # Check if there are any pending conflicts for this turn
                check_query = """
                    SELECT COUNT(*) as conflict_count 
                    FROM conflicts 
                    WHERE turn_number = :turn_number AND resolution_status = 'pending'
                """
                result = self.db_manager.execute_query(check_query, {"turn_number": turn_number})
                
                if result and result[0]['conflict_count'] > 0:
                    # Delete conflict factions
                    self.db_manager.execute_update("""
                        DELETE FROM conflict_factions 
                        WHERE conflict_id IN (
                            SELECT id FROM conflicts 
                            WHERE turn_number = :turn_number AND resolution_status = 'pending'
                        )
                    """, {"turn_number": turn_number})
                    
                    # Delete conflict pieces
                    self.db_manager.execute_update("""
                        DELETE FROM conflict_pieces 
                        WHERE conflict_id IN (
                            SELECT id FROM conflicts 
                            WHERE turn_number = :turn_number AND resolution_status = 'pending'
                        )
                    """, {"turn_number": turn_number})
                    
                    # Delete conflicts
                    self.db_manager.execute_update("""
                        DELETE FROM conflicts 
                        WHERE turn_number = :turn_number AND resolution_status = 'pending'
                    """, {"turn_number": turn_number})
                    
                    self._log_message(f"Deleted pending conflicts for turn {turn_number}")
            
            # Reset action roll results to null
            with self.db_manager.connection:
                # Check if there are actions with roll results
                check_query = """
                    SELECT COUNT(*) as action_count 
                    FROM actions 
                    WHERE turn_number = :turn_number AND roll_result IS NOT NULL
                """
                result = self.db_manager.execute_query(check_query, {"turn_number": turn_number})
                
                if result and result[0]['action_count'] > 0:
                    self.db_manager.execute_update("""
                        UPDATE actions 
                        SET roll_result = NULL, 
                            outcome_tier = NULL, 
                            conflict_penalty = NULL,
                            in_conflict = 0,
                            conflict_id = NULL,
                            updated_at = :now
                        WHERE turn_number = :turn_number
                    """, {"turn_number": turn_number, "now": datetime.now().isoformat()})
                    
                    self._log_message(f"Reset {result[0]['action_count']} action rolls for turn {turn_number}")
            
            # Clear any enemy penalties
            with self.db_manager.connection:
                # Check if enemy_penalties table exists
                check_table_query = """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='enemy_penalties'
                """
                table_exists = self.db_manager.execute_query(check_table_query)
                
                if table_exists:
                    # Check if there are enemy penalties for this turn
                    check_query = """
                        SELECT COUNT(*) as penalty_count 
                        FROM enemy_penalties 
                        WHERE turn_number = :turn_number
                    """
                    result = self.db_manager.execute_query(check_query, {"turn_number": turn_number})
                    
                    if result and result[0]['penalty_count'] > 0:
                        self.db_manager.execute_update("""
                            DELETE FROM enemy_penalties 
                            WHERE turn_number = :turn_number
                        """, {"turn_number": turn_number})
                        
                        self._log_message(f"Deleted enemy penalties for turn {turn_number}")
            
            # Clear decay results if they exist
            with self.db_manager.connection:
                # Check if decay_results table exists
                check_table_query = """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='decay_results'
                """
                table_exists = self.db_manager.execute_query(check_table_query)
                
                if table_exists:
                    # Check if there are decay results for this turn
                    check_query = """
                        SELECT COUNT(*) as decay_count 
                        FROM decay_results 
                        WHERE turn_number = :turn_number
                    """
                    result = self.db_manager.execute_query(check_query, {"turn_number": turn_number})
                    
                    if result and result[0]['decay_count'] > 0:
                        # Store the current decay results for potential restoration
                        decay_query = """
                            SELECT district_id, faction_id, influence_change
                            FROM decay_results
                            WHERE turn_number = :turn_number
                        """
                        decay_records = self.db_manager.execute_query(decay_query, {"turn_number": turn_number})
                        
                        # Restore influence for each decay record
                        for record in decay_records:
                            district = self.district_repository.find_by_id(record['district_id'])
                            if district:
                                # Get current influence
                                current_influence = district.get_faction_influence(record['faction_id'])
                                # Restore the decayed influence (negate the influence_change which is negative)
                                district.set_faction_influence(record['faction_id'], current_influence - record['influence_change'])
                                # Save district
                                self.district_repository.update(district)
                        
                        # Delete the decay records
                        self.db_manager.execute_update("""
                            DELETE FROM decay_results 
                            WHERE turn_number = :turn_number
                        """, {"turn_number": turn_number})
                        
                        self._log_message(f"Reverted influence decay for turn {turn_number} and deleted decay records")
            
            # Clear treeviews
            for item in self.decay_tree.get_children():
                self.decay_tree.delete(item)
            
            for item in self.action_roll_tree.get_children():
                self.action_roll_tree.delete(item)
            
            for item in self.enemy_penalty_tree.get_children():
                self.enemy_penalty_tree.delete(item)
            
            # Update UI to show current state
            self._update_ui_state()
            
            # Notify user
            messagebox.showinfo("Reset Complete", f"Turn {turn_number} processing has been reset to the beginning.")
        except Exception as e:
            logging.error(f"Error in _reset_turn_processing: {str(e)}")
            messagebox.showerror("Error", f"Error resetting turn processing: {str(e)}")

    def _on_action_result_selected(self, event):
        """Handle action selection in the action results tree."""
        selection = self.action_result_tree.selection()
        if not selection:
            return
        
        # Get selected action ID
        action_id_short = self.action_result_tree.item(selection[0])["values"][0]
        
        # Find full action ID (since we only display the first 8 chars)
        query = """
            SELECT id
            FROM actions 
            WHERE id LIKE :prefix
        """
        
        result = self.db_manager.execute_query(query, {"prefix": f"{action_id_short}%"})
        if not result:
            return
            
        action_id = result[0]["id"]
        
        # Get action details
        query = """
            SELECT a.*, f.name as faction_name, d.name as district_name,
                   a.action_description
            FROM actions a
            JOIN factions f ON a.faction_id = f.id
            JOIN districts d ON a.district_id = d.id
            WHERE a.id = :action_id
        """
        
        result = self.db_manager.execute_query(query, {"action_id": action_id})
        if not result:
            return
            
        action = dict(result[0])
        
        # Debug logging to help troubleshoot
        logging.info(f"DEBUG - Action details for ID {action_id}: action_type={action['action_type']}")
        logging.info(f"DEBUG - Action description value: '{action.get('action_description')}'")
        
        # Get piece details
        piece_name = "Unknown"
        piece_details = "No details available"
        
        if action["piece_type"] == "agent":
            agent = self.agent_repository.find_by_id(action["piece_id"])
            if agent:
                piece_name = agent.name
                piece_details = (
                    f"Attributes: ATN:{agent.attunement} INT:{agent.intellect} "
                    f"FIN:{agent.finesse} MIG:{agent.might} PRE:{agent.presence}\n"
                    f"Skills: INF:{agent.infiltration} PER:{agent.persuasion} "
                    f"COM:{agent.combat} STR:{agent.streetwise} SUR:{agent.survival} "
                    f"ART:{agent.artifice} ARC:{agent.arcana}"
                )
        elif action["piece_type"] == "squadron":
            squadron = self.squadron_repository.find_by_id(action["piece_id"])
            if squadron:
                piece_name = squadron.name
                piece_details = (
                    f"Mobility: {squadron.mobility}\n"
                    f"Aptitudes: COM:{squadron.combat_aptitude} UND:{squadron.underworld_aptitude} "
                    f"SOC:{squadron.social_aptitude} TEC:{squadron.technical_aptitude}\n"
                    f"LAB:{squadron.labor_aptitude} ARC:{squadron.arcane_aptitude} "
                    f"WIL:{squadron.wilderness_aptitude} MON:{squadron.monitoring_aptitude}"
                )
        
        # Get target faction name if applicable
        target_faction_name = "None"
        if action["target_faction_id"]:
            target_faction = self.faction_repository.find_by_id(action["target_faction_id"])
            target_faction_name = target_faction.name if target_faction else "Unknown"
        
        # Get actual roll details
        roll_value = action.get("roll_result", "N/A")
        dc = action.get("dc", "N/A")
        outcome = action.get("outcome_tier", "Unknown")
        
        # Format the action description for display
        action_description = None
        if "action_description" in action and action["action_description"]:
            action_description = action["action_description"]
        
        # Format roll details
        details = (
            f"Action ID: {action_id}\n"
            f"Type: {action['action_type'].replace('_', ' ').title()}\n"
            f"Piece: {action['piece_type'].title()} - {piece_name}\n"
            f"Faction: {action['faction_name']}\n"
            f"District: {action['district_name']}\n"
            f"Target Faction: {target_faction_name}\n\n"
        )
        
        # Always show description for all action types, especially freeform
        if action_description:
            details += f"Description: {action_description}\n\n"
        
        details += (
            f"------- RESULT DETAILS -------\n"
            f"Roll: {roll_value}\n"
            f"DC: {dc}\n"
            f"Outcome: {outcome}\n\n"
        )
        
        # Add piece details
        details += f"------- PIECE DETAILS -------\n{piece_details}"
        
        # Update details text
        self.action_details_text.delete("1.0", "end")
        self.action_details_text.insert("1.0", details)

    def _apply_faction_filter(self, event=None):
        """Filter action results by selected faction."""
        selected_faction = self.faction_filter_var.get()
        
        if not hasattr(self, '_all_action_results'):
            # If we haven't stored all results yet, nothing to filter
            return
        
        # Clear existing data
        for item in self.action_result_tree.get_children():
            self.action_result_tree.delete(item)
        
        # Apply filter
        for result in self._all_action_results:
            # Get faction name
            faction = self.faction_repository.find_by_id(result["faction_id"])
            faction_name = faction.name if faction else "Unknown"
            
            # Apply filter
            if selected_faction == "All Factions" or faction_name == selected_faction:
                # Get district name
                district = self.district_repository.find_by_id(result["district_id"])
                district_name = district.name if district else "Unknown"
                
                # Get piece name
                piece_name = "Unknown"
                if result["piece_type"] == "agent":
                    agent = self.agent_repository.find_by_id(result["piece_id"])
                    piece_name = agent.name if agent else "Unknown"
                elif result["piece_type"] == "squadron":
                    squadron = self.squadron_repository.find_by_id(result["piece_id"])
                    piece_name = squadron.name if squadron else "Unknown"
                
                # Format action type
                action_type = result["action_type"].replace("_", " ").title()
                
                # Add to treeview
                self.action_result_tree.insert(
                    "", "end", values=(
                        result["action_id"][:8],
                        faction_name,
                        f"{result['piece_type'].title()}: {piece_name}",
                        district_name,
                        action_type,
                        result["result"]
                    )
                )