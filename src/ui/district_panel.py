import tkinter as tk
from tkinter import ttk, messagebox
import logging

from ..models.rumor import Rumor  # Add this import at the top


class DistrictPanel:
    """Panel for managing districts."""
    
    def __init__(self, parent, db_manager, district_repository):
        """Initialize the district panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
        """
        self.parent = parent
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.current_district_id = None  # Track the currently selected district
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create panel layout
        self.create_layout()
        
        # Load initial data
        self.load_districts()
    
    def create_layout(self):
        """Create the panel layout."""
        # Split into left and right panes
        self.paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left pane for district list
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=1)
        
        # Right pane for district details
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=2)
        
        # Create district list
        self.create_district_list()
        
        # Create district detail form
        self.create_district_detail_form()
    
    def create_district_list(self):
        """Create the district list component."""
        # List frame
        self.list_frame = ttk.LabelFrame(self.left_frame, text="Districts")
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # District treeview
        self.district_tree = ttk.Treeview(
            self.list_frame, 
            columns=("district_id", "name"),
            show="headings",
            selectmode="browse"
        )
        self.district_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        self.district_tree.heading("district_id", text="ID")
        self.district_tree.heading("name", text="Name")
        
        self.district_tree.column("district_id", width=0, stretch=False)  # Hide ID column
        self.district_tree.column("name", width=200)
        
        # Scrollbar
        self.tree_scrollbar = ttk.Scrollbar(
            self.list_frame, 
            orient=tk.VERTICAL, 
            command=self.district_tree.yview
        )
        self.tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.district_tree.configure(yscrollcommand=self.tree_scrollbar.set)
        
        # Bind selection event
        self.district_tree.bind("<<TreeviewSelect>>", self.on_district_select)
        
        # Button frame
        self.list_button_frame = ttk.Frame(self.left_frame)
        self.list_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add button
        self.add_button = ttk.Button(
            self.list_button_frame, 
            text="Add District", 
            command=self.add_district
        )
        self.add_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Delete button
        self.delete_button = ttk.Button(
            self.list_button_frame, 
            text="Delete District", 
            command=self.delete_district
        )
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def create_district_detail_form(self):
        """Create the district detail form."""
        # Detail frame
        self.detail_frame = ttk.LabelFrame(self.right_frame, text="District Details")
        self.detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create info section
        self.info_frame = ttk.Frame(self.detail_frame)
        self.info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Organize in grid
        self.info_frame.columnconfigure(1, weight=1)
        self.info_frame.columnconfigure(3, weight=1)
        
        # District name
        ttk.Label(self.info_frame, text="Name:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(self.info_frame, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # District ID (display only)
        ttk.Label(self.info_frame, text="ID:").grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.id_var = tk.StringVar()
        id_entry = ttk.Entry(self.info_frame, textvariable=self.id_var, state="readonly")
        id_entry.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=5)
        
        # District description
        ttk.Label(self.info_frame, text="Description:").grid(
            row=1, column=0, sticky=tk.NW, padx=5, pady=5
        )
        
        self.description_text = tk.Text(self.info_frame, height=3, width=40)
        self.description_text.grid(
            row=1, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=5
        )
        
        # District attributes
        ttk.Label(self.info_frame, text="Commerce Value:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.commerce_var = tk.IntVar()
        commerce_spinner = ttk.Spinbox(
            self.info_frame, 
            from_=0, 
            to=10, 
            textvariable=self.commerce_var, 
            width=5
        )
        commerce_spinner.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.info_frame, text="Muster Value:").grid(
            row=2, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.muster_var = tk.IntVar()
        muster_spinner = ttk.Spinbox(
            self.info_frame, 
            from_=0, 
            to=10, 
            textvariable=self.muster_var, 
            width=5
        )
        muster_spinner.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.info_frame, text="Aristocratic Value:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.aristocratic_var = tk.IntVar()
        aristocratic_spinner = ttk.Spinbox(
            self.info_frame, 
            from_=0, 
            to=10, 
            textvariable=self.aristocratic_var, 
            width=5
        )
        aristocratic_spinner.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # District preferred attributes
        ttk.Label(self.info_frame, text="Preferred Actions:").grid(
            row=4, column=0, columnspan=4, sticky=tk.W, padx=5, pady=(15, 5)
        )
        
        # Gain influence preferences
        ttk.Label(self.info_frame, text="Gain Influence:").grid(
            row=5, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        # Frame for gain influence preferences
        gain_frame = ttk.Frame(self.info_frame)
        gain_frame.grid(row=5, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(gain_frame, text="Attribute:").pack(side=tk.LEFT, padx=2)
        
        self.gain_attribute_var = tk.StringVar()
        gain_attribute_combo = ttk.Combobox(
            gain_frame, 
            textvariable=self.gain_attribute_var,
            values=["intellect", "presence", "finesse", "might", "attunement"],
            width=10,
            state="readonly"
        )
        gain_attribute_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(gain_frame, text="Skill:").pack(side=tk.LEFT, padx=2)
        
        self.gain_skill_var = tk.StringVar()
        gain_skill_combo = ttk.Combobox(
            gain_frame, 
            textvariable=self.gain_skill_var,
            values=["infiltration", "persuasion", "combat", "streetwise", 
                    "survival", "artifice", "arcana"],
            width=10,
            state="readonly"
        )
        gain_skill_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(gain_frame, text="Squadron:").pack(side=tk.LEFT, padx=2)
        
        self.gain_aptitude_var = tk.StringVar()
        gain_aptitude_combo = ttk.Combobox(
            gain_frame, 
            textvariable=self.gain_aptitude_var,
            values=["combat", "underworld", "social", "technical", 
                    "labor", "arcane", "wilderness"],
            width=10,
            state="readonly"
        )
        gain_aptitude_combo.pack(side=tk.LEFT, padx=2)
        
        # Monitor preferences
        ttk.Label(self.info_frame, text="Monitoring:").grid(
            row=6, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        # Frame for monitoring preferences
        monitor_frame = ttk.Frame(self.info_frame)
        monitor_frame.grid(row=6, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(monitor_frame, text="Attribute:").pack(side=tk.LEFT, padx=2)
        
        self.monitor_attribute_var = tk.StringVar()
        monitor_attribute_combo = ttk.Combobox(
            monitor_frame, 
            textvariable=self.monitor_attribute_var,
            values=["intellect", "presence", "finesse", "might", "attunement"],
            width=10,
            state="readonly"
        )
        monitor_attribute_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(monitor_frame, text="Skill:").pack(side=tk.LEFT, padx=2)
        
        self.monitor_skill_var = tk.StringVar()
        monitor_skill_combo = ttk.Combobox(
            monitor_frame, 
            textvariable=self.monitor_skill_var,
            values=["infiltration", "persuasion", "combat", "streetwise", 
                    "survival", "artifice", "arcana"],
            width=10,
            state="readonly"
        )
        monitor_skill_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(monitor_frame, text="Squadron:").pack(side=tk.LEFT, padx=2)
        
        self.monitor_aptitude_var = tk.StringVar()
        monitor_aptitude_combo = ttk.Combobox(
            monitor_frame, 
            textvariable=self.monitor_aptitude_var,
            values=["monitoring"],
            width=10,
            state="readonly"
        )
        monitor_aptitude_combo.pack(side=tk.LEFT, padx=2)
        
        # Create influence tab control
        self.tab_control = ttk.Notebook(self.detail_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Influence tab
        self.influence_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(self.influence_frame, text="Influence")
        
        # Adjacency tab
        self.adjacency_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(self.adjacency_frame, text="Adjacent Districts")
        
        # Rumors tab
        self.rumors_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(self.rumors_frame, text="Rumors")
        
        # Create influence table
        self.create_influence_table()
        
        # Create adjacency table
        self.create_adjacency_table()
        
        # Create rumors table
        self.create_rumors_table()
        
        # Save button
        self.save_button = ttk.Button(
            self.detail_frame, 
            text="Save Changes", 
            command=self.save_district
        )
        self.save_button.pack(side=tk.RIGHT, padx=10, pady=10)
    
    def create_influence_table(self):
        """Create the influence table."""
        # Influence treeview
        self.influence_tree = ttk.Treeview(
            self.influence_frame, 
            columns=("faction_id", "faction_name", "influence", "stronghold"),
            show="headings"
        )
        self.influence_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        self.influence_tree.heading("faction_id", text="ID")
        self.influence_tree.heading("faction_name", text="Faction")
        self.influence_tree.heading("influence", text="Influence")
        self.influence_tree.heading("stronghold", text="Stronghold")
        
        self.influence_tree.column("faction_id", width=0, stretch=False)  # Hide ID column
        self.influence_tree.column("faction_name", width=150)
        self.influence_tree.column("influence", width=80, anchor=tk.CENTER)
        self.influence_tree.column("stronghold", width=80, anchor=tk.CENTER)
        
        # Button frame
        self.influence_button_frame = ttk.Frame(self.influence_frame)
        self.influence_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add influence button
        self.add_influence_button = ttk.Button(
            self.influence_button_frame, 
            text="Add Influence", 
            command=self.add_influence
        )
        self.add_influence_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Edit influence button
        self.edit_influence_button = ttk.Button(
            self.influence_button_frame, 
            text="Edit Influence", 
            command=self.edit_influence
        )
        self.edit_influence_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Remove influence button
        self.remove_influence_button = ttk.Button(
            self.influence_button_frame, 
            text="Remove Influence", 
            command=self.remove_influence
        )
        self.remove_influence_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def create_adjacency_table(self):
        """Create the adjacency table."""
        # Adjacency treeview
        self.adjacency_tree = ttk.Treeview(
            self.adjacency_frame, 
            columns=("district_id", "district_name"),
            show="headings"
        )
        self.adjacency_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        self.adjacency_tree.heading("district_id", text="ID")
        self.adjacency_tree.heading("district_name", text="District")
        
        self.adjacency_tree.column("district_id", width=0, stretch=False)  # Hide ID column
        self.adjacency_tree.column("district_name", width=200)
        
        # Button frame
        self.adjacency_button_frame = ttk.Frame(self.adjacency_frame)
        self.adjacency_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add adjacency button
        self.add_adjacency_button = ttk.Button(
            self.adjacency_button_frame, 
            text="Add Adjacent", 
            command=self.add_adjacency
        )
        self.add_adjacency_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Remove adjacency button
        self.remove_adjacency_button = ttk.Button(
            self.adjacency_button_frame, 
            text="Remove Adjacent", 
            command=self.remove_adjacency
        )
        self.remove_adjacency_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def create_rumors_table(self):
        """Create the rumors table."""
        # Rumors treeview
        self.rumors_tree = ttk.Treeview(
            self.rumors_frame, 
            columns=("rumor_id", "text", "dc", "discovered"),
            show="headings"
        )
        self.rumors_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        self.rumors_tree.heading("rumor_id", text="ID")
        self.rumors_tree.heading("text", text="Rumor Text")
        self.rumors_tree.heading("dc", text="DC")
        self.rumors_tree.heading("discovered", text="Discovered")
        
        self.rumors_tree.column("rumor_id", width=0, stretch=False)  # Hide ID column
        self.rumors_tree.column("text", width=300)
        self.rumors_tree.column("dc", width=50, anchor=tk.CENTER)
        self.rumors_tree.column("discovered", width=80, anchor=tk.CENTER)
        
        # Button frame
        self.rumors_button_frame = ttk.Frame(self.rumors_frame)
        self.rumors_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add rumor button
        self.add_rumor_button = ttk.Button(
            self.rumors_button_frame, 
            text="Add Rumor", 
            command=self.add_rumor
        )
        self.add_rumor_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Edit rumor button
        self.edit_rumor_button = ttk.Button(
            self.rumors_button_frame, 
            text="Edit Rumor", 
            command=self.edit_rumor
        )
        self.edit_rumor_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Remove rumor button
        self.remove_rumor_button = ttk.Button(
            self.rumors_button_frame, 
            text="Remove Rumor", 
            command=self.remove_rumor
        )
        self.remove_rumor_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def load_districts(self):
        """Load districts into the list."""
        try:
            # Clear existing items
            for item in self.district_tree.get_children():
                self.district_tree.delete(item)
            
            # Get all districts
            districts = self.district_repository.find_all()
            
            for district in districts:
                self.district_tree.insert(
                    "", 
                    tk.END, 
                    values=(district.id, district.name)
                )
        except Exception as e:
            logging.error(f"Error loading districts: {str(e)}")
            messagebox.showerror("Error", f"Failed to load districts: {str(e)}")
    
    def load_district_details(self, district_id):
        """Load district details into the form.
        
        Args:
            district_id (str): District ID to load.
        """
        try:
            # Get district
            district = self.district_repository.find_by_id(district_id)
            
            if not district:
                messagebox.showerror("Error", f"District not found: {district_id}")
                return
            
            # Set form values
            self.id_var.set(district.id)
            self.name_var.set(district.name)
            
            # Set description
            self.description_text.delete(1.0, tk.END)
            if district.description:
                self.description_text.insert(1.0, district.description)
            
            # Set attribute values
            self.commerce_var.set(district.commerce_value)
            self.muster_var.set(district.muster_value)
            self.aristocratic_var.set(district.aristocratic_value)
            
            # Set preferred action values
            self.gain_attribute_var.set(district.preferred_gain_attribute)
            self.gain_skill_var.set(district.preferred_gain_skill)
            self.gain_aptitude_var.set(district.preferred_gain_squadron_aptitude)
            
            self.monitor_attribute_var.set(district.preferred_monitor_attribute)
            self.monitor_skill_var.set(district.preferred_monitor_skill)
            self.monitor_aptitude_var.set(district.preferred_monitor_squadron_aptitude)
            
            # Load influence data
            self.load_influence_data(district)
            
            # Load adjacency data
            self.load_adjacency_data(district)
            
            # Load rumors data
            self.load_rumors_data(district)
        except Exception as e:
            logging.error(f"Error loading district details: {str(e)}")
            messagebox.showerror("Error", f"Failed to load district details: {str(e)}")
    
    def load_influence_data(self, district):
        """Load influence data for a district.
        
        Args:
            district: District instance.
        """
        try:
            # Clear existing items
            for item in self.influence_tree.get_children():
                self.influence_tree.delete(item)
            
            # No influence data
            if not district.faction_influence:
                return
            
            # Get faction names
            faction_names = {}
            
            query = "SELECT id, name FROM factions"
            factions = self.db_manager.execute_query(query)
            
            for faction in factions:
                faction_names[faction["id"]] = faction["name"]
            
            # Add influence entries
            for faction_id, influence in district.faction_influence.items():
                faction_name = faction_names.get(faction_id, "Unknown Faction")
                stronghold = "Yes" if district.has_stronghold(faction_id) else "No"
                
                self.influence_tree.insert(
                    "", 
                    tk.END, 
                    values=(faction_id, faction_name, influence, stronghold)
                )
        except Exception as e:
            logging.error(f"Error loading influence data: {str(e)}")
            raise
    
    def load_adjacency_data(self, district):
        """Load adjacency data for a district.
        
        Args:
            district: District instance.
        """
        try:
            # Clear existing items
            for item in self.adjacency_tree.get_children():
                self.adjacency_tree.delete(item)
            
            # No adjacency data
            if not district.adjacent_districts:
                return
            
            # Get district names
            district_names = {}
            
            for d in self.district_repository.find_all():
                district_names[d.id] = d.name
            
            # Add adjacency entries
            for adjacent_id in district.adjacent_districts:
                district_name = district_names.get(adjacent_id, "Unknown District")
                
                self.adjacency_tree.insert(
                    "", 
                    tk.END, 
                    values=(adjacent_id, district_name)
                )
        except Exception as e:
            logging.error(f"Error loading adjacency data: {str(e)}")
            raise
    
    def load_rumors_data(self, district):
        """Load rumors data for a district.
        
        Args:
            district: District instance.
        """
        try:
            # Clear existing items
            for item in self.rumors_tree.get_children():
                self.rumors_tree.delete(item)
            
            # Get rumors for this district
            query = """
                SELECT id, rumor_text, discovery_dc, is_discovered
                FROM district_rumors
                WHERE district_id = :district_id
            """
            
            rumors = self.db_manager.execute_query(query, {"district_id": district.id})
            
            if not rumors:
                return
            
            # Add rumor entries
            for rumor in rumors:
                discovered = "Yes" if rumor["is_discovered"] else "No"
                
                self.rumors_tree.insert(
                    "", 
                    tk.END, 
                    values=(rumor["id"], rumor["rumor_text"], rumor["discovery_dc"], discovered)
                )
        except Exception as e:
            logging.error(f"Error loading rumors data: {str(e)}")
            raise
    
    def on_district_select(self, event):
        """Handle district selection event.
        
        Args:
            event: Event object.
        """
        # Get selected item
        selection = self.district_tree.selection()
        
        if not selection:
            return
            
        # Get district ID
        district_id = self.district_tree.item(selection[0], "values")[0]
        
        # Store the current district ID
        self.current_district_id = district_id
        
        # Load district details
        self.load_district_details(district_id)
    
    def add_district(self):
        """Handle add district button click."""
        # Create a simple dialog for new district
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add District")
        dialog.geometry("300x120")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.frame.winfo_rootx() + (self.frame.winfo_width() / 2) - 150,
            self.frame.winfo_rooty() + (self.frame.winfo_height() / 2) - 60
        ))
        
        # Name field
        ttk.Label(dialog, text="District Name:").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=25)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.focus_set()
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Create button
        create_button = ttk.Button(
            button_frame, 
            text="Create", 
            command=lambda: self.create_district(name_var.get(), dialog)
        )
        create_button.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    def create_district(self, name, dialog):
        """Create a new district.
        
        Args:
            name (str): District name.
            dialog: Dialog window to close.
        """
        if not name:
            messagebox.showerror("Error", "District name is required")
            return
            
        try:
            # Create district with default values
            from ..models.district import District
            
            district = District(name=name)
            district.description = ""
            district.commerce_value = 5
            district.muster_value = 5
            district.aristocratic_value = 5
            district.preferred_gain_attribute = "presence"
            district.preferred_gain_skill = "persuasion"
            district.preferred_gain_squadron_aptitude = "social"
            district.preferred_monitor_attribute = "intellect"
            district.preferred_monitor_skill = "streetwise"
            district.preferred_monitor_squadron_aptitude = "monitoring"
            
            # Save district
            if self.district_repository.create(district):
                # Close dialog
                dialog.destroy()
                
                # Refresh district list
                self.load_districts()
                
                # Select the new district
                for item in self.district_tree.get_children():
                    if self.district_tree.item(item, "values")[0] == district.id:
                        self.district_tree.selection_set(item)
                        self.district_tree.see(item)
                        break
                        
                # Load district details
                self.load_district_details(district.id)
            else:
                messagebox.showerror("Error", "Failed to create district")
        except Exception as e:
            logging.error(f"Error creating district: {str(e)}")
            messagebox.showerror("Error", f"Failed to create district: {str(e)}")
    
    def delete_district(self):
        """Handle delete district button click."""
        # Get selected item
        selection = self.district_tree.selection()
        
        if not selection:
            messagebox.showinfo("Info", "Please select a district to delete")
            return
            
        # Get district ID
        district_id = self.district_tree.item(selection[0], "values")[0]
        district_name = self.district_tree.item(selection[0], "values")[1]
        
        # Confirm deletion
        if not messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete district '{district_name}'?"
        ):
            return
            
        try:
            # Delete district
            if self.district_repository.delete(district_id):
                # Refresh district list
                self.load_districts()
                
                # Clear form
                self.clear_form()
            else:
                messagebox.showerror("Error", "Failed to delete district")
        except Exception as e:
            logging.error(f"Error deleting district: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete district: {str(e)}")
    
    def clear_form(self):
        """Clear the district detail form."""
        self.current_district_id = None
        self.id_var.set("")
        self.name_var.set("")
        self.description_text.delete(1.0, tk.END)
        self.commerce_var.set(0)
        self.muster_var.set(0)
        self.aristocratic_var.set(0)
        self.gain_attribute_var.set("")
        self.gain_skill_var.set("")
        self.gain_aptitude_var.set("")
        self.monitor_attribute_var.set("")
        self.monitor_skill_var.set("")
        self.monitor_aptitude_var.set("")
        
        # Clear tables
        for item in self.influence_tree.get_children():
            self.influence_tree.delete(item)
            
        for item in self.adjacency_tree.get_children():
            self.adjacency_tree.delete(item)
            
        for item in self.rumors_tree.get_children():
            self.rumors_tree.delete(item)
    
    def save_district(self):
        """Handle save district button click."""
        # Get district ID
        district_id = self.id_var.get()
        
        if not district_id:
            messagebox.showinfo("Info", "No district selected")
            return
            
        try:
            # Get district
            district = self.district_repository.find_by_id(district_id)
            
            if not district:
                messagebox.showerror("Error", f"District not found: {district_id}")
                return
            
            # Update district with form values
            district.name = self.name_var.get()
            district.description = self.description_text.get(1.0, tk.END).strip()
            district.commerce_value = self.commerce_var.get()
            district.muster_value = self.muster_var.get()
            district.aristocratic_value = self.aristocratic_var.get()
            district.preferred_gain_attribute = self.gain_attribute_var.get()
            district.preferred_gain_skill = self.gain_skill_var.get()
            district.preferred_gain_squadron_aptitude = self.gain_aptitude_var.get()
            district.preferred_monitor_attribute = self.monitor_attribute_var.get()
            district.preferred_monitor_skill = self.monitor_skill_var.get()
            district.preferred_monitor_squadron_aptitude = self.monitor_aptitude_var.get()
            
            # Save district
            if self.district_repository.update(district):
                messagebox.showinfo("Success", "District saved successfully")
                
                # Refresh district list to update name
                self.load_districts()
                
                # Select the district again
                for item in self.district_tree.get_children():
                    if self.district_tree.item(item, "values")[0] == district_id:
                        self.district_tree.selection_set(item)
                        break
            else:
                messagebox.showerror("Error", "Failed to save district")
        except Exception as e:
            logging.error(f"Error saving district: {str(e)}")
            messagebox.showerror("Error", f"Failed to save district: {str(e)}")
    
    def add_influence(self):
        """Handle add influence button click."""
        # Get district ID
        district_id = self.id_var.get()
        
        if not district_id:
            messagebox.showinfo("Info", "No district selected")
            return
            
        # Create a dialog for adding influence
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add Faction Influence")
        dialog.geometry("300x150")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.frame.winfo_rootx() + (self.frame.winfo_width() / 2) - 150,
            self.frame.winfo_rooty() + (self.frame.winfo_height() / 2) - 75
        ))
        
        # Get factions
        try:
            query = "SELECT id, name FROM factions"
            factions = self.db_manager.execute_query(query)
            
            faction_dict = {}
            for faction in factions:
                faction_dict[faction["name"]] = faction["id"]
            
            # Faction field
            ttk.Label(dialog, text="Faction:").grid(
                row=0, column=0, sticky=tk.W, padx=10, pady=10
            )
            
            faction_var = tk.StringVar()
            faction_combo = ttk.Combobox(
                dialog, 
                textvariable=faction_var,
                values=list(faction_dict.keys()),
                width=25,
                state="readonly"
            )
            faction_combo.grid(row=0, column=1, padx=10, pady=10)
            
            # Influence field
            ttk.Label(dialog, text="Influence:").grid(
                row=1, column=0, sticky=tk.W, padx=10, pady=10
            )
            
            influence_var = tk.IntVar(value=1)
            influence_spinner = ttk.Spinbox(
                dialog, 
                from_=1, 
                to=10, 
                textvariable=influence_var, 
                width=5
            )
            influence_spinner.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
            
            # Button frame
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=2, column=0, columnspan=2, pady=10)
            
            # Add button
            add_button = ttk.Button(
                button_frame, 
                text="Add", 
                command=lambda: self.add_faction_influence(
                    district_id, 
                    faction_dict.get(faction_var.get()), 
                    influence_var.get(),
                    dialog
                )
            )
            add_button.pack(side=tk.LEFT, padx=5)
            
            # Cancel button
            cancel_button = ttk.Button(
                button_frame, 
                text="Cancel", 
                command=dialog.destroy
            )
            cancel_button.pack(side=tk.LEFT, padx=5)
        except Exception as e:
            logging.error(f"Error loading factions: {str(e)}")
            messagebox.showerror("Error", f"Failed to load factions: {str(e)}")
            dialog.destroy()
    
    def add_faction_influence(self, district_id, faction_id, influence, dialog):
        """Add faction influence to a district.
        
        Args:
            district_id (str): District ID.
            faction_id (str): Faction ID.
            influence (int): Influence value.
            dialog: Dialog window to close.
        """
        if not faction_id:
            messagebox.showerror("Error", "Please select a faction")
            return
            
        try:
            # Get district
            district = self.district_repository.find_by_id(district_id)
            
            if not district:
                messagebox.showerror("Error", f"District not found: {district_id}")
                dialog.destroy()
                return
            
            # Check if faction already has influence
            if district.get_faction_influence(faction_id) > 0:
                messagebox.showerror("Error", "Faction already has influence in this district")
                return
            
            # Check available influence
            if district.influence_pool < influence:
                messagebox.showerror(
                    "Error", 
                    f"Not enough influence available. Maximum: {district.influence_pool}"
                )
                return
            
            # Add influence
            district.set_faction_influence(faction_id, influence)
            
            # Save district
            if self.district_repository.update(district):
                # Close dialog
                dialog.destroy()
                
                # Reload influence data
                self.load_influence_data(district)
            else:
                messagebox.showerror("Error", "Failed to add faction influence")
        except Exception as e:
            logging.error(f"Error adding faction influence: {str(e)}")
            messagebox.showerror("Error", f"Failed to add faction influence: {str(e)}")
    
    def edit_influence(self):
        """Handle edit influence button click."""
        # Get district ID
        district_id = self.id_var.get()
        
        if not district_id:
            messagebox.showinfo("Info", "No district selected")
            return
            
        # Get selected influence
        selection = self.influence_tree.selection()
        
        if not selection:
            messagebox.showinfo("Info", "Please select a faction to edit")
            return
            
        # Get influence data
        faction_id = self.influence_tree.item(selection[0], "values")[0]
        faction_name = self.influence_tree.item(selection[0], "values")[1]
        current_influence = int(self.influence_tree.item(selection[0], "values")[2])
        current_stronghold = self.influence_tree.item(selection[0], "values")[3] == "Yes"
        
        # Create a dialog for editing influence
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Edit Influence: {faction_name}")
        dialog.geometry("300x150")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.frame.winfo_rootx() + (self.frame.winfo_width() / 2) - 150,
            self.frame.winfo_rooty() + (self.frame.winfo_height() / 2) - 75
        ))
        
        # Influence field
        ttk.Label(dialog, text="Influence:").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=10
        )
        
        influence_var = tk.IntVar(value=current_influence)
        influence_spinner = ttk.Spinbox(
            dialog, 
            from_=0, 
            to=10, 
            textvariable=influence_var, 
            width=5
        )
        influence_spinner.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Stronghold field
        stronghold_var = tk.BooleanVar(value=current_stronghold)
        stronghold_check = ttk.Checkbutton(
            dialog, 
            text="Stronghold", 
            variable=stronghold_var
        )
        stronghold_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=10, pady=10)
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Update button
        update_button = ttk.Button(
            button_frame, 
            text="Update", 
            command=lambda: self.update_faction_influence(
                district_id, 
                faction_id, 
                influence_var.get(),
                stronghold_var.get(),
                dialog
            )
        )
        update_button.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    def update_faction_influence(self, district_id, faction_id, influence, stronghold, dialog):
        """Update faction influence in a district.
        
        Args:
            district_id (str): District ID.
            faction_id (str): Faction ID.
            influence (int): Influence value.
            stronghold (bool): Stronghold flag.
            dialog: Dialog window to close.
        """
        try:
            # Get district
            district = self.district_repository.find_by_id(district_id)
            
            if not district:
                messagebox.showerror("Error", f"District not found: {district_id}")
                dialog.destroy()
                return
            
            # Get current influence
            current_influence = district.get_faction_influence(faction_id)
            
            # Calculate required influence pool
            required_pool = influence - current_influence
            
            # Check available influence if increasing
            if required_pool > 0 and district.influence_pool < required_pool:
                messagebox.showerror(
                    "Error", 
                    f"Not enough influence available. Maximum increase: {district.influence_pool}"
                )
                return
            
            # Update influence
            if influence == 0:
                # Remove faction influence
                district.faction_influence.pop(faction_id, None)
            else:
                district.faction_influence[faction_id] = influence
            
            # Update stronghold
            district.strongholds[faction_id] = stronghold
            
            # Recalculate influence pool
            district.influence_pool = 10 - district.calculate_total_influence()
            
            # Save district
            if self.district_repository.update(district):
                # Close dialog
                dialog.destroy()
                
                # Reload influence data
                self.load_influence_data(district)
            else:
                messagebox.showerror("Error", "Failed to update faction influence")
        except Exception as e:
            logging.error(f"Error updating faction influence: {str(e)}")
            messagebox.showerror("Error", f"Failed to update faction influence: {str(e)}")
    
    def remove_influence(self):
        """Handle remove influence button click."""
        # Get district ID
        district_id = self.id_var.get()
        
        if not district_id:
            messagebox.showinfo("Info", "No district selected")
            return
            
        # Get selected influence
        selection = self.influence_tree.selection()
        
        if not selection:
            messagebox.showinfo("Info", "Please select a faction to remove")
            return
            
        # Get influence data
        faction_id = self.influence_tree.item(selection[0], "values")[0]
        faction_name = self.influence_tree.item(selection[0], "values")[1]
        
        # Confirm removal
        if not messagebox.askyesno(
            "Confirm Remove", 
            f"Are you sure you want to remove {faction_name}'s influence from this district?"
        ):
            return
            
        try:
            # Get district
            district = self.district_repository.find_by_id(district_id)
            
            if not district:
                messagebox.showerror("Error", f"District not found: {district_id}")
                return
            
            # Remove influence
            if faction_id in district.faction_influence:
                district.faction_influence.pop(faction_id)
            
            # Remove stronghold
            if faction_id in district.strongholds:
                district.strongholds.pop(faction_id)
            
            # Recalculate influence pool
            district.influence_pool = 10 - district.calculate_total_influence()
            
            # Save district
            if self.district_repository.update(district):
                # Reload influence data
                self.load_influence_data(district)
            else:
                messagebox.showerror("Error", "Failed to remove faction influence")
        except Exception as e:
            logging.error(f"Error removing faction influence: {str(e)}")
            messagebox.showerror("Error", f"Failed to remove faction influence: {str(e)}")
    
    def add_adjacency(self):
        """Handle add adjacency button click."""
        # Get district ID
        district_id = self.id_var.get()
        
        if not district_id:
            messagebox.showinfo("Info", "No district selected")
            return
            
        # Create a dialog for adding adjacency
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add Adjacent District")
        dialog.geometry("300x150")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.frame.winfo_rootx() + (self.frame.winfo_width() / 2) - 150,
            self.frame.winfo_rooty() + (self.frame.winfo_height() / 2) - 75
        ))
        
        # Get districts
        try:
            # Get district
            current_district = self.district_repository.find_by_id(district_id)
            
            if not current_district:
                messagebox.showerror("Error", f"District not found: {district_id}")
                dialog.destroy()
                return
            
            # Get all districts except current and already adjacent
            all_districts = self.district_repository.find_all()
            
            district_dict = {}
            for district in all_districts:
                if district.id != district_id and district.id not in current_district.adjacent_districts:
                    district_dict[district.name] = district.id
            
            if not district_dict:
                messagebox.showinfo("Info", "No more districts available to add as adjacent")
                dialog.destroy()
                return
            
            # District field
            ttk.Label(dialog, text="District:").grid(
                row=0, column=0, sticky=tk.W, padx=10, pady=10
            )
            
            district_var = tk.StringVar()
            district_combo = ttk.Combobox(
                dialog, 
                textvariable=district_var,
                values=list(district_dict.keys()),
                width=25,
                state="readonly"
            )
            district_combo.grid(row=0, column=1, padx=10, pady=10)
            
            # Button frame
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=1, column=0, columnspan=2, pady=10)
            
            # Add button
            add_button = ttk.Button(
                button_frame, 
                text="Add", 
                command=lambda: self.add_adjacent_district(
                    district_id, 
                    district_dict.get(district_var.get()), 
                    dialog
                )
            )
            add_button.pack(side=tk.LEFT, padx=5)
            
            # Cancel button
            cancel_button = ttk.Button(
                button_frame, 
                text="Cancel", 
                command=dialog.destroy
            )
            cancel_button.pack(side=tk.LEFT, padx=5)
        except Exception as e:
            logging.error(f"Error loading districts: {str(e)}")
            messagebox.showerror("Error", f"Failed to load districts: {str(e)}")
            dialog.destroy()
    
    def add_adjacent_district(self, district_id, adjacent_id, dialog):
        """Add an adjacent district.
        
        Args:
            district_id (str): District ID.
            adjacent_id (str): Adjacent district ID.
            dialog: Dialog window to close.
        """
        if not adjacent_id:
            messagebox.showerror("Error", "Please select a district")
            return
            
        try:
            # Get district
            district = self.district_repository.find_by_id(district_id)
            
            if not district:
                messagebox.showerror("Error", f"District not found: {district_id}")
                dialog.destroy()
                return
            
            # Add adjacency
            district_updated = district.add_adjacent_district(adjacent_id)
            
            # Get adjacent district
            adjacent_district = self.district_repository.find_by_id(adjacent_id)
            
            if adjacent_district:
                # Add bidirectional adjacency
                adjacent_district.add_adjacent_district(district_id)
                adjacent_updated = self.district_repository.update(adjacent_district)
            else:
                adjacent_updated = False
            
            # Save district
            if district_updated and self.district_repository.update(district):
                # Close dialog
                dialog.destroy()
                
                # Reload adjacency data
                self.load_adjacency_data(district)
                
                # Show warning if adjacent district update failed
                if not adjacent_updated:
                    messagebox.showwarning(
                        "Warning", 
                        "Added adjacency, but failed to update the adjacent district"
                    )
            else:
                messagebox.showerror("Error", "Failed to add adjacent district")
        except Exception as e:
            logging.error(f"Error adding adjacent district: {str(e)}")
            messagebox.showerror("Error", f"Failed to add adjacent district: {str(e)}")
    
    def remove_adjacency(self):
        """Remove an adjacency relationship between districts."""
        try:
            # Get the selected item
            selection = self.adjacency_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an adjacency to remove.")
                return
            
            # Check if district is currently being edited
            if not self.current_district_id:
                messagebox.showwarning("No District", "Please select a district first.")
                return
                
            # Get selected adjacency ID
            item = self.adjacency_tree.item(selection[0])
            adjacency_id = item['values'][0]
            
            # Get district data
            district = self.district_repository.find_by_id(self.current_district_id)
            if not district:
                messagebox.showerror("Error", "District not found.")
                return
            
            # Confirm removal
            adjacent_name = item['values'][1]
            if not messagebox.askyesno("Confirm Removal", 
                                      f"Are you sure you want to remove '{adjacent_name}' as an adjacent district?"):
                return
            
            # Remove adjacency
            with self.db_manager.connection:
                query = """
                    DELETE FROM district_adjacency
                    WHERE (district_id = :district_id AND adjacent_district_id = :adjacent_id)
                    OR (district_id = :adjacent_id AND adjacent_district_id = :district_id)
                """
                
                self.db_manager.execute_update(query, {
                    "district_id": self.current_district_id,
                    "adjacent_id": adjacency_id
                })
            
            # Reload adjacency data
            self.load_adjacency_data(district)
            
            # Log success
            logging.info(f"Removed adjacency between district {self.current_district_id} and {adjacency_id}")
            
        except Exception as e:
            logging.error(f"Error removing adjacency: {str(e)}")
            messagebox.showerror("Error", f"Failed to remove adjacency: {str(e)}")
            
    def get_rumor_repository(self):
        """Get the rumor repository.
        
        Returns:
            RumorRepository: Repository for rumor operations.
        """
        return self.db_manager.get_repository("rumor")
    
    def add_rumor(self):
        """Add a new rumor to the current district."""
        try:
            # Check if district is currently being edited
            if not self.current_district_id:
                messagebox.showwarning("No District", "Please select a district first.")
                return
                
            # Get district data
            district = self.district_repository.find_by_id(self.current_district_id)
            if not district:
                messagebox.showerror("Error", "District not found.")
                return
                
            # Create a dialog for adding a rumor
            dialog = tk.Toplevel(self.frame)
            dialog.title("Add Rumor")
            dialog.geometry("500x300")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            # Add form fields
            ttk.Label(dialog, text="Rumor Text:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            
            text_frame = ttk.Frame(dialog)
            text_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
            
            rumor_text = tk.Text(text_frame, height=5, width=50)
            rumor_text.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(dialog, text="Discovery DC:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
            
            dc_var = tk.IntVar(value=15)
            discovery_dc = ttk.Spinbox(dialog, from_=1, to=30, textvariable=dc_var)
            discovery_dc.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
            
            # Configure dialog grid
            dialog.columnconfigure(1, weight=1)
            dialog.rowconfigure(0, weight=1)
            
            # Add buttons
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.E)
            
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
            def save_rumor():
                """Save the rumor and close the dialog."""
                try:
                    text = rumor_text.get("1.0", tk.END).strip()
                    dc = dc_var.get()
                    
                    if not text:
                        messagebox.showwarning("Validation Error", "Rumor text is required.")
                        return
                        
                    # Create rumor
                    rumor = Rumor(
                        district_id=district.id,
                        rumor_text=text,
                        discovery_dc=dc,
                        is_discovered=False
                    )
                    
                    # Get rumor repository
                    rumor_repository = self.get_rumor_repository()
                    
                    # Save to database
                    if rumor_repository.create(rumor):
                        # Reload rumors data
                        self.load_rumors_data(district)
                        dialog.destroy()
                        
                        # Log success
                        logging.info(f"Added new rumor to district {district.id}")
                    else:
                        messagebox.showerror("Error", "Failed to create rumor.")
                except Exception as e:
                    logging.error(f"Error creating rumor: {str(e)}")
                    messagebox.showerror("Error", f"Failed to create rumor: {str(e)}")
            
            ttk.Button(button_frame, text="Save", command=save_rumor).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            logging.error(f"Error adding rumor: {str(e)}")
            messagebox.showerror("Error", f"Failed to add rumor: {str(e)}")
            
    def edit_rumor(self):
        """Edit an existing rumor."""
        try:
            # Get the selected item
            selection = self.rumors_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a rumor to edit.")
                return
            
            # Check if district is currently being edited
            if not self.current_district_id:
                messagebox.showwarning("No District", "Please select a district first.")
                return
                
            # Get selected rumor ID
            item = self.rumors_tree.item(selection[0])
            rumor_id = item['values'][0]
            
            # Get rumor repository
            rumor_repository = self.get_rumor_repository()
            
            # Get rumor data
            rumor = rumor_repository.find_by_id(rumor_id)
            if not rumor:
                messagebox.showerror("Error", "Rumor not found.")
                return
                
            # Create a dialog for editing the rumor
            dialog = tk.Toplevel(self.frame)
            dialog.title("Edit Rumor")
            dialog.geometry("500x300")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            # Add form fields
            ttk.Label(dialog, text="Rumor Text:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            
            text_frame = ttk.Frame(dialog)
            text_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
            
            rumor_text = tk.Text(text_frame, height=5, width=50)
            rumor_text.insert("1.0", rumor.rumor_text)
            rumor_text.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(dialog, text="Discovery DC:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
            
            dc_var = tk.IntVar(value=rumor.discovery_dc)
            discovery_dc = ttk.Spinbox(dialog, from_=1, to=30, textvariable=dc_var)
            discovery_dc.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
            
            ttk.Label(dialog, text="Is Discovered:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
            
            is_discovered_var = tk.BooleanVar(value=rumor.is_discovered)
            is_discovered = ttk.Checkbutton(dialog, variable=is_discovered_var)
            is_discovered.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
            
            # Configure dialog grid
            dialog.columnconfigure(1, weight=1)
            dialog.rowconfigure(0, weight=1)
            
            # Add buttons
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.E)
            
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
            def save_rumor():
                """Save the edited rumor and close the dialog."""
                try:
                    text = rumor_text.get("1.0", tk.END).strip()
                    dc = dc_var.get()
                    is_disc = is_discovered_var.get()
                    
                    if not text:
                        messagebox.showwarning("Validation Error", "Rumor text is required.")
                        return
                        
                    # Update rumor
                    rumor.rumor_text = text
                    rumor.discovery_dc = dc
                    rumor.is_discovered = is_disc
                    
                    # Save to database
                    if rumor_repository.update(rumor):
                        # Get district data
                        district = self.district_repository.find_by_id(self.current_district_id)
                        
                        # Reload rumors data
                        self.load_rumors_data(district)
                        dialog.destroy()
                        
                        # Log success
                        logging.info(f"Updated rumor {rumor.id} in district {district.id}")
                    else:
                        messagebox.showerror("Error", "Failed to update rumor.")
                except Exception as e:
                    logging.error(f"Error updating rumor: {str(e)}")
                    messagebox.showerror("Error", f"Failed to update rumor: {str(e)}")
            
            ttk.Button(button_frame, text="Save", command=save_rumor).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            logging.error(f"Error editing rumor: {str(e)}")
            messagebox.showerror("Error", f"Failed to edit rumor: {str(e)}")
            
    def remove_rumor(self):
        """Remove a rumor from the current district."""
        try:
            # Get the selected item
            selection = self.rumors_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a rumor to remove.")
                return
            
            # Check if district is currently being edited
            if not self.current_district_id:
                messagebox.showwarning("No District", "Please select a district first.")
                return
                
            # Get selected rumor ID
            item = self.rumors_tree.item(selection[0])
            rumor_id = item['values'][0]
            rumor_text = item['values'][1]
            
            # Confirm removal
            if not messagebox.askyesno("Confirm Removal", 
                                      f"Are you sure you want to remove this rumor?"):
                return
            
            # Get rumor repository
            rumor_repository = self.get_rumor_repository()
            
            # Remove rumor using the repository
            if rumor_repository.delete(rumor_id):
                # Get district data
                district = self.district_repository.find_by_id(self.current_district_id)
                
                # Reload rumors data
                self.load_rumors_data(district)
                
                # Log success
                logging.info(f"Removed rumor {rumor_id} from district {self.current_district_id}")
            else:
                messagebox.showerror("Error", "Failed to remove rumor.")
            
        except Exception as e:
            logging.error(f"Error removing rumor: {str(e)}")
            messagebox.showerror("Error", f"Failed to remove rumor: {str(e)}")