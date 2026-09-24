## Reasoning

**Step 1 – Enumerate candidates.**
The digits must satisfy a > b > c (strictly decreasing, all distinct) and a + b + c = 18.

| a | possible (b, c) pairs | number |
|---|----------------------|--------|
| 9 | (8,1) (7,2) (6,3) (5,4) | 981, 972, 963, 954 |
| 8 | (7,3) (6,4) | 873, 864 |
| 7 | (6,5) | 765 |

**Step 2 – Test divisibility by 17.**

- 981 ÷ 17 ≈ 57.7 → no
- 972 ÷ 17 ≈ 57.2 → no
- 963 ÷ 17 ≈ 56.6 → no
- 954 ÷ 17 ≈ 56.1 → no
- 873 ÷ 17 ≈ 51.4 → no
- 864 ÷ 17 ≈ 50.8 → no
- **765 ÷ 17 = 45 exactly** ✔️

**Verification:** 7 + 6 + 5 = 18 ✔️, 7 > 6 > 5 ✔️, all digits distinct ✔️, 17 × 45 = 765 ✔️.

ANSWER: 765