import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog, simpledialog
import json
import uuid
import math
from datetime import datetime
from PIL import Image, ImageTk
import io
import logging
from ..models.district import District


class MapPanel(ttk.Frame):
    """Panel for map visualization and editing."""
    
    def __init__(self, parent, db_manager, district_repository, faction_repository):
        """Initialize the map panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
        """
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        
        # Initialize state variables
        self.base_map_image = None
        self.base_map_photoimage = None
        self.districts = {}
        self.factions = {}
        self.selected_district_id = None
        self.editing_mode = False
        self.drawing_district = False
        self.current_shape_points = []
        self.edit_selected_point = None
        self.map_config = self._load_map_configuration()
        
        # Store current map dimensions for relative coordinate calculations
        self.original_map_width = self.map_config.get("map_width", 800)
        self.original_map_height = self.map_config.get("map_height", 600)
        
        # Store district IDs for listbox
        self.district_listbox_ids = []
        
        # Drawing parameters - all configurable sizes grouped here for easy access
        self.district_fill_alpha = 0.3  # Transparency for district fill
        self.district_border_width = 2
        self.selected_district_border_width = 3
        
        # Configurable visualization sizes
        self.district_name_font_size = 10  # Base font size for district names
        self.confidence_text_font_size = 8  # Base font size for confidence text
        self.influence_dot_radius = 5      # Size of influence dots
        self.stronghold_size = 10          # Size of stronghold stars
        
        # Zoom and pan state
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # View state
        self.current_view = "dm"  # "dm" or "faction"
        self.view_faction_id = None
        
        self._create_widgets()
        self._bind_events()
        self._load_data()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Create main layout frames
        self.sidebar_frame = ttk.Frame(self, padding="10 10 10 10", width=250)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)  # Fixed width
        
        self.map_frame = ttk.Frame(self)
        self.map_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Add controls to sidebar
        ttk.Label(self.sidebar_frame, text="Map Controls", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        ttk.Separator(self.sidebar_frame).pack(fill=tk.X, pady=5)
        
        # Base Map selection
        ttk.Label(self.sidebar_frame, text="Base Map:").pack(anchor=tk.W, pady=(10, 5))
        base_map_frame = ttk.Frame(self.sidebar_frame)
        base_map_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(base_map_frame, text="Select Base Map", command=self._select_base_map).pack(side=tk.LEFT)
        self.base_map_label = ttk.Label(self.sidebar_frame, text="No base map selected", font=("Arial", 8))
        self.base_map_label.pack(anchor=tk.W)
        
        ttk.Separator(self.sidebar_frame).pack(fill=tk.X, pady=5)
        
        # View mode selection
        ttk.Label(self.sidebar_frame, text="View Mode:").pack(anchor=tk.W, pady=(10, 5))
        self.view_mode_var = tk.StringVar(value="dm")
        ttk.Radiobutton(self.sidebar_frame, text="DM View", variable=self.view_mode_var, 
                       value="dm", command=self._change_view_mode).pack(anchor=tk.W)
        
        faction_frame = ttk.Frame(self.sidebar_frame)
        faction_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(faction_frame, text="Faction View:", variable=self.view_mode_var,
                       value="faction", command=self._change_view_mode).pack(side=tk.LEFT)
        
        self.faction_combobox = ttk.Combobox(faction_frame, state="readonly", width=15)
        self.faction_combobox.pack(side=tk.RIGHT)
        self.faction_combobox.bind("<<ComboboxSelected>>", self._on_faction_selected)
        
        ttk.Separator(self.sidebar_frame).pack(fill=tk.X, pady=5)
        
        # Zoom controls
        ttk.Label(self.sidebar_frame, text="Zoom:").pack(anchor=tk.W, pady=(10, 5))
        zoom_frame = ttk.Frame(self.sidebar_frame)
        zoom_frame.pack(fill=tk.X)
        
        ttk.Button(zoom_frame, text="-", width=3, command=self._zoom_out).pack(side=tk.LEFT)
        self.zoom_scale = ttk.Scale(zoom_frame, from_=0.25, to=4.0, value=1.0, 
                                   orient=tk.HORIZONTAL, command=self._on_zoom_change)
        self.zoom_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(zoom_frame, text="+", width=3, command=self._zoom_in).pack(side=tk.LEFT)
        
        self.zoom_label = ttk.Label(self.sidebar_frame, text="100%")
        self.zoom_label.pack(anchor=tk.W)
        
        ttk.Button(self.sidebar_frame, text="Reset View", command=self._reset_view).pack(anchor=tk.W, pady=5)
        
        ttk.Separator(self.sidebar_frame).pack(fill=tk.X, pady=5)
        
        # District selection
        ttk.Label(self.sidebar_frame, text="Districts:").pack(anchor=tk.W, pady=(10, 5))
        self.district_listbox = tk.Listbox(self.sidebar_frame, height=10)
        self.district_listbox.pack(fill=tk.X)
        self.district_listbox.bind("<<ListboxSelect>>", self._on_district_selected)
        
        # District editing controls
        ttk.Separator(self.sidebar_frame).pack(fill=tk.X, pady=5)
        ttk.Label(self.sidebar_frame, text="District Editing:").pack(anchor=tk.W, pady=(10, 5))
        
        self.edit_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.sidebar_frame, text="Edit Mode", variable=self.edit_mode_var,
                       command=self._toggle_edit_mode).pack(anchor=tk.W)
        
        edit_frame = ttk.Frame(self.sidebar_frame)
        edit_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(edit_frame, text="New District", command=self._start_new_district).pack(side=tk.LEFT)
        ttk.Button(edit_frame, text="Clear Points", command=self._clear_drawing_points).pack(side=tk.LEFT, padx=5)
        
        # Edit color buttons
        color_frame = ttk.Frame(self.sidebar_frame)
        color_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(color_frame, text="Fill Color", command=self._change_fill_color).pack(side=tk.LEFT)
        ttk.Button(color_frame, text="Border Color", command=self._change_border_color).pack(side=tk.LEFT, padx=5)
        
        # Save actions
        ttk.Button(self.sidebar_frame, text="Save Shape", command=self._save_district_shape).pack(anchor=tk.W, pady=5)
        
        # Export controls
        ttk.Separator(self.sidebar_frame).pack(fill=tk.X, pady=5)
        ttk.Label(self.sidebar_frame, text="Export:").pack(anchor=tk.W, pady=(10, 5))
        
        export_frame = ttk.Frame(self.sidebar_frame)
        export_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(export_frame, text="Export Current View", command=self._export_current_view).pack(side=tk.LEFT)
        ttk.Button(export_frame, text="Export All Views", command=self._export_all_views).pack(side=tk.LEFT, padx=5)
        
        # Create map canvas
        canvas_frame = ttk.Frame(self.map_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        self.h_scrollbar = ttk.Scrollbar(self.map_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = ttk.Scrollbar(self.map_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
    
    def _bind_events(self):
        """Bind UI events."""
        # Canvas mouse events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self._on_mousewheel)   # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mousewheel)   # Linux scroll down
        
        # Window resize
        self.map_frame.bind("<Configure>", self._on_window_resize)
    
    def _load_data(self):
        """Load map and district data."""
        # Load districts
        self.districts = {district.id: district for district in self.district_repository.find_all()}
        
        # Load factions
        self.factions = {faction.id: faction for faction in self.faction_repository.find_all()}
        
        # Populate district listbox
        self.district_listbox.delete(0, tk.END)
        self.district_listbox_ids = []
        for district_id, district in sorted(self.districts.items(), key=lambda x: x[1].name):
            self.district_listbox.insert(tk.END, district.name)
            self.district_listbox_ids.append(district_id)
        
        # Populate faction combobox
        self.faction_combobox['values'] = [faction.name for faction in self.factions.values()]
        
        # Load base map if available
        if self.map_config and self.map_config.get("base_map_path"):
            self._load_base_map(self.map_config["base_map_path"])
            # Update base map label
            base_map_path = self.map_config.get("base_map_path")
            if base_map_path:
                import os
                filename = os.path.basename(base_map_path)
                self.base_map_label.config(text=f"Map: {filename}")
            else:
                self.base_map_label.config(text="No base map selected")
        
        # Draw the map
        self._draw_map()
    
    def _load_map_configuration(self):
        """Load map configuration from database.
        
        Returns:
            dict: Map configuration.
        """
        try:
            logging.info("Loading map configuration from database")
            query = """
                SELECT base_map_path, map_width, map_height
                FROM map_configuration
                WHERE id = 'current'
            """
            
            result = self.db_manager.execute_query(query)
            logging.info(f"Query result: {result}")
            
            if result:
                logging.info(f"Result type: {type(result)}, Result[0] type: {type(result[0])}")
                # Use dict() constructor to convert sqlite3.Row to dict
                config = dict(result[0])
                logging.info(f"Converted config: {config}")
                return config
            else:
                # Create default config if none exists
                logging.info("No map configuration found, creating default")
                now = datetime.now().isoformat()
                
                query = """
                    INSERT INTO map_configuration (
                        id, created_at, updated_at
                    )
                    VALUES (
                        'current', :now, :now
                    )
                """
                
                with self.db_manager.connection:
                    self.db_manager.execute_update(query, {"now": now})
                
                return {"base_map_path": None, "map_width": 800, "map_height": 600}
        except Exception as e:
            print(f"Error loading map configuration: {str(e)}")
            return {"base_map_path": None, "map_width": 800, "map_height": 600}
    
    def _save_map_configuration(self, config):
        """Save map configuration to database.
        
        Args:
            config (dict): Map configuration.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            query = """
                UPDATE map_configuration SET
                    base_map_path = :base_map_path,
                    map_width = :map_width,
                    map_height = :map_height,
                    updated_at = :updated_at
                WHERE id = 'current'
            """
            
            with self.db_manager.connection:
                self.db_manager.execute_update(query, {
                    "base_map_path": config.get("base_map_path"),
                    "map_width": config.get("map_width", 800),
                    "map_height": config.get("map_height", 600),
                    "updated_at": datetime.now().isoformat()
                })
            
            return True
        except Exception as e:
            print(f"Error saving map configuration: {str(e)}")
            return False
    
    def _load_base_map(self, path):
        """Load base map image.
        
        Args:
            path (str): Path to image file.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Load image using Pillow
            self.base_map_image = Image.open(path)
            
            # Store dimensions in config
            old_width = self.map_config.get("map_width", 800)
            old_height = self.map_config.get("map_height", 600)
            new_width = self.base_map_image.width
            new_height = self.base_map_image.height
            
            # Update map config with new dimensions
            self.map_config["map_width"] = new_width
            self.map_config["map_height"] = new_height
            self._save_map_configuration(self.map_config)
            
            # Store original dimensions for coordinate calculations
            self.original_map_width = new_width
            self.original_map_height = new_height
            
            # Convert to PhotoImage for canvas
            self.base_map_photoimage = ImageTk.PhotoImage(self.base_map_image)
            
            # If dimensions have changed significantly, we might need to rescale district coordinates
            if abs(old_width - new_width) > 100 or abs(old_height - new_height) > 100:
                self._rescale_district_coordinates(old_width, old_height, new_width, new_height)
            
            return True
        except Exception as e:
            print(f"Error loading base map: {str(e)}")
            self.base_map_image = None
            self.base_map_photoimage = None
            return False
    
    def _rescale_district_coordinates(self, old_width, old_height, new_width, new_height):
        """Rescale district coordinates when base map dimensions change significantly.
        
        Args:
            old_width (int): Previous map width
            old_height (int): Previous map height
            new_width (int): New map width
            new_height (int): New map height
        """
        # Only rescale if old dimensions are valid
        if old_width <= 0 or old_height <= 0:
            return
            
        try:
            width_ratio = new_width / old_width
            height_ratio = new_height / old_height
            
            for district_id, district in self.districts.items():
                if not district.shape_data or not district.shape_data.get("points"):
                    continue
                    
                # Rescale each point
                for point in district.shape_data["points"]:
                    point["x"] = point["x"] * width_ratio
                    point["y"] = point["y"] * height_ratio
                
                # Save updated district
                self.district_repository.update(district)
                
            messagebox.showinfo("Coordinates Rescaled", 
                               "District coordinates have been rescaled to match the new base map dimensions.")
        except Exception as e:
            print(f"Error rescaling coordinates: {str(e)}")
            messagebox.showerror("Error", "Failed to rescale district coordinates.")
    
    def _draw_map(self):
        """Draw the map on the canvas."""
        # Clear existing map
        self.canvas.delete("all")
        
        # Calculate map dimensions based on base map or config
        if self.base_map_image:
            map_width = self.base_map_image.width * self.zoom_level
            map_height = self.base_map_image.height * self.zoom_level
        else:
            # Handle case where map_config might be None
            if self.map_config is None:
                logging.warning("map_config is None, using default dimensions")
                self.map_config = {"map_width": 800, "map_height": 600}
                
            # Make sure we get integer values even if the values in map_config are None
            map_width = (self.map_config.get("map_width") or 800) * self.zoom_level
            map_height = (self.map_config.get("map_height") or 600) * self.zoom_level
            logging.info(f"Using map dimensions: {map_width} x {map_height}")
        
        # Set canvas size and scrollregion
        self.canvas.config(width=map_width, height=map_height,
                          scrollregion=(0, 0, map_width, map_height))
        
        # Draw base map if available
        if self.base_map_photoimage:
            # Need to resize for zoom
            resized_image = self.base_map_image.resize(
                (int(map_width), int(map_height)),
                Image.LANCZOS
            )
            self.base_map_photoimage = ImageTk.PhotoImage(resized_image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.base_map_photoimage, tags="base_map")
        
        # Store the current map dimensions for coordinate calculations
        self.current_map_width = map_width
        self.current_map_height = map_height
        
        # Draw districts
        for district_id, district in self.districts.items():
            self._draw_district(district)
        
        # Draw influence dots and strongholds
        if self.current_view == "dm":
            # DM view shows actual influence and strongholds
            for district_id, district in self.districts.items():
                self._draw_influence_dots(district, district.faction_influence, district.strongholds)
        else:
            # Faction view shows perceived influence and strongholds
            faction = self.factions.get(self.view_faction_id)
            if faction:
                for district_id, district in self.districts.items():
                    # Get perceived influences
                    perceived_influences = faction.perceived_influence.get(district_id, {})
                    perceived_values = {}
                    for faction_id, data in perceived_influences.items():
                        perceived_values[faction_id] = data.get("value", 0)
                    
                    # Get perceived strongholds
                    perceived_strongholds = faction.perceived_strongholds.get(district_id, {})
                    stronghold_values = {}
                    for faction_id, data in perceived_strongholds.items():
                        if data:
                            stronghold_values[faction_id] = data.get("has_stronghold", False)
                    
                    # Add current faction's actual influence and stronghold status (they always know their own)
                    if district.has_faction(faction.id):
                        perceived_values[faction.id] = district.get_faction_influence(faction.id)
                        stronghold_values[faction.id] = district.has_stronghold(faction.id)
                    
                    self._draw_influence_dots(district, perceived_values, stronghold_values)
        
        # Draw editing overlays
        if self.editing_mode:
            # Draw current shape being created
            if self.current_shape_points:
                self._draw_current_shape()
            
            # Draw editing handles for selected district
            if self.selected_district_id and self.districts[self.selected_district_id].shape_data:
                self._draw_edit_handles()
    
    def _draw_district(self, district):
        """Draw a district on the canvas.
        
        Args:
            district: District instance to draw.
        """
        # Get district shape data
        shape_data = district.shape_data
        if not shape_data:
            return
        
        # Apply zoom and pan to coordinates
        points = []
        for point in shape_data.get("points", []):
            # Ensure we have proper coordinates to work with
            x_coord = point.get("x", 0)
            y_coord = point.get("y", 0)
            
            # Convert coordinates based on current map dimensions and zoom
            x = x_coord * self.zoom_level + self.pan_x
            y = y_coord * self.zoom_level + self.pan_y
            
            points.append(x)
            points.append(y)
        
        if len(points) < 6:  # Need at least 3 points (6 coordinates)
            return
        
        # Create polygon with no fill and no outline
        self.canvas.create_polygon(
            points,
            fill="",  # No fill (completely transparent)
            outline="",  # No border
            width=0,
            tags=("district", f"district_{district.id}")
        )
        
        # Add district name label
        centroid_x = sum(points[::2]) / (len(points) // 2)
        centroid_y = sum(points[1::2]) / (len(points) // 2)
        
        # Scale font size with zoom
        font_size = int(self.district_name_font_size * self.zoom_level)
        font_size = max(8, min(24, font_size))  # Clamp between 8 and 24
        
        # Create text with white outline for better visibility against any background
        # First draw text outline in white
        for offset_x, offset_y in [(1,1), (1,-1), (-1,1), (-1,-1)]:
            self.canvas.create_text(
                centroid_x + offset_x, centroid_y + offset_y,
                text=district.name,
                font=("Arial", font_size, "bold"),
                fill="#FFFFFF",
                tags=("district_label_shadow", f"district_label_shadow_{district.id}")
            )
        
        # Draw the actual text
        self.canvas.create_text(
            centroid_x, centroid_y,
            text=district.name,
            font=("Arial", font_size, "bold"),
            fill="#000000",
            tags=("district_label", f"district_label_{district.id}")
        )
    
    def _draw_influence_dots(self, district, influence_values, strongholds):
        """Draw influence dots for a district.
        
        Args:
            district: District instance.
            influence_values (dict): Faction ID to influence value mapping.
            strongholds (dict): Faction ID to stronghold status mapping.
        """
        if not district.shape_data or not district.shape_data.get("points"):
            return
        
        points = district.shape_data.get("points", [])
        if not points:
            return
        
        # Draw dots for each faction
        for faction_id, influence in influence_values.items():
            if influence <= 0:
                continue
            
            # Get faction color
            faction = self.factions.get(faction_id)
            color = faction.color if faction else "#CCCCCC"
            
            # Create influence dots randomly placed within the district shape
            for i in range(influence):
                # Generate a random point inside the polygon
                # We'll use a simple rejection sampling method
                import random
                
                # Get the bounding box of the district
                min_x = min(p["x"] for p in points)
                max_x = max(p["x"] for p in points)
                min_y = min(p["y"] for p in points)
                max_y = max(p["y"] for p in points)
                
                # Find a random point inside the polygon
                found = False
                max_attempts = 50  # Prevent infinite loop
                attempts = 0
                
                while not found and attempts < max_attempts:
                    # Generate a random point within the bounding box
                    rand_x = min_x + random.random() * (max_x - min_x)
                    rand_y = min_y + random.random() * (max_y - min_y)
                    
                    # Check if the point is inside the polygon
                    if self._point_in_polygon(rand_x, rand_y, points):
                        found = True
                        
                        # Convert to screen coordinates
                        screen_x = rand_x * self.zoom_level + self.pan_x
                        screen_y = rand_y * self.zoom_level + self.pan_y
                        
                        # Draw dot
                        dot_radius = self.influence_dot_radius * self.zoom_level
                        self.canvas.create_oval(
                            screen_x - dot_radius, screen_y - dot_radius,
                            screen_x + dot_radius, screen_y + dot_radius,
                            fill=color, outline="#000000",
                            tags=("influence", f"influence_{district.id}_{faction_id}")
                        )
                    
                    attempts += 1
            
            # Draw stronghold if present
            if strongholds.get(faction_id, False):
                self._draw_stronghold(district, faction_id, color)
    
    def _draw_stronghold(self, district, faction_id, color):
        """Draw a stronghold marker for a faction in a district.
        
        Args:
            district: District instance.
            faction_id (str): Faction ID.
            color (str): Faction color.
        """
        if not district.shape_data or not district.shape_data.get("points"):
            return
        
        points = district.shape_data.get("points", [])
        if not points:
            return
        
        # Generate a random point inside the polygon for the stronghold
        # We'll use the same rejection sampling method as for influence dots
        import random
        
        # Get the bounding box of the district
        min_x = min(p["x"] for p in points)
        max_x = max(p["x"] for p in points)
        min_y = min(p["y"] for p in points)
        max_y = max(p["y"] for p in points)
        
        # Find a random point inside the polygon
        found = False
        max_attempts = 50  # Prevent infinite loop
        attempts = 0
        
        while not found and attempts < max_attempts:
            # Generate a random point within the bounding box
            rand_x = min_x + random.random() * (max_x - min_x)
            rand_y = min_y + random.random() * (max_y - min_y)
            
            # Check if the point is inside the polygon
            if self._point_in_polygon(rand_x, rand_y, points):
                found = True
                
                # Convert to screen coordinates
                screen_x = rand_x * self.zoom_level + self.pan_x
                screen_y = rand_y * self.zoom_level + self.pan_y
                
                # Draw stronghold marker (star shape)
                size = self.stronghold_size * self.zoom_level
                star_points = []
                
                # Create 5-pointed star
                for i in range(10):
                    angle = math.pi/2 + i * math.pi/5
                    radius = size if i % 2 == 0 else size/2
                    x = screen_x + radius * math.cos(angle)
                    y = screen_y - radius * math.sin(angle)
                    star_points.append(x)
                    star_points.append(y)
                
                self.canvas.create_polygon(
                    star_points,
                    fill=color, outline="#000000",
                    tags=("stronghold", f"stronghold_{district.id}_{faction_id}")
                )
            
            attempts += 1
        
        # If we couldn't find a point inside the polygon, use the centroid
        if not found:
            centroid_x = sum(p["x"] for p in points) / len(points) * self.zoom_level + self.pan_x
            centroid_y = sum(p["y"] for p in points) / len(points) * self.zoom_level + self.pan_y
            
            # Draw stronghold marker (star shape)
            size = self.stronghold_size * self.zoom_level
            star_points = []
            
            # Create 5-pointed star
            for i in range(10):
                angle = math.pi/2 + i * math.pi/5
                radius = size if i % 2 == 0 else size/2
                x = centroid_x + radius * math.cos(angle)
                y = centroid_y - radius * math.sin(angle)
                star_points.append(x)
                star_points.append(y)
            
            self.canvas.create_polygon(
                star_points,
                fill=color, outline="#000000",
                tags=("stronghold", f"stronghold_{district.id}_{faction_id}")
            )
    
    def _draw_current_shape(self):
        """Draw the shape currently being created."""
        if not self.current_shape_points:
            return
        
        # Apply zoom and pan to coordinates
        points = []
        for point in self.current_shape_points:
            x = point["x"] * self.zoom_level + self.pan_x
            y = point["y"] * self.zoom_level + self.pan_y
            points.append(x)
            points.append(y)
        
        # Draw lines connecting points
        for i in range(0, len(points), 2):
            if i > 0:
                self.canvas.create_line(
                    points[i-2], points[i-1], points[i], points[i+1],
                    fill="#FF0000", width=2,
                    tags="current_shape"
                )
        
        # Draw line back to start if we have a complete shape
        if len(points) >= 6:  # At least 3 points
            self.canvas.create_line(
                points[-2], points[-1], points[0], points[1],
                fill="#FF0000", dash=(5, 5), width=2,
                tags="current_shape"
            )
        
        # Draw points
        for i in range(0, len(points), 2):
            self.canvas.create_oval(
                points[i] - 5, points[i+1] - 5,
                points[i] + 5, points[i+1] + 5,
                fill="#FF0000", outline="#000000",
                tags=("current_shape", f"point_{i//2}")
            )
    
    def _draw_edit_handles(self):
        """Draw edit handles for selected district."""
        if not self.selected_district_id or not self.districts[self.selected_district_id].shape_data:
            return
        
        district = self.districts[self.selected_district_id]
        points = district.shape_data.get("points", [])
        
        for i, point in enumerate(points):
            x = point["x"] * self.zoom_level + self.pan_x
            y = point["y"] * self.zoom_level + self.pan_y
            
            self.canvas.create_rectangle(
                x - 5, y - 5, x + 5, y + 5,
                fill="#00FF00", outline="#000000",
                tags=("edit_handle", f"edit_handle_{i}")
            )
    
    def _change_view_mode(self):
        """Handle view mode change."""
        mode = self.view_mode_var.get()
        self.current_view = mode
        
        if mode == "faction":
            # Enable faction selection
            self.faction_combobox["state"] = "readonly"
            
            # Get selected faction
            selection = self.faction_combobox.current()
            if selection >= 0:
                faction_name = self.faction_combobox.get()
                for faction_id, faction in self.factions.items():
                    if faction.name == faction_name:
                        self.view_faction_id = faction_id
                        break
        else:
            # Disable faction selection for DM view
            self.faction_combobox["state"] = "disabled"
            self.view_faction_id = None
        
        # Redraw map with new view
        self._draw_map()
    
    def _on_faction_selected(self, event):
        """Handle faction selection for faction view."""
        if self.view_mode_var.get() == "faction":
            selection = self.faction_combobox.current()
            if selection >= 0:
                faction_name = self.faction_combobox.get()
                for faction_id, faction in self.factions.items():
                    if faction.name == faction_name:
                        self.view_faction_id = faction_id
                        break
                
                # Redraw map with new faction view
                self._draw_map()
    
    def _on_district_selected(self, event):
        """Handle district selection in listbox."""
        selection = self.district_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.district_listbox_ids):
                self.selected_district_id = self.district_listbox_ids[index]
                self._draw_map()  # Redraw to show selection
    
    def _toggle_edit_mode(self):
        """Toggle district editing mode."""
        self.editing_mode = self.edit_mode_var.get()
        
        # Clear current shape if exiting edit mode
        if not self.editing_mode:
            self.current_shape_points = []
            self.edit_selected_point = None
        
        # Redraw map with edit overlays if needed
        self._draw_map()
    
    def _start_new_district(self):
        """Start creating a new district."""
        if not self.editing_mode:
            messagebox.showinfo("Edit Mode Required", "Please enable Edit Mode first.")
            return
        
        # Clear any existing drawing points
        self.current_shape_points = []
        self.drawing_district = True
        
        # Create a new district
        district_name = simpledialog.askstring("New District", "Enter district name:")
        if not district_name:
            return
        
        # Create district in database
        district = District(
            id=str(uuid.uuid4()),
            name=district_name,
            description="",
            commerce_value=5,
            muster_value=5,
            aristocratic_value=5
        )
        
        success = self.district_repository.create(district)
        if success:
            # Add to local cache
            self.districts[district.id] = district
            self.selected_district_id = district.id
            
            # Update district listbox
            self.district_listbox.insert(tk.END, district.name)
            self.district_listbox_ids.append(district.id)
            
            # Select the new district
            self.district_listbox.selection_clear(0, tk.END)
            self.district_listbox.selection_set(tk.END)
            
            messagebox.showinfo("District Created", 
                               "New district created. Click on the map to add shape points.")
        else:
            messagebox.showerror("Error", "Failed to create district.")
    
    def _clear_drawing_points(self):
        """Clear current drawing points."""
        self.current_shape_points = []
        self._draw_map()
    
    def _change_fill_color(self):
        """Change fill color for selected district."""
        if not self.selected_district_id:
            messagebox.showinfo("No Selection", "Please select a district first.")
            return
        
        district = self.districts[self.selected_district_id]
        if not district.shape_data:
            messagebox.showinfo("No Shape", "Selected district has no shape data.")
            return
        
        # Get current color
        style = district.shape_data.get("style", {})
        current_color = style.get("fill_color", "#CCCCCC")
        
        # Open color chooser
        color = colorchooser.askcolor(initialcolor=current_color, title="Select Fill Color")
        if color[1]:  # [1] is the hex color string
            # Update district shape style
            if "style" not in district.shape_data:
                district.shape_data["style"] = {}
            
            district.shape_data["style"]["fill_color"] = color[1]
            
            # Save to database
            self._save_district_shape()
            
            # Redraw map
            self._draw_map()
    
    def _change_border_color(self):
        """Change border color for selected district."""
        if not self.selected_district_id:
            messagebox.showinfo("No Selection", "Please select a district first.")
            return
        
        district = self.districts[self.selected_district_id]
        if not district.shape_data:
            messagebox.showinfo("No Shape", "Selected district has no shape data.")
            return
        
        # Get current color
        style = district.shape_data.get("style", {})
        current_color = style.get("border_color", "#000000")
        
        # Open color chooser
        color = colorchooser.askcolor(initialcolor=current_color, title="Select Border Color")
        if color[1]:  # [1] is the hex color string
            # Update district shape style
            if "style" not in district.shape_data:
                district.shape_data["style"] = {}
            
            district.shape_data["style"]["border_color"] = color[1]
            
            # Save to database
            self._save_district_shape()
            
            # Redraw map
            self._draw_map()
    
    def _save_district_shape(self):
        """Save the current shape to the selected district."""
        if not self.selected_district_id:
            messagebox.showinfo("No Selection", "Please select a district first.")
            return
        
        district = self.districts[self.selected_district_id]
        
        # If we have drawing points, use those
        if self.current_shape_points and len(self.current_shape_points) >= 3:
            # Initialize shape data if needed
            if not district.shape_data:
                district.shape_data = {
                    "type": "polygon",
                    "points": [],
                    "style": {
                        "fill_color": "#CCCCCC",
                        "border_color": "#000000",
                        "border_width": self.district_border_width,
                        "fill_opacity": self.district_fill_alpha
                    }
                }
            
            # Update points
            district.shape_data["points"] = self.current_shape_points.copy()
            
            # Clear current drawing
            self.current_shape_points = []
        
        # Save district to database
        success = self.district_repository.update(district)
        if success:
            messagebox.showinfo("Success", "District shape saved successfully.")
            self._draw_map()
        else:
            messagebox.showerror("Error", "Failed to save district shape.")
    
    def _export_current_view(self):
        """Export current map view as an image."""
        # TODO: Implement export functionality
        messagebox.showinfo("Not Implemented", "Export functionality not yet implemented.")
    
    def _export_all_views(self):
        """Export maps for all factions."""
        # TODO: Implement export functionality
        messagebox.showinfo("Not Implemented", "Export functionality not yet implemented.")
    
    def _on_canvas_click(self, event):
        """Handle canvas click events.
        
        Args:
            event: Mouse event.
        """
        # Get canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Convert to map coordinates (accounting for zoom and pan)
        map_x = (canvas_x - self.pan_x) / self.zoom_level
        map_y = (canvas_y - self.pan_y) / self.zoom_level

        # Ensure map coordinates are within bounds
        map_width = self.original_map_width
        map_height = self.original_map_height
        map_x = max(0, min(map_x, map_width))
        map_y = max(0, min(map_y, map_height))
        
        if self.editing_mode:
            # Check if we're editing an existing point
            if self.edit_selected_point is not None:
                # Update point position
                district = self.districts[self.selected_district_id]
                district.shape_data["points"][self.edit_selected_point] = {"x": map_x, "y": map_y}
                self.edit_selected_point = None
                self._draw_map()
                return
            
            # Check if clicking on an edit handle
            if self.selected_district_id and self.districts[self.selected_district_id].shape_data:
                district = self.districts[self.selected_district_id]
                points = district.shape_data.get("points", [])
                
                for i, point in enumerate(points):
                    point_x = point["x"] * self.zoom_level + self.pan_x
                    point_y = point["y"] * self.zoom_level + self.pan_y
                    
                    # Check if click is within handle
                    if (abs(canvas_x - point_x) <= 5 and abs(canvas_y - point_y) <= 5):
                        self.edit_selected_point = i
                        return
            
            # If drawing a district, add point
            if self.drawing_district and self.selected_district_id:
                self.current_shape_points.append({"x": map_x, "y": map_y})
                self._draw_map()
        else:
            # Regular click - select district
            closest_district = None
            min_distance = float('inf')
            
            for district_id, district in self.districts.items():
                if not district.shape_data:
                    continue
                
                points = district.shape_data.get("points", [])
                if self._point_in_polygon(map_x, map_y, points):
                    # Find district in listbox and select it
                    try:
                        index = self.district_listbox_ids.index(district_id)
                        self.district_listbox.selection_clear(0, tk.END)
                        self.district_listbox.selection_set(index)
                        self.district_listbox.see(index)
                        self.selected_district_id = district_id
                        self._draw_map()
                        return
                    except ValueError:
                        # District ID not found in listbox
                        pass
            
            # If no district found, try to select closest one
            for district_id, district in self.districts.items():
                if not district.shape_data:
                    continue
                
                points = district.shape_data.get("points", [])
                centroid_x = sum(p["x"] for p in points) / len(points)
                centroid_y = sum(p["y"] for p in points) / len(points)
                
                # Calculate distance
                distance = math.sqrt((map_x - centroid_x)**2 + (map_y - centroid_y)**2)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_district = district_id
            
            if closest_district:
                try:
                    # Find district in listbox and select it
                    index = self.district_listbox_ids.index(closest_district)
                    self.district_listbox.selection_clear(0, tk.END)
                    self.district_listbox.selection_set(index)
                    self.district_listbox.see(index)
                    self.selected_district_id = closest_district
                    self._draw_map()
                except ValueError:
                    # District ID not found in listbox
                    pass
    
    def _on_canvas_drag(self, event):
        """Handle canvas drag events.
        
        Args:
            event: Mouse event.
        """
        # Get canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        if self.editing_mode and self.edit_selected_point is not None:
            # Moving an edit point
            map_x = (canvas_x - self.pan_x) / self.zoom_level
            map_y = (canvas_y - self.pan_y) / self.zoom_level
            
            # Ensure map coordinates are within bounds
            map_width = self.original_map_width
            map_height = self.original_map_height
            map_x = max(0, min(map_x, map_width))
            map_y = max(0, min(map_y, map_height))
            
            district = self.districts[self.selected_district_id]
            district.shape_data["points"][self.edit_selected_point] = {"x": map_x, "y": map_y}
            self._draw_map()
        elif not self.editing_mode:
            # Pan the view
            if not self.dragging:
                self.dragging = True
                self.drag_start_x = canvas_x
                self.drag_start_y = canvas_y
            else:
                # Calculate delta
                dx = canvas_x - self.drag_start_x
                dy = canvas_y - self.drag_start_y
                
                # Update pan
                self.pan_x += dx
                self.pan_y += dy
                
                # Update drag start
                self.drag_start_x = canvas_x
                self.drag_start_y = canvas_y
                
                # Redraw map
                self._draw_map()
    
    def _on_canvas_release(self, event):
        """Handle canvas release events.
        
        Args:
            event: Mouse event.
        """
        self.dragging = False
    
    def _on_canvas_right_click(self, event):
        """Handle canvas right-click events.
        
        Args:
            event: Mouse event.
        """
        if self.editing_mode and self.current_shape_points and len(self.current_shape_points) >= 3:
            # Complete the shape
            self._save_district_shape()
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel events for zooming.
        
        Args:
            event: Mouse wheel event.
        """
        # Get direction
        if event.num == 4 or event.delta > 0:
            # Zoom in
            self._zoom_in()
        elif event.num == 5 or event.delta < 0:
            # Zoom out
            self._zoom_out()
    
    def _on_window_resize(self, event):
        """Handle window resize events.
        
        Args:
            event: Window resize event.
        """
        # Redraw map to fit new size
        self._draw_map()
    
    def _zoom_in(self):
        """Zoom in on the map."""
        # Limit zoom level
        if self.zoom_level < 4.0:
            self.zoom_level *= 1.2
            self.zoom_level = min(4.0, self.zoom_level)
            self.zoom_scale.set(self.zoom_level)
            self._update_zoom_label()
            self._draw_map()
    
    def _zoom_out(self):
        """Zoom out on the map."""
        # Limit zoom level
        if self.zoom_level > 0.25:
            self.zoom_level /= 1.2
            self.zoom_level = max(0.25, self.zoom_level)
            self.zoom_scale.set(self.zoom_level)
            self._update_zoom_label()
            self._draw_map()
    
    def _on_zoom_change(self, value):
        """Handle zoom scale changes.
        
        Args:
            value: New zoom value.
        """
        self.zoom_level = float(value)
        self._update_zoom_label()
        self._draw_map()
    
    def _update_zoom_label(self):
        """Update the zoom level label."""
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
    
    def _reset_view(self):
        """Reset the map view to default."""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.zoom_scale.set(1.0)
        self._update_zoom_label()
        self._draw_map()
    
    def _point_in_polygon(self, x, y, points):
        """Check if a point is inside a polygon.
        
        Args:
            x (float): X coordinate.
            y (float): Y coordinate.
            points (list): List of polygon points.
            
        Returns:
            bool: True if point is inside polygon, False otherwise.
        """
        n = len(points)
        inside = False
        
        p1x, p1y = points[0]['x'], points[0]['y']
        for i in range(n + 1):
            p2x, p2y = points[i % n]['x'], points[i % n]['y']
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def refresh(self):
        """Refresh the map panel data."""
        self._load_data()

    def _select_base_map(self):
        """Open file dialog to select a base map image."""
        filetypes = [
            ("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg;*.jpeg"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Base Map Image",
            filetypes=filetypes
        )
        
        if file_path:
            # Update map configuration
            self.map_config["base_map_path"] = file_path
            self._save_map_configuration(self.map_config)
            
            # Load the new base map
            success = self._load_base_map(file_path)
            
            if success:
                # Update base map label
                import os
                filename = os.path.basename(file_path)
                self.base_map_label.config(text=f"Map: {filename}")
                
                # Redraw the map
                self._draw_map()
                messagebox.showinfo("Success", f"Base map loaded: {filename}")
            else:
                messagebox.showerror("Error", "Failed to load base map image")