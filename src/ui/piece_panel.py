import tkinter as tk
from tkinter import ttk, messagebox
import logging
import uuid
from datetime import datetime


class PiecePanel(ttk.Frame):
    """Panel for creating and managing agents and squadrons."""
    
    def __init__(self, parent, db_manager, agent_repository, squadron_repository, 
                 faction_repository, district_repository):
        """Initialize the piece panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            agent_repository: Repository for agent operations.
            squadron_repository: Repository for squadron operations.
            faction_repository: Repository for faction operations.
            district_repository: Repository for district operations.
        """
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.agent_repository = agent_repository
        self.squadron_repository = squadron_repository
        self.faction_repository = faction_repository
        self.district_repository = district_repository
        
        # Initialize UI
        self._init_ui()
        
        # Load initial data
        self._load_factions()
        self._load_districts()
        self._load_pieces()
    
    def _init_ui(self):
        """Initialize UI components."""
        # Create top controls
        self.top_frame = ttk.Frame(self)
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create piece type selector
        self.piece_type_var = tk.StringVar(value="agent")
        self.agent_radio = ttk.Radiobutton(self.top_frame, text="Agents", variable=self.piece_type_var, 
                                        value="agent", command=self._on_piece_type_changed)
        self.squadron_radio = ttk.Radiobutton(self.top_frame, text="Squadrons", variable=self.piece_type_var, 
                                           value="squadron", command=self._on_piece_type_changed)
        self.agent_radio.pack(side=tk.LEFT, padx=(0,10))
        self.squadron_radio.pack(side=tk.LEFT, padx=(0,10))
        
        # Create faction filter
        ttk.Label(self.top_frame, text="Faction:").pack(side=tk.LEFT, padx=(10,5))
        self.faction_filter_var = tk.StringVar(value="all")
        self.faction_filter = ttk.Combobox(self.top_frame, textvariable=self.faction_filter_var, state="readonly")
        self.faction_filter.pack(side=tk.LEFT, padx=(0,10))
        self.faction_filter.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Create district filter
        ttk.Label(self.top_frame, text="District:").pack(side=tk.LEFT, padx=(10,5))
        self.district_filter_var = tk.StringVar(value="all")
        self.district_filter = ttk.Combobox(self.top_frame, textvariable=self.district_filter_var, state="readonly")
        self.district_filter.pack(side=tk.LEFT, padx=(0,10))
        self.district_filter.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Create search box
        ttk.Label(self.top_frame, text="Search:").pack(side=tk.LEFT, padx=(10,5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.top_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, padx=(0,10), fill=tk.X, expand=True)
        self.search_var.trace_add("write", lambda name, index, mode: self._on_filter_changed(None))
        
        # Create buttons
        self.refresh_button = ttk.Button(self.top_frame, text="Refresh", command=self._load_pieces)
        self.refresh_button.pack(side=tk.RIGHT, padx=5)
        
        self.new_button = ttk.Button(self.top_frame, text="New", command=self._create_new_piece)
        self.new_button.pack(side=tk.RIGHT, padx=5)
        
        # Create main content area with splitter
        self.content_frame = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create piece list
        self.list_frame = ttk.Frame(self.content_frame)
        self.content_frame.add(self.list_frame, weight=1)
        
        # Create piece tree
        self._create_piece_tree()
        
        # Create detail panel
        self.detail_frame = ttk.Frame(self.content_frame)
        self.content_frame.add(self.detail_frame, weight=2)
        
        # Create notebook for detail tabs
        self.detail_notebook = ttk.Notebook(self.detail_frame)
        self.detail_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs for properties and assignment
        self.properties_frame = ttk.Frame(self.detail_notebook)
        self.assignment_frame = ttk.Frame(self.detail_notebook)
        
        self.detail_notebook.add(self.properties_frame, text="Properties")
        self.detail_notebook.add(self.assignment_frame, text="Assignment")
        
        # Create the properties form (initial empty state)
        self._create_properties_form()
        
        # Create the assignment form (initial empty state)
        self._create_assignment_form()
        
        # Detail panel buttons
        self.button_frame = ttk.Frame(self.detail_frame)
        self.button_frame.pack(fill=tk.X, pady=5)
        
        self.delete_button = ttk.Button(self.button_frame, text="Delete", command=self._delete_piece)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(self.button_frame, text="Save", command=self._save_piece)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
        # Disable detail panel buttons initially
        self._disable_detail_controls()
    
    def _create_piece_tree(self):
        """Create the piece tree view."""
        # Create tree frame
        tree_frame = ttk.Frame(self.list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tree
        self.piece_tree = ttk.Treeview(tree_frame, columns=("name", "faction", "district", "task"), show="headings")
        self.piece_tree.heading("name", text="Name")
        self.piece_tree.heading("faction", text="Faction")
        self.piece_tree.heading("district", text="District")
        self.piece_tree.heading("task", text="Task")
        
        # Configure column widths
        self.piece_tree.column("name", width=150)
        self.piece_tree.column("faction", width=150)
        self.piece_tree.column("district", width=150)
        self.piece_tree.column("task", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.piece_tree.yview)
        self.piece_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.piece_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.piece_tree.bind("<<TreeviewSelect>>", self._on_piece_selected)
    
    def _create_properties_form(self):
        """Create the properties form for a piece."""
        # Clear any existing widgets
        for widget in self.properties_frame.winfo_children():
            widget.destroy()
        
        # Create a frame for the form
        form_frame = ttk.Frame(self.properties_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Basic properties that apply to both agents and squadrons
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(form_frame, text="Faction:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.faction_var = tk.StringVar()
        self.faction_combo = ttk.Combobox(form_frame, textvariable=self.faction_var, state="readonly")
        self.faction_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Add a row counter for dynamic content
        self.form_row = 2
        
        # Agent-specific properties
        self.agent_properties_frame = ttk.LabelFrame(form_frame, text="Agent Properties")
        self.agent_properties_frame.grid(row=self.form_row, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.form_row += 1
        
        # Attributes
        ttk.Label(self.agent_properties_frame, text="Attributes:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        attributes_frame = ttk.Frame(self.agent_properties_frame)
        attributes_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Create attribute spinboxes
        self.attribute_vars = {}
        attribute_names = ["Might", "Finesse", "Presence", "Intellect", "Attunement"]
        
        for i, attr in enumerate(attribute_names):
            ttk.Label(attributes_frame, text=f"{attr}:").grid(row=i // 3, column=(i % 3) * 2, sticky=tk.W, padx=5, pady=2)
            attr_var = tk.StringVar(value="0")
            attr_spin = ttk.Spinbox(attributes_frame, from_=0, to=5, width=3, textvariable=attr_var)
            attr_spin.grid(row=i // 3, column=(i % 3) * 2 + 1, sticky=tk.W, padx=5, pady=2)
            self.attribute_vars[attr.lower()] = attr_var
        
        # Skills
        ttk.Label(self.agent_properties_frame, text="Skills:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        skills_frame = ttk.Frame(self.agent_properties_frame)
        skills_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Create skill spinboxes
        self.skill_vars = {}
        skill_names = ["Combat", "Infiltration", "Persuasion", "Streetwise", "Survival", "Artifice", "Arcana"]
        
        for i, skill in enumerate(skill_names):
            ttk.Label(skills_frame, text=f"{skill}:").grid(row=i // 3, column=(i % 3) * 2, sticky=tk.W, padx=5, pady=2)
            skill_var = tk.StringVar(value="0")
            skill_spin = ttk.Spinbox(skills_frame, from_=0, to=5, width=3, textvariable=skill_var)
            skill_spin.grid(row=i // 3, column=(i % 3) * 2 + 1, sticky=tk.W, padx=5, pady=2)
            self.skill_vars[skill.lower()] = skill_var
        
        # Squadron-specific properties
        self.squadron_properties_frame = ttk.LabelFrame(form_frame, text="Squadron Properties")
        self.squadron_properties_frame.grid(row=self.form_row, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.form_row += 1
        
        # Squadron type
        ttk.Label(self.squadron_properties_frame, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.type_var = tk.StringVar(value="general")
        self.type_combo = ttk.Combobox(self.squadron_properties_frame, textvariable=self.type_var, state="readonly")
        self.type_combo['values'] = ["general", "combat", "social", "technical", "arcane", "labor", "wilderness", "underworld"]
        self.type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Mobility
        ttk.Label(self.squadron_properties_frame, text="Mobility:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.mobility_var = tk.StringVar(value="0")
        self.mobility_spin = ttk.Spinbox(self.squadron_properties_frame, from_=0, to=5, width=3, textvariable=self.mobility_var)
        self.mobility_spin.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Aptitudes
        ttk.Label(self.squadron_properties_frame, text="Aptitudes:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        aptitudes_frame = ttk.Frame(self.squadron_properties_frame)
        aptitudes_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Create aptitude spinboxes
        self.aptitude_vars = {}
        aptitude_names = ["Combat", "Underworld", "Social", "Technical", "Labor", "Arcane", "Wilderness", "Monitoring"]
        
        for i, apt in enumerate(aptitude_names):
            ttk.Label(aptitudes_frame, text=f"{apt}:").grid(row=i // 2, column=(i % 2) * 2, sticky=tk.W, padx=5, pady=2)
            apt_var = tk.StringVar(value="-1")
            apt_spin = ttk.Spinbox(aptitudes_frame, from_=-3, to=5, width=3, textvariable=apt_var)
            apt_spin.grid(row=i // 2, column=(i % 2) * 2 + 1, sticky=tk.W, padx=5, pady=2)
            self.aptitude_vars[f"{apt.lower()}_aptitude"] = apt_var
        
        # Show/hide appropriate frames based on current piece type
        if self.piece_type_var.get() == "agent":
            self.agent_properties_frame.grid()
            self.squadron_properties_frame.grid_remove()
        else:
            self.agent_properties_frame.grid_remove()
            self.squadron_properties_frame.grid()
        
        # Status message at the bottom
        self.status_label = ttk.Label(form_frame, text="")
        self.status_label.grid(row=self.form_row, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.form_row += 1
    
    def _create_assignment_form(self):
        """Create the assignment form for a piece."""
        # Clear any existing widgets
        for widget in self.assignment_frame.winfo_children():
            widget.destroy()
        
        # Create a frame for the form
        form_frame = ttk.Frame(self.assignment_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # District Assignment
        ttk.Label(form_frame, text="Assign to District:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.assign_district_var = tk.StringVar()
        self.assign_district_combo = ttk.Combobox(form_frame, textvariable=self.assign_district_var, state="readonly")
        self.assign_district_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.assign_district_combo.bind("<<ComboboxSelected>>", self._on_district_changed)
        
        # Task Assignment
        ttk.Label(form_frame, text="Task:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.task_var = tk.StringVar(value="monitor")
        self.task_combo = ttk.Combobox(form_frame, textvariable=self.task_var, state="readonly")
        self.task_combo['values'] = ["monitor", "gain_influence", "take_influence", "freeform", "initiate_conflict"]
        self.task_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.task_combo.bind("<<ComboboxSelected>>", self._on_task_changed)
        
        # Target Faction (for take_influence and initiate_conflict)
        self.target_faction_label = ttk.Label(form_frame, text="Target Faction:")
        self.target_faction_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.target_faction_var = tk.StringVar()
        self.target_faction_combo = ttk.Combobox(form_frame, textvariable=self.target_faction_var, state="readonly")
        self.target_faction_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Manual modifier
        ttk.Label(form_frame, text="Manual Modifier:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.manual_modifier_var = tk.StringVar(value="0")
        self.manual_modifier_spin = ttk.Spinbox(form_frame, from_=-10, to=10, width=3, textvariable=self.manual_modifier_var)
        self.manual_modifier_spin.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Description (for freeform and initiate_conflict)
        self.description_label = ttk.Label(form_frame, text="Description:")
        self.description_label.grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(form_frame, textvariable=self.description_var)
        self.description_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # DC (for freeform and initiate_conflict)
        self.dc_label = ttk.Label(form_frame, text="DC:")
        self.dc_label.grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.dc_var = tk.StringVar(value="15")
        self.dc_spin = ttk.Spinbox(form_frame, from_=5, to=30, width=3, textvariable=self.dc_var)
        self.dc_spin.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Attribute/Skill/Aptitude selection
        # For agents
        self.agent_attr_label = ttk.Label(form_frame, text="Attribute:")
        self.agent_attr_label.grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.agent_attr_var = tk.StringVar()
        self.agent_attr_combo = ttk.Combobox(form_frame, textvariable=self.agent_attr_var, state="readonly")
        self.agent_attr_combo['values'] = ["might", "finesse", "presence", "intellect", "attunement"]
        self.agent_attr_combo.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.agent_skill_label = ttk.Label(form_frame, text="Skill:")
        self.agent_skill_label.grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
        self.agent_skill_var = tk.StringVar()
        self.agent_skill_combo = ttk.Combobox(form_frame, textvariable=self.agent_skill_var, state="readonly")
        self.agent_skill_combo['values'] = ["combat", "infiltration", "persuasion", "streetwise", "survival", "artifice", "arcana"]
        self.agent_skill_combo.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # For squadrons
        self.squadron_apt_label = ttk.Label(form_frame, text="Aptitude:")
        self.squadron_apt_label.grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.squadron_apt_var = tk.StringVar()
        self.squadron_apt_combo = ttk.Combobox(form_frame, textvariable=self.squadron_apt_var, state="readonly")
        self.squadron_apt_combo['values'] = ["combat", "underworld", "social", "technical", "labor", "arcane", "wilderness", "monitoring"]
        self.squadron_apt_combo.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Assignment buttons
        self.assign_button = ttk.Button(form_frame, text="Assign Task", command=self._assign_task)
        self.assign_button.grid(row=8, column=0, padx=5, pady=5)
        
        self.clear_button = ttk.Button(form_frame, text="Clear Assignment", command=self._clear_assignment)
        self.clear_button.grid(row=8, column=1, padx=5, pady=5)
        
        # Update form visibility based on task type
        self._update_assignment_form_visibility()
    
    def _update_assignment_form_visibility(self):
        """Update assignment form visibility based on current task and piece type."""
        # Task type determines some visibility
        task = self.task_combo.get()
        piece_type = self.piece_type_var.get()
        
        # Target faction selector (for take_influence and initiate_conflict)
        if task in ["take_influence", "initiate_conflict"]:
            self.target_faction_label.grid()
            self.target_faction_combo.grid()
        else:
            self.target_faction_label.grid_remove()
            self.target_faction_combo.grid_remove()
        
        # Description and DC (for freeform and initiate_conflict)
        if task in ["freeform", "initiate_conflict"]:
            self.description_label.grid()
            self.description_entry.grid()
            self.dc_label.grid()
            self.dc_spin.grid()
        else:
            self.description_label.grid_remove()
            self.description_entry.grid_remove()
            self.dc_label.grid_remove()
            self.dc_spin.grid_remove()
        
        # Attribute/Skill/Aptitude selection - show for all tasks
        if piece_type == "agent":
            self.agent_attr_label.grid()
            self.agent_attr_combo.grid()
            self.agent_skill_label.grid()
            self.agent_skill_combo.grid()
            
            # Hide squadron controls
            self.squadron_apt_label.grid_remove()
            self.squadron_apt_combo.grid_remove()
        else:  # piece_type == "squadron"
            self.squadron_apt_label.grid()
            self.squadron_apt_combo.grid()
            
            # Hide agent controls
            self.agent_attr_label.grid_remove()
            self.agent_attr_combo.grid_remove()
            self.agent_skill_label.grid_remove()
            self.agent_skill_combo.grid_remove()
    
    def _load_factions(self):
        """Load factions into the filter and assignment dropdowns."""
        try:
            # Get all factions
            factions = self.faction_repository.find_all()
            
            # Create faction options
            faction_values = [("all", "All Factions")]
            faction_values.extend([(f.id, f.name) for f in factions])
            
            # Set up faction filter
            self.faction_filter_var.set("all")
            self.faction_filter['values'] = [f[1] for f in faction_values]
            
            # Store mapping for lookup
            self._faction_filter_map = {f[1]: f[0] for f in faction_values}
            
            # Set up target faction selector in assignment form
            self.target_faction_combo['values'] = [f[1] for f in faction_values[1:]]  # Skip "All Factions"
            self._target_faction_map = {f[1]: f[0] for f in faction_values[1:]}
            
            # Set up faction combo in properties form (editing dropdown)
            if hasattr(self, 'faction_combo'):
                # Use only actual factions (not "All Factions")
                self.faction_combo['values'] = [f[1] for f in faction_values[1:]]
            
        except Exception as e:
            logging.error(f"Error loading factions: {str(e)}")
            messagebox.showerror("Error", "Failed to load factions")
    
    def _load_districts(self):
        """Load districts into the filter and assignment dropdowns."""
        try:
            # Get all districts
            districts = self.district_repository.find_all()
            
            # Create district options
            district_values = [("all", "All Districts"), ("none", "Unassigned")]
            district_values.extend([(d.id, d.name) for d in districts])
            
            # Set up district filter
            self.district_filter_var.set("all")
            self.district_filter['values'] = [d[1] for d in district_values]
            
            # Store mapping for lookup
            self._district_filter_map = {d[1]: d[0] for d in district_values}
            
            # Set up district selector in assignment form
            self.assign_district_combo['values'] = [d[1] for d in district_values[2:]]  # Skip "All" and "Unassigned"
            self._district_combo_map = {d[1]: d[0] for d in district_values[2:]}
            
        except Exception as e:
            logging.error(f"Error loading districts: {str(e)}")
            messagebox.showerror("Error", "Failed to load districts")
    
    def _load_pieces(self):
        """Load pieces into the tree view."""
        try:
            # Clear existing items
            for item in self.piece_tree.get_children():
                self.piece_tree.delete(item)
            
            # Get selected piece type
            piece_type = self.piece_type_var.get()
            
            # Get selected faction filter
            faction_name = self.faction_filter_var.get()
            faction_id = self._faction_filter_map.get(faction_name) if faction_name != "All" else None
            
            # Get selected district filter
            district_name = self.district_filter_var.get()
            district_id = self._district_filter_map.get(district_name) if district_name != "All" else None
            
            # Load pieces based on type
            if piece_type == "agent":
                pieces = self.agent_repository.find_all()
            else:
                pieces = self.squadron_repository.find_all()
            
            # Apply filters
            filtered_pieces = []
            for piece in pieces:
                if faction_id and piece.faction_id != faction_id:
                    continue
                if district_id and piece.district_id != district_id:
                    continue
                filtered_pieces.append(piece)
            
            # Add pieces to tree
            for piece in filtered_pieces:
                # Get faction name
                faction = self.faction_repository.find_by_id(piece.faction_id)
                faction_name = faction.name if faction else "Unknown"
                
                # Get district name
                district = self.district_repository.find_by_id(piece.district_id)
                district_name = district.name if district else "None"
                
                # Get task type
                task_type = "None"
                if piece.current_task:
                    task_type = piece.current_task.get("type", "None")
                    task_type = task_type.replace("_", " ").title()
                
                # Add to tree
                self.piece_tree.insert("", "end", piece.id, values=(
                    piece.name,
                    faction_name,
                    district_name,
                    task_type
                ))
            
            # Update status bar
            self._update_status(f"Loaded {len(filtered_pieces)} {piece_type}s")
            
        except Exception as e:
            logging.error(f"Error loading pieces: {str(e)}")
            messagebox.showerror("Error", "Failed to load pieces")
    
    def _on_piece_type_changed(self):
        """Handle piece type change."""
        # Update properties form visibility
        piece_type = self.piece_type_var.get()
        if piece_type == "agent":
            self.agent_properties_frame.grid()
            self.squadron_properties_frame.grid_remove()
        else:
            self.agent_properties_frame.grid_remove()
            self.squadron_properties_frame.grid()
        
        # Update assignment form visibility
        self._update_assignment_form_visibility()
        
        # Reload pieces
        self._load_pieces()
        
        # Clear selection and disable detail panel
        self._clear_selection()
    
    def _on_filter_changed(self, event):
        """Handle changes to any filter."""
        self._load_pieces()  # Reload with current filter values
    
    def _on_task_changed(self, event):
        """Handle task type change."""
        task_type = self.task_combo.get()
        district_name = self.assign_district_combo.get()
        
        # Set default attributes/skills based on district and task type
        if district_name:
            district_id = self._district_combo_map.get(district_name)
            if district_id:
                self._set_preferred_statistics(district_id, task_type)
                
        self._update_assignment_form_visibility()
    
    def _on_district_changed(self, event):
        """Handle district selection change."""
        district_name = self.assign_district_combo.get()
        if not district_name:
            return
            
        district_id = self._district_combo_map.get(district_name)
        if not district_id:
            return
            
        # Set preferred attributes/skills based on district and current task
        task_type = self.task_combo.get()
        self._set_preferred_statistics(district_id, task_type)
    
    def _set_preferred_statistics(self, district_id, task_type):
        """Set preferred attributes/skills/aptitudes based on district preferences and task type.
        
        Args:
            district_id (str): District ID
            task_type (str): Task type (monitor, gain_influence, etc.)
        """
        try:
            district = self.district_repository.find_by_id(district_id)
            if not district:
                return
                
            piece_type = self.piece_type_var.get()
            
            # Set appropriate attributes/skills/aptitudes based on task type
            if task_type == "monitor":
                if piece_type == "agent":
                    # Set preferred monitoring attribute/skill for agent
                    self.agent_attr_combo.set(district.preferred_monitor_attribute)
                    self.agent_skill_combo.set(district.preferred_monitor_skill)
                else:
                    # Set preferred monitoring aptitude for squadron
                    self.squadron_apt_combo.set(district.preferred_monitor_squadron_aptitude)
            elif task_type in ["gain_influence", "take_influence"]:
                if piece_type == "agent":
                    # Set preferred gain attribute/skill for agent
                    self.agent_attr_combo.set(district.preferred_gain_attribute)
                    self.agent_skill_combo.set(district.preferred_gain_skill)
                else:
                    # Set preferred gain aptitude for squadron
                    self.squadron_apt_combo.set(district.preferred_gain_squadron_aptitude)
        except Exception as e:
            logging.error(f"Error setting preferred statistics: {str(e)}")
    
    def _on_piece_selected(self, event):
        """Handle piece selection in the tree."""
        try:
            # Get selected item
            selection = self.piece_tree.selection()
            if not selection:
                return
                
            piece_id = selection[0]
            piece_type = self.piece_type_var.get()
            
            # Load piece
            if piece_type == "agent":
                piece = self.agent_repository.find_by_id(piece_id)
            else:
                piece = self.squadron_repository.find_by_id(piece_id)
            
            if not piece:
                self._disable_detail_controls()
                return
                
            logging.info(f"[UI_DEBUG] Selected {piece_type} {piece_id}: {piece.name}")
            logging.info(f"[UI_DEBUG] Assignment data - district_id: {piece.district_id}, current_task: {piece.current_task}")
            
            # Check for expected values in the UI tree
            tree_values = self.piece_tree.item(piece_id, "values")
            logging.info(f"[UI_DEBUG] Tree values: {tree_values}")
            
            # Update property form
            self._update_properties_form(piece)
            
            # Update assignment form
            self._update_assignment_form(piece)
            
            # Enable detail controls
            self._enable_detail_controls()
        except Exception as e:
            logging.error(f"Error selecting piece: {str(e)}")
            self._disable_detail_controls()
    
    def _update_properties_form(self, piece):
        """Update properties form with piece data."""
        # Update basic properties
        self.name_var.set(piece.name)
        
        # Set faction
        faction = self.faction_repository.find_by_id(piece.faction_id)
        if faction and self.faction_combo['values']:
            faction_index = 0
            faction_found = False
            # Try to find matching faction in the combobox values
            for i, faction_name in enumerate(self.faction_combo['values']):
                if faction_name and self._faction_filter_map.get(faction_name) == faction.id:
                    faction_index = i
                    faction_found = True
                    break
            
            # Only set current if a matching faction was found
            if faction_found:
                self.faction_combo.current(faction_index)
            elif len(self.faction_combo['values']) > 0:
                # Default to first item if faction not found but list isn't empty
                self.faction_combo.current(0)
        
        # Update piece-specific properties
        if hasattr(piece, 'attunement'):  # Agent
            # Set attributes
            for attr, var in self.attribute_vars.items():
                var.set(str(getattr(piece, attr, 0)))
            
            # Set skills
            for skill, var in self.skill_vars.items():
                var.set(str(getattr(piece, skill, 0)))
                
        else:  # Squadron
            # Set type
            if self.type_combo['values']:
                type_index = 0
                type_found = False
                for i, type_name in enumerate(self.type_combo['values']):
                    if type_name == piece.type:
                        type_index = i
                        type_found = True
                        break
                
                if type_found:
                    self.type_combo.current(type_index)
                elif len(self.type_combo['values']) > 0:
                    self.type_combo.current(0)
            
            # Set mobility
            self.mobility_var.set(str(getattr(piece, 'mobility', 0)))
            
            # Set aptitudes
            for apt, var in self.aptitude_vars.items():
                var.set(str(getattr(piece, apt, -1)))
    
    def _update_assignment_form(self, piece):
        """Update the assignment form with the selected piece's data.
        
        Args:
            piece: Selected piece (Agent or Squadron).
        """
        try:
            logging.info(f"[FORM_DEBUG] Updating assignment form for {piece.__class__.__name__} {piece.id}")
            logging.info(f"[FORM_DEBUG] Current assignment - district_id: {piece.district_id}, current_task: {piece.current_task}")
            
            # Reset form
            self.assign_district_combo.set("")
            self.task_combo.set("monitor")
            self.target_faction_combo.set("")
            self.dc_var.set("15")
            self.description_var.set("")
            self.agent_attr_combo.set("")
            self.agent_skill_combo.set("")
            self.squadron_apt_combo.set("")
            self.manual_modifier_var.set("0")
            
            # Load district
            if piece.district_id:
                district = self.district_repository.find_by_id(piece.district_id)
                if district:
                    logging.info(f"[FORM_DEBUG] Found district: {district.name}")
                    # Find the district name in the combo map
                    for name, id in self._district_combo_map.items():
                        if id == piece.district_id:
                            self.assign_district_combo.set(name)
                            logging.info(f"[FORM_DEBUG] Set district combo to: {name}")
                            break
            
            # Load task if assigned
            if piece.current_task:
                task = piece.current_task
                logging.info(f"[FORM_DEBUG] Found task: {task}")
                
                # Set task type
                task_type = task.get("type", "monitor")
                self.task_combo.set(task_type)
                logging.info(f"[FORM_DEBUG] Set task type to: {task_type}")
                
                # Set target faction if available
                target_faction_id = task.get("target_faction")
                if target_faction_id:
                    target_faction = self.faction_repository.find_by_id(target_faction_id)
                    if target_faction:
                        logging.info(f"[FORM_DEBUG] Found target faction: {target_faction.name}")
                        # Find the faction name in the target faction map
                        for name, id in self._target_faction_map.items():
                            if id == target_faction_id:
                                self.target_faction_combo.set(name)
                                logging.info(f"[FORM_DEBUG] Set target faction combo to: {name}")
                                break
                
                # Set DC if available
                dc = task.get("dc")
                if dc is not None:
                    self.dc_var.set(str(dc))
                    logging.info(f"[FORM_DEBUG] Set DC to: {dc}")
                
                # Set description (for freeform and initiate_conflict)
                description = task.get("description", "")
                self.description_var.set(description)
                
                # For agents
                if hasattr(piece, "get_attribute"):
                    # Set attribute
                    attribute = task.get("attribute")
                    if attribute:
                        self.agent_attr_combo.set(attribute)
                        logging.info(f"[FORM_DEBUG] Set attribute to: {attribute}")
                    
                    # Set skill
                    skill = task.get("skill")
                    if skill:
                        self.agent_skill_combo.set(skill)
                        logging.info(f"[FORM_DEBUG] Set skill to: {skill}")
                else:
                    # For squadrons - set aptitude
                    aptitude = task.get("primary_aptitude")
                    if aptitude:
                        self.squadron_apt_combo.set(aptitude)
                        logging.info(f"[FORM_DEBUG] Set aptitude to: {aptitude}")
                
                # Set manual modifier
                manual_modifier = task.get("manual_modifier", 0)
                self.manual_modifier_var.set(str(manual_modifier))
            
            # Update form visibility based on current task
            self._update_assignment_form_visibility()
            
            logging.info(f"[FORM_DEBUG] Assignment form update complete")
        except Exception as e:
            logging.error(f"Error updating assignment form: {str(e)}")
            messagebox.showerror("Error", "Failed to update assignment form")
    
    def _enable_detail_controls(self):
        """Enable detail panel controls."""
        # Properties form
        self.name_entry.config(state=tk.NORMAL)
        self.faction_combo.config(state="readonly")
        
        # Agent properties
        for var_name, var in self.attribute_vars.items():
            var.trace_add("write", self._validate_number_input)
        for var_name, var in self.skill_vars.items():
            var.trace_add("write", self._validate_number_input)
        
        # Squadron properties
        self.type_combo.config(state="readonly")
        self.mobility_var.trace_add("write", self._validate_number_input)
        for var_name, var in self.aptitude_vars.items():
            var.trace_add("write", self._validate_number_input)
        
        # Assignment form
        self.assign_district_combo.config(state="readonly")
        self.task_combo.config(state="readonly")
        self.target_faction_combo.config(state="readonly")
        self.manual_modifier_var.trace_add("write", self._validate_number_input)
        self.description_entry.config(state=tk.NORMAL)
        self.dc_var.trace_add("write", self._validate_number_input)
        self.agent_attr_combo.config(state="readonly")
        self.agent_skill_combo.config(state="readonly")
        self.squadron_apt_combo.config(state="readonly")
        
        # Buttons
        self.delete_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)
        self.assign_button.config(state=tk.NORMAL)
        self.clear_button.config(state=tk.NORMAL)
    
    def _disable_detail_controls(self):
        """Disable detail panel controls."""
        # Properties form
        self.name_entry.config(state=tk.DISABLED)
        self.faction_combo.config(state=tk.DISABLED)
        
        # Delete traces for spinboxes
        for var_name, var in list(self.attribute_vars.items()):
            try:
                var.trace_remove("write", self._validate_number_input)
            except:
                pass  # Trace may not exist
        
        for var_name, var in list(self.skill_vars.items()):
            try:
                var.trace_remove("write", self._validate_number_input)
            except:
                pass  # Trace may not exist
        
        # Squadron properties
        self.type_combo.config(state=tk.DISABLED)
        try:
            self.mobility_var.trace_remove("write", self._validate_number_input)
        except:
            pass  # Trace may not exist
        
        for var_name, var in list(self.aptitude_vars.items()):
            try:
                var.trace_remove("write", self._validate_number_input)
            except:
                pass  # Trace may not exist
        
        # Assignment form
        self.assign_district_combo.config(state=tk.DISABLED)
        self.task_combo.config(state=tk.DISABLED)
        self.target_faction_combo.config(state=tk.DISABLED)
        try:
            self.manual_modifier_var.trace_remove("write", self._validate_number_input)
        except:
            pass  # Trace may not exist
        self.description_entry.config(state=tk.DISABLED)
        try:
            self.dc_var.trace_remove("write", self._validate_number_input)
        except:
            pass  # Trace may not exist
        self.agent_attr_combo.config(state=tk.DISABLED)
        self.agent_skill_combo.config(state=tk.DISABLED)
        self.squadron_apt_combo.config(state=tk.DISABLED)
        
        # Buttons
        self.delete_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.assign_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
    
    def _validate_number_input(self, name, index, mode):
        """Validate numeric input for spinboxes."""
        # This is a placeholder - in a real implementation we would validate the input
        pass
    
    def _create_new_piece(self):
        """Create a new piece."""
        try:
            piece_type = self.piece_type_var.get()
            
            # Create new instance
            if piece_type == "agent":
                from ..models.agent import Agent
                piece = Agent()
                piece.name = "New Agent"
            else:
                from ..models.squadron import Squadron
                piece = Squadron()
                piece.name = "New Squadron"
                piece.type = "general"
            
            # Set default faction
            factions = self.faction_repository.find_all()
            if factions:
                piece.faction_id = factions[0].id
            
            # Initialize any additional required fields to avoid null reference errors
            if piece_type == "agent":
                # Set default attributes and skills
                for attr in ["might", "finesse", "presence", "intellect", "attunement"]:
                    setattr(piece, attr, 0)
                for skill in ["combat", "infiltration", "persuasion", "streetwise", "survival", "artifice", "arcana"]:
                    setattr(piece, skill, 0)
            else:
                # Set default squadron fields
                piece.mobility = 0
                for apt in ["combat_aptitude", "underworld_aptitude", "social_aptitude", "technical_aptitude",
                           "labor_aptitude", "arcane_aptitude", "wilderness_aptitude", "monitoring_aptitude"]:
                    setattr(piece, apt, -1)
            
            # Save to repository
            if piece_type == "agent":
                success = self.agent_repository.create(piece)
            else:
                success = self.squadron_repository.create(piece)
            
            if success:
                # Reload pieces
                self._load_pieces()
                
                # Select new piece
                self.piece_tree.selection_set(piece.id)
                self.piece_tree.see(piece.id)
                self._on_piece_selected(None)
                
                # Show success message
                self._update_status(f"Created new {piece_type}: {piece.name}")
            else:
                messagebox.showerror("Error", f"Failed to create new {piece_type}")
                
        except Exception as e:
            logging.error(f"Error creating new piece: {str(e)}")
            messagebox.showerror("Error", f"Failed to create new piece: {str(e)}")
    
    def _save_piece(self):
        """Save the current piece."""
        try:
            # Get selected piece ID
            selection = self.piece_tree.selection()
            if not selection:
                return
                
            piece_id = selection[0]
            piece_type = self.piece_type_var.get()
            
            # Load current piece
            if piece_type == "agent":
                piece = self.agent_repository.find_by_id(piece_id)
            else:
                piece = self.squadron_repository.find_by_id(piece_id)
            
            if not piece:
                messagebox.showerror("Error", f"Piece not found: {piece_id}")
                return
            
            # Update basic properties
            piece.name = self.name_var.get()
            
            # Update faction
            faction_name = self.faction_combo.get()
            piece.faction_id = self._faction_filter_map.get(faction_name)
            
            # Update piece-specific properties
            if piece_type == "agent":
                # Update attributes
                for attr, var in self.attribute_vars.items():
                    try:
                        setattr(piece, attr, int(var.get()))
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {attr}: {var.get()}")
                        return
                
                # Update skills
                for skill, var in self.skill_vars.items():
                    try:
                        setattr(piece, skill, int(var.get()))
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {skill}: {var.get()}")
                        return
            else:
                # Update squadron properties
                piece.type = self.type_combo.get()
                
                try:
                    piece.mobility = int(self.mobility_var.get())
                except ValueError:
                    messagebox.showerror("Error", f"Invalid value for mobility: {self.mobility_var.get()}")
                    return
                
                # Update aptitudes
                for apt, var in self.aptitude_vars.items():
                    try:
                        setattr(piece, apt, int(var.get()))
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {apt}: {var.get()}")
                        return
            
            # Save to repository
            if piece_type == "agent":
                success = self.agent_repository.update(piece)
            else:
                success = self.squadron_repository.update(piece)
            
            if success:
                # Reload pieces to reflect changes
                self._load_pieces()
                
                # Reselect piece
                self.piece_tree.selection_set(piece_id)
                self.piece_tree.see(piece_id)
                
                # Update tree item
                faction = self.faction_repository.find_by_id(piece.faction_id)
                faction_name = faction.name if faction else "Unknown"
                
                district_name = "None"
                if piece.district_id:
                    district = self.district_repository.find_by_id(piece.district_id)
                    district_name = district.name if district else "Unknown"
                
                self.piece_tree.item(piece_id, values=(piece.name, faction_name, district_name))
                
                # Show success message
                self.status_label.config(text=f"Saved {piece_type}: {piece.name}")
            else:
                messagebox.showerror("Error", f"Failed to save {piece_type}")
                
        except Exception as e:
            logging.error(f"Error saving piece: {str(e)}")
            messagebox.showerror("Error", f"Failed to save piece: {str(e)}")
    
    def _delete_piece(self):
        """Delete the current piece."""
        try:
            # Get selected piece ID
            selection = self.piece_tree.selection()
            if not selection:
                return
                
            piece_id = selection[0]
            piece_type = self.piece_type_var.get()
            
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this {piece_type}?"):
                return
            
            # Delete from repository
            if piece_type == "agent":
                success = self.agent_repository.delete(piece_id)
            else:
                success = self.squadron_repository.delete(piece_id)
            
            if success:
                # Remove from tree
                self.piece_tree.delete(piece_id)
                
                # Clear selection
                self._clear_selection()
                
                # Show success message
                self.status_label.config(text=f"Deleted {piece_type}: {piece_id}")
            else:
                messagebox.showerror("Error", f"Failed to delete {piece_type}")
                
        except Exception as e:
            logging.error(f"Error deleting piece: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete piece: {str(e)}")
    
    def _assign_task(self):
        """Assign a task to the selected piece."""
        try:
            # Get selected piece
            selection = self.piece_tree.selection()
            if not selection:
                return
                
            piece_id = selection[0]
            piece_type = self.piece_type_var.get()
            
            # Get district
            district_name = self.assign_district_combo.get()
            district_id = self._district_combo_map.get(district_name)
            
            # If district is "None", clear assignment
            if district_id == "none":
                self._clear_assignment()
                return
            
            # Get task type
            task_type = self.task_combo.get()
            
            # Get target faction for take_influence and initiate_conflict
            target_faction_id = None
            if task_type in ["take_influence", "initiate_conflict"]:
                target_faction_name = self.target_faction_combo.get()
                target_faction_id = self._target_faction_map.get(target_faction_name)
                
                if not target_faction_id:
                    messagebox.showerror("Error", "Target faction is required for this task")
                    return
            
            # Get description and DC for freeform and initiate_conflict
            description = None
            dc = None
            if task_type in ["freeform", "initiate_conflict"]:
                description = self.description_var.get()
                
                try:
                    dc = int(self.dc_var.get())
                    if dc < 5 or dc > 30:
                        raise ValueError("DC must be between 5 and 30")
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid DC: {str(e)}")
                    return
            
            # Get manual modifier
            try:
                manual_modifier = int(self.manual_modifier_var.get())
                if manual_modifier < -10 or manual_modifier > 10:
                    raise ValueError("Manual modifier must be between -10 and 10")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid manual modifier: {str(e)}")
                return
            
            # Get attribute/skill/aptitude based on piece type
            attribute = None
            skill = None
            aptitude = None
            
            if piece_type == "agent":
                attribute = self.agent_attr_combo.get()
                skill = self.agent_skill_combo.get()
                
                if not attribute or not skill:
                    messagebox.showerror("Error", "Attribute and skill are required for this task")
                    return
            else:
                aptitude = self.squadron_apt_combo.get()
                
                if not aptitude:
                    messagebox.showerror("Error", "Aptitude is required for this task")
                    return
            
            # Assign task
            if piece_type == "agent":
                success = self.agent_repository.assign_task(
                    piece_id, district_id, task_type, target_faction_id,
                    attribute, skill, dc, True, manual_modifier
                )
            else:
                success = self.squadron_repository.assign_task(
                    piece_id, district_id, task_type, target_faction_id,
                    aptitude, dc, True, manual_modifier
                )
            
            if success:
                # Get piece and update tree
                if piece_type == "agent":
                    piece = self.agent_repository.find_by_id(piece_id)
                else:
                    piece = self.squadron_repository.find_by_id(piece_id)
                
                if piece:
                    # Get faction name
                    faction = self.faction_repository.find_by_id(piece.faction_id)
                    faction_name = faction.name if faction else "Unknown"
                    
                    # Get district name
                    district = self.district_repository.find_by_id(district_id)
                    district_name = district.name if district else "None"
                    
                    # Format task type
                    formatted_task = task_type.replace("_", " ").title()
                    
                    # Update tree item
                    self.piece_tree.item(piece_id, values=(
                        piece.name,
                        faction_name,
                        district_name,
                        formatted_task
                    ))
                    
                    # Show success message
                    self.status_label.config(text=f"Assigned {formatted_task} task in {district_name}")
                    
                    # Update form to show current assignment
                    self._update_properties_form(piece)
                    self._update_assignment_form(piece)
                
                # Reselect piece
                self.piece_tree.selection_set(piece_id)
                self.piece_tree.see(piece_id)
            else:
                messagebox.showerror("Error", "Failed to assign task")
                
        except Exception as e:
            logging.error(f"Error assigning task: {str(e)}")
            messagebox.showerror("Error", f"Failed to assign task: {str(e)}")
    
    def _clear_assignment(self):
        """Clear the current piece's assignment."""
        try:
            # Get selected piece ID
            selection = self.piece_tree.selection()
            if not selection:
                return
                
            piece_id = selection[0]
            piece_type = self.piece_type_var.get()
            
            # Clear assignment
            if piece_type == "agent":
                success = self.agent_repository.clear_task(piece_id)
            else:
                success = self.squadron_repository.clear_task(piece_id)
            
            if success:
                # Get piece and update tree
                if piece_type == "agent":
                    piece = self.agent_repository.find_by_id(piece_id)
                else:
                    piece = self.squadron_repository.find_by_id(piece_id)
                
                if piece:
                    # Get faction name
                    faction = self.faction_repository.find_by_id(piece.faction_id)
                    faction_name = faction.name if faction else "Unknown"
                    
                    # Update tree item
                    self.piece_tree.item(piece_id, values=(
                        piece.name,
                        faction_name,
                        "None",
                        "None"
                    ))
                    
                    # Show success message
                    self.status_label.config(text="Assignment cleared")
                    
                    # Update form to show current assignment
                    self._update_properties_form(piece)
                    self._update_assignment_form(piece)
                
                # Reselect piece
                self.piece_tree.selection_set(piece_id)
                self.piece_tree.see(piece_id)
            else:
                messagebox.showerror("Error", "Failed to clear assignment")
                
        except Exception as e:
            logging.error(f"Error clearing assignment: {str(e)}")
            messagebox.showerror("Error", f"Failed to clear assignment: {str(e)}")
    
    def _clear_selection(self):
        """Clear the current selection and reset detail forms."""
        self.piece_tree.selection_remove(self.piece_tree.selection())
        self._disable_detail_controls()
        
        # Reset form values
        self.name_var.set("")
        self.faction_combo.set("")
        
        # Reset attributes and skills
        for var in self.attribute_vars.values():
            var.set("0")
        
        for var in self.skill_vars.values():
            var.set("0")
        
        # Reset squadron properties
        self.type_combo.set("")
        self.mobility_var.set("0")
        
        for var in self.aptitude_vars.values():
            var.set("-1")
        
        # Reset assignment form
        self.assign_district_combo.set("")
        self.task_combo.set("monitor")
        self.target_faction_combo.set("")
        self.manual_modifier_var.set("0")
        self.description_var.set("")
        self.dc_var.set("15")
        self.agent_attr_combo.set("")
        self.agent_skill_combo.set("")
        self.squadron_apt_combo.set("")
        
        # Clear status message
        self.status_label.config(text="")

    def _update_status(self, message):
        """Update the status label in the main window, if available."""
        try:
            # Navigate up to find the main window
            parent = self.master
            while parent and not hasattr(parent, 'status_label'):
                parent = parent.master
                
            if parent and hasattr(parent, 'status_label'):
                parent.status_label.config(text=message)
        except Exception as e:
            logging.error(f"Error updating status: {str(e)}")