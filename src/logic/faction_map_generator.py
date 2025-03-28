import logging
import os
import random
import math
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageColor

class FactionMapGenerator:
    """Generates faction-specific maps based on perception data."""
    
    def __init__(self, db_manager, district_repository, faction_repository, monitoring_manager):
        """Initialize the faction map generator.
        
        Args:
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            monitoring_manager: Monitoring manager for getting faction reports.
        """
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.monitoring_manager = monitoring_manager
        
        # Drawing parameters - all configurable sizes grouped here for easy access
        self.influence_dot_radius = 12      # Size of influence dots
        self.stronghold_size = 24          # Size of stronghold stars
        self.district_fill_alpha = 64      # 0-255 for alpha
        self.district_border_width = 2     # Width of district borders
        self.district_name_font_size = 65  # Font size for district names 
        self.confidence_font_size = 45     # Font size for confidence ratings
        
        # Create maps directory if it doesn't exist
        self.maps_dir = os.path.join(os.getcwd(), "maps")
        if not os.path.exists(self.maps_dir):
            os.makedirs(self.maps_dir)
        
        # Load map configuration
        self.map_config = self._load_map_configuration()
    
    def _load_map_configuration(self):
        """Load map configuration from database.
        
        Returns:
            dict: Map configuration.
        """
        try:
            query = """
                SELECT base_map_path, map_width, map_height
                FROM map_configuration
                WHERE id = 'current'
            """
            
            result = self.db_manager.execute_query(query)
            
            if result:
                config = dict(result[0])
                return config
            else:
                return {"base_map_path": None, "map_width": 800, "map_height": 600}
        except Exception as e:
            logging.error(f"Error loading map configuration: {str(e)}")
            return {"base_map_path": None, "map_width": 800, "map_height": 600}
    
    def generate_faction_maps(self, turn_number):
        """Generate maps for all factions based on their perception data.
        
        Args:
            turn_number (int): Turn number to generate maps for.
            
        Returns:
            dict: Map generation results.
        """
        try:
            results = {
                "generated_maps": [],
                "errors": []
            }
            
            # Load factions
            factions = self.faction_repository.find_all()
            
            # Load districts
            districts = self.district_repository.find_all()
            
            # Load base map
            base_map_path = self.map_config.get("base_map_path")
            if not base_map_path or not os.path.exists(base_map_path):
                logging.error("Base map not found")
                results["errors"].append("Base map not found")
                return results
            
            try:
                base_map = Image.open(base_map_path)
            except Exception as e:
                logging.error(f"Error loading base map: {str(e)}")
                results["errors"].append(f"Error loading base map: {str(e)}")
                return results
            
            # Load fonts
            try:
                # Try to load Arial, fall back to default
                try:
                    district_name_font = ImageFont.truetype("arial.ttf", self.district_name_font_size)
                    confidence_font = ImageFont.truetype("arial.ttf", self.confidence_font_size)
                except:
                    district_name_font = ImageFont.load_default()
                    confidence_font = ImageFont.load_default()
            except Exception as e:
                logging.error(f"Error loading fonts: {str(e)}")
                district_name_font = None
                confidence_font = None
            
            # Create turn directory
            turn_dir = os.path.join(self.maps_dir, f"turn_{turn_number}")
            if not os.path.exists(turn_dir):
                os.makedirs(turn_dir)
            
            # Generate a map for each faction
            for faction in factions:
                try:
                    # Generate the map for this faction
                    map_path = self._generate_faction_map(
                        faction, districts, turn_number, 
                        base_map, district_name_font, confidence_font, turn_dir
                    )
                    
                    results["generated_maps"].append({
                        "faction_id": faction.id,
                        "faction_name": faction.name,
                        "map_path": map_path
                    })
                except Exception as e:
                    logging.error(f"Error generating map for faction {faction.name}: {str(e)}")
                    results["errors"].append(f"Error generating map for faction {faction.name}: {str(e)}")
            
            return results
        except Exception as e:
            logging.error(f"Error in generate_faction_maps: {str(e)}")
            return {"errors": [str(e)]}
    
    def _generate_faction_map(self, faction, districts, turn_number, base_map, district_name_font, confidence_font, turn_dir):
        """Generate a map for a specific faction.
        
        Args:
            faction: Faction to generate map for.
            districts: List of all districts.
            turn_number: Current turn number.
            base_map: Base map image.
            district_name_font: Font to use for district names.
            confidence_font: Font to use for confidence labels.
            turn_dir: Directory to save maps in.
            
        Returns:
            str: Path to generated map.
        """
        # Create a copy of the base map
        faction_map = base_map.copy()
        draw = ImageDraw.Draw(faction_map, 'RGBA')
        
        # Get the weekly intelligence summary for this faction
        weekly_summary = self.monitoring_manager.generate_weekly_intelligence_summary(faction.id, turn_number)
        
        # Get faction's actual influence data
        actual_influence = {}
        actual_strongholds = {}
        for district in districts:
            actual_influence[district.id] = district.get_faction_influence(faction.id)
            actual_strongholds[district.id] = district.has_stronghold(faction.id)
        
        # Process each district
        for district in districts:
            # Skip districts without shape data
            if not district.shape_data or not district.shape_data.get("points"):
                continue
            
            # Get district points
            points = district.shape_data.get("points")
            if len(points) < 3:  # Need at least 3 points for a polygon
                continue
            
            # Convert points to pixel coordinates
            pixel_points = []
            for point in points:
                pixel_points.append((point["x"], point["y"]))
            
            # Make district shape completely transparent - no fill, no border
            # This makes the underlying base map completely visible
            
            # Calculate district centroid for positioning
            centroid_x = sum(p[0] for p in pixel_points) / len(pixel_points)
            centroid_y = sum(p[1] for p in pixel_points) / len(pixel_points)
            
            # Get monitoring data for this district
            district_data = weekly_summary.get("districts", {}).get(district.id)
            confidence = 0
            perceived_influences = {}
            perceived_strongholds = {}
            
            if district_data:
                confidence = district_data.get("confidence_rating", 0)
                
                # Get perceived influences
                for faction_id, value in district_data.get("perceived_influences", {}).items():
                    perceived_influences[faction_id] = value
                
                # Get perceived strongholds
                perceived_strongholds = district_data.get("perceived_strongholds", {})
                
                # Add phantom detections
                for phantom in district_data.get("phantom_detections", []):
                    perceived_influences[phantom["faction_id"]] = phantom["perceived_influence"]
            
            # Draw district name
            district_name = district.name
            try:
                # Use textbbox for newer PIL versions
                if hasattr(draw, 'textbbox'):
                    text_bbox = draw.textbbox((0, 0), district_name, font=district_name_font)
                    name_width = text_bbox[2] - text_bbox[0]
                    name_height = text_bbox[3] - text_bbox[1]
                else:
                    # Fall back to textsize for older PIL versions
                    name_width, name_height = draw.textsize(district_name, font=district_name_font)
                    
                # Draw white outline for name (for visibility against any background)
                for offset_x, offset_y in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                    draw.text(
                        (centroid_x - name_width/2 + offset_x, centroid_y - name_height - 20 + offset_y),
                        district_name,
                        fill=(255, 255, 255),
                        font=district_name_font
                    )
                
                # Draw the name text
                draw.text(
                    (centroid_x - name_width/2, centroid_y - name_height - 20),
                    district_name,
                    fill=(0, 0, 0),
                    font=district_name_font
                )
            except Exception as e:
                logging.error(f"Error drawing district name: {str(e)}")
            
            # Draw confidence label
            if confidence > 0 and confidence_font is not None:
                confidence_text = f"C{confidence}"
                try:
                    # Use textbbox for newer PIL versions
                    if hasattr(draw, 'textbbox'):
                        text_bbox = draw.textbbox((0, 0), confidence_text, font=confidence_font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_height = text_bbox[3] - text_bbox[1]
                    else:
                        # Fall back to textsize for older PIL versions
                        text_width, text_height = draw.textsize(confidence_text, font=confidence_font)
                    
                    # Draw white outline for confidence (for visibility against any background)
                    for offset_x, offset_y in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                        draw.text(
                            (centroid_x - text_width/2 + offset_x, centroid_y - text_height/2 + offset_y),
                            confidence_text,
                            fill=(255, 255, 255),
                            font=confidence_font
                        )
                    
                    # Draw the confidence text
                    draw.text(
                        (centroid_x - text_width/2, centroid_y - text_height/2),
                        confidence_text,
                        fill=(0, 0, 0),
                        font=confidence_font
                    )
                except Exception as e:
                    logging.error(f"Error drawing confidence text: {str(e)}")
            
            # Draw influence dots
            self._draw_influence_dots(draw, district, faction, actual_influence.get(district.id, 0), 
                                  perceived_influences, pixel_points)
            
            # Draw strongholds
            self._draw_strongholds(draw, district, faction, actual_strongholds.get(district.id, False),
                               perceived_strongholds, pixel_points)
        
        # Save the map
        map_filename = f"{faction.name.replace(' ', '_')}_map_turn_{turn_number}.png"
        map_path = os.path.join(turn_dir, map_filename)
        faction_map.save(map_path)
        
        return map_path
    
    def _draw_influence_dots(self, draw, district, faction, actual_influence, 
                            perceived_influences, pixel_points):
        """Draw influence dots for a district.
        
        Args:
            draw: ImageDraw instance.
            district: District to draw dots for.
            faction: Faction whose perspective we're showing.
            actual_influence: Actual influence of the faction in this district.
            perceived_influences: Dict of perceived influences for other factions.
            pixel_points: List of (x, y) tuples for district polygon.
        """
        # Collect all influences to draw
        all_influences = {}
        
        # Add actual influence for faction's own dots
        if actual_influence > 0:
            all_influences[faction.id] = actual_influence
        
        # Add perceived influences for other factions
        for faction_id, influence in perceived_influences.items():
            # Skip own faction (we use actual values for that)
            if faction_id == faction.id:
                continue
                
            if influence > 0:
                all_influences[faction_id] = influence
        
        # Calculate total dots to place
        total_dots = sum(all_influences.values())
        if total_dots == 0:
            return
        
        # Get the bounding box of the district
        min_x = min(p[0] for p in pixel_points)
        max_x = max(p[0] for p in pixel_points)
        min_y = min(p[1] for p in pixel_points)
        max_y = max(p[1] for p in pixel_points)
        
        # Create a simple polygon for point-in-polygon testing
        polygon = [(p[0], p[1]) for p in pixel_points]
        
        # Draw dots for each faction
        for faction_id, influence in all_influences.items():
            # Get faction color
            dot_faction = self.faction_repository.find_by_id(faction_id)
            color = dot_faction.color if dot_faction else "#CCCCCC"
            
            # Draw dots for this faction
            for i in range(influence):
                # Use rejection sampling to find a point inside the polygon
                max_attempts = 50
                found = False
                attempts = 0
                
                while not found and attempts < max_attempts:
                    # Generate a random point within the bounding box
                    x = min_x + random.random() * (max_x - min_x)
                    y = min_y + random.random() * (max_y - min_y)
                    
                    # Check if the point is inside the polygon
                    if self._point_in_polygon(x, y, polygon):
                        found = True
                        
                        # Draw dot
                        draw.ellipse(
                            [
                                x - self.influence_dot_radius, 
                                y - self.influence_dot_radius,
                                x + self.influence_dot_radius, 
                                y + self.influence_dot_radius
                            ],
                            fill=color, 
                            outline="#000000"
                        )
                    
                    attempts += 1
                
                # If we couldn't find a point inside the polygon, just place it at the centroid
                if not found:
                    centroid_x = sum(p[0] for p in pixel_points) / len(pixel_points)
                    centroid_y = sum(p[1] for p in pixel_points) / len(pixel_points)
                    
                    # Add some random jitter around the centroid
                    x = centroid_x + random.uniform(-10, 10)
                    y = centroid_y + random.uniform(-10, 10)
                    
                    # Draw dot
                    draw.ellipse(
                        [
                            x - self.influence_dot_radius, 
                            y - self.influence_dot_radius,
                            x + self.influence_dot_radius, 
                            y + self.influence_dot_radius
                        ],
                        fill=color, 
                        outline="#000000"
                    )
    
    def _draw_strongholds(self, draw, district, faction, actual_stronghold, perceived_strongholds, pixel_points):
        """Draw stronghold markers for a district.
        
        Args:
            draw: ImageDraw instance.
            district: District to draw strongholds for.
            faction: Faction whose perspective we're showing.
            actual_stronghold: Whether the faction has an actual stronghold in this district.
            perceived_strongholds: Dict of perceived strongholds by faction ID.
            pixel_points: List of (x, y) tuples for district polygon.
        """
        # Get the bounding box of the district
        min_x = min(p[0] for p in pixel_points)
        max_x = max(p[0] for p in pixel_points)
        min_y = min(p[1] for p in pixel_points)
        max_y = max(p[1] for p in pixel_points)
        
        # Create a simple polygon for point-in-polygon testing
        polygon = [(p[0], p[1]) for p in pixel_points]
        
        # Draw faction's own actual stronghold
        if actual_stronghold:
            self._place_stronghold_in_polygon(draw, polygon, min_x, max_x, min_y, max_y, faction.color)
        
        # Draw perceived strongholds for other factions
        offset_y = self.stronghold_size * 2  # Vertical offset between strongholds
        for faction_id, has_stronghold in perceived_strongholds.items():
            # Skip own faction (we use actual values for that)
            if faction_id == faction.id:
                continue
                
            if has_stronghold:
                # Get faction color
                other_faction = self.faction_repository.find_by_id(faction_id)
                if other_faction:
                    self._place_stronghold_in_polygon(draw, polygon, min_x, max_x, min_y, max_y, other_faction.color)
    
    def _place_stronghold_in_polygon(self, draw, polygon, min_x, max_x, min_y, max_y, color):
        """Place a stronghold marker randomly within a polygon.
        
        Args:
            draw: ImageDraw instance.
            polygon: List of (x, y) tuples forming the polygon.
            min_x, max_x, min_y, max_y: Bounding box coordinates.
            color: Stronghold color (faction color).
        """
        # Use rejection sampling to find a point inside the polygon
        max_attempts = 50
        found = False
        attempts = 0
        
        while not found and attempts < max_attempts:
            # Generate a random point within the bounding box
            x = min_x + random.random() * (max_x - min_x)
            y = min_y + random.random() * (max_y - min_y)
            
            # Check if the point is inside the polygon
            if self._point_in_polygon(x, y, polygon):
                found = True
                self._draw_stronghold_marker(draw, x, y, color)
            
            attempts += 1
        
        # If we couldn't find a point inside the polygon, use the centroid
        if not found:
            centroid_x = sum(p[0] for p in polygon) / len(polygon)
            centroid_y = sum(p[1] for p in polygon) / len(polygon)
            self._draw_stronghold_marker(draw, centroid_x, centroid_y, color)
    
    def _point_in_polygon(self, x, y, polygon):
        """Check if a point is inside a polygon.
        
        Args:
            x, y: Point coordinates.
            polygon: List of (x, y) tuples forming the polygon.
            
        Returns:
            bool: True if the point is inside the polygon.
        """
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _draw_stronghold_marker(self, draw, x, y, color):
        """Draw a star-shaped stronghold marker.
        
        Args:
            draw: ImageDraw instance.
            x: Center x-coordinate.
            y: Center y-coordinate.
            color: Stronghold color (faction color).
        """
        # Create 5-pointed star
        size = self.stronghold_size
        star_points = []
        
        for i in range(10):
            angle = math.pi/2 + i * math.pi/5
            radius = size if i % 2 == 0 else size/2
            point_x = x + radius * math.cos(angle)
            point_y = y - radius * math.sin(angle)
            star_points.append((point_x, point_y))
        
        # Draw star polygon
        draw.polygon(star_points, fill=color, outline=(0, 0, 0))
    
    def save_dm_map(self, turn_number):
        """Generate and save a DM map with actual influence values.
        
        Args:
            turn_number (int): Turn number.
            
        Returns:
            str: Path to generated map.
        """
        try:
            # Load districts
            districts = self.district_repository.find_all()
            
            # Load factions
            factions = self.faction_repository.find_all()
            
            # Load base map
            base_map_path = self.map_config.get("base_map_path")
            if not base_map_path or not os.path.exists(base_map_path):
                logging.error("Base map not found")
                return None
            
            try:
                base_map = Image.open(base_map_path)
            except Exception as e:
                logging.error(f"Error loading base map: {str(e)}")
                return None
            
            # Load fonts
            try:
                # Try to load Arial, fall back to default
                try:
                    font = ImageFont.truetype("arial.ttf", self.district_name_font_size)
                except:
                    font = ImageFont.load_default()
            except Exception as e:
                logging.error(f"Error loading fonts: {str(e)}")
                font = None
            
            # Create a copy of the base map
            dm_map = base_map.copy()
            draw = ImageDraw.Draw(dm_map, 'RGBA')
            
            # Create turn directory
            turn_dir = os.path.join(self.maps_dir, f"turn_{turn_number}")
            if not os.path.exists(turn_dir):
                os.makedirs(turn_dir)
            
            # Process each district
            for district in districts:
                # Skip districts without shape data
                if not district.shape_data or not district.shape_data.get("points"):
                    continue
                
                # Get district points
                points = district.shape_data.get("points")
                if len(points) < 3:  # Need at least 3 points for a polygon
                    continue
                
                # Convert points to pixel coordinates
                pixel_points = []
                for point in points:
                    pixel_points.append((point["x"], point["y"]))
                
                # No district shapes are drawn - we keep the base map fully visible
                
                # Calculate district centroid for positioning text and influence dots
                centroid_x = sum(p[0] for p in pixel_points) / len(pixel_points)
                centroid_y = sum(p[1] for p in pixel_points) / len(pixel_points)
                
                # Draw district name with white outline for visibility
                district_name = district.name
                if font is not None:
                    try:
                        # Use textbbox for newer PIL versions
                        if hasattr(draw, 'textbbox'):
                            text_bbox = draw.textbbox((0, 0), district_name, font=font)
                            name_width = text_bbox[2] - text_bbox[0]
                            name_height = text_bbox[3] - text_bbox[1]
                        else:
                            # Fall back to textsize for older PIL versions
                            name_width, name_height = draw.textsize(district_name, font=font)
                        
                        # Draw white outline for district name
                        for offset_x, offset_y in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                            draw.text(
                                (centroid_x - name_width/2 + offset_x, centroid_y - name_height - 20 + offset_y),
                                district_name,
                                fill=(255, 255, 255),
                                font=font
                            )
                        
                        # Draw the district name
                        draw.text(
                            (centroid_x - name_width/2, centroid_y - name_height - 20),
                            district_name,
                            fill=(0, 0, 0),
                            font=font
                        )
                    except Exception as e:
                        logging.error(f"Error drawing district name: {str(e)}")
                
                # Draw influence dots for all factions
                all_influences = {}
                all_strongholds = {}
                
                for faction in factions:
                    influence = district.get_faction_influence(faction.id)
                    if influence > 0:
                        all_influences[faction.id] = influence
                        all_strongholds[faction.id] = district.has_stronghold(faction.id)
                
                # Calculate total dots to place
                total_dots = sum(all_influences.values())
                if total_dots == 0:
                    continue
                
                # Arrange dots in a grid pattern
                grid_size = math.ceil(math.sqrt(total_dots))
                grid_spacing = self.influence_dot_radius * 3
                
                # Offset to start grid
                offset_x = -grid_spacing * (grid_size - 1) / 2
                offset_y = grid_spacing * 2  # Place below center
                
                # Draw dots for each faction
                dot_index = 0
                for faction_id, influence in all_influences.items():
                    # Get faction color
                    faction = self.faction_repository.find_by_id(faction_id)
                    color = faction.color if faction else "#CCCCCC"
                    
                    # Draw dots for this faction
                    for i in range(influence):
                        # Calculate grid position
                        row = dot_index // grid_size
                        col = dot_index % grid_size
                        
                        # Calculate dot position
                        x = centroid_x + offset_x + col * grid_spacing
                        y = centroid_y + offset_y + row * grid_spacing
                        
                        # Add some random jitter
                        x += random.uniform(-grid_spacing/3, grid_spacing/3)
                        y += random.uniform(-grid_spacing/3, grid_spacing/3)
                        
                        # Draw dot
                        draw.ellipse(
                            [
                                x - self.influence_dot_radius, 
                                y - self.influence_dot_radius,
                                x + self.influence_dot_radius, 
                                y + self.influence_dot_radius
                            ],
                            fill=color, 
                            outline="#000000"
                        )
                        
                        # Move to next position
                        dot_index += 1
                
                # Draw strongholds for all factions
                for faction_id, has_stronghold in all_strongholds.items():
                    if has_stronghold:
                        faction = self.faction_repository.find_by_id(faction_id)
                        if faction:
                            self._draw_stronghold_marker(draw, centroid_x, centroid_y - 15, faction.color)
            
            # Save the map
            map_filename = f"DM_map_turn_{turn_number}.png"
            map_path = os.path.join(turn_dir, map_filename)
            dm_map.save(map_path)
            
            return map_path
        except Exception as e:
            logging.error(f"Error in save_dm_map: {str(e)}")
            return None