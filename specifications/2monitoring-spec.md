# Monitoring System Specification

## Core Principles
- **Tiered Information Quality**: Higher rolls produce more accurate information
- **Deterministic Randomization**: Same roll always produces same error pattern using seeded RNG
- **Weighted Error Distribution**: Small magnitude errors more likely than large ones
- **Holistic Information Cap**: Total reported influence can never exceed 10
- **Influence-Based Detection**: Higher influence levels harder to miss or misreport
- **Error Types**: Omission, misattribution, magnitude errors, and phantom detection

## Monitoring Sources

### 1. Agent Monitoring
- Agents only monitor when specifically assigned to that task
- Roll: d20 + Attribute (district's preferred) + Skill (district's preferred) + Optional manual difficulty modifier (-10 to +10)

### 2. Squadron Monitoring
- **Primary Assignment**: d20 + Monitoring aptitude bonus + Optional manual difficulty modifier (-10 to +10)
- **Secondary Monitoring**: All squadrons automatically monitor regardless of assigned task
  - If performing another task: Roll with disadvantage (roll twice, take lower result)
- The Monitoring aptitude ranges from -3 to +5
- If not explicitly set, Monitoring defaults to -1

### 3. Faction Passive Monitoring
- Automatic in districts where they have ≥4 influence
- Roll: d20 + (Influence ÷ 2) + Faction monitoring bonus

## Information Discovery System

### 1. District Rumor Discovery
- Each district contains rumors with associated DCs
- Rumors discovered if roll beats the DC:
  - Roll beats DC by 7+: All such rumors discovered
  - Roll beats DC by <7: One random rumor discovered
- DCs decrease by 1 each week (during Rumor DC Update Phase)

### 2. Faction Influence Discovery System

#### Information Types Revealed by Check
1. Faction presence/absence in district
2. Influence magnitude for each faction
3. Recent influence changes (if any)
4. Stronghold presence/absence
5. Phantom faction detection (false positives)

#### Detailed Information Quality by Check Result

##### Legendary Results (30+)
- **Faction Detection**: 100% of all factions detected
- **Influence Accuracy**: 100% accuracy (exact values)
- **Recent Changes**: Detects all influence changes from past 3 turns with 100% accuracy
- **Strongholds**: All strongholds correctly identified
- **Phantom Detection**: 0% chance to perceive absent factions
- **Special Benefit**: 75% chance to detect one hidden activity planned by another faction for next turn

##### Exceptional Results (25-29)
- **Faction Detection**: 100% of all factions detected
- **Influence Accuracy**: 
  - Base: 90% chance of exact value
  - Linear scaling: Every point above 25 adds 2% chance of exact value (up to 100% at 30)
  - Remainder: ±1 error (weighted toward true value)
- **Recent Changes**: Detects influence changes from past 2 turns with 90% accuracy
- **Strongholds**: All strongholds correctly identified
- **Phantom Detection**: 0% chance to perceive absent factions
- **Special Benefit**: 25% chance to learn one faction relationship value

##### Very Good Results (20-24)
- **Faction Detection**:
  - 100% detection for factions with influence ≥2
  - 95% detection for factions with influence 1
  - Linear scaling: Each point above 20 adds 1% to detection chance for influence 1 (up to 100% at 25)
- **Influence Accuracy**:
  - Base for influence ≥5: 80% chance exact, 20% chance ±1 error
  - Base for influence 2-4: 75% chance exact, 25% chance ±1 error
  - Base for influence 1: 70% chance exact, 30% chance ±1 error
  - Linear scaling: Each point above 20 adds 1% to exactness chance
- **Recent Changes**: Detects influence changes from past turn with 80% accuracy
- **Strongholds**: 95% chance to correctly identify each stronghold
- **Phantom Detection**: 
  - 5% chance to perceive an absent faction
  - Linear scaling: Each point below 24 adds 0.5% to phantom chance (up to 7% at 20)
  - If phantom detected, influence value is 1 (80% chance) or 2 (20% chance)
  - Phantom detection weighted toward factions with influence in adjacent districts

##### Good Results (15-19)
- **Faction Detection**:
  - 100% detection for factions with influence ≥4
  - 90% detection for factions with influence 2-3
  - 75% detection for factions with influence 1
  - Linear scaling: Each point above 15 adds 2% to detection chance for influence 1 (up to 95% at 19)
  - Linear scaling: Each point above 15 adds 1% to detection chance for influence 2-3 (up to 94% at 19)
- **Influence Accuracy**:
  - Base for influence ≥5: 65% chance exact, 30% chance ±1 error, 5% chance ±2 error
  - Base for influence 2-4: 55% chance exact, 35% chance ±1 error, 10% chance ±2 error
  - Base for influence 1: 45% chance exact, 45% chance ±1 error, 10% chance ±2 error
  - Linear scaling: Each point above 15 adds 1% to exactness chance and reduces larger errors
- **Recent Changes**: 50% chance to detect major influence changes (≥2 points) from past turn
- **Strongholds**: 85% chance to correctly identify each stronghold
- **Phantom Detection**:
  - Base: 15% chance to perceive an absent faction
  - Linear scaling: Each point below 19 adds 1% to phantom chance (up to 19% at 15)
  - If phantom detected, influence values: 1 (70% chance), 2 (25% chance), or 3 (5% chance)
  - Phantom detection heavily weighted toward factions with influence in adjacent districts (3x likelihood)

##### Average Results (10-14)
- **Faction Detection**:
  - 95% detection for factions with influence ≥6
  - 80% detection for factions with influence 3-5
  - 60% detection for factions with influence 2
  - 0% detection for factions with influence 1 (never detected)
  - Linear scaling: Each point above 10 adds 3% to detection chance for influence 2 (up to 72% at 14)
  - Linear scaling: Each point above 10 adds 2% to detection chance for influence 3-5 (up to 88% at 14)
- **Influence Accuracy**:
  - Base for influence ≥6: 40% chance exact, 35% chance ±1 error, 20% chance ±2 error, 5% chance ±3 error
  - Base for influence 3-5: 30% chance exact, 40% chance ±1 error, 25% chance ±2 error, 5% chance ±3 error
  - Base for influence 2: 20% chance exact, 45% chance ±1 error, 30% chance ±2 error, 5% chance ±3 error
  - Linear scaling: Each point above 10 adds 2% to exactness chance and proportionally reduces errors
- **Recent Changes**: No reliable information about recent changes
- **Strongholds**: 70% chance to correctly identify each stronghold
- **Phantom Detection**:
  - Base: 25% chance to perceive an absent faction
  - Linear scaling: Each point above 10 reduces phantom chance by 1% (down to 21% at 14)
  - Linear scaling: Each point below 10 increases phantom chance by 2% (up to 33% at 6)
  - If phantom detected, influence values: 1 (50% chance), 2 (30% chance), 3 (15% chance), or 4 (5% chance)
  - Phantom detection moderately weighted toward factions with influence in adjacent districts (2x likelihood)

##### Poor Results (5-9)
- **Faction Detection**:
  - 90% detection for factions with influence ≥7
  - 70% detection for factions with influence 4-6
  - 50% detection for factions with influence 2-3
  - 0% detection for factions with influence 1 (never detected)
  - Linear scaling: Each point above 5 adds 4% to detection chance for influence 2-3 (up to 66% at 9)
  - Linear scaling: Each point above 5 adds 3% to detection chance for influence 4-6 (up to 82% at 9)
  - Linear scaling: Each point above 5 adds 1% to detection chance for influence ≥7 (up to 94% at 9)
- **Influence Accuracy**:
  - Major magnitude errors possible
  - Base for influence ≥7: 20% chance exact, 30% chance ±1-2 error, 50% chance ±3-4 error
  - Base for influence 4-6: 10% chance exact, 30% chance ±1-2 error, 60% chance ±3-4 error
  - Base for influence 2-3: 5% chance exact, 25% chance ±1-2 error, 70% chance ±3-4 error
  - Linear scaling: Each point above 5 adds 3% to exactness chance and reduces larger errors
  - 40% chance that high influence (≥6) appears low (≤4) or vice versa (scaling: -4% per point above 5)
- **Magnitude Direction Bias**:
  - 60% chance errors are randomly distributed
  - 25% chance errors trend toward underestimation
  - 15% chance errors trend toward overestimation
- **Strongholds**: 50% chance to correctly identify each stronghold, 10% chance to falsely identify a stronghold
- **Phantom Detection**:
  - Base: 35% chance to perceive an absent faction
  - Linear scaling: Each point above 5 reduces chance by 1% (down to 31% at 9)
  - If phantom detected, influence values: 1-2 (60% chance), 3-4 (30% chance), or 5-6 (10% chance)
  - Phantom detection slightly weighted toward factions with influence in adjacent districts (1.5x likelihood)

##### Very Poor Results (1-4)
- **Faction Detection**:
  - 80% detection for factions with influence ≥8
  - 60% detection for factions with influence 5-7
  - 40% detection for factions with influence 3-4
  - 0% detection for factions with influence 1-2 (never detected)
  - Linear scaling: Each point above 1 adds 5% to detection chance for influence 3-4 (up to 55% at 4)
  - Linear scaling: Each point above 1 adds 4% to detection chance for influence 5-7 (up to 72% at 4)
  - Linear scaling: Each point above 1 adds 3% to detection chance for influence ≥8 (up to 89% at 4)
- **Influence Accuracy**:
  - Severe magnitude errors common
  - Base for all detected factions: 5% chance exact, 15% chance ±1-2 error, 30% chance ±3-4 error, 50% chance ±5 error
  - Linear scaling: Each point above 1 adds 2% to lower error brackets at expense of higher ones
  - 60% chance that high influence (≥6) appears low (≤4) or vice versa (scaling: -3% per point above 1)
- **Magnitude Direction Bias**:
  - 40% chance errors are randomly distributed
  - 40% chance errors trend heavily toward underestimation
  - 20% chance errors trend heavily toward overestimation  
- **Strongholds**: 30% chance to correctly identify each stronghold, 25% chance to falsely identify a stronghold
- **Phantom Detection**:
  - Base: 45% chance to perceive an absent faction
  - Linear scaling: Each point above 1 reduces chance by 2% (down to 39% at 4)
  - If phantom detected, influence values: 1-3 (50% chance), 4-6 (40% chance), or 7-8 (10% chance)
  - Phantom detection negligibly weighted toward factions with influence in adjacent districts (1.1x likelihood)

##### Abysmal Results (0 or less)
- **Faction Detection**:
  - 60% detection for factions with influence ≥9
  - 40% detection for factions with influence 6-8
  - 20% detection for factions with influence 4-5
  - 0% detection for factions with influence 1-3 (never detected)
  - Linear scaling: For negative rolls, each point below 0 reduces detection chances by 5% per bracket
- **Influence Accuracy**:
  - Information is effectively random
  - For all detected factions: 0% chance exact, 5% chance ±1-3 error, 15% chance ±4-5 error, 80% chance ±6-9 error
  - Linear scaling: For negative rolls, each point below 0 increases chance of maximum error by 2%
- **Strongholds**: 20% chance to correctly identify each stronghold, 40% chance to falsely identify a stronghold
- **Phantom Detection**:
  - 60% chance to perceive an absent faction
  - Linear scaling: Each point below 0 increases chance by 3% (with practical ceiling of 90%)
  - If phantom detected, influence values uniformly random between 1-10
  - No weighting based on adjacent districts

### 3. Influence Total Adjustment Algorithm
- After determining all faction influence values (real and phantom):
  1. Calculate the sum of all perceived influence values
  2. If sum exceeds 10:
     - Randomly select factions and reduce their influence by 1 point
     - Continue until total influence equals 10
     - Ensure at least 1 influence remains for each detected faction
  3. No weighting or preferential treatment for any faction

### 4. Phantom Faction Detection Mechanics
- **Selection Process**:
  1. Roll to determine if phantom faction(s) will be detected based on check result tier
  2. If yes, determine number of phantom factions: 
     - 70% chance: 1 phantom faction
     - 25% chance: 2 phantom factions
     - 5% chance: 3 phantom factions
  3. For each phantom slot, select faction using weighted probability:
     - Equal probability for all factions not present in the district
     - If faction has influence in adjacent district: weight modifier based on check result
     - If faction is already detected (real presence): weight = 0
     - If faction is already selected as phantom: weight = 0

- **Influence Assignment**:
  - Use influence range specified for check result tier
  - Apply random selection within that range based on these weights:
    - Lower values more likely than higher values
    - Distribution skew based on check result tier (worse checks = more uniform distribution)

### 5. District Modifier Discovery System
- Monitoring rolls can reveal the current district DC modifier
- Discovery chance based solely on roll value and modifier magnitude

#### Detailed Discovery Chances by Modifier Magnitude

##### For ±2 modifiers (strongest effect, most noticeable)
- Roll 30+: 100% chance to discover exact value
- Roll 25-29: 100% chance to discover exact value
- Roll 20-24: 100% chance to discover exact value
- Roll 15-19: 80% chance to discover exact value, 20% chance of direction only
- Roll 10-14: 60% chance to discover exact value, 30% chance of direction only, 10% chance of nothing
- Roll 5-9: 40% chance to discover direction only, 60% chance of nothing
- Roll 1-4: 20% chance to discover direction only, 80% chance of nothing
- Roll 0 or less: 10% chance to discover direction only (possibly wrong), 90% chance of nothing

##### For ±1 modifiers (moderate effect, somewhat subtle)
- Roll 30+: 100% chance to discover exact value
- Roll 25-29: 95% chance to discover exact value, 5% chance of direction only
- Roll 20-24: 90% chance to discover exact value, 10% chance of direction only
- Roll 15-19: 70% chance to discover exact value, 20% chance of direction only, 10% chance of nothing
- Roll 10-14: 40% chance to discover exact value, 40% chance of direction only, 20% chance of nothing
- Roll 5-9: 20% chance to discover direction only, 80% chance of nothing
- Roll 1-4: 10% chance to discover direction only, 90% chance of nothing
- Roll 0 or less: 5% chance to discover direction only (possibly wrong), 95% chance of nothing

##### For 0 modifier (neutral state, hardest to definitively confirm)
- Roll 30+: 95% chance to discover exact value, 5% chance of ±1 error
- Roll 25-29: 85% chance to discover exact value, 15% chance of ±1 error
- Roll 20-24: 70% chance to discover exact value, 30% chance of nothing
- Roll 15-19: 50% chance to discover exact value, 50% chance of nothing
- Roll 10-14: 30% chance to discover exact value, 70% chance of nothing
- Roll 5-9: 15% chance to discover exact value, 85% chance of nothing
- Roll 1-4: 5% chance to discover exact value, 95% chance of nothing
- Roll 0 or less: 0% chance to discover anything meaningful

#### False Information Generation
- When discovery fails but a result is still provided (direction only):
  - Rolls 15+: 0% chance of false information
  - Rolls 10-14: 5% chance that direction is incorrect
  - Rolls 5-9: 15% chance that direction is incorrect
  - Rolls 1-4: 30% chance that direction is incorrect
  - Rolls 0 or less: 50% chance that direction is incorrect

- For false exact values (when applicable):
  - Error always ±1 from true value (never generates completely random values)
  - Error direction randomly determined

## Weekly Intelligence Report System

### Report Contents
- Each faction receives a weekly intelligence report for each district where monitoring occurred
- Report elements:
  - List of detected factions with perceived influence values
  - Stronghold presence/absence for each faction
  - District DC modifier (if discovered)
  - Overall district confidence rating (1-10)
  - Full descriptions of all discovered rumors in that district

### Confidence Rating Calculation
- Base confidence value determined by highest monitoring roll:
  - Roll 30+: Base confidence 10
  - Roll 25-29: Base confidence 9
  - Roll 20-24: Base confidence 8
  - Roll 15-19: Base confidence 7
  - Roll 10-14: Base confidence 5
  - Roll 5-9: Base confidence 3
  - Roll 1-4: Base confidence 2
  - Roll 0 or less: Base confidence 1

### Confidence Accuracy
- Error calculation:
  - Roll 20+: Exact confidence rating
  - Roll 15-19: ±0-1 error in confidence rating
  - Roll 10-14: ±0-2 error in confidence rating
  - Roll 5-9: ±1-3 error in confidence rating
  - Roll 1-4: ±2-4 error in confidence rating
  - Roll 0 or less: ±3-5 error in confidence rating

- Error direction randomly determined:
  - 50% chance: Higher than actual confidence
  - 50% chance: Lower than actual confidence

## Technical Implementation Notes
- Use deterministic random number generator seeded with roll value for all randomized results
- Each roll should produce consistent results when using the same seed
- Pre-compute probability tables for common checks
- Generate faction-specific reports in clearly formatted text structure
- Copy-friendly format with minimal formatting requirements