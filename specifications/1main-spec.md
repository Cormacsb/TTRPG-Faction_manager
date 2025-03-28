# Faction Management System Specification

## Core Functionality Requirements

### 1. Territory Control Tracking
- Track true control levels for each faction in each city district
- Generate admin map for DM and faction-specific "fog of war" maps
- Support overlay on existing map (PNG, SVG, JSON)

### 2. Faction Management
- Create/manage factions with unique properties
- Track faction relationships (-2 to +2 scale)
- Track faction monitoring bonus

### 3. Agent & Squadron System
- Create/manage individual agents with stats and abilities
- Create/manage squadrons with aptitude specializations
- Track location and activities

### 4. Action Resolution
- **Auto-calculated actions**: Information gathering and gain/take control
- **Manually set actions**: All other actions require manual DC and skill selection
- Calculate success chances for faction activities
- Identify conflicts between factions in the same location
- Roll dice and apply modifiers
- Report critical success/failure (beat DC by 10+/miss DC by 10+)

### 5. Information Distribution
- Track faction knowledge based on intelligence gathering
- Generate appropriate misinformation for fog of war maps

### 6. Newspaper System
- Independent system called between turns
- Combines auto-selected rumors with manually written content
- Provides hints about game state to factions
- Archives all previous issues

## Detailed Specifications

### Map System
- Distinct districts/neighborhoods with control values (0-10) per faction
- Support overlay system using existing PNG/SVG/JSON maps
- Generate weekly maps with color coding for control levels
- **Map Zoom Functionality**:
  - Implement smooth zooming of the map with mouse wheel and/or zoom controls
  - Maintain consistent positioning of district shapes relative to the base map during zoom operations
  - Ensure district shapes scale proportionally with the base map when zooming
  - Support zoom levels from 25% to 400% of original size
  - Provide zoom level indicator and reset-to-default button
  - Implement proper handling of text scaling for district labels and other map elements
  - Support panning of zoomed maps through drag operations

### District System
- Each district has:
  - Name and description
  - Available influence slots (total of 10)
  - Current influence distribution among factions
  - Remaining influence pool (10 minus sum of faction influence)
  - Likeability values for each faction (-5 to +5)
  - Strongholds: Boolean value per faction per district
  - List of discoverable rumors with associated DCs
  - Information status tracking
  - **District Attributes for Balancing**:
    - Commerce value (0-10): Represents economic activity and non-combat potential
    - Muster value (0-10): Represents military potential and combat capabilities
    - Aristocratic value (0-10): Represents political influence and social standing
  - **Preferred action parameters**:
    - For gain/take control: Preferred agent attribute, agent skill, and squadron aptitude
    - For monitoring: Preferred agent attribute, agent skill, and squadron aptitude (refers to the "monitoring" aptitude)

### Faction System
- Each faction has:
  - Name and description
  - Control values in each district
  - Relationship values with other factions (-2 to +2)
  - List of controlled agents and squadrons
  - Information gathering bonus (faction-wide)
  - List of known information pieces
  - **Faction Modifiers**:
    - Named modifiers with values (e.g., "Wealthy Patron: Commerce +10")
    - Modifiers can affect Commerce, Muster, and Aristocratic values
    - Each modifier has a name, type, and value
    - Modifiers can be added or removed as game conditions change
  - **Attribute Totals**:
    - Total Commerce: Sum of (Influence × Commerce Value) across all districts
    - Total Muster: Sum of (Influence × Muster Value) across all districts
    - Total Aristocratic: Sum of (Influence × Aristocratic Value) across all districts

### Faction Relationship System
- Track relationships between factions (-2 to +2 scale)
- Adjust relationships based on actions and results
- Provide relationship matrix for DM overview
- Automatically generate relationship modifiers for interactions

### Faction Support System
- Support between factions is managed through a simple boolean flag system:
  - Each faction-to-faction relationship has a support status (boolean value)
  - This support status defaults to 0 (no support)
  - For allied factions only (relationship +2), this status can be manually changed to 1 (will support)
  - For all other relationship values (-2, -1, 0, +1), support status is always 0 and cannot be changed
- When a faction is involved in a conflict:
  - If another faction has set their support status to 1 for this faction, their pieces join the conflict
  - Only pieces in the same district as the conflict may join
  - Supporting pieces cannot perform their assigned actions if they join a conflict
  - Supporting pieces are subject to the same outcome as the faction they support

### Relationship Mechanics
- **-2 (Hot War)**: 
  - Squadrons give -2 to enemy rolls within mobility range
  - Agents give -4 to a single randomly selected enemy piece in same district
  - 40% chance for impromptu manual conflict per turn
- **-1 (Cold War)**: 
  - Squadrons give -1 to enemy rolls within mobility range
  - Agents give -2 to a single randomly selected enemy piece in same district
  - 10% chance for impromptu manual conflict per turn
- **0 (Neutral)**: No effect
- **+1 (Friendly)**: Can negotiate assistance
- **+2 (Allied)**: Can decide whether pieces support each other in conflicts

When a manual conflict occurs due to negative relations:
- Affected pieces do not perform their selected actions
- DM receives a report listing all conflicts, involved pieces, and their intended actions

#### Roll Penalty Targeting Priority
- **Agents**: 
  - Always target enemy agents first if present
  - Only target enemy squadrons if no enemy agents are in their district
  - Apply penalty to a single randomly selected target based on priority
- **Squadrons**: 
  - Always target enemy squadrons first if present
  - Only target enemy agents if no enemy squadrons are in range
  - Apply penalties based on mobility range and limit
  - Choose targets randomly within priority type

### Agent Statistics
- **Primary Stats**: Intellect, Presence, Finesse, Might, Attunement (0-5 each)
- **Skills**: Infiltration, Persuasion, Combat, Streetwise, Survival, Artifice, Arcana (0-5 each)

### Squadron Statistics
- **Mobility**: 0-5 (determines range of influence and assistance)
  - 0: Cannot impact enemy pieces
  - 1: Can impact up to 1 enemy piece in same district
  - 2: Can impact up to 1 enemy piece in same district or adjacent district
  - 3: Can impact up to 1 enemy piece in same district AND up to 1 piece in an adjacent district
  - 4: Can impact up to 2 enemy pieces in same district or adjacent districts
  - 5: Can impact up to 1 enemy piece in same district AND up to 2 pieces in same district or adjacent districts
  - Chance to join a conflict in an adjacent district = mobility × 10%
- **Aptitudes**: Combat, Underworld, Social, Technical, Labor, Arcane, Wilderness, Monitoring (-3 to +5 each, default: -1)

## Action Resolution System

### 1. Main Action Types

#### A. Monitoring
- **No manually set DC** - roll result determines quality/accuracy of information
- **Sources**:
  - Agents assigned to monitor
  - Squadrons assigned to monitor
  - Any squadron doing a different action (monitors with disadvantage)
  - Passive faction monitoring (in districts with ≥4 influence)
- **Auto-selection of skills**: System uses district's preferred agent attribute, agent skill, and squadron aptitude

#### A.1 Faction Passive Monitoring
- Automatically occurs in districts where faction has ≥4 influence
- No piece assignment needed - this represents the faction's natural information gathering
- Roll: d20 + (Influence ÷ 2) + Faction monitoring bonus
- Processed after agent and squadron monitoring activities in a separate phase
- Uses the same information quality tiers as other monitoring sources
- Results are combined with other monitoring sources to generate weekly intelligence reports

#### B. Gain/Take Control (Influence)
- **Auto-calculated DC** based on:
  - Base DC: 11
  - Modified by district's likeability value for faction
  - Further modified by current influence level:
    - 0 influence: +3 to DC
    - 1 influence: +1 to DC
    - 2-3 influence: -1 to DC
    - 4-5 influence: No modifier
    - 6 influence: +1 to DC
    - 7 influence: +2 to DC
    - 8 influence: +3 to DC
    - 9 influence: +4 to DC
  - Stronghold bonus: -2 if present
  - Weekly fluctuation (random walk between -2 and +2)
  - Target selection (+3 if targeting specific faction)
- **Auto-selection of skills**: System uses district's preferred agent attribute, agent skill, and squadron aptitude

#### C. Initiate Conflict
- **Manually set DC** required when assigning the action
- **Manually specified skills** needed for the action
- **Manual targeting** of specific faction required
- **Success Results**:
  - Standard Success: 70% chance to trigger a manual conflict
  - Critical Success (beat DC by 10+): 95% chance to trigger a manual conflict
- When a manual conflict is triggered:
  - Affected pieces do not perform their selected actions
  - DM receives a report listing all conflicts, involved pieces, and their intended actions
  
#### D. Other Actions
- **Manually set DC** required when assigning the action
- **Manually specified skills** needed for the action
- **Resolution reporting**: Success, Failure, Critical Success, or Critical Failure
- DM manually implements effects based on outcome and context

### 2. Turn Resolution System

#### Weekly Phase Order
1. **Preparation Phase**: Calculate stronghold-based decay protection
2. **Influence Decay Phase**: Apply percentage-based and district saturation decay
3. **Assignment Phase**: Factions assign pieces to districts with specific tasks
4. **Conflict Detection Phase**: 
   - Check for manually initiated conflicts (from Initiate Conflict actions)
   - Check for spontaneous conflicts based on faction relationships
   - For each pair of factions with pieces in the same district:
     - -1 relationship: 10% chance of manual conflict
     - -2 relationship: 40% chance of manual conflict
   - Check for adjacent conflicts that squadrons might join based on mobility
   - Calculate adjacent district participation (Mobility × 10% chance)
   - Process faction support based on support settings
   - Generate conflict reports for all detected conflicts
5. **Action Roll Phase**:
   - Calculate rolls for all actions (including pieces involved in conflicts)
   - Record results but do not apply effects for pieces in conflicts

   --- TURN PROCESSING PAUSED FOR MANUAL CONFLICT RESOLUTION ---

6. **Manual Conflict Resolution Phase**:
   - DM reviews all conflicts and determines outcomes (win/loss/draw)
   - System records the results of manual resolution

   --- TURN PROCESSING RESUMED ---

7. **Action Resolution Phase**: 
   - Apply conflict resolution results (winning sides proceed normally, losing sides fail)
   - Apply -2 penalty to actions in draw outcomes
   - Process all non-conflicted actions normally
8. **Random Walk Update Phase**: Update district weekly DC modifiers (bounded between -2 and +2)
9. **Monitoring Phase**: Process monitoring activities from agent and squadron pieces
10. **Faction Passive Monitoring Phase**: Process automatic monitoring for factions with ≥4 influence in districts
11. **Rumor DC Update Phase**: Decrease all rumor DCs by 1
12. **Map Update Phase**: Update true influence map, generate faction-specific maps
13. **Turn Completion Phase**: Increment turn counter, save game state, generate summary

### 3. Influence Decay Mechanics
- **Base Decay**:
  - For each district where faction has >2 influence: 
    - 5% chance to lose 1 influence for each point above 2
  - If faction has a stronghold: 
    - 5% chance to lose 1 influence for each point above 5
  
- **Saturation Decay**:
  - Districts with 9/10 influence slots filled:
    - 10% chance for one faction to lose influence
    - Random selection weighted by proportion of total influence
  - Districts with 10/10 influence slots filled:
    - 35% chance for one faction to lose influence
    - Random selection weighted by proportion of total influence

### 4. Piece Assignment System
- Each piece (agent or squadron) can be:
  - Left unassigned (no action)
  - Assigned to a district with specific task

### 5. Influence Change Resolution
- **Success Results**:
  - **Standard Success**:
    - Taking from pool: Gain 1 influence
    - Taking from faction: 80% chance to gain 1 and target loses 1
  
  - **Critical Success** (beat DC by 10+):
    - Taking from pool: 80% chance to gain 2 (if available), 20% chance to gain 1
    - Taking from faction: 
      - 40% chance: Gain 2, target loses 2
      - 40% chance: Gain 2, target loses 1 (if neutral pool has space, otherwise gain 1)
      - 20% chance: Gain 1, target loses 1
  
  - **Failure Results**:
    - Standard failure: No change
    
  - **Critical Failure** (miss DC by 10+):
    - Taking from pool: 50% chance to lose 1 influence
    - Taking from faction: 40% chance to lose 1 influence, and if that happens, 50% chance target gains 1 influence

## Newspaper System Specification

### 1. Core Functionality
- Newspaper generation independent from turn resolution
- DM manually triggers creation between game turns
- Contains auto-selected rumors/hints and manual content

### 2. Newspaper Creation Process
- System auto-increments issue number, sets date, initializes sections, selects rumors
- DM creates custom articles, edits auto-generated content, finalizes layout

### 3. Content Selection & Generation
- System selects information based on newspaper_weight values
- Filter out information already known to all factions
- Hints are subtle and require interpretation

### 6. Newspaper Database Model
```json
{
  "id": "string",
  "title": "string",
  "issue_number": "int",
  "turn_number": "int",
  "publication_date": "string",
  "sections": [
    {
      "section_name": "string",
      "articles": [
        {
          "headline": "string",
          "content": "string",
          "author": "string",
          "contains_hint": "boolean",
          "related_information_id": "string",
          "related_district_id": "string",
          "length": "string"
        }
      ]
    }
  ],
  "manual_content": [
    {
      "section": "string",
      "headline": "string",
      "content": "string",
      "author": "string",
      "position": "string"
    }
  ],
  "distribution_record": ["faction_id_1", "faction_id_2"],
  "archived": "boolean"
}
```

## Data Models & Database Structure

### District Data
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "coordinates": {"x": "float", "y": "float"},
  "shape_data": {
    "type": "string",  // "polygon", "rectangle", "circle", etc.
    "points": [
      {"x": "float", "y": "float"},
      {"x": "float", "y": "float"}
      // Additional points for the shape
    ],
    "style": {
      "border_color": "string",
      "border_width": "float",
      "fill_color": "string",
      "fill_opacity": "float"
    }
  },
  "adjacent_districts": ["district_id_1", "district_id_2"],
  "faction_influence": {
    "faction_id_1": "int",
    "faction_id_2": "int"
  },
  "influence_pool": "int",
  "faction_likeability": {
    "faction_id_1": "int",
    "faction_id_2": "int"
  },
  "weekly_dc_modifier": "int",
  "weekly_dc_modifier_history": ["int", "int"],
  "faction_detection_modifiers": {
    "faction_id_1": "int",
    "faction_id_2": "int"
  },
  "strongholds": {
    "faction_id_1": "boolean",
    "faction_id_2": "boolean"
  },
  "commerce_value": "int",
  "muster_value": "int",
  "aristocratic_value": "int",
  "information": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "discovery_dc": "int",
      "initial_dc": "int",
      "known_by": ["faction_id_1", "faction_id_2"],
      "discovery_turn": {
        "faction_id_1": "int",
        "faction_id_2": "int"
      },
      "newspaper_hint": "string",
      "newspaper_weight": "float"
    }
  ],
  "preferred_actions": {
    "monitoring": {
      "agent_attribute": "string",
      "agent_skill": "string",
      "squadron_aptitude": "string" // Name of the aptitude to use (e.g. "monitoring")
    },
    "influence_control": {
      "agent_attribute": "string",
      "agent_skill": "string", 
      "squadron_aptitude": "string" // Name of the aptitude to use (e.g. "combat")
    }
  }
}
```

### Faction Data
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "color": "string",
  "relationships": {
    "faction_id_1": "int",
    "faction_id_2": "int"
  },
  "info_gathering_bonus": "int",
  "resources": {
    "resource_type_1": "int",
    "resource_type_2": "int"
  },
  "modifiers": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "value": "int"
    }
  ],
  "known_information": ["information_id_1", "information_id_2"],
  "perceived_influence": {
    "district_id_1": {
      "faction_id_1": {
        "value": "int",
        "last_updated": "int"
      },
      "faction_id_2": {
        "value": "int",
        "last_updated": "int"
      }
    }
  },
  "district_history": {
    "district_id_1": {
      "last_detected_turn": "int",
      "historical_presence": "boolean"
    },
    "district_id_2": {
      "last_detected_turn": "int",
      "historical_presence": "boolean"
    }
  }
}
```

### Agent Data
```json
{
  "id": "string",
  "name": "string",
  "faction_id": "string",
  "stats": {
    "intellect": "int",
    "presence": "int",
    "finesse": "int",
    "might": "int",
    "attunement": "int"
  },
  "skills": {
    "infiltration": "int",
    "persuasion": "int",
    "combat": "int",
    "streetwise": "int",
    "survival": "int",
    "artifice": "int",
    "arcana": "int"
  },
  "current_district": "string",
  "current_task": {
    "type": "string",
    "target_faction": "string",
    "attribute": "string",
    "skill": "string",
    "dc": "int",
    "performs_monitoring": "boolean"
  }
}
```

### Squadron Data
```json
{
  "id": "string",
  "name": "string",
  "faction_id": "string",
  "mobility": "int",
  "aptitudes": {
    "combat": "int",
    "underworld": "int",
    "social": "int",
    "technical": "int",
    "labor": "int",
    "arcane": "int",
    "wilderness": "int",
    "monitoring": "int"
  },
  "current_district": "string",
  "current_task": {
    "type": "string",
    "target_faction": "string",
    "primary_aptitude": "string",
    "dc": "int",
    "performs_monitoring": "boolean"
  }
}
```

### Turn Data
```json
{
  "turn_number": "int",
  "decay_results": [
    {
      "district_id": "string",
      "faction_id": "string",
      "influence_change": "int"
    }
  ],
  "action_results": [
    {
      "piece_id": "string",
      "piece_type": "string",
      "district_id": "string",
      "task_type": "string",
      "roll": "int",
      "success": "boolean",
      "influence_change": "int",
      "target_faction": "string",
      "target_influence_change": "int"
    }
  ],
  "random_walk_results": [
    {
      "district_id": "string",
      "previous_dc_modifier": "int",
      "new_dc_modifier": "int",
      "roll_type": "string"
    }
  ],
  "monitoring_results": [
    {
      "piece_id": "string",
      "piece_type": "string",
      "district_id": "string",
      "roll": "int",
      "monitoring_type": "string",
      "discovered_rumors": ["rumor_id_1", "rumor_id_2"],
      "perceived_influences": {
        "faction_id_1": "int",
        "faction_id_2": "int"
      },
      "phantom_detections": [
        {
          "faction_id": "string",
          "perceived_influence": "int"
        }
      ],
      "discovered_district_modifier": {
        "value": "int",
        "direction_only": "boolean",
        "sign": "string"
      }
    }
  ],
  "rumor_dc_updates": [
    {
      "rumor_id": "string",
      "previous_dc": "int",
      "new_dc": "int"
    }
  ],
  "conflicts": [
    {
      "district_id": "string",
      "factions_involved": ["faction_id_1", "faction_id_2"],
      "pieces_involved": ["piece_id_1", "piece_id_2"],
      "resolution_notes": "string"
    }
  ],
  "notes": "string"
}
```

### Map Data
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "base_map": {
    "file_path": "string",
    "file_type": "string",  // "png", "jpg", "svg"
    "width": "int",
    "height": "int",
    "scale_factor": "float"
  },
  "district_assignments": [
    {
      "district_id": "string",
      "shape_id": "string"
    }
  ],
  "display_settings": {
    "show_influence_dots": "boolean",
    "show_strongholds": "boolean",
    "highlight_unassigned": "boolean",
    "dot_size": "float",
    "stronghold_size": "float",
    "faction_colors": {
      "faction_id_1": "string",
      "faction_id_2": "string"
    }
  },
  "view_state": {
    "center_x": "float",
    "center_y": "float",
    "zoom_level": "float",
    "selected_district_id": "string"
  },
  "map_history": [
    {
      "turn_number": "int",
      "map_snapshot_path": "string",
      "faction_snapshots": {
        "faction_id_1": "string",
        "faction_id_2": "string"
      }
    }
  ]
}
```

## Save/Load System Specification

### 1. File Format and Structure
- Format: Custom binary format with JSON metadata header
- Extension: .fms (Faction Management System)

### 2. Save File Components

#### Metadata Header
```json
{
  "version": "string",
  "save_format_version": "string",
  "campaign_name": "string",
  "game_name": "string",
  "creator": "string",
  "creation_timestamp": "ISO datetime string",
  "last_modified_timestamp": "ISO datetime string",
  "turn_number": "int",
  "checksum_algorithm": "string",
  "data_checksum": "string",
  "metadata_checksum": "string"
}
```

### 3. Save Operations
- Auto-save after turn completion and every 15 minutes during editing
- Quick Save and Save As functionality
- Checkpoint saves at significant points

### 4. Map and District Shape Persistence
- **Base Map Storage**:
  - Store base map as reference image (PNG, JPG) or vector graphic (SVG)
  - Maintain original image dimensions and scale factor
  - Support replacement of base map while preserving district shapes
  - Optionally store map overlay layers (grid, labels, etc.)

- **District Shape Storage**:
  - Store district shapes as SVG paths or GeoJSON polygon coordinates
  - Save style information (border color, fill color, opacity) per district
  - Maintain district-to-shape assignment mapping
  - Support adding new districts and shapes during gameplay
  - Store shape revision history to support undo/redo operations

- **Coordinate System**:
  - Use relative coordinates (0.0-1.0) for portability across different base maps
  - Store absolute coordinates for rendering at specific resolutions
  - Include district center points for labeling and selection
  - Maintain adjacency relationships between districts

- **Map Generation**:
  - Store faction-specific map snapshots at each turn
  - Generate PNG exports of map state for distribution
  - Cache intermediate rendering products for performance
  - Include metadata with turn number and date in exported maps

- **Influence Visualization Data**:
  - Store dot placement algorithms and parameters
  - Calculate and store dot positions for each district based on shape
  - Generate stronghold marker positions within district boundaries
  - Maintain visual consistency across map updates

### Database Requirements
- Use SQLite for data persistence and portability
- Implement proper schema with appropriate indexes for performance
- Ensure consistent transaction handling using the context manager pattern
- Follow the detailed guidelines in database_transaction_guidelines.md
- Maintain data integrity through proper foreign key constraints
- Implement backup and restore functionality

### User Interface Requirements
- Use Tkinter for cross-platform compatibility
- Tabbed interface for different management sections
