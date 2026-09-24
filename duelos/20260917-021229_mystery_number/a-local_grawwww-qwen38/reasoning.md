Let me work through this step-by-step.

I need a three-digit number where:
1. All digits are different
2. Digits are strictly decreasing from left to right (so if digits are a, b, c, then a > b > c)
3. a + b + c = 18
4. The number is divisible by 17

Let me think about what three digits (distinct, strictly decreasing) sum to 18.

Let me list all possible triples (a, b, c) with a > b > c ≥ 0 and a + b + c = 18.

a can be at most 9 (since it's a digit).

If a = 9: b + c = 9, with b > c, b < 9, c < b, all different
- b = 8, c = 1
- b = 7, c = 2
- b = 6, c = 3
- b = 5, c = 4

If a = 8: b + c = 10, with b > c, b < 8
- b = 7, c = 3
- b = 6, c = 4
- b = 5, c = 5 → not allowed (not different)

If a = 7: b + c = 11, with b > c, b < 7
- b = 6, c = 5

So possible numbers:
981, 972, 963, 954, 873, 864, 765

Now check divisibility by 17:
- 981 / 17 = 57.70... → 17 × 57 = 969, 17 × 58 = 986 → no
- 972 / 17 = 57.17... → 17 × 57 = 969 → no
- 963 / 17 = 56.64... → 17 × 56 = 952, 17 × 57 = 969 → no
- 954 / 17 = 56.11... → 17 × 56 = 952 → no
- 873 / 17 = 51.35... → 17 × 51 = 867 → no
- 864 / 17 = 50.82... → 17 × 50 = 850, 17 × 51 = 867 → no
- 765 / 17 = 45 → 17 × 45 = 765 → YES!

Let me verify: 765
- Digits: 7, 6, 5 — all different ✓
- Strictly decreasing: 7 > 6 > 5 ✓
- Sum: 7 + 6 + 5 = 18 ✓
- Divisible by 17: 17 × 45 = 765 ✓

The answer is 765.
