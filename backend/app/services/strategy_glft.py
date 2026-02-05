from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class GLFTParams:
    gamma: float
    sigma: float
    A: float
    k: float
    order_size: float
    time_horizon_seconds: int


def compute_coeff(gamma: float, delta: float, A: float, k: float) -> tuple[float, float]:
    inv_k = 1.0 / max(k, 1e-9)
    xi = gamma
    c1 = 1.0 / (xi * delta) * math.log(1 + xi * delta * inv_k)
    c2 = math.sqrt(
        (gamma / (2 * A * delta * k))
        * ((1 + xi * delta * inv_k) ** (k / (xi * delta) + 1))
    )
    return c1, c2


def compute_quotes(
    mid_price: float, inventory: float, params: GLFTParams
) -> tuple[float, float, float]:
    c1, c2 = compute_coeff(params.gamma, params.order_size, params.A, params.k)
    half_spread = c1 + params.order_size / 2.0 * c2 * params.sigma
    time_factor = max(params.time_horizon_seconds, 1) / 3600.0
    skew = c2 * params.sigma * math.sqrt(time_factor)
    reservation_price = mid_price - skew * inventory
    bid = reservation_price - half_spread
    ask = reservation_price + half_spread
    spread = ask - bid
    return bid, ask, spread
