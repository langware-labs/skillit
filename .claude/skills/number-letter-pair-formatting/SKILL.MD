---
name: number-letter-pair-formatting
description: >
  Ensures that when counting numbers paired with letters, each number-letter pair
  (1A, 2B, 3C, etc.) is written on its own separate line. Triggered when listing
  numbered items with letters, counting sequences, pairing numbers with letters,
  or when asked to count or enumerate items in a numbered-letter format.
  Prevents all pairs from being placed on a single line.
---

# Number Letter Pair Formatting

This skill enforces correct formatting when counting or listing number-letter pairs, ensuring each pair appears on its own line rather than all on one row.

## Instructions

1. When asked to count numbers paired with letters (e.g., 1A, 2B, 3C or similar enumeration), always place each pair on its own separate line.
2. Do NOT write all pairs on a single line separated by spaces or commas.
3. Use a simple line-by-line format: one pair per line.
4. This applies to any context where numbers and letters are paired in a sequence, including counting exercises, enumeration lists, and formatted outputs.

## Examples

### Example 1: Counting with letter pairs (correct format)

**Input:**
```
List the first 5 number-letter pairs.
```

**Output:**
```
1A
2B
3C
4D
5E
```

### Example 2: Wrong format to avoid

**Input:**
```
Count from 1 to 3 with matching letters.
```

**Bad Output (do NOT do this):**
```
1A 2B 3C
```

**Correct Output:**
```
1A
2B
3C
```

### Example 3: Longer sequence

**Input:**
```
Give me pairs from 1 to 8.
```

**Output:**
```
1A
2B
3C
4D
5E
6F
7G
8H
```
