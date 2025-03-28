# Faction Management System UI Specification - Simplified Windows Implementation

## CRITICAL IMPLEMENTATION REQUIREMENT
**All UI components must be directly integrated with the database and core logic systems. No hardcoded test data or mock implementations are acceptable.**

### Database Integration Requirements - IMPLEMENT FIRST
- **PRIORITY**: Database integration must be implemented BEFORE any UI components
- Every UI component must load data directly from the database using repository classes
- All changes made through the UI must be immediately persisted to the database
- UI components must reflect the current state of the database at all times
- Lists, dropdown menus, and selection controls must dynamically populate with actual database entities
- No UI component should contain hardcoded example data (faction names, values, etc.)
- Implement a standardized pattern for UI-database synchronization across all components

### Core Logic Integration Requirements
- All calculations must use the actual logic implementations from previous phases
- Turn processing must use the complete turn resolution system
- Monitoring must use the real monitoring system
- All mechanics must function through the UI exactly as specified in requirements
- No simplified UI-only implementations of game logic are acceptable

### Testing Requirements
- For comprehensive testing guidelines, refer to the Unified Testing Framework document

## Application Architecture

### 1. Implementation Approach
- **Desktop Application**: Standalone Windows executable
- **Technology Stack**:
  - **Primary Technology**: Python with Tkinter (built-in GUI library)
  - **Data Storage**: SQLite database for persistence
  - **Deployment**: PyInstaller for creating standalone executables
- **Offline Operation**: All functionality works without internet connectivity

### 2. Global UI Structure
- **Main Window**: Single application window with tabbed interface
- **Navigation Tabs**: Top tabs for accessing main sections
- **Status Bar**: Bottom bar showing system status, current turn, save status
- **Menu Bar**: Standard Windows-style menu for file operations and tools

### 3. Layout Approach
- **Tabbed Design**: Separate tabs for major functionality areas
- **Simple Forms**: Standard input widgets for data entry
- **Tables**: Use of Tkinter Treeview for data display
- **Basic Canvas**: Simple 2D visualization for maps

## Core Screens and Workflows

### 1. Dashboard Tab

#### Layout
- **Overview Panel**: Current turn, faction summary, district summary
- **Quick Action Buttons**: Process turn, create newspaper, save game
- **Notification Area**: List of pending actions, conflicts, and alerts
- **Simple Mini-Map**: Basic visualization of current map state
- **Turn Phase Indicator**: Text-based indication of current phase

#### Implementation
- Use Tkinter Frames to organize content
- Implement buttons using standard Tkinter Button widgets
- Use Listbox or Treeview for notifications
- Implement mini-map with Tkinter Canvas

### 2. District Management Tab

#### Layout
- **District List**: Treeview list of all districts
- **District Detail Form**: Form-based editor for district properties
- **Influence Display**: Table showing faction influence in selected district
- **Rumor Management**: Table of rumors with editing controls

#### Implementation
- Use Tkinter Treeview for district list
- Implement forms with standard Entry, Combobox, and Spinbox widgets
- Use Treeview for influence and rumor tables
- Add simple button controls for editing operations

### 3. Map Visualization Tab

#### Layout
- **Map Canvas**: Interactive canvas for displaying and editing map elements
- **Base Map Display**: Area showing the imported background map image
- **District Overlay**: Vector shapes representing districts drawn on top of base map
- **Influence Visualization**: Faction influence displayed as colored dots within districts
- **Stronghold Indicators**: Special markers showing faction strongholds
- **Legend**: Color key for faction influence and stronghold indicators
- **District Selection**: Dropdown or list for selecting districts
- **View Controls**: Radio buttons for different visualization modes (DM view, faction views)
- **Editing Tools**: Controls for drawing and modifying district shapes

#### Implementation
- Use Tkinter Canvas for rendering the map visualization system
- Support importing background images (PNG, JPG, SVG) as base maps
- Implement vector-based district drawing with polygon shapes
- Create district-to-shape assignment mechanism to link data with visuals
- Implement influence visualization using colored dots using faction's color attribute
- Add stronghold visualization using distinct faction-colored markers
- Enable district shape editing with drawing tools (add, modify, delete points)
- Implement faction-specific map generation based on perceived influence
- Create export functionality for maps (PNG, PDF formats)
- Add zoom/pan navigation for detailed map inspection
- Support saving and loading of district shape data separate from base map

#### Map System Features

##### Base Map Management
- **Import Base Map**: Support for importing PNG, JPG, or SVG files as background
- **Base Map Scaling**: Automatically or manually scale the imported map
- **Base Map Replacement**: Ability to replace base map while preserving district shapes

##### District Shape Management
- **District Drawing Tools**: Polygon drawing tools with point-by-point creation
- **Shape Editing**: Add, move, or delete points in existing district shapes
- **District Assignment**: Link drawn shapes to district data objects
- **Shape Styling**: Configure border and fill styles for district shapes
- **Post-Game Editing**: Modify existing shapes or add new districts during gameplay

##### Influence Visualization
- **Dot-Based Representation**: Display faction influence as colored dots using faction's color attribute
- **Automatic Dot Arrangement**: Algorithm to position dots within district boundaries
- **Dot Scaling**: Adjust dot size based on district size and influence levels
- **Stronghold Markers**: Special indicators for faction strongholds using faction's color attribute
- **Custom Styling**: Configurable styles for influence visualization, always respecting faction colors

##### Faction-Specific Map Generation
- **Perception-Based Views**: Generate maps based on faction's perceived intelligence
- **Turn-Based Snapshots**: Create map images at the end of each turn
- **Fog of War**: Hide or distort information unknown to the faction
- **Intelligence Quality Effects**: Show more accurate information for better intelligence rolls
- **Export Options**: Save generated maps as image files or printable reports

##### Technical Implementation Details
- Use Tkinter Canvas with custom drawing capabilities
- Implement district shapes as polygon objects with editable points
- Store shape coordinates relative to base map dimensions
- Use scaling factor to maintain proper proportions when resizing
- Create object-to-data binding system for district shapes
- Implement undo/redo functionality for shape editing

### 4. Faction Management Tab

#### Layout
- **Faction List**: List of all factions with key metrics
- **Faction Editor**: Form for editing faction properties
- **Faction Color Selection**: Color picker for selecting faction representation color
- **Relationship Table**: Grid for setting inter-faction relationships
- **Resource Tracker**: Simple inputs for tracking faction resources

#### Implementation
- Use Treeview for faction list
  - Include color indicators as visual cues next to faction names
- Create form with standard input widgets
- Implement color picker using Tkinter's colorchooser dialog
  - Display current color in a small colored rectangle button
  - Clicking opens the color picker dialog
- Implement relationship table as a grid of Combobox widgets
- Use Spinbox widgets for resource tracking

#### Color Management
- **Random Color Generation**: When creating a new faction, generate a random distinctive color
- **Color Persistence**: Save color selections directly to database using repository
- **Color Validation**: Ensure colors are valid hex format

### 5. Agent & Squadron Management Tab

#### Layout
- **Piece List**: Filterable list of all agents and squadrons
- **Piece Editor**: Form for editing piece properties
- **Assignment Controls**: Interface for assigning pieces to districts
- **Batch Actions**: Simple buttons for common operations

#### Implementation
- Use Treeview with filtering capability
- Create property editor with standard form widgets
- Implement assignment with Combobox and Button widgets
- Add batch action buttons with confirmation dialogs

### 6. Turn Resolution Tab

#### Layout
- **Phase Controls**: Next/Previous buttons for navigating phases
- **Current Phase Display**: Frame showing controls for current phase
- **Results Display**: Text or table output showing outcomes
- **Conflict Resolution**: Specialized interface for manual conflict resolution
- **Turn Part Indicator**: Displays whether in Part 1 (Pre-Conflict) or Part 2 (Post-Conflict)
- **Action Assignment Panel**: Specialized UI for assigning the four action types:
  - **Monitoring Actions**: Controls for assigning monitoring tasks
  - **Influence Actions**: Controls for gain/take influence actions
  - **Freeform Actions**: Form with DC setting, attribute/skill selection, and description field
  - **Initiate Conflict Actions**: Form with DC setting, attribute/skill selection, target faction selection, and description field

#### Implementation
- Use Button widgets for phase navigation
- Create card-style layout with Frame widgets
- Implement results display with Text or Treeview widgets
- Create specialized conflict resolution interface with:
  - Conflict details display
  - Faction participation list
  - Win/Loss/Draw selector
  - Resolution notes field
  - Apply Resolution button
- Create specialized panels for each action type:
  - Monitoring panel with automatic skill selection
  - Influence panel with target selection and automatic DC calculation
  - Freeform action panel with manual DC setting, attribute/skill selection, and description field
  - Initiate Conflict panel with manual DC setting, attribute/skill selection, target faction selection, and description field
- Implement two-part turn resolution with persistent state between parts
- Create ability to pause and resume turn processing after conflict resolution

#### Action Assignment UI Components

##### Monitoring Action Panel
- **District Selection**: Dropdown for target district
- **Information**: Display of district's preferred attributes/skills for monitoring
- **Auto-Selected Values**: Display automatically selected attributes/skills
- **Manual Difficulty Modifier**: Spinbox or slider for optional manual modifier (-10 to +10)
- **Preview**: Estimate of roll modifier and potential outcome tiers

##### Influence Action Panel
- **Action Type**: Radio buttons for "Gain Influence" or "Take Influence"
- **District Selection**: Dropdown for target district
- **Target Faction**: Dropdown for target faction (for Take Influence)
- **Auto-Calculated DC**: Display of calculated DC with breakdown of modifiers
- **District Preferences**: Display of district's preferred attributes/skills
- **Auto-Selected Values**: Display automatically selected attributes/skills
- **Manual Difficulty Modifier**: Spinbox or slider for optional manual modifier (-10 to +10)
- **Preview**: Estimate of success probability

##### Freeform Action Panel
- **Action Description**: Text field for detailed description (up to 500 chars)
- **DC Setting**: Spinbox for manually setting DC (5-30)
- **Attribute Selection**: Dropdown for selecting primary attribute/type
- **Skill Selection**: Dropdown for selecting relevant skill
- **Target Faction**: Optional dropdown for selecting target faction
- **District Selection**: Dropdown for selecting district
- **Manual Difficulty Modifier**: Spinbox or slider for optional manual modifier (-10 to +10)
- **Resources**: Optional fields for resource allocation
- **Preview**: Estimate of success probability

##### Initiate Conflict Action Panel
- **Action Description**: Text field for detailed conflict description (up to 500 chars)
- **DC Setting**: Spinbox for manually setting DC (5-30)
- **Attribute Selection**: Dropdown for selecting primary attribute/type
- **Skill Selection**: Dropdown for selecting relevant skill
- **Target Faction**: Required dropdown for selecting target faction
- **District Selection**: Dropdown for selecting district
- **Manual Difficulty Modifier**: Spinbox or slider for optional manual modifier (-10 to +10)
- **Preview**: Estimate of success probability

#### Conflict Resolution UI Components

##### Conflict List Panel
- **Conflicts Table**: List of all pending conflicts with details
- **Conflict Type Filter**: Filter conflicts by type (manual, relationship, target, adjacent)
- **District Filter**: Filter conflicts by district
- **Faction Filter**: Filter conflicts by involved faction

##### Conflict Resolution Panel
- **Conflict Details**: Display conflict type, location, and involved factions
- **Factions Display**: Shows all factions involved with roles (initiator, target, ally, adjacent)
- **Pieces List**: Shows all pieces involved with their actions and roll results
- **Resolution Controls**:
  - Winning Faction selector
  - Draw checkbox
  - Special ruling notes field
- **Resolution History**: Display of previously resolved conflicts
- **Apply Button**: Submits the resolution and updates the system

### 7. Newspaper Editor Tab

#### Layout
- **Issue Properties**: Form for setting issue metadata
- **Section List**: Listbox for managing sections
- **Article List**: List of articles in current section
- **Article Editor**: Simple text editor for content

#### Implementation
- Use standard form controls for issue properties
- Implement Listbox for section management
- Use Treeview for article list
- Create Text widget with basic formatting for article editing
- Add export button for generating newspaper files

### 8. Reports Tab

#### Layout
- **Report Selector**: Dropdown for different report types
- **Faction Filter**: Dropdown to filter by faction perspective
- **Report Viewer**: Text display for generated reports
- **Export Button**: Button to save reports as text or CSV

#### Implementation
- Use Combobox widgets for selectors
- Implement report viewer with Text widget
- Add simple export functionality with filedialog
- Create print function for reports

### 9. Game Setup Dialog

#### Layout
- **Wizard Interface**: Simple multi-step dialog
- **Setup Forms**: Sequence of forms for initial setup
- **Navigation Buttons**: Next/Back buttons between steps
- **Template Options**: Dropdown for selecting templates

#### Implementation
- Create custom dialog window for setup wizard
- Use Frame switching for different steps
- Implement validation with error messages
- Add progress indicator for current step

## Implementation Components

### 1. Database Integration Components (IMPLEMENT FIRST)
- **Repository Access Layer**: Create standardized access to all repositories
- **Data Binding Mechanism**: Implement UI-to-database binding
- **Change Notification System**: Create update notifications when data changes
- **Validation Framework**: Ensure data validity before database operations
- **Transaction Management**: Implement proper transaction handling for UI operations

### 2. Data Display Components
- **Treeview**: For all tabular data (districts, factions, pieces)
- **Text**: For report display and article editing
- **Labels**: For static information display
- **Canvas**: For basic map visualization

### 3. Input Components
- **Entry**: For text input
- **Spinbox**: For numeric values with bounds
- **Combobox**: For selection from predefined options
- **Checkbutton**: For boolean values
- **Radiobutton**: For mutually exclusive options

### 4. Layout Components
- **Frame**: For organizing widgets
- **LabelFrame**: For grouping related controls
- **Notebook**: For tab management
- **PanedWindow**: For resizable areas (when needed)

### 5. Dialog Components
- **messagebox**: For alerts, confirmations, and errors
- **filedialog**: For file operations
- **simpledialog**: For simple input prompts
- **Custom dialogs**: For complex operations like conflict resolution

### 6. Styling Approach
- Use ttk themed widgets for modern appearance
- Create consistent padding and spacing
- Define a simple color scheme for the application
- Use standard Windows UI patterns where possible

## Key UI Workflows

### 1. Game Setup Workflow
```
File Menu > New Game
└── Setup Wizard Dialog
    ├── Basic Information
    │   ├── Campaign Name
    │   ├── Game Parameters
    │   └── Template Selection
    ├── District Definition
    │   ├── Create Districts
    │   ├── Set Properties
    │   └── Define Adjacency
    ├── Faction Creation
    │   ├── Define Factions
    │   ├── Assign Random Colors (can be changed)
    │   ├── Set Relationships
    │   └── Assign Resources
    ├── Piece Creation
    │   ├── Create Agents
    │   ├── Create Squadrons
    │   └── Assign to Factions
    └── Initial Setup
        ├── Set Starting Influence
        ├── Place Strongholds
        └── Finalize Setup
```

### 2. Turn Resolution Workflow
```
Process Turn Tab
└── Start Turn Button
    ├── Preparation Phase
    │   └── Review and Continue
    ├── Influence Decay Phase
    │   ├── Review Results
    │   └── Confirm Changes
    ├── Assignment Phase
    │   ├── Select Faction
    │   ├── Assign Actions
    │   └── Confirm All Assignments
    ├── Conflict Detection Phase
    │   ├── Process Manual Conflicts
    │   ├── Process Automatic Conflicts
    │   ├── Calculate Adjacent Participation
    │   └── Review Potential Conflicts
    ├── Action Roll Phase
    │   ├── Calculate All Rolls
    │   └── Display Results

    --- TURN PROCESSING PAUSED FOR MANUAL CONFLICT RESOLUTION ---
    
    ├── Manual Conflict Resolution Phase
    │   ├── Review Conflict Details
    │   ├── Determine Outcomes (Win/Loss/Draw)
    │   ├── Add Resolution Notes
    │   └── Apply Resolutions
    
    --- TURN PROCESSING RESUMED ---
    
    ├── Action Resolution Phase
    │   ├── Apply Conflict Outcomes
    │   ├── Process Automatic Actions
    │   └── Apply Results
    ├── Random Walk Update Phase
    │   └── View Updated Modifiers
    ├── Monitoring Phase
    │   └── Process Results
    ├── Faction Passive Monitoring Phase
    │   └── Process Automatic Faction Monitoring
    ├── Rumor DC Update Phase
    │   └── Apply Updates
    ├── Map Update Phase
    │   └── Generate Maps
    └── Turn Completion Phase
        ├── Save Game
        └── Generate Reports
```

### 3. Newspaper Creation Workflow
```
Newspaper Tab
└── Create New Issue Button
    ├── Issue Setup
    │   ├── Set Number and Date
    │   └── Configure Sections
    ├── Content Generation
    │   ├── Auto-Generate Articles
    │   ├── Edit Generated Content
    │   └── Add Manual Articles
    ├── Article Arrangement
    │   ├── Organize Articles
    │   └── Preview Layout
    └── Publication
        ├── Save to Archive
        └── Export for Distribution
```

## Technical Implementation Notes

### 1. Application Structure
```
faction_manager/
├── main.py                  # Application entry point
├── database/                # Database handling
│   ├── db_manager.py        # Database connection and operations
│   └── models.py            # Data models
├── ui/                      # UI components 
│   ├── main_window.py       # Main application window
│   ├── dashboard.py         # Dashboard panel
│   ├── district_panel.py    # District management
│   ├── faction_panel.py     # Faction management
│   ├── map_panel.py         # Simple map visualization
│   ├── turn_panel.py        # Turn resolution
│   └── newspaper_panel.py   # Newspaper editor
└── logic/                   # Core game logic
    ├── turn_processor.py    # Turn resolution logic
    ├── monitoring.py        # Monitoring system
    ├── influence.py         # Influence mechanics
    └── newspaper.py         # Newspaper generation
```

### 2. Dependencies
- **Python**: 3.8 or higher
- **Tkinter**: Built-in with Python (verify during installation)
- **sqlite3**: Built-in with Python
- **Pillow**: For image handling if needed
- **PyInstaller**: For creating standalone executable

### 3. Packaging Instructions
1. Install PyInstaller: `pip install pyinstaller`
2. Create spec file: `pyinstaller --name="Faction Manager" --windowed main.py`
3. Build executable: `pyinstaller "Faction Manager.spec"`
4. Distribute dist folder or create simple installer

### 4. Performance Considerations
- Keep UI responsive by running long operations in separate threads
- Use database indexes for frequently queried fields
- Implement asynchronous loading for large datasets
- Cache frequently accessed data
- Optimize map rendering for performance

### 5. System Requirements
- Windows 10 or later
- 4GB RAM minimum
- 500MB disk space
- 1280x720 minimum screen resolution
- Admin rights for installation only

### 6. File Operations
- Use standard Windows file dialogs
- Store game files in user's Documents folder
- Implement auto-save every 15 minutes
- Add file recovery for crashed sessions
- Store configuration in AppData folder

4. **Faction Support Status UI Tests**:
   - Test faction selection UI with relationship value display
   - Verify support toggle is only enabled for relationships with value +2 (Allied)
   - Validate support status persistence through turn processing
   - Test UI updates when relationship values change
   - Verify proper integration with conflict detection system