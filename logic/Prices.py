def Calculate_Prices(product_data, profit_option='A'):
    """
    Calculate fair prices for products given profit options.
    
    Args:
        product_data: list of tuples (min_price, max_price, purchase_price, name, quantity)
        profit_option: one of 'A', 'B', or 'C' defining target profit margins
        
    Returns:
        List of assigned prices (floats), same order as input products.
    """
    profit_map = {'A': 0.08, 'B': 0.18, 'C': 0.30}
    if profit_option not in profit_map:
        raise ValueError("Profit option must be 'A', 'B', or 'C'")
    target_profit = profit_map[profit_option]
    allowed_lower_bound = target_profit - 0.015

    products = []
    for tup in product_data:
        min_price, max_price, purchase_price, name, qty = tup
        products.append({
            'name': name,
            'purchase_price': purchase_price,
            'min_price': min_price,
            'max_price': max_price,
            'quantity': qty,
        })

    for p in products:
        p['fixed'] = (p['min_price'] == p['max_price'])

    fixed_products = [p for p in products if p['fixed']]
    variable_products = [p for p in products if not p['fixed']]

    total_purchase = sum(p['purchase_price'] * p['quantity'] for p in products)
    fixed_total_sell = sum(p['min_price'] * p['quantity'] for p in fixed_products)
    target_total_sell = total_purchase * (1 + target_profit)

    for p in variable_products:
        p['min_profit_pct'] = ((p['min_price'] - p['purchase_price']) / p['purchase_price']) * 100
        p['max_profit_pct'] = ((p['max_price'] - p['purchase_price']) / p['purchase_price']) * 100

    if variable_products:
        low = max(min(p['min_profit_pct'] for p in variable_products), -100)
        high = min(max(p['max_profit_pct'] for p in variable_products), 100)
    else:
        low = high = 0

    best_prices = None
    best_achieved = None

    for _ in range(30):
        mid = (low + high) / 2
        curr_prices = []
        for p in variable_products:
            lower = max(p['min_profit_pct'], mid - 3)
            upper = min(p['max_profit_pct'], mid + 3)
            use_pct = max(lower, min(upper, mid))
            price = p['purchase_price'] * (1 + use_pct / 100)
            price = min(max(price, p['min_price']), p['max_price'])
            curr_prices.append(price)

        curr_total = fixed_total_sell + sum(price * p['quantity'] for price, p in zip(curr_prices, variable_products))
        achieved_profit = (curr_total - total_purchase) / total_purchase

        if achieved_profit > target_profit:
            high = mid
        else:
            low = mid
            best_prices = curr_prices[:]
            best_achieved = achieved_profit

    if best_achieved is None or best_achieved < allowed_lower_bound:
        return [float(p['min_price']) for p in products]

    idx = 0
    prices_out = []
    for p in products:
        if not p['fixed']:
            prices_out.append(round(best_prices[idx], 2))
            idx += 1
        else:
            prices_out.append(float(p['min_price']))

    return prices_out
