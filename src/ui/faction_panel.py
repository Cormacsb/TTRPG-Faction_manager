import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import logging


class FactionPanel:
    """Panel for managing factions."""
    
    def __init__(self, parent, db_manager, faction_repository, district_repository):
        """Initialize the faction panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            faction_repository: Repository for faction operations.
            district_repository: Repository for district operations.
        """
        self.parent = parent
        self.db_manager = db_manager
        self.faction_repository = faction_repository
        self.district_repository = district_repository
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create panel layout
        self.create_layout()
        
        # Load initial data
        self.load_factions()
    
    def create_layout(self):
        """Create the panel layout."""
        # Split into left and right panes
        self.paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left pane for faction list
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=1)
        
        # Right pane for faction details
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=2)
        
        # Create faction list
        self.create_faction_list()
        
        # Create faction detail form
        self.create_faction_detail_form()
    
    def create_faction_list(self):
        """Create the faction list component."""
        # List frame
        self.list_frame = ttk.LabelFrame(self.left_frame, text="Factions")
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Faction treeview
        self.faction_tree = ttk.Treeview(
            self.list_frame, 
            columns=("faction_id", "name", "color"),
            show="headings",
            selectmode="browse"
        )
        self.faction_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        self.faction_tree.heading("faction_id", text="ID")
        self.faction_tree.heading("name", text="Name")
        self.faction_tree.heading("color", text="Color")
        
        self.faction_tree.column("faction_id", width=0, stretch=False)  # Hide ID column
        self.faction_tree.column("name", width=150)
        self.faction_tree.column("color", width=50)
        
        # Scrollbar
        self.tree_scrollbar = ttk.Scrollbar(
            self.list_frame, 
            orient=tk.VERTICAL, 
            command=self.faction_tree.yview
        )
        self.tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.faction_tree.configure(yscrollcommand=self.tree_scrollbar.set)
        
        # Bind selection event
        self.faction_tree.bind("<<TreeviewSelect>>", self.on_faction_select)
        
        # Button frame
        self.list_button_frame = ttk.Frame(self.left_frame)
        self.list_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add button
        self.add_button = ttk.Button(
            self.list_button_frame, 
            text="Add Faction", 
            command=self.add_faction
        )
        self.add_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Delete button
        self.delete_button = ttk.Button(
            self.list_button_frame, 
            text="Delete Faction", 
            command=self.delete_faction
        )
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def create_faction_detail_form(self):
        """Create the faction detail form."""
        # Detail frame
        self.detail_frame = ttk.LabelFrame(self.right_frame, text="Faction Details")
        self.detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create info section
        self.info_frame = ttk.Frame(self.detail_frame)
        self.info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Organize in grid
        self.info_frame.columnconfigure(1, weight=1)
        self.info_frame.columnconfigure(3, weight=1)
        
        # Faction name
        ttk.Label(self.info_frame, text="Name:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(self.info_frame, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Faction ID (display only)
        ttk.Label(self.info_frame, text="ID:").grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.id_var = tk.StringVar()
        id_entry = ttk.Entry(self.info_frame, textvariable=self.id_var, state="readonly")
        id_entry.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=5)
        
        # Faction color
        ttk.Label(self.info_frame, text="Color:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        # Color frame with custom canvas
        self.color_frame = ttk.Frame(self.info_frame)
        self.color_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.color_var = tk.StringVar(value="#3498db")  # Default blue
        self.color_canvas = tk.Canvas(self.color_frame, width=30, height=20, bd=1, relief=tk.SUNKEN)
        self.color_canvas.pack(side=tk.LEFT)
        self.color_canvas.bind("<Button-1>", self.choose_color)
        
        self.color_button = ttk.Button(
            self.color_frame, 
            text="Choose Color", 
            command=self.choose_color
        )
        self.color_button.pack(side=tk.LEFT, padx=5)
        
        # Monitoring bonus
        ttk.Label(self.info_frame, text="Monitoring Bonus:").grid(
            row=1, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.monitoring_bonus_var = tk.IntVar()
        monitoring_bonus_spinner = ttk.Spinbox(
            self.info_frame, 
            from_=-5, 
            to=10, 
            textvariable=self.monitoring_bonus_var, 
            width=5
        )
        monitoring_bonus_spinner.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Faction description
        ttk.Label(self.info_frame, text="Description:").grid(
            row=2, column=0, sticky=tk.NW, padx=5, pady=5
        )
        
        self.description_text = tk.Text(self.info_frame, height=3, width=40)
        self.description_text.grid(
            row=2, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=5
        )
        
        # Create tab control
        self.tab_control = ttk.Notebook(self.detail_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Relationships tab
        self.relationships_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(self.relationships_frame, text="Relationships")
        
        # Resources tab
        self.resources_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(self.resources_frame, text="Resources")
        
        # Create relationships table
        self.create_relationships_table()
        
        # Create resources table
        self.create_resources_table()
        
        # Save button
        self.save_button = ttk.Button(
            self.detail_frame, 
            text="Save Changes", 
            command=self.save_faction
        )
        self.save_button.pack(side=tk.RIGHT, padx=10, pady=10)
    
    def create_relationships_table(self):
        """Create the relationships table."""
        # Relationships treeview
        self.relationships_tree = ttk.Treeview(
            self.relationships_frame, 
            columns=("faction_id", "faction_name", "relationship"),
            show="headings"
        )
        self.relationships_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        self.relationships_tree.heading("faction_id", text="ID")
        self.relationships_tree.heading("faction_name", text="Faction")
        self.relationships_tree.heading("relationship", text="Relationship")
        
        self.relationships_tree.column("faction_id", width=0, stretch=False)  # Hide ID column
        self.relationships_tree.column("faction_name", width=150)
        self.relationships_tree.column("relationship", width=150, anchor=tk.CENTER)
        
        # Button frame
        self.relationships_button_frame = ttk.Frame(self.relationships_frame)
        self.relationships_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Edit relationship button
        self.edit_relationship_button = ttk.Button(
            self.relationships_button_frame, 
            text="Edit Relationship", 
            command=self.edit_relationship
        )
        self.edit_relationship_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def create_resources_table(self):
        """Create the influence metrics table."""
        # Resources treeview
        self.resources_tree = ttk.Treeview(
            self.resources_frame, 
            columns=("district_name", "commerce", "aristocratic", "muster", "total"),
            show="headings"
        )
        self.resources_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        self.resources_tree.heading("district_name", text="District")
        self.resources_tree.heading("commerce", text="Commerce")
        self.resources_tree.heading("aristocratic", text="Aristocratic")
        self.resources_tree.heading("muster", text="Muster")
        self.resources_tree.heading("total", text="Total")
        
        self.resources_tree.column("district_name", width=150)
        self.resources_tree.column("commerce", width=80, anchor=tk.CENTER)
        self.resources_tree.column("aristocratic", width=80, anchor=tk.CENTER)
        self.resources_tree.column("muster", width=80, anchor=tk.CENTER)
        self.resources_tree.column("total", width=80, anchor=tk.CENTER)
        
        # Add a totals row at the bottom with a separate display
        self.metrics_totals_frame = ttk.Frame(self.resources_frame)
        self.metrics_totals_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create labels for totals
        ttk.Label(self.metrics_totals_frame, text="TOTALS:", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        
        self.commerce_total_var = tk.StringVar(value="0")
        self.aristocratic_total_var = tk.StringVar(value="0")
        self.muster_total_var = tk.StringVar(value="0")
        self.grand_total_var = tk.StringVar(value="0")
        
        ttk.Label(self.metrics_totals_frame, text="Commerce Total:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(self.metrics_totals_frame, textvariable=self.commerce_total_var, font=("Arial", 9, "bold")).grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        
        ttk.Label(self.metrics_totals_frame, text="Aristocratic Total:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(self.metrics_totals_frame, textvariable=self.aristocratic_total_var, font=("Arial", 9, "bold")).grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        
        ttk.Label(self.metrics_totals_frame, text="Muster Total:").grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(self.metrics_totals_frame, textvariable=self.muster_total_var, font=("Arial", 9, "bold")).grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        
        ttk.Label(self.metrics_totals_frame, text="GRAND TOTAL:").grid(row=4, column=0, padx=5, pady=2, sticky=tk.W)
        ttk.Label(self.metrics_totals_frame, textvariable=self.grand_total_var, font=("Arial", 9, "bold")).grid(row=4, column=1, padx=5, pady=2, sticky=tk.W)
        
        # Button frame
        self.resources_button_frame = ttk.Frame(self.resources_frame)
        self.resources_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Export CSV button
        self.export_csv_button = ttk.Button(
            self.resources_button_frame, 
            text="Export to CSV", 
            command=self.export_metrics_to_csv
        )
        self.export_csv_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def load_factions(self):
        """Load factions into the list."""
        try:
            # Clear existing items
            for item in self.faction_tree.get_children():
                self.faction_tree.delete(item)
            
            # Get all factions
            factions = self.faction_repository.find_all()
            
            for faction in factions:
                # Add color display
                color = faction.color
                
                self.faction_tree.insert(
                    "", 
                    tk.END, 
                    values=(faction.id, faction.name, ""),
                    tags=(color,)
                )
                
                # Configure color tag
                self.faction_tree.tag_configure(color, background=color)
        except Exception as e:
            logging.error(f"Error loading factions: {str(e)}")
            messagebox.showerror("Error", f"Failed to load factions: {str(e)}")
    
    def load_faction_details(self, faction_id):
        """Load faction details into the form.
        
        Args:
            faction_id (str): Faction ID to load.
        """
        try:
            # Get faction
            faction = self.faction_repository.find_by_id(faction_id)
            
            if not faction:
                messagebox.showerror("Error", f"Faction not found: {faction_id}")
                return
            
            # Set form values
            self.id_var.set(faction.id)
            self.name_var.set(faction.name)
            self.color_var.set(faction.color)
            self.monitoring_bonus_var.set(faction.monitoring_bonus)
            
            # Update color display
            self.update_color_display(faction.color)
            
            # Set description
            self.description_text.delete(1.0, tk.END)
            if faction.description:
                self.description_text.insert(1.0, faction.description)
            
            # Load relationships data
            self.load_relationships_data(faction)
            
            # Load resources data
            self.load_resources_data(faction)
        except Exception as e:
            logging.error(f"Error loading faction details: {str(e)}")
            messagebox.showerror("Error", f"Failed to load faction details: {str(e)}")
    
    def load_relationships_data(self, faction):
        """Load relationships data for a faction.
        
        Args:
            faction: Faction instance.
        """
        try:
            # Clear existing items
            for item in self.relationships_tree.get_children():
                self.relationships_tree.delete(item)
            
            # No relationships data
            if not faction.relationships:
                return
            
            # Get faction names
            faction_names = {}
            
            query = "SELECT id, name FROM factions"
            factions = self.db_manager.execute_query(query)
            
            for f in factions:
                faction_names[f["id"]] = f["name"]
            
            # Add relationship entries
            for target_id, value in faction.relationships.items():
                faction_name = faction_names.get(target_id, "Unknown Faction")
                
                # Convert value to display text
                relationship_text = self.get_relationship_text(value)
                
                self.relationships_tree.insert(
                    "", 
                    tk.END, 
                    values=(target_id, faction_name, relationship_text)
                )
        except Exception as e:
            logging.error(f"Error loading relationships data: {str(e)}")
            raise
    
    def load_resources_data(self, faction):
        """Load influence metrics data for a faction.
        
        Args:
            faction: Faction instance.
        """
        try:
            # Clear existing items
            for item in self.resources_tree.get_children():
                self.resources_tree.delete(item)
            
            # Get all districts
            districts = self.district_repository.find_all()
            
            # Calculate metrics
            commerce_total = 0
            aristocratic_total = 0
            muster_total = 0
            grand_total = 0
            
            # Add entries for each district
            for district in districts:
                # Get faction influence in this district
                influence = district.get_faction_influence(faction.id)
                
                if influence > 0:
                    # Calculate weighted values
                    commerce = influence * district.commerce_value
                    aristocratic = influence * district.aristocratic_value
                    muster = influence * district.muster_value
                    total = commerce + aristocratic + muster
                    
                    # Add to totals
                    commerce_total += commerce
                    aristocratic_total += aristocratic
                    muster_total += muster
                    grand_total += total
                    
                    # Add to tree
                    self.resources_tree.insert(
                        "", 
                        tk.END, 
                        values=(district.name, commerce, aristocratic, muster, total)
                    )
            
            # Update totals display
            self.commerce_total_var.set(str(commerce_total))
            self.aristocratic_total_var.set(str(aristocratic_total))
            self.muster_total_var.set(str(muster_total))
            self.grand_total_var.set(str(grand_total))
            
        except Exception as e:
            logging.error(f"Error loading influence metrics data: {str(e)}")
            raise
    
    def update_color_display(self, color):
        """Update the color display with the selected color.
        
        Args:
            color (str): Color hex code.
        """
        try:
            self.color_canvas.delete("all")
            self.color_canvas.create_rectangle(0, 0, 30, 20, fill=color, outline="black")
        except Exception as e:
            logging.error(f"Error updating color display: {str(e)}")
    
    def get_relationship_text(self, value):
        """Convert relationship value to display text.
        
        Args:
            value (int): Relationship value (-2 to +2).
            
        Returns:
            str: Relationship text.
        """
        if value == -2:
            return "Hot War (-2)"
        elif value == -1:
            return "Cold War (-1)"
        elif value == 0:
            return "Neutral (0)"
        elif value == 1:
            return "Friendly (+1)"
        elif value == 2:
            return "Allied (+2)"
        else:
            return f"Unknown ({value})"
    
    def get_relationship_value(self, text):
        """Convert relationship text to value.
        
        Args:
            text (str): Relationship text.
            
        Returns:
            int: Relationship value (-2 to +2).
        """
        if "Hot War" in text or "-2" in text:
            return -2
        elif "Cold War" in text or "-1" in text:
            return -1
        elif "Neutral" in text or "0" in text:
            return 0
        elif "Friendly" in text or "+1" in text:
            return 1
        elif "Allied" in text or "+2" in text:
            return 2
        else:
            try:
                # Try to extract number
                import re
                match = re.search(r"[-+]?\d+", text)
                if match:
                    return int(match.group())
                else:
                    return 0
            except:
                return 0
    
    def on_faction_select(self, event):
        """Handle faction selection event.
        
        Args:
            event: Event object.
        """
        # Get selected item
        selection = self.faction_tree.selection()
        
        if not selection:
            return
            
        # Get faction ID
        faction_id = self.faction_tree.item(selection[0], "values")[0]
        
        # Load faction details
        self.load_faction_details(faction_id)
    
    def choose_color(self, event=None):
        """Open color chooser dialog."""
        # Get current color
        current_color = self.color_var.get()
        
        # Open color chooser
        color = colorchooser.askcolor(initialcolor=current_color)
        
        # Update color if selected
        if color[1]:
            self.color_var.set(color[1])
            self.update_color_display(color[1])
    
    def add_faction(self):
        """Handle add faction button click."""
        # Create a simple dialog for new faction
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add Faction")
        dialog.geometry("300x120")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.frame.winfo_rootx() + (self.frame.winfo_width() / 2) - 150,
            self.frame.winfo_rooty() + (self.frame.winfo_height() / 2) - 60
        ))
        
        # Name field
        ttk.Label(dialog, text="Faction Name:").grid(
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
            command=lambda: self.create_faction(name_var.get(), dialog)
        )
        create_button.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    def create_faction(self, name, dialog):
        """Create a new faction.
        
        Args:
            name (str): Faction name.
            dialog: Dialog window to close.
        """
        if not name:
            messagebox.showerror("Error", "Faction name is required")
            return
            
        try:
            # Create faction with default values
            from ..models.faction import Faction
            
            # Generate a random color
            import random
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            faction = Faction(name=name, color=color)
            faction.description = ""
            faction.monitoring_bonus = 0
            
            # Save faction
            if self.faction_repository.create(faction):
                # Close dialog
                dialog.destroy()
                
                # Refresh faction list
                self.load_factions()
                
                # Select the new faction
                for item in self.faction_tree.get_children():
                    if self.faction_tree.item(item, "values")[0] == faction.id:
                        self.faction_tree.selection_set(item)
                        self.faction_tree.see(item)
                        break
                        
                # Load faction details
                self.load_faction_details(faction.id)
            else:
                messagebox.showerror("Error", "Failed to create faction")
        except Exception as e:
            logging.error(f"Error creating faction: {str(e)}")
            messagebox.showerror("Error", f"Failed to create faction: {str(e)}")
    
    def delete_faction(self):
        """Handle delete faction button click."""
        # Get selected item
        selection = self.faction_tree.selection()
        
        if not selection:
            messagebox.showinfo("Info", "Please select a faction to delete")
            return
            
        # Get faction ID
        faction_id = self.faction_tree.item(selection[0], "values")[0]
        faction_name = self.faction_tree.item(selection[0], "values")[1]
        
        # Confirm deletion
        if not messagebox.askyesno(
            "Confirm Delete", 
            f"Are you sure you want to delete faction '{faction_name}'?"
        ):
            return
            
        try:
            # Check if faction has any influence
            query = """
                SELECT d.name
                FROM district_influence di
                JOIN districts d ON d.id = di.district_id
                WHERE di.faction_id = :faction_id
                LIMIT 1
            """
            
            has_influence = self.db_manager.execute_query(query, {"faction_id": faction_id})
            
            if has_influence:
                district_name = has_influence[0]["name"]
                messagebox.showerror(
                    "Error", 
                    f"Cannot delete faction with influence. " +
                    f"This faction has influence in district '{district_name}'."
                )
                return
            
            # Check if faction has any agents
            query = "SELECT COUNT(*) as count FROM agents WHERE faction_id = :faction_id"
            agent_count = self.db_manager.execute_query(query, {"faction_id": faction_id})
            
            if agent_count and agent_count[0]["count"] > 0:
                messagebox.showerror(
                    "Error", 
                    f"Cannot delete faction with agents. " +
                    f"This faction has {agent_count[0]['count']} agents."
                )
                return
            
            # Check if faction has any squadrons
            query = "SELECT COUNT(*) as count FROM squadrons WHERE faction_id = :faction_id"
            squadron_count = self.db_manager.execute_query(query, {"faction_id": faction_id})
            
            if squadron_count and squadron_count[0]["count"] > 0:
                messagebox.showerror(
                    "Error", 
                    f"Cannot delete faction with squadrons. " +
                    f"This faction has {squadron_count[0]['count']} squadrons."
                )
                return
            
            # Delete faction
            if self.faction_repository.delete(faction_id):
                # Refresh faction list
                self.load_factions()
                
                # Clear form
                self.clear_form()
            else:
                messagebox.showerror("Error", "Failed to delete faction")
        except Exception as e:
            logging.error(f"Error deleting faction: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete faction: {str(e)}")
    
    def clear_form(self):
        """Clear the faction detail form."""
        self.id_var.set("")
        self.name_var.set("")
        self.color_var.set("#3498db")  # Default blue
        self.update_color_display("#3498db")
        self.monitoring_bonus_var.set(0)
        self.description_text.delete(1.0, tk.END)
        
        # Clear tables
        for item in self.relationships_tree.get_children():
            self.relationships_tree.delete(item)
            
        for item in self.resources_tree.get_children():
            self.resources_tree.delete(item)
    
    def save_faction(self):
        """Handle save faction button click."""
        # Get faction ID
        faction_id = self.id_var.get()
        
        if not faction_id:
            messagebox.showinfo("Info", "No faction selected")
            return
            
        try:
            # Get faction
            faction = self.faction_repository.find_by_id(faction_id)
            
            if not faction:
                messagebox.showerror("Error", f"Faction not found: {faction_id}")
                return
            
            # Update faction with form values
            faction.name = self.name_var.get()
            faction.color = self.color_var.get()
            faction.monitoring_bonus = self.monitoring_bonus_var.get()
            faction.description = self.description_text.get(1.0, tk.END).strip()
            
            # Save faction
            if self.faction_repository.update(faction):
                messagebox.showinfo("Success", "Faction saved successfully")
                
                # Refresh faction list to update name
                self.load_factions()
                
                # Select the faction again
                for item in self.faction_tree.get_children():
                    if self.faction_tree.item(item, "values")[0] == faction_id:
                        self.faction_tree.selection_set(item)
                        break
            else:
                messagebox.showerror("Error", "Failed to save faction")
        except Exception as e:
            logging.error(f"Error saving faction: {str(e)}")
            messagebox.showerror("Error", f"Failed to save faction: {str(e)}")
    
    def edit_relationship(self):
        """Handle edit relationship button click."""
        # Get faction ID
        faction_id = self.id_var.get()
        
        if not faction_id:
            messagebox.showinfo("Info", "No faction selected")
            return
            
        # Get selected relationship
        selection = self.relationships_tree.selection()
        
        if not selection:
            # No relationship selected, show a list of all factions
            try:
                # Get faction
                faction = self.faction_repository.find_by_id(faction_id)
                
                if not faction:
                    messagebox.showerror("Error", f"Faction not found: {faction_id}")
                    return
                
                # Get all other factions
                query = "SELECT id, name FROM factions WHERE id != :faction_id"
                factions = self.db_manager.execute_query(query, {"faction_id": faction_id})
                
                if not factions:
                    messagebox.showinfo("Info", "No other factions available")
                    return
                
                # Create a dialog for selecting a faction
                dialog = tk.Toplevel(self.frame)
                dialog.title("Select Faction")
                dialog.geometry("300x250")
                dialog.transient(self.frame)
                dialog.grab_set()
                
                # Center the dialog
                dialog.geometry("+%d+%d" % (
                    self.frame.winfo_rootx() + (self.frame.winfo_width() / 2) - 150,
                    self.frame.winfo_rooty() + (self.frame.winfo_height() / 2) - 125
                ))
                
                # Instructions
                ttk.Label(dialog, text="Select a faction to set relationship:").pack(padx=10, pady=10)
                
                # Create a listbox
                faction_listbox = tk.Listbox(dialog, height=10, width=30)
                faction_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                
                # Populate listbox
                faction_dict = {}
                for f in factions:
                    faction_dict[f["name"]] = f["id"]
                    faction_listbox.insert(tk.END, f["name"])
                
                # Button frame
                button_frame = ttk.Frame(dialog)
                button_frame.pack(fill=tk.X, padx=10, pady=10)
                
                # Select button
                select_button = ttk.Button(
                    button_frame, 
                    text="Select", 
                    command=lambda: self.show_relationship_dialog(
                        faction_id, 
                        faction_dict[faction_listbox.get(faction_listbox.curselection()[0])], 
                        dialog
                    ) if faction_listbox.curselection() else None
                )
                select_button.pack(side=tk.LEFT, padx=5)
                
                # Cancel button
                cancel_button = ttk.Button(
                    button_frame, 
                    text="Cancel", 
                    command=dialog.destroy
                )
                cancel_button.pack(side=tk.LEFT, padx=5)
            except Exception as e:
                logging.error(f"Error showing faction selection: {str(e)}")
                messagebox.showerror("Error", f"Failed to show faction selection: {str(e)}")
        else:
            # Get relationship data
            target_id = self.relationships_tree.item(selection[0], "values")[0]
            target_name = self.relationships_tree.item(selection[0], "values")[1]
            relationship_text = self.relationships_tree.item(selection[0], "values")[2]
            
            # Show relationship dialog
            self.show_relationship_dialog(faction_id, target_id, None, target_name, relationship_text)
    
    def show_relationship_dialog(self, faction_id, target_id, parent_dialog=None, 
                               target_name=None, relationship_text=None):
        """Show dialog for editing relationship.
        
        Args:
            faction_id (str): Faction ID.
            target_id (str): Target faction ID.
            parent_dialog: Parent dialog to close. Defaults to None.
            target_name (str, optional): Target faction name. Defaults to None.
            relationship_text (str, optional): Current relationship text. Defaults to None.
        """
        try:
            # Get faction and target faction
            faction = self.faction_repository.find_by_id(faction_id)
            target_faction = self.faction_repository.find_by_id(target_id)
            
            if not faction or not target_faction:
                if parent_dialog:
                    parent_dialog.destroy()
                messagebox.showerror("Error", "Faction not found")
                return
            
            # Close parent dialog if provided
            if parent_dialog:
                parent_dialog.destroy()
            
            # Get target name if not provided
            if not target_name:
                target_name = target_faction.name
            
            # Get current relationship
            current_value = faction.get_relationship(target_id)
            
            # Create a dialog for editing relationship
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Edit Relationship with {target_name}")
            dialog.geometry("300x150")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            # Center the dialog
            dialog.geometry("+%d+%d" % (
                self.frame.winfo_rootx() + (self.frame.winfo_width() / 2) - 150,
                self.frame.winfo_rooty() + (self.frame.winfo_height() / 2) - 75
            ))
            
            # Relationship field
            ttk.Label(dialog, text="Relationship:").grid(
                row=0, column=0, sticky=tk.W, padx=10, pady=10
            )
            
            relationship_var = tk.StringVar()
            relationship_combo = ttk.Combobox(
                dialog, 
                textvariable=relationship_var,
                values=[
                    "Hot War (-2)",
                    "Cold War (-1)",
                    "Neutral (0)",
                    "Friendly (+1)",
                    "Allied (+2)"
                ],
                width=15,
                state="readonly"
            )
            relationship_combo.grid(row=0, column=1, padx=10, pady=10)
            
            # Set current value
            relationship_combo.set(self.get_relationship_text(current_value))
            
            # Button frame
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=1, column=0, columnspan=2, pady=10)
            
            # Update button
            update_button = ttk.Button(
                button_frame, 
                text="Update", 
                command=lambda: self.update_relationship(
                    faction_id, 
                    target_id, 
                    self.get_relationship_value(relationship_var.get()),
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
        except Exception as e:
            logging.error(f"Error showing relationship dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to show relationship dialog: {str(e)}")
    
    def update_relationship(self, faction_id, target_id, value, dialog):
        """Update relationship between factions.
        
        Args:
            faction_id (str): Faction ID.
            target_id (str): Target faction ID.
            value (int): Relationship value (-2 to +2).
            dialog: Dialog window to close.
        """
        try:
            # Get faction and target faction
            faction = self.faction_repository.find_by_id(faction_id)
            target_faction = self.faction_repository.find_by_id(target_id)
            
            if not faction or not target_faction:
                dialog.destroy()
                messagebox.showerror("Error", "Faction not found")
                return
            
            # Update relationship
            faction.set_relationship(target_id, value)
            
            # Save faction
            if self.faction_repository.update(faction):
                # Close dialog
                dialog.destroy()
                
                # Reload relationships data
                self.load_relationships_data(faction)
                
                # Update reciprocal relationship
                target_faction.set_relationship(faction_id, value)
                self.faction_repository.update(target_faction)
            else:
                messagebox.showerror("Error", "Failed to update relationship")
        except Exception as e:
            logging.error(f"Error updating relationship: {str(e)}")
            messagebox.showerror("Error", f"Failed to update relationship: {str(e)}")
    
    def export_metrics_to_csv(self):
        """Export faction metrics to CSV file."""
        try:
            # Get faction ID
            faction_id = self.id_var.get()
            
            if not faction_id:
                messagebox.showinfo("Info", "No faction selected")
                return
                
            # Get faction
            faction = self.faction_repository.find_by_id(faction_id)
            
            if not faction:
                messagebox.showerror("Error", f"Faction not found: {faction_id}")
                return
            
            # Create file dialog
            from tkinter import filedialog
            import csv
            import os
            from datetime import datetime
            
            # Get current turn
            try:
                query = "SELECT value FROM game_state WHERE key = 'current_turn'"
                result = self.db_manager.execute_query(query)
                current_turn = int(result[0]["value"]) if result else 1
            except:
                current_turn = 1
            
            # Default filename
            default_filename = f"{faction.name.replace(' ', '_')}_metrics_turn_{current_turn}.csv"
            
            # Ask for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if not file_path:
                return  # User canceled
            
            # Get all factions
            all_factions = self.faction_repository.find_all()
            
            # Get all districts
            all_districts = self.district_repository.find_all()
            
            # Calculate metrics for all factions
            metrics_data = []
            
            for f in all_factions:
                commerce_total = 0
                aristocratic_total = 0
                muster_total = 0
                grand_total = 0
                
                for district in all_districts:
                    influence = district.get_faction_influence(f.id)
                    
                    if influence > 0:
                        commerce = influence * district.commerce_value
                        aristocratic = influence * district.aristocratic_value
                        muster = influence * district.muster_value
                        total = commerce + aristocratic + muster
                        
                        commerce_total += commerce
                        aristocratic_total += aristocratic
                        muster_total += muster
                        grand_total += total
                
                metrics_data.append({
                    "faction_id": f.id,
                    "faction_name": f.name,
                    "commerce_total": commerce_total,
                    "aristocratic_total": aristocratic_total,
                    "muster_total": muster_total,
                    "grand_total": grand_total,
                    "turn_number": current_turn,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Write to CSV
            with open(file_path, 'w', newline='') as csvfile:
                fieldnames = ["faction_name", "commerce_total", "aristocratic_total", 
                              "muster_total", "grand_total", "turn_number", "timestamp"]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for data in metrics_data:
                    writer.writerow({k: data[k] for k in fieldnames})
            
            messagebox.showinfo("Success", f"Metrics exported to {file_path}")
            
        except Exception as e:
            logging.error(f"Error exporting metrics to CSV: {str(e)}")
            messagebox.showerror("Error", f"Failed to export metrics: {str(e)}")