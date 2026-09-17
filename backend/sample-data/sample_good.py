"""A small, well-structured utility module used as a 'good quality' demo sample."""
from dataclasses import dataclass


@dataclass
class Order:
    amount: float
    tax_rate: float
    discount: float = 0.0


def calculate_total(order: Order) -> float:
    """Return the final total for an order after discount and tax."""
    discounted = order.amount - order.discount
    return round(discounted * (1 + order.tax_rate), 2)


def apply_discount_code(order: Order, discount_amount: float) -> Order:
    """Return a new Order with the discount applied."""
    return Order(amount=order.amount, tax_rate=order.tax_rate, discount=discount_amount)


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format a numeric amount as a currency string."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency, "")
    return f"{symbol}{amount:.2f}"
