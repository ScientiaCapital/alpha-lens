"""
Options asset implementation with pricing and Greeks.
"""

from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from scipy.stats import norm
from loguru import logger

from alphalens.assets.base import BaseAsset, AssetType


class OptionType(Enum):
    """Option type."""
    CALL = "call"
    PUT = "put"


class OptionStyle(Enum):
    """Option exercise style."""
    AMERICAN = "american"
    EUROPEAN = "european"


@dataclass
class Greeks:
    """Option Greeks."""
    delta: float  # Change in option price per $1 change in underlying
    gamma: float  # Change in delta per $1 change in underlying
    theta: float  # Time decay per day
    vega: float  # Change in option price per 1% change in IV
    rho: float  # Change in option price per 1% change in interest rate


class OptionAsset(BaseAsset):
    """
    Options contract.

    Supports:
    - Black-Scholes pricing
    - Greeks calculation
    - Implied volatility
    - American and European styles
    """

    def __init__(
        self,
        symbol: str,
        underlying_symbol: str,
        strike: float,
        expiry: datetime,
        option_type: OptionType,
        style: OptionStyle = OptionStyle.AMERICAN,
        exchange: str = "CBOE",
        contract_size: int = 100,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize option asset.

        Args:
            symbol: Option symbol (e.g., "AAPL210115C00135000")
            underlying_symbol: Underlying asset symbol
            strike: Strike price
            expiry: Expiration date
            option_type: Call or Put
            style: American or European
            exchange: Exchange
            contract_size: Number of shares per contract (usually 100)
            metadata: Additional metadata
        """
        metadata = metadata or {}
        metadata.update({
            "underlying": underlying_symbol,
            "strike": strike,
            "expiry": expiry.isoformat(),
            "type": option_type.value,
            "style": style.value,
            "contract_size": contract_size
        })

        super().__init__(
            symbol=symbol,
            asset_type=AssetType.OPTION,
            exchange=exchange,
            metadata=metadata
        )

        self.underlying_symbol = underlying_symbol
        self.strike = strike
        self.expiry = expiry
        self.option_type = option_type
        self.style = style
        self.contract_size = contract_size

        self._greeks: Optional[Greeks] = None
        self._implied_volatility: Optional[float] = None

    def get_identifier(self) -> str:
        """Get unique identifier for option."""
        exp_str = self.expiry.strftime("%y%m%d")
        type_str = "C" if self.option_type == OptionType.CALL else "P"
        strike_str = f"{int(self.strike * 1000):08d}"
        return f"{self.underlying_symbol}{exp_str}{type_str}{strike_str}"

    def is_tradeable(self) -> bool:
        """Check if option is tradeable (not expired)."""
        return datetime.now() < self.expiry

    def get_lot_size(self) -> float:
        """Options trade in contracts of 1."""
        return 1.0

    def calculate_value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate option position value.

        Args:
            quantity: Number of contracts
            price: Option price per share (current price if None)

        Returns:
            Total value (quantity * price * contract_size)
        """
        if price is None:
            price = self.get_current_price()
            if price is None:
                raise ValueError(f"No price available for {self.symbol}")

        return quantity * price * self.contract_size

    def days_to_expiry(self) -> float:
        """Calculate days until expiration."""
        now = datetime.now()
        if now >= self.expiry:
            return 0.0

        delta = self.expiry - now
        return delta.total_seconds() / (24 * 3600)

    def time_to_expiry(self) -> float:
        """Calculate time to expiry in years."""
        return self.days_to_expiry() / 365.0

    def is_itm(self, underlying_price: float) -> bool:
        """
        Check if option is in-the-money.

        Args:
            underlying_price: Current underlying price

        Returns:
            True if ITM
        """
        if self.option_type == OptionType.CALL:
            return underlying_price > self.strike
        else:  # PUT
            return underlying_price < self.strike

    def intrinsic_value(self, underlying_price: float) -> float:
        """
        Calculate intrinsic value.

        Args:
            underlying_price: Current underlying price

        Returns:
            Intrinsic value (max of 0 or ITM amount)
        """
        if self.option_type == OptionType.CALL:
            return max(0, underlying_price - self.strike)
        else:  # PUT
            return max(0, self.strike - underlying_price)

    def black_scholes_price(
        self,
        underlying_price: float,
        volatility: float,
        risk_free_rate: float = 0.02,
        dividend_yield: float = 0.0
    ) -> float:
        """
        Calculate option price using Black-Scholes model.

        Args:
            underlying_price: Current underlying price
            volatility: Implied volatility (annualized)
            risk_free_rate: Risk-free interest rate (annualized)
            dividend_yield: Dividend yield (annualized)

        Returns:
            Option theoretical price
        """
        S = underlying_price
        K = self.strike
        T = self.time_to_expiry()
        r = risk_free_rate
        q = dividend_yield
        sigma = volatility

        if T <= 0:
            # Expired option
            return self.intrinsic_value(S)

        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if self.option_type == OptionType.CALL:
            price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # PUT
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

        return price

    def calculate_greeks(
        self,
        underlying_price: float,
        volatility: float,
        risk_free_rate: float = 0.02,
        dividend_yield: float = 0.0
    ) -> Greeks:
        """
        Calculate option Greeks.

        Args:
            underlying_price: Current underlying price
            volatility: Implied volatility
            risk_free_rate: Risk-free rate
            dividend_yield: Dividend yield

        Returns:
            Greeks object
        """
        S = underlying_price
        K = self.strike
        T = self.time_to_expiry()
        r = risk_free_rate
        q = dividend_yield
        sigma = volatility

        if T <= 0:
            # Expired option - all Greeks are zero
            return Greeks(delta=0, gamma=0, theta=0, vega=0, rho=0)

        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Delta
        if self.option_type == OptionType.CALL:
            delta = np.exp(-q * T) * norm.cdf(d1)
        else:  # PUT
            delta = -np.exp(-q * T) * norm.cdf(-d1)

        # Gamma (same for calls and puts)
        gamma = (np.exp(-q * T) * norm.pdf(d1)) / (S * sigma * np.sqrt(T))

        # Vega (same for calls and puts, per 1% change in IV)
        vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T) / 100

        # Theta (per day)
        if self.option_type == OptionType.CALL:
            theta = (
                -S * norm.pdf(d1) * sigma * np.exp(-q * T) / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * norm.cdf(d2)
                + q * S * np.exp(-q * T) * norm.cdf(d1)
            ) / 365
        else:  # PUT
            theta = (
                -S * norm.pdf(d1) * sigma * np.exp(-q * T) / (2 * np.sqrt(T))
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
                - q * S * np.exp(-q * T) * norm.cdf(-d1)
            ) / 365

        # Rho (per 1% change in interest rate)
        if self.option_type == OptionType.CALL:
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:  # PUT
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

        greeks = Greeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )

        self._greeks = greeks
        return greeks

    def implied_volatility(
        self,
        option_price: float,
        underlying_price: float,
        risk_free_rate: float = 0.02,
        dividend_yield: float = 0.0,
        max_iterations: int = 100,
        tolerance: float = 1e-5
    ) -> Optional[float]:
        """
        Calculate implied volatility using Newton-Raphson method.

        Args:
            option_price: Observed option price
            underlying_price: Current underlying price
            risk_free_rate: Risk-free rate
            dividend_yield: Dividend yield
            max_iterations: Maximum iterations
            tolerance: Convergence tolerance

        Returns:
            Implied volatility or None if not found
        """
        # Initial guess
        sigma = 0.3

        for i in range(max_iterations):
            # Calculate price and vega at current sigma
            price = self.black_scholes_price(
                underlying_price, sigma, risk_free_rate, dividend_yield
            )

            greeks = self.calculate_greeks(
                underlying_price, sigma, risk_free_rate, dividend_yield
            )

            # Calculate difference
            diff = price - option_price

            # Check convergence
            if abs(diff) < tolerance:
                self._implied_volatility = sigma
                return sigma

            # Newton-Raphson update
            if greeks.vega > 0:
                sigma = sigma - diff / (greeks.vega * 100)  # vega is per 1% change

                # Keep sigma positive and reasonable
                sigma = max(0.01, min(sigma, 5.0))
            else:
                break

        logger.warning(f"Implied volatility did not converge for {self.symbol}")
        return None

    def get_greeks(self) -> Optional[Greeks]:
        """Get cached Greeks."""
        return self._greeks

    def get_implied_volatility(self) -> Optional[float]:
        """Get cached implied volatility."""
        return self._implied_volatility

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            "underlying": self.underlying_symbol,
            "strike": self.strike,
            "expiry": self.expiry.isoformat(),
            "option_type": self.option_type.value,
            "style": self.style.value,
            "days_to_expiry": self.days_to_expiry(),
            "contract_size": self.contract_size
        })

        if self._greeks:
            data["greeks"] = {
                "delta": self._greeks.delta,
                "gamma": self._greeks.gamma,
                "theta": self._greeks.theta,
                "vega": self._greeks.vega,
                "rho": self._greeks.rho
            }

        if self._implied_volatility:
            data["implied_volatility"] = self._implied_volatility

        return data
