# Unified Testing Framework for Faction Management System

## Testing Philosophy

The Faction Management System requires a comprehensive testing approach that grows with each implementation phase. This document outlines the testing strategy that will be followed throughout development.

### Core Testing Principles

1. **Progressive Test Coverage**: Each implementation phase adds new tests specific to that phase
2. **Regression Protection**: All tests from previous phases must continue to pass
3. **Test First Approach**: Tests are written before or alongside implementation
4. **Deterministic Testing**: Random elements use fixed seeds for consistent verification
5. **Self-Validation**: Each implementation phase validates itself before proceeding

## Test Organization Structure

```
tests/
├── unit/                     # Tests for individual functions and classes
│   ├── core/                 # Core system functionality tests
│   ├── models/               # Data model tests
│   ├── logic/                # Business logic tests
│   └── utils/                # Utility function tests
├── integration/              # Tests for component interactions
│   ├── db_integration/       # Database interaction tests
│   ├── workflow/             # Process workflow tests
│   └── system/               # Multi-component system tests
├── fixtures/                 # Test data and configuration
│   ├── test_data/            # Sample datasets for testing
│   ├── seeds/                # Seeds for deterministic randomization
│   └── configurations/       # Test configurations
└── conftest.py               # Pytest configuration and shared fixtures
```

## Testing Tools and Frameworks

1. **Primary Testing Framework**: pytest
2. **Coverage Measurement**: pytest-cov
3. **Property Testing**: hypothesis
4. **Mock Objects**: pytest-mock
5. **UI Testing**: pytest-tk (for Tkinter UI testing)

## Testing Approach by Component Type

### 1. Data Models Testing

- **Test Class**: TestModelName
- **Validation Tests**: Ensure data validation works correctly
- **Serialization Tests**: Verify models serialize/deserialize correctly
- **Relationship Tests**: Validate relationships between models
- **Edge Case Tests**: Test model behavior with extreme values

### 2. Business Logic Testing

- **Test Class**: TestLogicName
- **Calculation Tests**: Verify algorithm implementations
- **Boundary Tests**: Test edge cases and boundaries
- **State Tests**: Ensure state transitions work correctly
- **Error Handling Tests**: Verify appropriate error responses

### 3. Database Integration Testing

- **Test Class**: TestDBIntegration
- **CRUD Tests**: Verify create, read, update, delete operations
- **Query Tests**: Test complex query functionality
- **Transaction Tests**: Ensure transaction integrity
- **Migration Tests**: Verify database migration functionality

### 4. UI Component Testing

- **Test Class**: TestUIComponentName
- **Rendering Tests**: Verify components render correctly
- **Interaction Tests**: Test user interaction flows
- **Data Binding Tests**: Verify UI components bind to data correctly
- **Event Tests**: Test event handling and propagation

## Test Fixtures Design

### 1. Standard Test Fixtures

- **District Fixtures**: Standard district configurations
- **Faction Fixtures**: Sample faction configurations
- **Agent Fixtures**: Sample agent configurations
- **Squadron Fixtures**: Sample squadron configurations
- **Rumor Fixtures**: Sample rumors
- **Turn Fixtures**: Sample turn state configurations

### 2. Complex System Fixtures

- **Game State Fixtures**: Complete game state snapshots
- **Multi-Turn Fixtures**: Fixtures spanning multiple turns
- **Edge Case Fixtures**: Fixtures designed to test boundary conditions

## Deterministic Testing Strategy

### 1. Random Number Generation Control

- All random operations use a seeded RNG instance
- Tests that involve randomness use specific fixed seeds
- Expected probability distributions are validated with statistical tests

### 2. Test Determinism Enforcement

- Test isolation ensures one test cannot affect another
- Database state is reset between tests
- Global state is properly isolated or reset between tests

## Per-Phase Testing Approach

Each implementation phase includes specific test requirements:

### Phase 1: Core Data Models
- Data validation tests
- Model relationship tests
- Serialization/deserialization tests

### Phase 2: Database Layer
- CRUD operation tests
- Query functionality tests
- Transaction integrity tests

### Phase 3: Core Logic
- Algorithm implementation tests
- Business rule validation tests
- State management tests

### Phase 4: Monitoring System
- Information quality tier tests
- Error generation tests
- Information distribution tests

### Phase 5: Turn Resolution System
- `tests/unit/logic/test_turn_phases.py`
- `tests/unit/logic/test_action_resolution.py`
- `tests/unit/logic/test_conflict_detection.py`
- `tests/unit/logic/test_conflict_resolution.py`
- `tests/integration/workflow/test_complete_turn.py`
- `tests/integration/workflow/test_two_part_turn.py`

**Action Resolution System Tests**
The following tests must be implemented to validate the action resolution system:

1. **Monitoring Action Tests**:
   - Test monitoring roll calculation for all sources (agents, squadrons, passive)
   - Verify information quality tier determination based on roll result
   - Test rumor discovery mechanics across all quality tiers
   - Validate monitoring report generation
   - Verify information is correctly associated with faction
   - Test that manual difficulty modifiers correctly affect monitoring roll results and outcome tiers

2. **Influence Action Tests**:
   - Test DC calculation for gain influence actions
   - Test DC calculation for take influence actions
   - Verify success/failure/critical results for influence actions
   - Test multiple gain influence resolution with limited pool
   - Validate influence changes are correctly applied to factions
   - Test that manual difficulty modifiers correctly affect roll results but not DC values

3. **Freeform Action Tests**:
   - Test resolution of actions with manually set DCs
   - Verify custom attribute/skill selection works correctly
   - Test critical success/failure boundaries
   - Validate report generation with action descriptions
   - Test that manual difficulty modifiers correctly affect roll results but not DC values

4. **Initiate Conflict Action Tests**:
   - Test initiation of conflicts with manually set DCs
   - Verify target faction is properly recorded
   - Test roll calculation and outcome tier determination
   - Validate proper conflict record generation
   - Test manual difficulty modifiers effect on roll results
   - Verify conflicts are processed before other actions

5. **Conflict Detection Tests**:
   - Verify manual conflict detection works correctly
   - Test relationship-based conflict detection (10%/40% chances)
   - Test target-based conflict detection for limited resources
   - Validate adjacent district participation calculations
   - Test conflict classification and prioritization
   - Verify all pieces involved are properly identified

6. **Faction Support Tests**:
   - Test faction support status boolean initialization (defaults to 0)
   - Verify only relationships with value +2 (Allied) can have support status set to 1
   - Test that support status cannot be changed for non-allied relationships
   - Validate that pieces only join conflicts when support status is 1
   - Test that support status correctly persists through turn processing

7. **Adjacent District Participation Tests**:
   - Test squadron mobility effect on join chance percentage
   - Verify correct calculation of adjacent district participation
   - Test that only eligible squadrons can join adjacent conflicts
   - Validate squadrons from adjacent districts are properly recorded
   - Test all participation probability tiers (10% through 50%)

8. **Two-Part Turn Processing Tests**:
   - Test proper pausing of turn processing after conflict detection
   - Verify all rolls are calculated but results not applied
   - Test persistence of turn state during manual resolution phase
   - Validate correct application of conflict outcomes after resolution
   - Test complete turn resumption after all conflicts are resolved
   - Verify correct integration of both parts of turn processing

9. **Manual Conflict Resolution Tests**:
   - Test recording of win/loss/draw outcomes
   - Verify winning side's actions proceed normally
   - Test losing side's actions correctly fail
   - Validate draw results apply -2 penalty to all involved pieces
   - Test special ruling persistence and application
   - Verify conflict resolution history is properly stored

10. **Faction Passive Monitoring Tests**:
   - Test automatic detection of districts with ≥4 influence
   - Verify correct roll calculation (d20 + (Influence ÷ 2) + Faction monitoring bonus)
   - Test that monitoring results are correctly assigned to factions
   - Validate that monitoring quality tier determination works correctly
   - Test that rumor discovery functions correctly in passive monitoring
   - Verify that passive monitoring phase executes after regular monitoring phase

These tests are **mandatory** before considering Phase 5 complete.

### Phase 6: UI Components
- `tests/unit/ui/test_district_panel.py`
- `tests/unit/ui/test_faction_panel.py`
- `tests/unit/ui/test_map_panel.py`
- `tests/unit/ui/test_conflict_resolution_panel.py`
- `tests/unit/ui/test_action_panels.py`
- `tests/integration/ui/test_ui_workflows.py`
- `tests/integration/ui/test_database_integration.py`
- `tests/integration/ui/test_core_logic_integration.py`
- `tests/integration/ui/test_two_part_turn_ui.py`

**Critical Database Integration Tests**
The following tests must be implemented and pass to ensure proper database integration:

1. **Data Loading Tests**:
   - Verify all UI components correctly load data from the database
   - Test dynamic population of dropdowns and lists with database entities
   - Confirm UI reflects the current state of the database

2. **Data Persistence Tests**:
   - Verify all changes made through UI are properly saved to database
   - Test that database updates occur immediately after UI actions
   - Confirm data integrity is maintained through UI operations

3. **No Hardcoded Data Tests**:
   - Verify no UI component contains hardcoded test data
   - Test UI behavior with empty database to confirm no phantom data appears
   - Confirm all displayed data can be traced to database records

**Core Logic Integration Tests**
Additional tests must verify that:

1. UI components use the actual logic implementations from previous phases
2. Turn processing through UI uses the complete turn resolution system
3. Monitoring through UI uses the real monitoring system
4. All calculations match those performed by direct API calls
5. No simplified UI-only implementations exist anywhere

These integration tests are **mandatory** before considering Phase 6 complete.

**Conflict Resolution UI Tests**
The following tests must be implemented to validate the conflict resolution UI components:

1. **Conflict List Panel Tests**:
   - Verify proper display of all pending conflicts
   - Test conflict filtering by type, district, and faction
   - Validate conflict details are properly displayed
   - Test navigation between conflicts
   - Verify conflicts are properly ordered by priority

2. **Conflict Resolution Panel Tests**:
   - Test display of conflict details (type, location, factions)
   - Verify involved pieces and actions are properly displayed
   - Test resolution controls (win/loss/draw selection)
   - Validate resolution notes field functionality
   - Test resolution submission and validation

3. **Two-Part Turn UI Tests**:
   - Verify proper UI state during turn part 1
   - Test UI state persistence during manual resolution phase
   - Validate proper UI state during turn part 2
   - Test turn continuation after all conflicts resolved
   - Verify proper UI feedback throughout the two-part process

4. **Faction Support Status UI Tests**:
   - Test faction selection controls with relationship value display
   - Verify support toggle is only enabled for relationships with value +2 (Allied)
   - Validate support status persistence
   - Test UI updates when relationship values change
   - Verify proper integration with conflict detection

5. **Initiate Conflict Action Panel Tests**:
   - Test DC setting controls
   - Verify attribute/skill selection functionality
   - Validate target faction selection requirement
   - Test district selection controls
   - Verify preview calculation accuracy
   - Validate proper database integration

These UI component tests are **mandatory** before considering Phase 6 complete.

### Phase 7: Integration and System
- `tests/system/test_game_setup.py`
- `tests/system/test_multi_turn_game.py`
- `tests/system/test_save_load.py`
- `tests/system/test_newspaper.py`

## Continuous Integration

### 1. Test Execution Pipeline

1. **Stage 1**: Unit Tests (fast, run on every change)
2. **Stage 2**: Integration Tests (medium, run on significant changes)
3. **Stage 3**: System Tests (slow, run before releases)

### 2. Coverage Requirements

- **Core Logic**: Minimum 95% statement coverage
- **Data Models**: Minimum 90% statement coverage
- **UI Components**: Minimum 80% statement coverage
- **Overall**: Minimum 85% statement coverage

## Test Implementation Guidelines

### 1. Test Structure

Each test follows this structure:
```python
def test_specific_functionality_scenario_expected_result():
    # ARRANGE
    # Set up test conditions
    
    # ACT
    # Execute the functionality being tested
    
    # ASSERT
    # Verify results match expectations
```

### 2. Test Naming Convention

Tests are named according to this pattern:
```
test_<functionality>_<scenario>_<expected_result>
```

Examples:
- `test_influence_decay_above_threshold_reduces_by_one`
- `test_information_gathering_legendary_roll_perfect_accuracy`
- `test_faction_relationships_hotwar_applies_penalties`

### 3. Test Documentation

Each test includes:
- Clear docstring explaining test purpose
- References to requirements being tested
- Explanation of edge cases or special considerations

## Test Assessment Criteria

Tests are evaluated based on:

1. **Completeness**: Tests cover all specified functionality
2. **Correctness**: Tests validate actual requirements
3. **Robustness**: Tests handle edge cases and errors
4. **Maintainability**: Tests are well-structured and documented
5. **Performance**: Tests execute efficiently

## Automated Test Execution

Run tests with the following command structure:

```bash
# Run all tests
pytest

# Run tests for a specific phase
pytest tests/phase_x/

# Run tests with coverage report
pytest --cov=src tests/

# Run only unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/
```

## Phase-Specific Test Files

Each implementation phase has specific test files that must pass before proceeding:

### Phase 1: Core Data Models
- `tests/unit/models/test_district.py`
- `tests/unit/models/test_faction.py`
- `tests/unit/models/test_agent.py`
- `tests/unit/models/test_squadron.py`
- `tests/unit/models/test_rumor.py`

### Phase 2: Database Layer
- `tests/unit/db/test_db_manager.py`
- `tests/integration/db_integration/test_model_persistence.py`
- `tests/integration/db_integration/test_query_operations.py`

### Phase 3: Core Logic
- `tests/unit/logic/test_influence.py`
- `tests/unit/logic/test_relationship.py`
- `tests/unit/logic/test_district_mechanics.py`
- `tests/integration/workflow/test_basic_turn.py`

### Phase 4: Monitoring System
- `tests/unit/logic/test_monitoring.py`
- `tests/unit/logic/test_information_quality.py`
- `tests/unit/logic/test_error_generation.py`
- `tests/integration/workflow/test_information_flow.py`

### Phase 5: Turn Resolution System
- `tests/unit/logic/test_turn_phases.py`
- `tests/unit/logic/test_action_resolution.py`
- `tests/unit/logic/test_conflict_detection.py`
- `tests/unit/logic/test_conflict_resolution.py`
- `tests/integration/workflow/test_complete_turn.py`
- `tests/integration/workflow/test_two_part_turn.py`

### Phase 6: UI Components
- `tests/unit/ui/test_district_panel.py`
- `tests/unit/ui/test_faction_panel.py`
- `tests/unit/ui/test_map_panel.py`
- `tests/unit/ui/test_conflict_resolution_panel.py`
- `tests/unit/ui/test_action_panels.py`
- `tests/integration/ui/test_ui_workflows.py`
- `tests/integration/ui/test_database_integration.py`
- `tests/integration/ui/test_core_logic_integration.py`
- `tests/integration/ui/test_two_part_turn_ui.py`

**Critical Database Integration Tests**
The following tests must be implemented and pass to ensure proper database integration:

1. **Data Loading Tests**:
   - Verify all UI components correctly load data from the database
   - Test dynamic population of dropdowns and lists with database entities
   - Confirm UI reflects the current state of the database

2. **Data Persistence Tests**:
   - Verify all changes made through UI are properly saved to database
   - Test that database updates occur immediately after UI actions
   - Confirm data integrity is maintained through UI operations

3. **No Hardcoded Data Tests**:
   - Verify no UI component contains hardcoded test data
   - Test UI behavior with empty database to confirm no phantom data appears
   - Confirm all displayed data can be traced to database records

**Core Logic Integration Tests**
Additional tests must verify that:

1. UI components use the actual logic implementations from previous phases
2. Turn processing through UI uses the complete turn resolution system
3. Monitoring through UI uses the real monitoring system
4. All calculations match those performed by direct API calls
5. No simplified UI-only implementations exist anywhere

These integration tests are **mandatory** before considering Phase 6 complete.

**Conflict Resolution UI Tests**
The following tests must be implemented to validate the conflict resolution UI components:

1. **Conflict List Panel Tests**:
   - Verify proper display of all pending conflicts
   - Test conflict filtering by type, district, and faction
   - Validate conflict details are properly displayed
   - Test navigation between conflicts
   - Verify conflicts are properly ordered by priority

2. **Conflict Resolution Panel Tests**:
   - Test display of conflict details (type, location, factions)
   - Verify involved pieces and actions are properly displayed
   - Test resolution controls (win/loss/draw selection)
   - Validate resolution notes field functionality
   - Test resolution submission and validation

3. **Two-Part Turn UI Tests**:
   - Verify proper UI state during turn part 1
   - Test UI state persistence during manual resolution phase
   - Validate proper UI state during turn part 2
   - Test turn continuation after all conflicts resolved
   - Verify proper UI feedback throughout the two-part process

4. **Faction Support Status UI Tests**:
   - Test faction selection controls with relationship value display
   - Verify support toggle is only enabled for relationships with value +2 (Allied)
   - Validate support status persistence
   - Test UI updates when relationship values change
   - Verify proper integration with conflict detection

5. **Initiate Conflict Action Panel Tests**:
   - Test DC setting controls
   - Verify attribute/skill selection functionality
   - Validate target faction selection requirement
   - Test district selection controls
   - Verify preview calculation accuracy
   - Validate proper database integration

These UI component tests are **mandatory** before considering Phase 6 complete.

### Phase 7: Integration and System
- `tests/system/test_game_setup.py`
- `tests/system/test_multi_turn_game.py`
- `tests/system/test_save_load.py`
- `tests/system/test_newspaper.py`