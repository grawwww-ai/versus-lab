Let me work through this step by step.

I need a three-digit number where:
1. Digits are all different and strictly decreasing from left to right (so if digits are a, b, c then a > b > c)
2. Sum of digits is 18
3. Divisible by 17

Let me first find all three-digit numbers with digits a > b > c where a + b + c = 18.

The maximum sum of three distinct digits in decreasing order is 9 + 8 + 7 = 24, minimum is 2 + 1 + 0 = 3.

I need a + b + c = 18 with a > b > c, where a is 1-9, b is 0-9, c is 0-9.

Let me enumerate:
- a = 9: b + c = 9, b > c, b < 9
  - b = 8, c = 1: 981 ✓
  - b = 7, c = 2: 972 ✓
  - b = 6, c = 3: 963 ✓
  - b = 5, c = 4: 954 ✓

- a = 8: b + c = 10, b > c, b < 8
  - b = 7, c = 3: 873 ✓
  - b = 6, c = 4: 864 ✓
  - b = 5, c = 5: not strictly decreasing ✗

- a = 7: b + c = 11, b > c, b < 7
  - b = 6, c = 5: 765 ✓
  - b = 5, c = 6: not decreasing ✗

So candidates: 981, 972, 963, 954, 873, 864, 765

Now check divisibility by 17:
- 981 / 17 = 57.7... → 17 × 57 = 969, 17 × 58 = 986. Not divisible.
- 972 / 17 = 57.17... → 17 × 57 = 969. Not divisible.
- 963 / 17 = 56.6... → 17 × 56 = 952, 17 × 57 = 969. Not divisible.
- 954 / 17 = 56.1... → 17 × 56 = 952. Not divisible.
- 873 / 17 = 51.35... → 17 × 51 = 867. Not divisible.
- 864 / 17 = 50.8... → 17 × 50 = 850, 17 × 51 = 867. Not divisible.
- 765 / 17 = 45.0 → 17 × 45 = 765. Yes! Divisible.

Let me verify: 7 + 6 + 5 = 18 ✓, digits 7 > 6 > 5 ✓, all different ✓, 765 / 17 = 45 ✓.

The answer is 765.
