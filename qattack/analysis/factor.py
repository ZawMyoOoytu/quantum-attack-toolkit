from math import gcd


def derive_factors(
    a: int,
    r: int,
    n: int,
) -> tuple[int, int] | None:
    """
    Derive non-trivial factors from an even order.

    For the N=15 benchmark:

        a = 2
        r = 4

    gives:

        2^(4/2) = 4

        gcd(4 - 1, 15) = 3
        gcd(4 + 1, 15) = 5
    """

    if a <= 0:
        return None

    if r <= 0:
        return None

    if n <= 1:
        return None

    if r % 2 != 0:
        return None

    x = pow(
        a,
        r // 2,
        n,
    )

    factor_1 = gcd(
        x - 1,
        n,
    )

    factor_2 = gcd(
        x + 1,
        n,
    )

    if factor_1 in (1, n):
        return None

    if factor_2 in (1, n):
        return None

    if factor_1 * factor_2 != n:
        return None

    return (
        min(factor_1, factor_2),
        max(factor_1, factor_2),
    )