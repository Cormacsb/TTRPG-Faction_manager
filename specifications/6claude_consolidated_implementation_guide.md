# Consolidated Implementation Guide for Claude 3.7

This comprehensive guide provides structured instructions for Claude 3.7 to implement the Faction Management System. It outlines the step-by-step approach across all implementation phases, critical requirements, and testing strategies.

## Table of Contents
1. [General Implementation Principles](#general-implementation-principles)
2. [Critical Implementation Requirements](#critical-implementation-requirements)
3. [Context Management Between Phases](#context-management-between-phases)
4. [Implementation Phases](#implementation-phases)
   - [Phase 1: Core Data Models](#phase-1-core-data-models)
   - [Phase 2: Database Layer](#phase-2-database-layer)
   - [Phase 3: Core Logic](#phase-3-core-logic)
   - [Phase 4: Monitoring System](#phase-4-monitoring-system)
   - [Phase 5: Turn Resolution System](#phase-5-turn-resolution-system)
   - [Phase 6: User Interface](#phase-6-user-interface)
   - [Phase 7: Integration & Finalization](#phase-7-integration--finalization)
5. [Common Pitfalls and Edge Cases](#common-pitfalls-and-edge-cases)
6. [Implementation Validation Checklist](#implementation-validation-checklist)

## General Implementation Principles

1. **Phased Implementation**: Follow each implementation phase in sequence, building upon previous work.
2. **Test-Driven Development**: Write tests first, then implement the code to make them pass.
3. **Documentation**: Document all code with clear docstrings and comments.
4. **Error Handling**: Implement proper error handling for all functions.
5. **Progressive Refinement**: Start with core functionality and progressively add complexity.
6. **Code Organization**: Maintain a clean, modular code structure.
7. **Consistency**: Follow established patterns and naming conventions throughout the codebase.

## Critical Implementation Requirements

### Database Integration

**All components, especially the UI, must directly integrate with the database system:**

1. **No Hardcoded Data**: Never use hardcoded test data in any implementation.
2. **Repository Pattern**: All data access must use the repository classes from Phase 2.
3. **Real-Time Persistence**: Changes must be immediately persisted to the database.
4. **Dynamic Data Loading**: UI elements must load data directly from the database.
5. **Complete Data Flow**: Ensure proper data flow from UI to database and back.

### Transaction Management

**Transaction handling MUST be implemented early as a foundational part of the database layer:**

1. **Early Implementation**: Implement transaction handling before creating any repository classes.
2. **Context Manager Pattern**: Use the Python context manager pattern (`with self.db_manager.connection:`) for all transactions.
3. **Avoid Direct Statements**: Never use explicit BEGIN/COMMIT/ROLLBACK statements.
4. **Consistent Approach**: Use the same transaction pattern throughout the entire codebase.
5. **Proper Error Handling**: Place try/except blocks outside the context manager.
6. **Appropriate Scope**: Ensure operations spanning multiple tables are in single transactions.
7. **Transaction Testing**: Test all transaction scenarios including error conditions.

### Core Logic Integration

**All functionality must use the actual implementations from earlier phases:**

1. **Use Existing Systems**: Never reimplement logic that already exists in previous phases.
2. **Complete Implementation**: Don't create simplified versions of complex systems.
3. **End-to-End Integration**: Ensure all systems work together through the UI.
4. **Consistent Behavior**: System behavior should be identical whether accessed through code or UI.
5. **Full Feature Coverage**: All features specified in requirements must be implemented and accessible.

## Project Directory Structure

The Faction Management System should follow this directory structure:

```
<PROJECT_ROOT>/              # Root project directory (whatever name you choose)
├── src/                     # Main source code directory
│   ├── models/              # Data models
│   │   ├── base.py          # Base model class
│   │   ├── district.py      # District model
│   │   ├── faction.py       # Faction model
│   │   ├── agent.py         # Agent model
│   │   ├── squadron.py      # Squadron model
│   │   └── rumor.py         # Rumor model
│   ├── db/                  # Database layer
│   │   ├── db_manager.py    # Database connection manager
│   │   ├── transaction.py   # Transaction handling
│   │   └── repositories/    # Repository classes
│   │       ├── base.py      # Base repository
│   │       ├── district.py  # District repository
│   │       ├── faction.py   # Faction repository
│   │       ├── agent.py     # Agent repository
│   │       ├── squadron.py  # Squadron repository
│   │       └── rumor.py     # Rumor repository
│   ├── logic/               # Business logic
│   │   ├── influence.py     # Influence mechanics
│   │   ├── monitoring.py    # Monitoring system
│   │   ├── turn.py          # Turn processing
│   │   └── action.py        # Action resolution
│   ├── ui/                  # User interface
│   │   ├── main_window.py   # Main application window
│   │   ├── dashboard.py     # Dashboard panel
│   │   ├── map_panel.py     # Map visualization
│   │   └── components/      # Reusable UI components
│   └── utils/               # Utility functions
│       ├── random.py        # Randomization utilities
│       └── validators.py    # Input validation
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test fixtures
├── resources/               # Static resources
│   ├── images/              # Image files
│   └── templates/           # Templates
├── specifications/          # Specifications
├── main.py                  # Application entry point
└── README.md                # Project documentation
```

All implementation work must follow this directory structure. Source code must be placed within the appropriate subdirectories inside the `src/` directory. The top-level directory name can be changed as needed, but the internal structure should remain consistent.

## Context Management Between Phases

Since Claude 3.7 will start with zero context at the beginning of each major implementation phase, it's important to:

1. **Review Existing Code**: At the start of each phase, examine the existing codebase to understand what has been implemented.
2. **Read Specifications**: Review the relevant specification documents for the phase you're implementing.
3. **Check Tests**: Review existing tests to understand expected behavior.
4. **Follow Naming Conventions**: Maintain consistent naming and patterns established in previous phases.
5. **Assess Implementation Status**: Identify what has been completed and what remains to be done.
6. **Connect with Previous Work**: Ensure new implementation properly connects with existing components.

## Implementation Phases

### Phase 1: Core Data Models

**Context for Claude:**
- You are implementing the foundational data models for the system.
- Follow the specifications in `main-spec.txt` and `information-spec.txt`.
- Implement proper validation and relationship handling in all models.

**Implementation Steps:**

1. **Base Model Class**
   - Implement `base.py` model with common functionality
   - Add validation methods and error handling
   - Include JSON serialization/deserialization capabilities
   - Implement relationship management methods

2. **District Model**
   - Create District class inheriting from base model
   - Implement influence slot management (total of 10)
   - Add faction influence tracking
   - Implement likeability values for factions (-5 to +5)
   - Add stronghold boolean tracking per faction
   - Implement district attributes (Commerce, Muster, Aristocratic values)
   - Add preferred action parameters

3. **Faction Model**
   - Create Faction class inheriting from base model
   - Implement district control tracking
   - Add relationship values with other factions (-2 to +2)
   - Track controlled agents and squadrons
   - Implement resources
   - Add monitoring bonus

4. **Agent Model**
   - Create Agent class inheriting from base model
   - Implement attributes and skills
   - Add assignment and status tracking

5. **Squadron Model**
   - Create Squadron class inheriting from base model
   - Implement aptitudes (Combat, Underworld, Social, etc.)
   - Add assignment and status tracking
   - Implement mobility mechanics

6. **Rumor Model**
   - Create Rumor class inheriting from base model
   - Implement discovery status tracking
   - Add discovery difficulty class (DC)
   - Implement rumor content and metadata

**Note:** For testing implementation, refer to the Unified Testing Framework document which provides comprehensive testing guidelines.

### Phase 2: Database Layer

**Context for Claude:**
- You are implementing the database layer for persistence
- This builds on the models implemented in Phase 1
- Use SQLite for the database backend

**Implementation Steps:**

1. **Database Manager**
   - Implement the DatabaseManager class for connection handling
   - Add database initialization and schema creation
   - Implement backup and restore capabilities
   - Add error handling and logging

2. **Transaction Management (CRITICAL)**
   - Implement transaction management using Python's context manager pattern
   - Create connection context manager with proper commit/rollback
   - Implement transaction isolation levels
   - Add error handling within transactions
   - Document the standard transaction pattern for repositories

3. **Model Serialization Enhancement**
   - Add to/from database methods to the base Model class
   - Implement serialization/deserialization for complex types
   - Add validation before database operations

4. **Repository Base Class**
   - Create a base repository with common CRUD operations
   - Implement transaction handling using the context manager pattern
   - Add error handling and logging
   - Implement query building capabilities

5. **Model-Specific Repositories**
   - Implement DistrictRepository
   - Implement FactionRepository
   - Implement AgentRepository
   - Implement SquadronRepository
   - Implement RumorRepository
   - Add specialized queries for each model type

6. **Query Building System**
   - Implement flexible query construction
   - Add support for filtering, sorting, and pagination
   - Implement join operations for related data
   - Add parameter binding for security

7. **Migration System**
   - Implement simple schema versioning
   - Add migration scripts for version upgrades
   - Implement data transformation during migrations

**Note:** For testing implementation, refer to the Unified Testing Framework document which provides comprehensive testing guidelines.

### Phase 3: Core Logic

**Context for Claude:**
- You are implementing the core game mechanics
- This builds on models and database layer from previous phases
- Focus on influence, relationships, and turn structure

**Implementation Steps:**

1. **Influence Management**
   - Implement influence gain and loss mechanics
   - Add stronghold mechanics and protection
   - Implement decay algorithms
   - Add influence cap enforcement
   - Implement influence transfer between factions

2. **Relationship System**
   - Implement faction relationship management
   - Add relationship effects on gameplay
   - Implement diplomatic actions
   - Add relationship change triggers
   - Implement relationship constraints

3. **Turn Structure Foundation**
   - Implement basic turn phasing
   - Add phase sequencing and dependencies
   - Implement game state management
   - Add turn history tracking
   - Implement turn validation

4. **Task Management**
   - Implement agent and squadron assignment
   - Add task resolution framework
   - Implement success/failure mechanics
   - Add task prerequisites and constraints
   - Implement task outcomes and effects

5. **Random Systems**
   - Implement configurable random generators with seed support
   - Add seeded randomization for deterministic results
   - Implement probability distribution functions
   - Add controlled randomness for game events

6. **Configuration System**
   - Implement game parameters management
   - Add difficulty settings
   - Implement rules customization
   - Add game mode configuration

**Note:** For testing implementation, refer to the Unified Testing Framework document which provides comprehensive testing guidelines.

### Phase 4: Monitoring System

**Context for Claude:**
- You are implementing the monitoring system
- This is a complex subsystem with many interdependent parts
- Focus on accuracy tiers, detection mechanics, and report generation
- Refer to information-spec.md for complete probability tables and detailed mechanics

**Implementation Steps:**

1. **Information Quality Tiers**
   - Implement the quality tier system as specified in information-spec.txt
   - Add roll-based quality determination
   - Implement accuracy scaling within tiers
   - Add roll modifiers and bonuses
   - Implement determistic randomization based on seeded RNG

2. **Faction Detection System**
   - Implement faction presence/absence detection
   - Add influence-based detection probability
   - Implement tier-based detection rates
   - Add adjacency effects on detection

3. **Influence Accuracy System**
   - Implement influence accuracy for each quality tier
   - Add error generation for influence values
   - Implement error distribution based on quality
   - Add stronghold detection accuracy

4. **Phantom Detection System**
   - Implement phantom (non-existent) faction detection
   - Add tier-based phantom probability
   - Implement adjacency-weighted phantom selection
   - Add phantom influence value assignment

5. **District Modifier Discovery**
   - Implement modifier discovery mechanics
   - Add tier-based discovery chances
   - Implement direction vs. exact value discovery
   - Add false information generation

6. **Monitoring Sources**
   - Implement agent monitoring
   - Add squadron monitoring (primary and secondary)
   - Implement faction passive monitoring
   - Add source-specific modifiers and bonuses

7. **Report Generation System**
   - Implement weekly intelligence reporting
   - Add confidence rating calculation
   - Implement report formatting and structure
   - Add faction-specific reporting
   - Implement historic report archiving

**Note:** For testing implementation, refer to the Unified Testing Framework document which provides comprehensive testing guidelines.

### Phase 5: Turn Resolution System

**Context for Claude:**
- You are implementing the complete turn resolution system
- This integrates all previous components into a cohesive workflow
- Focus on phase management and comprehensive resolution
- **Refer to action-resolution-spec.md for detailed action resolution mechanics**

**Implementation Steps:**

1. **Complete Phase Sequence**
   - Implement preparation phase
   - Add influence decay phase
   - Add assignment phase
   - Implement conflict detection phase
   - Add action roll phase
   - Implement manual conflict resolution phase with pause/resume capability
   - Add action resolution phase with conflict outcomes
   - Implement monitoring phase for agent and squadron actions
   - Add faction passive monitoring phase for factions with ≥4 influence
   - Implement rumor DC update phase
   - Add map update phase
   - Implement turn completion phase

2. **Two-Part Turn Resolution**
   - Implement the pause mechanism after conflict detection
   - Add state persistence during the pause period
   - Implement the resume capability after manual resolution
   - Add validation to ensure data integrity across the pause/resume boundary
   - Implement UI indicators for the current processing part

3. **Assignment Validation**
   - Implement action validation system
   - Add prerequisite checking
   - Implement resource requirement validation
   - Add legality verification
   - Implement limitation enforcement

4. **Conflict System**
   - Implement comprehensive conflict detection:
     - Manually initiated conflicts (from Initiate Conflict actions)
     - Relationship-based conflicts (10% for -1, 40% for -2)
     - Target-based conflicts (limited resources)
     - Adjacent district conflicts
   - Add ally support mechanics
   - Implement adjacent district participation calculation (Mobility × 10%)
   - Add conflict categorization and prioritization
   - Implement detailed conflict reporting

5. **Manual Conflict Resolution**
   - Implement conflict resolution UI
   - Add win/loss/draw outcome recording
   - Implement outcome application logic:
     - Winners proceed normally
     - Losers automatically fail
     - Draws proceed with -2 penalty
   - Add conflict resolution history tracking
   - Implement special ruling capability

6. **Action Resolution**
   - Implement comprehensive action resolution following action-resolution-spec.md
   - Add critical success/failure systems
   - Implement opposed action resolution
   - Add consequence application
   - Implement resolution history
   - Add handling for all four action types: Monitoring, Influence, Freeform, and Initiate Conflict
   - Implement multiple gain influence resolution

7. **Map Update System**
   - Implement influence map updates
   - Add control visualization
   - Implement faction-specific map generation
   - Add historic map archiving

8. **Summary Generation**
   - Implement turn summary generation
   - Add faction-specific reporting
   - Implement conflict outcome reporting
   - Add event logging
   - Implement statistical tracking

**Note:** For testing implementation, refer to the Unified Testing Framework document which provides comprehensive testing guidelines.

### Phase 6: User Interface

**Context for Claude:**
- You are implementing the Tkinter-based UI
- This provides a graphical interface to the underlying system
- Focus on usability and clear information presentation
- **CRITICAL: The UI must be fully integrated with the database and core functions**
- **NO hardcoded test data or mock implementations are acceptable**

**Implementation Steps:**

1. **Database Integration Framework (IMPLEMENT FIRST)**
   - Create reusable database access methods for UI components
   - Implement data change notification system
   - Set up UI refresh mechanisms for database updates
   - Establish pattern for UI-to-database synchronization
   - Create validation for ensuring no hardcoded data exists
   - Implement standard UI-database transaction pattern

2. **Application Framework**
   - Implement the main application window
   - Add menu system and navigation
   - Implement tabbed interface
   - Add status bar and notifications
   - Implement application settings
   - Add help system

3. **Dashboard Panel**
   - Implement the dashboard panel for game overview
   - Add summary displays for current state
   - Implement notification area
   - Add quick action buttons

4. **District Management Panel**
   - Implement district management panel
   - Add district list and detail views
   - Implement influence display and editing
   - Add information management controls

5. **Map Visualization Panel**
   - Implement map visualization using Tkinter Canvas
   - Add district rendering with color-coding
   - Implement selection and highlighting
   - Add visualization modes (true, faction-specific)
   - Implement map zooming functionality:
     - Develop a scaling system that maintains district shapes' positions relative to the base map
     - Implement smooth zooming with mouse wheel and control buttons
     - Support zoom levels from 25% to 400% of original size
     - Add zoom level indicator and reset-to-default button
     - Implement text scaling for district labels
     - Support panning of zoomed maps through drag operations

6. **Faction Management Panel**
   - Implement faction management panel
   - Add faction list and detail views
   - Implement relationship matrix
   - Add resource and ability management

7. **Agent & Squadron Panel**
   - Implement agent and squadron management panel
   - Add piece list with filtering
   - Implement property editing
   - Add assignment controls

8. **Turn Resolution Panel**
   - Implement turn resolution interface
   - Add phase navigation controls
   - Implement results display
   - Add manual conflict resolution

9. **Newspaper Editor**
   - Implement newspaper creation interface
   - Add article management
   - Implement formatting tools
   - Add export functionality

**Critical UI-Database Integration Requirements:**
1. Every UI component must load its data from the database using repository classes
2. All changes made through the UI must be immediately saved to the database
3. No UI component should contain hardcoded data values
4. UI must refresh to show database updates
5. All displayed data must come from database queries
6. All UI actions must persist changes to the database

**Critical UI-Logic Integration Requirements:**
1. All calculations and logic must use the implementations from Phase 3
2. UI must reflect the actual state of the game system
3. All turn processing must use the turn resolution system from Phase 5
4. Monitoring must use the system from Phase 4
5. No simplified UI-only implementations of game logic are acceptable

**Note:** For testing implementation, refer to the Unified Testing Framework document which provides comprehensive testing guidelines.

### Phase 7: Integration & Finalization

**Context for Claude:**
- You are finalizing the complete system
- This involves integration, optimization, and polishing
- Focus on creating a robust, user-friendly application

**Implementation Steps:**

1. **System Integration**
   - Finalize integration of all components
   - Fix any integration issues
   - Implement cohesive workflow
   - Add cross-component verification

2. **Performance Optimization**
   - Identify and fix performance bottlenecks
   - Implement caching for frequent operations
   - Add asynchronous loading for large data
   - Optimize database queries

3. **Error Recovery**
   - Implement comprehensive error handling
   - Add recovery mechanisms
   - Implement data validation
   - Add logging and diagnostics

4. **Final Polishing**
   - Improve UI styling and appearance
   - Add helpful tooltips and guidance
   - Implement keyboard shortcuts
   - Add accessibility features

5. **Distribution Package**
   - Create installer using PyInstaller
   - Add configuration for different environments
   - Implement automatic updates
   - Add documentation and help files

**Note:** For testing implementation, refer to the Unified Testing Framework document which provides comprehensive testing guidelines.

## Common Pitfalls and Edge Cases

### Common Pitfalls to Avoid

1. **Over-Engineering**: Keep implementations as simple as possible while meeting requirements
2. **Under-Testing**: Ensure all edge cases are tested
3. **Tight Coupling**: Maintain separation of concerns between components
4. **Magic Numbers**: Use constants for any fixed values from specifications
5. **Reinventing**: Use standard library functions where appropriate
6. **Inconsistent Transaction Handling**: Use the context manager pattern consistently across all database operations
7. **Hardcoded Data**: Never use hardcoded test data in production code
8. **Disconnected UI**: Ensure all UI elements affect the actual game state
9. **Partial Implementation**: Implement all features completely, not just visually
10. **Mock Functions**: Use actual game logic, not simplified UI-only versions
11. **Missing Refreshes**: Ensure UI updates when database changes

### Critical Edge Cases to Test

1. **Influence Limits**:
   - Maximum district influence (10)
   - Minimum influence values (0)
   - Stronghold decay protection mechanics

2. **Information Quality**:
   - Roll boundaries between quality tiers
   - Phantom detection probabilities
   - Influence total adjustment algorithm

3. **Turn Processing**:
   - Phase sequence and dependencies
   - Conflict detection priorities
   - Critical success/failure mechanics

4. **UI Interactions**:
   - Form validation and error handling
   - Data updates and refresh
   - Map visualization with invalid data

## Implementation Validation Checklist

Before considering each phase complete, verify:

### General Validation
1. **Test Coverage**: All functionality has appropriate tests
2. **Documentation**: Code is properly documented
3. **Specification Compliance**: Implementation matches specifications
4. **Error Handling**: All error conditions are handled properly
5. **Performance**: Code is reasonably optimized

### Database Integration Validation
1. All data is loaded from and saved to the database
2. No hardcoded values or mock implementations exist
3. Proper transaction handling is used consistently
4. Database operations have appropriate error handling
5. All repositories follow the same patterns and conventions

### UI Integration Validation
1. All displayed data comes from database queries
2. All UI actions persist changes to the database
3. UI refreshes to show database updates
4. No hardcoded test data exists anywhere in the UI
5. All game mechanics function through the UI exactly as specified

### Final System Validation
1. All components work together cohesively
2. System behaves according to specifications in all scenarios
3. Performance is acceptable under normal operating conditions
4. Error recovery works for all expected error conditions
5. Distribution package installs and runs correctly 