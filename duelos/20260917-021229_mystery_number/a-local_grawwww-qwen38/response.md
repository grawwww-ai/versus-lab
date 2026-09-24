## Reasoning

**Setting up the digit constraints.** Let the digits be *a > b > c ≥ 0*, all distinct, with *a + b + c = 18*.

**Enumerating valid triples.**

- *a* = 9 → *b + c* = 9 with *b > c*: (8,1), (7,2), (6,3), (5,4) → **981, 972, 963, 954**
- *a* = 8 → *b + c* = 10 with *b > c < 8*: (7,3), (6,4) → **873, 864**
- *a* = 7 → *b + c* = 11 with *b > c < 7*: (6,5) → **765**

**Testing divisibility by 17.**

| Number | ÷ 17 | Result |
|--------|------|--------|
| 981 | 57.71 | ✗ |
| 972 | 57.18 | ✗ |
| 963 | 56.65 | ✗ |
| 954 | 56.12 | ✗ |
| 873 | 51.35 | ✗ |
| 864 | 50.82 | ✗ |
| **765** | **45.00** | **✓ (17 × 45 = 765)** |

Only 765 satisfies every condition: digits 7 > 6 > 5 are distinct and strictly decreasing, their sum is 18, and 17 × 45 = 765.

ANSWER: 765