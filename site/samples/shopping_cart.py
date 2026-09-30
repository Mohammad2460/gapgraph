"""A tiny shopping cart, written to be read.

Concepts, in the order they build on each other:
Item -> Cart (holds Items) -> discounts -> checkout total.
"""

from dataclasses import dataclass, field


@dataclass
class Item:
    """One product with a price in rupees. Prices are never negative."""

    name: str
    price: float

    def __post_init__(self) -> None:
        # Validate early so a bad price can never reach the total.
        if self.price < 0:
            raise ValueError("price cannot be negative")


@dataclass
class Cart:
    """A cart stores (item, quantity) pairs and knows how to total them."""

    lines: list[tuple[Item, int]] = field(default_factory=list)

    def add(self, item: Item, quantity: int = 1) -> None:
        """Put `quantity` copies of an item in the cart."""
        if quantity < 1:
            raise ValueError("quantity must be at least 1")
        self.lines.append((item, quantity))

    def subtotal(self) -> float:
        """Sum of price * quantity over every line, before any discount."""
        return sum(item.price * qty for item, qty in self.lines)


def apply_discount(amount: float, percent: float) -> float:
    """Return `amount` reduced by `percent` (0-100)."""
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return amount * (1 - percent / 100)


def checkout(cart: Cart, discount_percent: float = 0) -> float:
    """Final amount to pay: the subtotal, then the discount, rounded to paise."""
    total = apply_discount(cart.subtotal(), discount_percent)
    return round(total, 2)


if __name__ == "__main__":
    cart = Cart()
    cart.add(Item("Notebook", 50.0), 3)
    cart.add(Item("Pen", 10.0), 5)
    print(checkout(cart, discount_percent=10))  # (150 + 50) * 0.9 = 180.0
