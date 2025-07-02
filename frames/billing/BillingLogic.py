# BillingLogic.py

def calculate_subtotal(cart):
    """Returns subtotal for a list of cart items."""
    return sum(item.get('total', 0) or 0 for item in cart)

def apply_discount(subtotal, discount, discount_type):
    """Returns (discount_amount, grand_total) after applying discount."""
    if discount_type == "%":
        discount_amount = subtotal * float(discount) / 100.0
    else:
        discount_amount = float(discount)
    grand_total = max(subtotal - discount_amount, 0.0)
    return discount_amount, grand_total

def validate_payment(grand_total, payment_breakdown):
    """Checks if payments add up and returns (valid, error_msg)."""
    paid_sum = 0.0
    for amt in payment_breakdown.values():
        try:
            paid_sum += float(amt)
        except Exception:
            pass
    if abs(paid_sum - grand_total) > 0.01:
        return False, f"Payment sum ({paid_sum}) does not match total ({grand_total})"
    return True, ""

def add_to_cart(cart, product):
    """Appends a product dict to cart."""
    cart.append(product)
    return cart

def remove_from_cart(cart, idx):
    """Removes item at idx from cart."""
    if 0 <= idx < len(cart):
        cart.pop(idx)
    return cart

def update_cart_item(cart, idx, new_item):
    """Updates a cart item in place."""
    if 0 <= idx < len(cart):
        cart[idx] = new_item
    return cart
