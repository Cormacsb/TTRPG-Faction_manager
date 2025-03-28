import tkinter as tk
from tkinter import ttk, messagebox
import logging
import json
from datetime import datetime


class ReportsPanel(ttk.Frame):
    """Panel for viewing and managing reports."""
    
    def __init__(self, parent, db_manager, district_repository, faction_repository, 
                 rumor_repository, monitoring_manager):
        """Initialize the reports panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            rumor_repository: Repository for rumor operations.
            monitoring_manager: Monitoring manager instance.
        """
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.rumor_repository = rumor_repository
        self.monitoring_manager = monitoring_manager
        
        # Initialize UI elements
        self._create_widgets()
        
        # Load initial data
        self._load_data()
    
    def _create_widgets(self):
        """Create the panel widgets."""
        # Main layout - split into two columns
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=1)
        
        # Left side - controls and filters
        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Report type selection
        report_type_frame = ttk.LabelFrame(left_frame, text="Report Type")
        report_type_frame.pack(fill="x", padx=5, pady=5)
        
        self.report_type = tk.StringVar(value="monitoring")
        
        ttk.Radiobutton(
            report_type_frame, 
            text="Monitoring Reports", 
            variable=self.report_type, 
            value="monitoring",
            command=self._on_report_type_changed
        ).pack(anchor="w", padx=5, pady=2)
        
        ttk.Radiobutton(
            report_type_frame, 
            text="Weekly Intelligence Summaries", 
            variable=self.report_type, 
            value="weekly",
            command=self._on_report_type_changed
        ).pack(anchor="w", padx=5, pady=2)
        
        ttk.Radiobutton(
            report_type_frame, 
            text="Turn History", 
            variable=self.report_type, 
            value="turn_history",
            command=self._on_report_type_changed
        ).pack(anchor="w", padx=5, pady=2)
        
        # Faction selection
        faction_frame = ttk.LabelFrame(left_frame, text="Faction")
        faction_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(faction_frame, text="Select Faction:").pack(anchor="w", padx=5, pady=2)
        
        self.faction_var = tk.StringVar()
        self.faction_combobox = ttk.Combobox(faction_frame, textvariable=self.faction_var)
        self.faction_combobox.pack(fill="x", padx=5, pady=2)
        
        # Turn selection
        turn_frame = ttk.LabelFrame(left_frame, text="Turn")
        turn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(turn_frame, text="Turn Number:").pack(anchor="w", padx=5, pady=2)
        
        self.turn_var = tk.StringVar()
        self.turn_combobox = ttk.Combobox(turn_frame, textvariable=self.turn_var)
        self.turn_combobox.pack(fill="x", padx=5, pady=2)
        
        # District selection (for monitoring reports)
        self.district_frame = ttk.LabelFrame(left_frame, text="District")
        self.district_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(self.district_frame, text="Select District:").pack(anchor="w", padx=5, pady=2)
        
        self.district_var = tk.StringVar()
        self.district_combobox = ttk.Combobox(self.district_frame, textvariable=self.district_var)
        self.district_combobox.pack(fill="x", padx=5, pady=2)
        
        # Load report button
        self.load_report_button = ttk.Button(
            left_frame, 
            text="Load Report", 
            command=self._load_report
        )
        self.load_report_button.pack(fill="x", padx=5, pady=10)
        
        # Right side - report display
        right_frame = ttk.Frame(self)
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Report notebook
        self.report_notebook = ttk.Notebook(right_frame)
        self.report_notebook.pack(fill="both", expand=True)
        
        # Individual report tabs
        self.report_tab = ttk.Frame(self.report_notebook)
        self.report_notebook.add(self.report_tab, text="Report Details")
        
        # Report text widget with scrollbar
        report_text_frame = ttk.Frame(self.report_tab)
        report_text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.report_text = tk.Text(report_text_frame, wrap="word")
        self.report_text.pack(side="left", fill="both", expand=True)
        
        report_scrollbar = ttk.Scrollbar(report_text_frame, orient="vertical", command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=report_scrollbar.set)
        report_scrollbar.pack(side="right", fill="y")
        
        # Bind events
        self.faction_combobox.bind("<<ComboboxSelected>>", self._on_faction_changed)
        self.turn_combobox.bind("<<ComboboxSelected>>", self._on_turn_changed)
        self.district_combobox.bind("<<ComboboxSelected>>", self._on_district_changed)
    
    def _load_data(self):
        """Load initial data for the panel."""
        # Load factions
        self._load_factions()
        
        # Load turns
        self._load_turns()
        
        # Load districts
        self._load_districts()
        
        # Initialize with first values
        if self.faction_combobox["values"]:
            self.faction_var.set(self.faction_combobox["values"][0])
            
        if self.turn_combobox["values"]:
            self.turn_var.set(self.turn_combobox["values"][0])
            
        if self.district_combobox["values"]:
            self.district_var.set(self.district_combobox["values"][0])
    
    def _load_factions(self):
        """Load factions for the faction combobox."""
        try:
            # Get all factions
            factions = self.faction_repository.find_all()
            
            # Set combobox values
            faction_names = [faction.name for faction in factions]
            self.faction_combobox["values"] = faction_names
            
            # Store faction mapping
            self.faction_map = {faction.name: faction.id for faction in factions}
            
        except Exception as e:
            logging.error(f"Error loading factions: {str(e)}")
            messagebox.showerror("Error", f"Error loading factions: {str(e)}")
    
    def _load_turns(self):
        """Load available turns for the turn combobox."""
        try:
            # Get turn numbers
            query = """
                SELECT DISTINCT turn_number
                FROM actions
                ORDER BY turn_number DESC
            """
            
            results = self.db_manager.execute_query(query)
            
            if not results:
                # Check turn history
                query = """
                    SELECT DISTINCT turn_number
                    FROM turn_history
                    ORDER BY turn_number DESC
                """
                
                results = self.db_manager.execute_query(query)
            
            if not results:
                # Use current turn
                query = """
                    SELECT current_turn
                    FROM game_state
                    WHERE id = 'current'
                """
                
                results = self.db_manager.execute_query(query)
            
            # Extract turn numbers
            turn_numbers = []
            if results:
                for row in results:
                    # Convert sqlite3.Row to dict to use .get() method
                    row_dict = dict(row)
                    turn_number = row_dict.get("turn_number", row_dict.get("current_turn"))
                    if turn_number is not None:
                        turn_numbers.append(str(turn_number))
            
            # Add "All Turns" option
            if turn_numbers:
                turn_numbers.insert(0, "All Turns")
            
            # Set combobox values
            self.turn_combobox["values"] = turn_numbers
            
        except Exception as e:
            logging.error(f"Error loading turns: {str(e)}")
            messagebox.showerror("Error", f"Error loading turns: {str(e)}")
    
    def _load_districts(self):
        """Load districts for the district combobox."""
        try:
            # Get all districts
            districts = self.district_repository.find_all()
            
            # Set combobox values
            district_names = [district.name for district in districts]
            
            # Add "All Districts" option
            if district_names:
                district_names.insert(0, "All Districts")
            
            self.district_combobox["values"] = district_names
            
            # Store district mapping
            self.district_map = {district.name: district.id for district in districts}
            
        except Exception as e:
            logging.error(f"Error loading districts: {str(e)}")
            messagebox.showerror("Error", f"Error loading districts: {str(e)}")
    
    def _on_report_type_changed(self):
        """Handle report type change."""
        report_type = self.report_type.get()
        
        # Update UI based on report type
        if report_type == "monitoring":
            self.district_frame.pack(fill="x", padx=5, pady=5)
        else:
            self.district_frame.pack_forget()
    
    def _on_faction_changed(self, event):
        """Handle faction selection change."""
        # Nothing to do here for now
        pass
    
    def _on_turn_changed(self, event):
        """Handle turn selection change."""
        # Nothing to do here for now
        pass
    
    def _on_district_changed(self, event):
        """Handle district selection change."""
        # Nothing to do here for now
        pass
    
    def _load_report(self):
        """Load and display the selected report."""
        report_type = self.report_type.get()
        
        if report_type == "monitoring":
            self._load_monitoring_report()
        elif report_type == "weekly":
            self._load_weekly_report()
        elif report_type == "turn_history":
            self._load_turn_history()
    
    def _load_monitoring_report(self):
        """Load and display monitoring reports."""
        try:
            # Get selected values
            faction_name = self.faction_var.get()
            turn_selection = self.turn_var.get()
            district_selection = self.district_var.get()
            
            if not faction_name:
                messagebox.showerror("Error", "Please select a faction")
                return
                
            # Get faction ID
            faction_id = self.faction_map.get(faction_name)
            if not faction_id:
                messagebox.showerror("Error", "Invalid faction selected")
                return
            
            # Parse turn number (none for "All Turns")
            turn_number = None
            if turn_selection and turn_selection != "All Turns":
                try:
                    turn_number = int(turn_selection)
                except ValueError:
                    messagebox.showerror("Error", "Invalid turn number")
                    return
            
            # Get district ID (none for "All Districts")
            district_id = None
            if district_selection and district_selection != "All Districts":
                district_id = self.district_map.get(district_selection)
                if not district_id:
                    messagebox.showerror("Error", "Invalid district selected")
                    return
            
            # Get reports
            reports = []
            
            if district_id:
                # Get specific district reports
                query = """
                    SELECT id, district_id, turn_number, report_json, confidence_rating, created_at
                    FROM faction_monitoring_reports
                    WHERE faction_id = :faction_id
                    AND district_id = :district_id
                """
                
                params = {"faction_id": faction_id, "district_id": district_id}
                
                if turn_number is not None:
                    query += " AND turn_number = :turn_number"
                    params["turn_number"] = turn_number
                
                query += " ORDER BY turn_number DESC, created_at DESC"
                
                results = self.db_manager.execute_query(query, params)
                
                for row in results:
                    report = dict(row)
                    
                    # Parse JSON data
                    report["data"] = json.loads(report["report_json"])
                    del report["report_json"]
                    
                    # Get district name
                    district = self.district_repository.find_by_id(report["district_id"])
                    report["district_name"] = district.name if district else "Unknown District"
                    
                    reports.append(report)
            else:
                # Get all districts in selected turn
                reports = self.monitoring_manager.get_faction_reports(faction_id, turn_number)
            
            # Clear text
            self.report_text.delete("1.0", "end")
            
            # Generate report display
            if not reports:
                self.report_text.insert("end", "No monitoring reports found with the selected criteria.")
                return
            
            # Sort reports by turn and district
            reports.sort(key=lambda r: (r["turn_number"], r["district_name"]), reverse=True)
            
            # Group by turn number
            reports_by_turn = {}
            for report in reports:
                turn = report["turn_number"]
                if turn not in reports_by_turn:
                    reports_by_turn[turn] = []
                reports_by_turn[turn].append(report)
            
            # Format and display reports
            for turn, turn_reports in sorted(reports_by_turn.items(), reverse=True):
                turn_header = f"=== TURN {turn} MONITORING REPORTS ===\n\n"
                self.report_text.insert("end", turn_header)
                
                for report in turn_reports:
                    report_text = self._format_monitoring_report(report)
                    self.report_text.insert("end", report_text)
                    self.report_text.insert("end", "\n" + "-" * 50 + "\n\n")
            
            # Scroll to top
            self.report_text.see("1.0")
            
        except Exception as e:
            logging.error(f"Error loading monitoring report: {str(e)}")
            messagebox.showerror("Error", f"Error loading monitoring report: {str(e)}")
    
    def _format_monitoring_report(self, report):
        """Format a monitoring report for display.
        
        Args:
            report (dict): Monitoring report data.
            
        Returns:
            str: Formatted report text.
        """
        try:
            # Get basic report info
            district_name = report["district_name"]
            confidence = report["confidence_rating"]
            created_at = datetime.fromisoformat(report["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format header
            header = (
                f"District: {district_name}\n"
                f"Confidence Rating: {confidence}/10\n"
                f"Generated: {created_at}\n\n"
            )
            
            # Get report data
            data = report["data"]
            
            # Format perceived influences
            influences = data.get("perceived_influences", {})
            phantom_detections = data.get("phantom_detections", [])
            
            influence_text = "Detected Faction Influence:\n"
            
            if not influences and not phantom_detections:
                influence_text += "  No factions detected in this district.\n"
            else:
                # Format real factions
                for faction_id, influence in influences.items():
                    faction = self.faction_repository.find_by_id(faction_id)
                    faction_name = faction.name if faction else "Unknown Faction"
                    influence_text += f"  {faction_name}: {influence} influence\n"
                
                # Format phantom factions
                for phantom in phantom_detections:
                    faction_id = phantom["faction_id"]
                    faction = self.faction_repository.find_by_id(faction_id)
                    faction_name = faction.name if faction else "Unknown Faction"
                    influence_text += f"  {faction_name}: {phantom['perceived_influence']} influence\n"
            
            # Format district modifier
            modifier = data.get("district_modifier")
            modifier_text = "District Difficulty Modifier:\n"
            
            if not modifier:
                modifier_text += "  No information available about district difficulty.\n"
            elif modifier.get("direction_only", False):
                direction = modifier.get("direction", "unknown")
                modifier_text += f"  District appears to have a {direction} modifier to difficulty checks.\n"
            else:
                value = modifier.get("value", 0)
                if value == 0:
                    modifier_text += "  District has no modifier to difficulty checks.\n"
                else:
                    sign = "+" if value > 0 else ""
                    modifier_text += f"  District has a {sign}{value} modifier to difficulty checks.\n"
            
            # Format discovered rumors
            rumors = data.get("discovered_rumors", [])
            rumor_text = "Discovered Information:\n"
            
            if not rumors:
                rumor_text += "  No new information discovered.\n"
            else:
                for rumor_id in rumors:
                    rumor = self.rumor_repository.find_by_id(rumor_id)
                    if rumor:
                        rumor_text += f"  • {rumor.rumor_text}\n"
            
            # Combine all sections
            full_report = header + influence_text + "\n" + modifier_text + "\n" + rumor_text
            
            return full_report
            
        except Exception as e:
            logging.error(f"Error formatting monitoring report: {str(e)}")
            return f"Error formatting report: {str(e)}"
    
    def _load_weekly_report(self):
        """Load and display weekly intelligence summary."""
        try:
            # Get selected values
            faction_name = self.faction_var.get()
            turn_selection = self.turn_var.get()
            
            if not faction_name:
                messagebox.showerror("Error", "Please select a faction")
                return
                
            # Get faction ID
            faction_id = self.faction_map.get(faction_name)
            if not faction_id:
                messagebox.showerror("Error", "Invalid faction selected")
                return
            
            # Parse turn number (none for "All Turns")
            turn_number = None
            if turn_selection and turn_selection != "All Turns":
                try:
                    turn_number = int(turn_selection)
                except ValueError:
                    messagebox.showerror("Error", "Invalid turn number")
                    return
            
            # Clear text
            self.report_text.delete("1.0", "end")
            
            if turn_number is None:
                # Get latest turn
                query = """
                    SELECT MAX(turn_number) as latest_turn
                    FROM faction_monitoring_reports
                    WHERE faction_id = :faction_id
                """
                
                result = self.db_manager.execute_query(query, {"faction_id": faction_id})
                if result and result[0]["latest_turn"] is not None:
                    turn_number = result[0]["latest_turn"]
                else:
                    self.report_text.insert("end", "No monitoring reports found for this faction.")
                    return
            
            # Generate weekly report
            weekly_report = self.monitoring_manager.generate_weekly_report(faction_id, turn_number)
            
            if "error" in weekly_report:
                self.report_text.insert("end", f"Error generating report: {weekly_report['error']}")
                return
            
            # Format report
            report_text = self._format_weekly_report(weekly_report)
            
            # Display report
            self.report_text.insert("end", report_text)
            
            # Scroll to top
            self.report_text.see("1.0")
            
        except Exception as e:
            logging.error(f"Error loading weekly report: {str(e)}")
            messagebox.showerror("Error", f"Error loading weekly report: {str(e)}")
    
    def _format_weekly_report(self, report):
        """Format a weekly intelligence summary for display.
        
        Args:
            report (dict): Weekly report data.
            
        Returns:
            str: Formatted report text.
        """
        try:
            # Get basic report info
            faction_name = report["faction_name"]
            turn_number = report["turn_number"]
            report_time = datetime.fromisoformat(report["report_time"]).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format header
            header = (
                f"=== WEEKLY INTELLIGENCE SUMMARY ===\n"
                f"Faction: {faction_name}\n"
                f"Turn: {turn_number}\n"
                f"Generated: {report_time}\n\n"
                f"This report consolidates all intelligence gathered during the past week.\n"
                f"Districts are listed in order of intelligence confidence.\n\n"
            )
            
            # Sort districts by confidence rating (highest first)
            districts = sorted(report["districts"], key=lambda d: d["confidence_rating"], reverse=True)
            
            # Format district sections
            district_sections = []
            
            for district_data in districts:
                district_name = district_data["district_name"]
                confidence = district_data["confidence_rating"]
                
                district_header = (
                    f"--- {district_name} (Confidence: {confidence}/10) ---\n\n"
                )
                
                # Format factions
                factions_text = "Detected Factions:\n"
                
                detected_factions = district_data["factions_detected"]
                if not detected_factions:
                    factions_text += "  No factions detected in this district.\n"
                else:
                    # Sort by influence (highest first)
                    detected_factions.sort(key=lambda f: f["influence"], reverse=True)
                    
                    for faction in detected_factions:
                        faction_name = faction["faction_name"]
                        influence = faction["influence"]
                        is_phantom = faction["is_phantom"]
                        
                        phantom_text = " (Low confidence)" if is_phantom else ""
                        factions_text += f"  {faction_name}: {influence} influence{phantom_text}\n"
                
                # Format district modifier
                modifier = district_data.get("district_modifier")
                modifier_text = "District Conditions:\n"
                
                if not modifier:
                    modifier_text += "  No information available about district conditions.\n"
                elif modifier.get("direction_only", False):
                    direction = modifier.get("direction", "unknown")
                    modifier_text += f"  District appears to have a {direction} modifier to difficulty checks.\n"
                else:
                    value = modifier.get("value", 0)
                    if value == 0:
                        modifier_text += "  District has normal difficulty conditions.\n"
                    else:
                        sign = "+" if value > 0 else ""
                        modifier_text += f"  District has a {sign}{value} modifier to difficulty checks.\n"
                
                # Format discovered rumors
                rumors = district_data.get("discovered_rumors", [])
                rumor_text = "Intelligence:\n"
                
                if not rumors:
                    rumor_text += "  No significant intelligence gathered.\n"
                else:
                    for rumor in rumors:
                        rumor_text += f"  • {rumor['rumor_text']}\n"
                
                # Combine district section
                district_section = district_header + factions_text + "\n" + modifier_text + "\n" + rumor_text
                district_sections.append(district_section)
            
            # Combine all sections
            if district_sections:
                full_report = header + "\n".join(district_sections)
            else:
                full_report = header + "No intelligence reports available for this turn."
            
            return full_report
            
        except Exception as e:
            logging.error(f"Error formatting weekly report: {str(e)}")
            return f"Error formatting report: {str(e)}"
    
    def _load_turn_history(self):
        """Load and display turn history."""
        try:
            # Get selected values
            turn_selection = self.turn_var.get()
            
            # Parse turn number (none for "All Turns")
            turn_number = None
            if turn_selection and turn_selection != "All Turns":
                try:
                    turn_number = int(turn_selection)
                except ValueError:
                    messagebox.showerror("Error", "Invalid turn number")
                    return
            
            # Get turn history
            query = """
                SELECT turn_number, phase, action_description, result_description, created_at
                FROM turn_history
            """
            
            params = {}
            
            if turn_number is not None:
                query += " WHERE turn_number = :turn_number"
                params["turn_number"] = turn_number
            
            query += " ORDER BY turn_number DESC, created_at ASC"
            
            results = self.db_manager.execute_query(query, params)
            
            # Clear text
            self.report_text.delete("1.0", "end")
            
            if not results:
                self.report_text.insert("end", "No turn history found with the selected criteria.")
                return
            
            # Group by turn number
            history_by_turn = {}
            for row in results:
                data = dict(row)
                turn = data["turn_number"]
                if turn not in history_by_turn:
                    history_by_turn[turn] = []
                history_by_turn[turn].append(data)
            
            # Format and display history
            for turn, entries in sorted(history_by_turn.items(), reverse=True):
                turn_header = f"=== TURN {turn} HISTORY ===\n\n"
                self.report_text.insert("end", turn_header)
                
                for entry in entries:
                    # Format timestamp
                    timestamp = datetime.fromisoformat(entry["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Format phase
                    phase = entry["phase"].replace("_", " ").title()
                    
                    # Format entry
                    entry_text = (
                        f"[{timestamp}] Phase: {phase}\n"
                        f"Action: {entry['action_description']}\n"
                    )
                    
                    if entry["result_description"]:
                        entry_text += f"Result: {entry['result_description']}\n"
                        
                    entry_text += "\n"
                    
                    self.report_text.insert("end", entry_text)
                
                self.report_text.insert("end", "\n" + "=" * 50 + "\n\n")
            
            # Scroll to top
            self.report_text.see("1.0")
            
        except Exception as e:
            logging.error(f"Error loading turn history: {str(e)}")
            messagebox.showerror("Error", f"Error loading turn history: {str(e)}")