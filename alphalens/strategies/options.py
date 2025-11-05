"""
Options trading strategies.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from alphalens.assets.option import OptionAsset, OptionType, Greeks
from alphalens.assets.equity import EquityAsset
from loguru import logger


@dataclass
class Position:
    """Position in an asset."""
    asset: Any  # BaseAsset
    quantity: float  # Positive for long, negative for short
    entry_price: float


class OptionsStrategy:
    """
    Base class for options strategies.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize options strategy.

        Args:
            name: Strategy name
            description: Strategy description
        """
        self.name = name
        self.description = description
        self.positions: List[Position] = []

    def add_position(self, asset: Any, quantity: float, entry_price: float) -> None:
        """Add a position to the strategy."""
        self.positions.append(Position(asset, quantity, entry_price))

    def calculate_value(self, prices: Dict[str, float]) -> float:
        """
        Calculate current strategy value.

        Args:
            prices: Dictionary of symbol -> current price

        Returns:
            Total strategy value
        """
        total_value = 0.0

        for pos in self.positions:
            symbol = pos.asset.symbol
            current_price = prices.get(symbol, pos.entry_price)
            value = pos.asset.calculate_value(pos.quantity, current_price)
            total_value += value

        return total_value

    def calculate_pnl(self, prices: Dict[str, float]) -> float:
        """
        Calculate current P&L.

        Args:
            prices: Dictionary of symbol -> current price

        Returns:
            Total P&L
        """
        current_value = self.calculate_value(prices)

        # Calculate initial value
        initial_value = 0.0
        for pos in self.positions:
            value = pos.asset.calculate_value(pos.quantity, pos.entry_price)
            initial_value += value

        return current_value - initial_value

    def calculate_greeks(self, underlying_price: float, volatility: float) -> Optional[Greeks]:
        """
        Calculate aggregate Greeks for strategy.

        Args:
            underlying_price: Current underlying price
            volatility: Implied volatility

        Returns:
            Aggregate Greeks or None
        """
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0
        total_rho = 0.0

        for pos in self.positions:
            if isinstance(pos.asset, OptionAsset):
                greeks = pos.asset.calculate_greeks(underlying_price, volatility)
                total_delta += greeks.delta * pos.quantity
                total_gamma += greeks.gamma * pos.quantity
                total_theta += greeks.theta * pos.quantity
                total_vega += greeks.vega * pos.quantity
                total_rho += greeks.rho * pos.quantity
            elif isinstance(pos.asset, EquityAsset):
                # Stock has delta of 1
                total_delta += pos.quantity

        return Greeks(
            delta=total_delta,
            gamma=total_gamma,
            theta=total_theta,
            vega=total_vega,
            rho=total_rho
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "positions": [
                {
                    "asset": pos.asset.symbol,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price
                }
                for pos in self.positions
            ]
        }


class CoveredCall(OptionsStrategy):
    """
    Covered Call: Long stock + short call.

    Generate income by selling call against stock position.
    """

    def __init__(
        self,
        stock: EquityAsset,
        call: OptionAsset,
        stock_quantity: float,
        stock_price: float,
        call_price: float
    ):
        """
        Create covered call strategy.

        Args:
            stock: Stock asset
            call: Call option
            stock_quantity: Number of shares (must be positive)
            stock_price: Stock entry price
            call_price: Call premium received
        """
        super().__init__(
            name="Covered Call",
            description=f"Long {stock_quantity} {stock.symbol} + Short {stock_quantity//100} {call.symbol}"
        )

        # Long stock
        self.add_position(stock, stock_quantity, stock_price)

        # Short call (one contract per 100 shares)
        call_contracts = stock_quantity // call.contract_size
        self.add_position(call, -call_contracts, call_price)

        logger.info(f"Covered call created: {stock_quantity} {stock.symbol} @ ${stock_price}, "
                   f"{call_contracts} {call.symbol} @ ${call_price}")


class ProtectivePut(OptionsStrategy):
    """
    Protective Put: Long stock + long put.

    Protect downside by buying put.
    """

    def __init__(
        self,
        stock: EquityAsset,
        put: OptionAsset,
        stock_quantity: float,
        stock_price: float,
        put_price: float
    ):
        """
        Create protective put strategy.

        Args:
            stock: Stock asset
            put: Put option
            stock_quantity: Number of shares
            stock_price: Stock entry price
            put_price: Put premium paid
        """
        super().__init__(
            name="Protective Put",
            description=f"Long {stock_quantity} {stock.symbol} + Long {stock_quantity//100} {put.symbol}"
        )

        # Long stock
        self.add_position(stock, stock_quantity, stock_price)

        # Long put
        put_contracts = stock_quantity // put.contract_size
        self.add_position(put, put_contracts, put_price)

        logger.info(f"Protective put created: {stock_quantity} {stock.symbol} @ ${stock_price}, "
                   f"{put_contracts} {put.symbol} @ ${put_price}")


class VerticalSpread(OptionsStrategy):
    """
    Vertical Spread: Buy one option, sell another at different strike.

    Can be bullish (call spread) or bearish (put spread).
    """

    def __init__(
        self,
        long_option: OptionAsset,
        short_option: OptionAsset,
        contracts: int,
        long_price: float,
        short_price: float
    ):
        """
        Create vertical spread.

        Args:
            long_option: Option to buy
            short_option: Option to sell
            contracts: Number of contracts
            long_price: Price paid for long option
            short_price: Price received for short option
        """
        spread_type = "Call" if long_option.option_type == OptionType.CALL else "Put"
        direction = "Bull" if long_option.strike < short_option.strike else "Bear"

        super().__init__(
            name=f"{direction} {spread_type} Spread",
            description=f"Long {contracts} {long_option.symbol} + Short {contracts} {short_option.symbol}"
        )

        self.add_position(long_option, contracts, long_price)
        self.add_position(short_option, -contracts, short_price)

        net_debit = (long_price - short_price) * contracts * long_option.contract_size
        logger.info(f"Vertical spread created for net debit of ${net_debit:.2f}")


class IronCondor(OptionsStrategy):
    """
    Iron Condor: Sell OTM call + put spread.

    Profit from low volatility within a range.
    """

    def __init__(
        self,
        put_spread_long: OptionAsset,
        put_spread_short: OptionAsset,
        call_spread_short: OptionAsset,
        call_spread_long: OptionAsset,
        contracts: int,
        prices: Dict[str, float]
    ):
        """
        Create iron condor.

        Args:
            put_spread_long: Long put (lower strike)
            put_spread_short: Short put (higher strike)
            call_spread_short: Short call (lower strike)
            call_spread_long: Long call (higher strike)
            contracts: Number of contracts
            prices: Dictionary of option symbol -> price
        """
        super().__init__(
            name="Iron Condor",
            description="Sell OTM put spread + OTM call spread"
        )

        # Put spread (bearish)
        self.add_position(put_spread_long, contracts, prices[put_spread_long.symbol])
        self.add_position(put_spread_short, -contracts, prices[put_spread_short.symbol])

        # Call spread (bullish)
        self.add_position(call_spread_short, -contracts, prices[call_spread_short.symbol])
        self.add_position(call_spread_long, contracts, prices[call_spread_long.symbol])

        logger.info("Iron condor created")


class Straddle(OptionsStrategy):
    """
    Straddle: Long call + long put at same strike.

    Profit from large move in either direction.
    """

    def __init__(
        self,
        call: OptionAsset,
        put: OptionAsset,
        contracts: int,
        call_price: float,
        put_price: float
    ):
        """
        Create straddle.

        Args:
            call: Call option
            put: Put option
            contracts: Number of contracts
            call_price: Call price
            put_price: Put price
        """
        super().__init__(
            name="Long Straddle",
            description=f"Long {contracts} {call.symbol} + Long {contracts} {put.symbol}"
        )

        self.add_position(call, contracts, call_price)
        self.add_position(put, contracts, put_price)

        total_cost = (call_price + put_price) * contracts * call.contract_size
        logger.info(f"Straddle created for total cost of ${total_cost:.2f}")


class Strangle(OptionsStrategy):
    """
    Strangle: Long OTM call + long OTM put.

    Similar to straddle but cheaper (requires bigger move).
    """

    def __init__(
        self,
        call: OptionAsset,
        put: OptionAsset,
        contracts: int,
        call_price: float,
        put_price: float
    ):
        """
        Create strangle.

        Args:
            call: OTM call option
            put: OTM put option
            contracts: Number of contracts
            call_price: Call price
            put_price: Put price
        """
        super().__init__(
            name="Long Strangle",
            description=f"Long {contracts} {call.symbol} + Long {contracts} {put.symbol}"
        )

        self.add_position(call, contracts, call_price)
        self.add_position(put, contracts, put_price)

        total_cost = (call_price + put_price) * contracts * call.contract_size
        logger.info(f"Strangle created for total cost of ${total_cost:.2f}")
