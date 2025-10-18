def calculate_delivery_cost(weight_g: int) -> int:
    """
    Рассчитывает стоимость доставки по весу в граммах.

    :param weight_g: вес товара в граммах
    :return: стоимость доставки в тенге
    """
    base_price = 900  # до 1 кг
    extra_rate = 60  # за каждый кг сверху

    if weight_g <= 1000:
        return base_price
    else:
        extra_weight_g = weight_g - 1000
        # переводим граммы в кг и округляем вверх до целого кг
        extra_kilos = -(-extra_weight_g // 1000)  # эквивалент math.ceil
        return base_price + extra_kilos * extra_rate
