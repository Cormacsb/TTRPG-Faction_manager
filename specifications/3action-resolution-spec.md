# Action Resolution System Specification

## Overview

The Action Resolution System is a core component of the Faction Management System, responsible for determining the outcomes of all actions taken by faction pieces (agents and squadrons). It integrates with the turn structure, monitoring system, and influence mechanics to create a cohesive gameplay experience.

### Key Principles

1. **Deterministic Randomization**: All randomized outcomes use seeded RNG for consistent results
2. **Tiered Success**: Actions can result in critical failure, failure, success, or critical success
3. **Conflict Detection**: The system identifies when actions conflict with each other
4. **Resource Management**: Actions consume faction resources appropriately
5. **Narrative Support**: The system provides sufficient information for storytelling

## Action Types

The system handles four primary action types, each with distinct resolution mechanics:

### 1. Monitoring Actions

Monitoring actions gather information about districts, including faction influence levels and rumors. These actions do not have set DCs but produce variable quality results based on the roll value.

#### Key Characteristics

- **No set DC**: Quality tier determined by roll result
- **Information accuracy**: Higher rolls = more accurate information
- **Rumor discovery**: Higher rolls reveal more rumors and higher DC rumors
- **Auto-selected skills**: System uses district's preferred agent attribute, agent skill, and squadron aptitude (can be manually overridden)

#### Monitoring Sources

1. **Agent Monitoring**
   - Agents specifically assigned to monitor a district
   - Roll: d20 + Attribute (district's preferred) + Skill (district's preferred)

2. **Primary Squadron Monitoring**
   - Squadrons specifically assigned to monitor a district
   - Roll: d20 + aptitude bonus (district's preferred)

3. **Secondary Squadron Monitoring**
   - All squadrons automatically monitor their assigned district regardless of primary task
   - Roll with disadvantage (roll twice, take lower result) if performing another task
   - Roll: d20 + aptitude bonus (district's preferred)

4. **Faction Passive Monitoring**
   - Automatic in districts where faction has ≥4 influence
   - Roll: d20 + (Influence ÷ 2) + Faction monitoring bonus

#### Resolution Process

1. Calculate the monitoring roll for each source in a district
2. Determine information quality tier based on roll result
3. Apply appropriate error distribution for influence discovery
4. Apply tier-based rumor discovery chances
5. Generate and store the monitoring report
6. Associate discovered information with the faction

### 2. Influence Actions

Influence actions allow factions to gain control in districts, either by gaining new influence from the available pool (gain influence) or by taking influence from other factions (take influence).

#### Key Characteristics

- **Auto-calculated DC**: System determines difficulty based on district conditions
- **Auto-selected skills**: System uses district's preferred agent attribute, agent skill, and squadron aptitude (can be manually overridden)
- **Resource-limited**: The district influence pool is limited to 10 total points

#### Gain Influence Action

- **Target**: Influence pool (unallocated influence in district)
- **DC Calculation**:
  - Base DC: 11
  - District likeability modifier: -5 to +5 based on district's attitude toward faction
  - Current influence modifier:
    - 0 influence: +3 to DC
    - 1 influence: +1 to DC
    - 2-3 influence: -1 to DC
    - 4-5 influence: No modifier
    - 6 influence: +1 to DC
    - 7 influence: +2 to DC
    - 8 influence: +3 to DC
    - 9 influence: +4 to DC
  - Stronghold bonus: -2 DC if faction has a stronghold in district
  - Weekly fluctuation: Random walk between -2 and +2, updated each turn
- **Resolution**: 
  - Success = Roll ≥ DC
  - Critical Success = Roll ≥ (DC + 10)
  - Failure = Roll < DC
  - Critical Failure = Roll ≤ (DC - 10)
- **Results**:
  - **Success**: Gain 1 influence point
  - **Critical Success**: 80% chance to gain 2 influence points (if available), 20% chance to gain 1
  - **Failure**: No change
  - **Critical Failure**: 50% chance to lose 1 influence point if present
  

#### Take Influence Action

- **Target**: Specific faction's influence in district
- **DC Calculation**:
  - Same as Gain Influence, plus:
  - Target faction modifier: +3 to DC
  - Target faction relationship modifier:
    - -2 relationship: -2 to DC
    - -1 relationship: -1 to DC
    - 0 relationship: No modifier
    - +1 relationship: +1 to DC
    - +2 relationship: +2 to DC
- **Resolution**: Same as Gain Influence
- **Results**:
  - **Success**: 80% chance that target faction loses 1 influence and acting faction gains 1 influence
  - **Critical Success**:
    - 40% chance: Gain 2 influence, target loses 2 influence
    - 40% chance: Gain 2 influence, target loses 1 influence (if neutral pool has space, otherwise gain 1)
    - 20% chance: Gain 1 influence, target loses 1 influence
  - **Failure**: No change
  - **Critical Failure**: 40% chance to lose 1 influence point if present, and if that happens, 50% chance target gains 1 influence


#### Multiple Gain Influence Resolution

When multiple factions attempt to gain influence in the same district and the total requested exceeds the available pool:

1. Actions are resolved in order of roll result (highest to lowest)
2. Each successful faction gains influence if still available in the pool
3. Once the pool is exhausted, remaining actions automatically fail
4. Critical successes are prioritized over regular successes
5. In case of tied rolls, resolve randomly using seeded RNG

### 3. Freeform Actions

Freeform actions represent custom activities not covered by the standard types. These require manual configuration and are primarily used for roleplay and special scenarios.

#### Key Characteristics

- **Manually set DC**: The DC must be specified when assigning the action
- **Manually selected skills**: The attribute/skill/aptitude must be specified when assigning the action
- **Description field**: Text field to describe the action's intent and context
- **Custom resolution**: Results may require manual implementation by the DM

#### Configuration Options

- **DC**: Manually set value between 5-30
- **Primary attribute/skill selection**:
  - For agents: Must select both a primary attribute (Intellect, Presence, etc.) AND a skill (Infiltration, Persuasion, etc.)
  - For squadrons: Must select a primary aptitude (Combat, Underworld, etc.)
- **Action description**: Text field describing the action (up to 500 chars)
- **Target faction**: Optional selection of a specific faction as target
- **Target district**: Required district where action takes place

#### Resolution Process

1. Roll calculation:
   - For agents: d20 + primary attribute bonus + skill bonus (both selections are required and combined)
   - For squadrons: d20 + selected aptitude bonus
2. Determine outcome tier:
   - Critical Failure: Roll ≤ (DC - 10)
   - Failure: Roll < DC
   - Success: Roll ≥ DC
   - Critical Success: Roll ≥ (DC + 10)
3. Generate result report with action description and outcome
4. DM may manually implement additional consequences based on the outcome

### 4. Initiate Conflict Actions

Initiate Conflict actions allow factions to deliberately start a conflict with another faction in a district. These conflicts are manually resolved by the DM and can significantly impact other actions.

#### Key Characteristics

- **Manually set DC**: The DC must be specified when assigning the action
- **Manually selected skills**: The attribute/skill/aptitude must be specified when assigning the action
- **Description field**: Text field to describe the conflict's intent and context
- **Target faction required**: Must specify which faction is being targeted for conflict
- **Processed before other actions**: Conflicts are identified and rolled before any other actions

#### Configuration Options

- **DC**: Manually set value between 5-30
- **Primary attribute/skill selection**:
  - For agents: Must select both a primary attribute AND a skill
  - For squadrons: Must select a primary aptitude
- **Conflict description**: Text field describing the action (up to 500 chars)
- **Target faction**: Required selection of a specific faction as target
- **Target district**: Required district where conflict takes place

#### Resolution Process

1. Roll calculation:
   - For agents: d20 + primary attribute bonus + skill bonus
   - For squadrons: d20 + selected aptitude bonus
2. Determine outcome tier:
   - Critical Failure: Roll ≤ (DC - 10)
   - Failure: Roll < DC
   - Success: Roll ≥ DC
   - Critical Success: Roll ≥ (DC + 10)
3. Generate conflict report with all involved pieces, factions, and roll results
4. Record roll outcome but do not apply any direct effects
5. Wait for manual DM resolution to determine actual conflict outcome

## Resolution Mechanics

### Roll Calculation

#### Agent Roll Calculation
1. Base roll: d20
2. Add attribute bonus (0-5)
3. Add skill bonus (0-5)
4. Add faction modifiers (if applicable)
5. Add optional manual difficulty modifier (-10 to +10)
6. Apply penalty from enemy pieces (if applicable)
7. Apply advantage/disadvantage (if applicable)

#### Squadron Roll Calculation
1. Base roll: d20
2. Add aptitude bonus (-3 to +5)
3. Add faction modifiers (if applicable)
4. Add optional manual difficulty modifier (-10 to +10)
5. Apply penalty from enemy pieces (if applicable)
6. Apply advantage/disadvantage (if applicable)

### Optional Manual Difficulty Modifier

An optional manual difficulty modifier can be applied to any action to account for situational factors not explicitly covered in the existing systems. This modifier functions as follows:

- **Range**: -10 to +10
- **Default**: 0 (no modification)
- **Application**: Directly modifies the roll result, not the DC
- **Purpose**: Accounts for unique circumstances, environmental factors, or special conditions
- **Applies To**: All action types (Monitoring, Influence, and Freeform)
- **Implementation**: Must be explicitly set during action assignment
- **UI Representation**: Simple input control in all action assignment panels
- **Persistence**: Stored with action record for historical reference

This modifier is particularly important for monitoring actions where the quality of information is based on the absolute roll value rather than comparing against a DC. For example, a +5 manual modifier on a monitoring roll could push a result from the "Good" tier (15-19) to the "Very Good" tier (20-24), significantly improving information accuracy.

### Enemy Piece Penalties

Penalties from enemy pieces are applied based on faction relationships:

#### -2 Relationship (Hot War)
- Enemy squadrons give -2 to rolls within mobility range
- Enemy agents give -4 to a single randomly selected enemy piece in same district

#### -1 Relationship (Cold War)
- Enemy squadrons give -1 to rolls within mobility range
- Enemy agents give -2 to a single randomly selected enemy piece in same district

#### Application to Actions
- Enemy piece penalties apply to **all** action types:
  - Monitoring actions
  - Influence actions
  - Freeform actions
- Penalties are applied after all bonuses and before advantage/disadvantage
- Multiple penalties from different sources are cumulative
- **Timing**: All enemy piece penalties must be calculated at the beginning of the Action Resolution Phase, before any actions are resolved
- Once calculated, these penalties remain fixed throughout the entire action resolution process for that turn

#### Targeting Mechanics
1. **Targeting Priorities**:
   - **Relationship Priority**: Pieces will always target -2 relationship factions before -1 relationship factions
   - **Agent Targeting**: Agents will always target enemy agents before squadrons
   - **Squadron Targeting**: Squadrons will always target enemy squadrons before agents

2. **Agent Impact Limitation**:
   - Agents can only impact a **single** enemy piece, regardless of circumstances
   - This single target must be in the same district as the agent
   - If multiple valid targets exist, selection is based on targeting priorities

3. **Squadron Impact Range (By Mobility Rating)**:
   - **Mobility 0**: Cannot impact any enemy pieces
   - **Mobility 1**: Can impact up to 1 enemy piece in same district
   - **Mobility 2**: Can impact up to 1 enemy piece in same district OR adjacent district
   - **Mobility 3**: Can impact up to 1 enemy piece in same district AND up to 1 piece in an adjacent district
   - **Mobility 4**: Can impact up to 2 enemy pieces in same district or adjacent districts
   - **Mobility 5**: Can impact up to 1 enemy piece in same district AND up to 2 pieces in adjacent districts or same district

4. **Target Selection Process**:
   - Sort potential targets by relationship (-2 before -1)
   - Within each relationship tier, sort by piece type (according to targeting preferences)
   - If there are more potential targets than can be affected:
     - For agents: Select randomly using seeded RNG
     - For squadrons: Select randomly using seeded RNG, respecting mobility limitations

5. **Multiple Enemy Piece Resolution**:
   - If multiple enemy pieces can apply penalties to the same target:
     - Calculate penalties from all applicable sources
     - Apply cumulative penalty to the target's roll

6. **Tie-breaking**:
   - If there are more valid targets than can be affected, random selection using seeded RNG determines which targets receive penalties
   - This randomization is determined at the beginning of each turn and remains consistent throughout that turn

### Critical Success/Failure Determination

- **Critical Success**: Roll ≥ (DC + 10)
- **Success**: Roll ≥ DC
- **Failure**: Roll < DC
- **Critical Failure**: Roll ≤ (DC - 10)

### Opposed Action Handling

When actions directly oppose each other (e.g., multiple factions targeting the same resource):

1. Both sides roll their respective checks
2. The side with the higher roll result wins
3. In case of a tie, the side with the higher attribute/skill/aptitude bonus wins
4. If still tied, neither side succeeds

## Conflict Detection and Resolution

### Conflict Types and Detection

The system identifies four types of potential conflicts:

1. **Manually Initiated Conflicts**:
   - Any piece using the "Initiate Conflict" action type
   - These always create a conflict that requires manual resolution
   - The targeted faction's pieces in the district are automatically involved

2. **Relationship-based conflicts**:
   - For each pair of factions with pieces in the same district:
     - -1 relationship: 10% chance of manual conflict
     - -2 relationship: 40% chance of manual conflict

3. **Target-based conflicts**:
   - Multiple factions targeting the same limited resource
   - Take influence actions targeting the same faction

4. **Adjacent conflicts**:
   - Squadrons may join conflicts in adjacent districts based on mobility
   - Chance to join = mobility × 10%

### Conflict Processing Order

Conflicts are processed in the following order:
1. Manually initiated conflicts (always processed first)
2. Relationship-based conflicts
3. Target-based conflicts
4. Adjacent conflicts

### Faction Support System

For allied factions (relationship +2), support is handled via a simple boolean value:

1. **Support Status**:
   - Each faction has a boolean support status with every other faction
   - This status defaults to 0 (no support)
   - For allied factions (relationship +2), this status can be manually changed to 1 (will support)
   - For all other relationship values (-2, -1, 0, +1), support status is always 0 and cannot be changed

2. **Support Activation**:
   - When an ally is involved in a conflict, supporting pieces must join if support status is 1
   - Only pieces in the same district as the conflict may join
   - The supporting pieces are added to the conflict report
   - Supporting pieces cannot perform their assigned actions if they join a conflict

### Adjacent District Participation

Squadrons have a chance to join conflicts in adjacent districts:

1. **Eligibility**:
   - Only applies if the squadron's faction is involved in the conflict
   - Only applies to adjacent districts (sharing a border)
   - Only applies if the squadron is not already involved in a conflict

2. **Join Chance**:
   - Probability = Squadron mobility × 10%
   - Examples:
     - Mobility 1: 10% chance
     - Mobility 2: 20% chance
     - Mobility 3: 30% chance
     - Mobility 4: 40% chance
     - Mobility 5: 50% chance

3. **Process**:
   - For each eligible squadron, roll against the join chance
   - If successful, add squadron to the conflict
   - The squadron performs normal action roll but results are not applied until conflict resolution

### Two-Part Turn Resolution

To accommodate manual conflict resolution, the turn process is split into two parts:

#### Part 1: Pre-Conflict Resolution
1. Assignment Phase: Factions assign pieces to districts with specific actions
2. Conflict Detection Phase:
   - Detect all manually initiated conflicts
   - Detect relationship-based conflicts
   - Detect target-based conflicts
   - Calculate adjacent squadron participation
3. Action Roll Phase:
   - All pieces (including those in conflicts) roll for their assigned actions
   - Results are recorded but not applied for pieces in conflicts
4. Conflict Report Generation:
   - Generate detailed reports for all conflicts
   - Include roll results and potential outcomes
   - Provide to DM for manual resolution

#### Pause for Manual Resolution
- The system waits for DM to manually resolve all conflicts
- DM examines each conflict and determines outcome (win/loss/draw)
- Resolution may take minutes, hours, or days depending on complexity
- System remains in waiting state until all conflicts are resolved

#### Part 2: Post-Conflict Resolution
1. Conflict Outcome Application:
   - For each conflict:
     - If one side wins: All their pieces proceed with actions normally, opposing pieces fail
     - If draw: Both sides proceed with actions but take -2 penalty to rolls
2. Action Resolution Phase: System resolves all non-conflicting actions
3. Monitoring Phase: System processes all monitoring activities from agent and squadron pieces
4. Faction Passive Monitoring Phase: Processes automatic monitoring for factions with ≥4 influence in districts
5. Rumor DC Update Phase: Decreases rumor DCs by 1 each turn
6. Map Update Phase: System updates influence values based on action results

### Manual Conflict Resolution Process

When conflicts are detected, they require manual resolution by the DM:

1. **Conflict Report Review**:
   - DM reviews all generated conflict reports
   - Reports contain all involved pieces, factions, intended actions, and rolls

2. **Resolution Determination**:
   - For each conflict, DM decides the outcome:
     - Win for one faction
     - Loss for one faction
     - Draw between factions

3. **Result Recording**:
   - DM records the conflict outcome in the system
   - For each conflict, the following must be specified:
     - Which faction(s) won/lost/drew
     - Optional notes about the resolution

4. **Outcome Effects**:
   - **Win Outcome**: Winning side's pieces perform their assigned actions normally, losing side's pieces automatically fail their actions
   - **Draw Outcome**: All involved pieces perform their assigned actions but with a -2 penalty to their roll result (which may change success/failure)
   - **Special Rulings**: DM may make special rulings for particular conflicts that override the standard outcomes

### Conflict Result Data Structure

```json
{
  "conflict_id": "string",
  "turn_number": "int",
  "district_id": "string",
  "conflict_type": "string",
  "detection_source": "string",
  "factions_involved": ["faction_id_1", "faction_id_2"],
  "allies_involved": ["faction_id_3", "faction_id_4"],
  "pieces_involved": ["piece_id_1", "piece_id_2"],
  "adjacent_pieces_involved": ["piece_id_3", "piece_id_4"],
  "initial_rolls": [
    {
      "piece_id": "string",
      "roll_result": "int",
      "outcome_tier": "string"
    }
  ],
  "intended_actions": [
    {
      "piece_id": "string",
      "action_type": "string",
      "action_description": "string",
      "potential_outcome": "string"
    }
  ],
  "dm_resolution": {
    "winning_factions": ["faction_id_1"],
    "losing_factions": ["faction_id_2"],
    "draw_factions": [],
    "resolution_notes": "string",
    "resolution_timestamp": "ISO datetime string"
  },
  "created_at": "ISO datetime string",
  "updated_at": "ISO datetime string"
}
```

## Result Storage and Reporting

### Action Result Data Structure

```json
{
  "action_id": "string",
  "turn_number": "int",
  "piece_id": "string",
  "piece_type": "string",
  "faction_id": "string",
  "district_id": "string",
  "action_type": "string",
  "action_description": "string", 
  "target_faction_id": "string",
  "attribute_used": "string",
  "skill_used": "string",
  "aptitude_used": "string",
  "dc": "int",
  "manual_modifier": "int",
  "roll_result": "int",
  "outcome_tier": "string",
  "influence_gained": "int",
  "influence_lost": "int",
  "target_influence_lost": "int",
  "target_influence_gained": "int",
  "monitoring_report_id": "string",
  "conflict_id": "string",
  "in_conflict": "boolean",
  "conflict_penalty": "int",
  "dm_notes": "string",
  "timestamp": "ISO datetime string"
}
```

### Monitoring Result Data Structure

```json
{
  "monitoring_id": "string",
  "turn_number": "int",
  "piece_id": "string",
  "piece_type": "string",
  "faction_id": "string",
  "district_id": "string",
  "roll_result": "int",
  "quality_tier": "string",
  "confidence_rating": "int",
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
  "discovered_rumors": ["rumor_id_1", "rumor_id_2"],
  "discovered_district_modifier": {
    "value": "int",
    "direction_only": "boolean"
  },
  "timestamp": "ISO datetime string"
}
```

## Integration with Turn Structure

The Action Resolution System integrates with the turn structure as follows:

1. **Assignment Phase**: Factions assign pieces to districts with specific actions
2. **Conflict Detection Phase**: System detects all potential conflicts
3. **Action Roll Phase**: All pieces roll for their assigned actions (results for conflicted pieces recorded but not applied)
4. **Manual Conflict Resolution Phase**: DM manually resolves all conflicts (may take multiple days)
5. **Action Resolution Phase**: System resolves all non-conflicting actions and applies conflict outcomes
6. **Monitoring Phase**: System processes all monitoring activities from agent and squadron pieces
7. **Faction Passive Monitoring Phase**: Processes automatic monitoring for factions with ≥4 influence in districts
8. **Rumor DC Update Phase**: Decreases rumor DCs by 1 each turn
9. **Map Update Phase**: System updates influence values based on action results

## Example Resolution Workflows

### Example 1: Standard Monitoring

1. Agent with Intellect 3, Infiltration 2 is assigned to monitor District A
2. District A prefers Intellect + Infiltration
3. Roll: d20 + 3 + 2 = 17 (assuming d20 roll of 12)
4. Quality tier: Good (15-19)
5. System applies Good tier detection and accuracy rates
6. Monitoring report generated with appropriate errors
7. Discovered information assigned to faction

### Example 2: Multiple Gain Influence

1. Faction A, B, and C all attempt to gain influence in District X
2. District X has 2 available influence points
3. Faction A rolls 18 vs DC 14 (Success)
4. Faction B rolls 23 vs DC 13 (Critical Success)
5. Faction C rolls 14 vs DC 15 (Failure)
6. Resolution order: B (Critical Success), A (Success), C (Failure)
7. Faction B gains 2 influence (80% chance) or 1 influence (20% chance), exhausting or nearly exhausting the pool
8. If there's influence remaining, Faction A gains 1 influence, otherwise its action fails
9. Faction C gains nothing (failure)

### Example 3: Freeform Action

1. Faction assigns agent to "Sabotage rival's warehouse" in District Y
2. DM sets DC 16, selects Finesse + Infiltration
3. Agent has Finesse 4, Infiltration 3
4. Roll: d20 + 4 + 3 = 24 (assuming d20 roll of 17)
5. Outcome: Critical Success (exceeds DC by 8+)
6. System reports critical success
7. DM implements effects based on outcome (e.g., target faction losing resources)

### Example 4: Manual Conflict Resolution

1. Faction A initiates a conflict against Faction B in District X
   - Agent from Faction A (Finesse 3, Infiltration 4) initiates conflict (DC 16)
   - Roll: d20 + 3 + 4 = 19 (assuming d20 roll of 12)
   - Outcome: Success (exceeds DC by 3)

2. Conflict detection adds pieces to the conflict:
   - Faction B has a squadron in District X (automatically added to conflict)
   - Faction B has a squadron in adjacent District Y with Mobility 3
   - System rolls for adjacent participation: 30% chance → successful roll
   - The squadron from District Y is added to the conflict

3. Allied support check:
   - Faction C (ally of Faction A) has declared support
   - Faction C has an agent in District X
   - Agent is added to the conflict on Faction A's side

4. Action rolls for all pieces are calculated:
   - Faction A agent rolls 19 (Success) for Initiate Conflict
   - Faction B squadron in District X rolls 22 (Success) for Monitor
   - Faction B squadron from District Y rolls 15 (Success) for Gain Influence
   - Faction C agent rolls 13 (Failure) for Freeform action

5. System generates conflict report with all details and waits for DM

6. DM reviews and manually resolves conflict:
   - DM determines Faction A wins the conflict
   - Resolution recorded in system

7. System applies conflict outcome effects:
   - Faction A's agent action proceeds normally (Success)
   - Faction C's agent action fails automatically (losing side)
   - Both Faction B squadrons' actions fail automatically (losing side)

8. Turn proceeds with remaining pieces' actions

### Example 5: Relationship-Based Conflict with Draw

1. Relationship conflict detected:
   - Faction A and Faction D have -2 relationship (Hot War)
   - Both have pieces in District Z
   - 40% chance of conflict → successful roll
   - Conflict automatically created

2. Action rolls for all pieces are calculated:
   - Faction A agent rolls 18 (Success) for Gain Influence
   - Faction D squadron rolls 21 (Success) for Take Influence

3. System generates conflict report and waits for DM

4. DM reviews and manually resolves conflict:
   - DM determines it's a draw
   - Resolution recorded in system

5. System applies conflict outcome effects:
   - Both pieces proceed with their actions but with -2 penalty
   - Faction A agent: 18 - 2 = 16 (still Success for Gain Influence)
   - Faction D squadron: 21 - 2 = 19 (still Success for Take Influence)
   - Both actions are processed during the Action Resolution Phase

## Technical Implementation Notes

1. **Deterministic RNG**: Use seeded random number generation for all randomized results
2. **Transaction Management**: Ensure all action results are stored in atomic transactions
3. **Conflict Detection**: Implement efficient conflict detection algorithms that look for specific patterns
4. **Result Storage**: Store all action results for historical analysis and reporting
5. **UI Integration**: Provide clear visualization of action outcomes in the user interface
6. **State Management**: Implement proper state management for the two-part turn resolution
7. **Persistence**: Ensure the system can be safely paused between turn parts without data loss
8. **Conflict Resolution UI**: Create a specialized UI for DM conflict resolution