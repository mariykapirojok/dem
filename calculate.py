import sqlite3
from typing import Tuple

def calculate_material_requirement(
    product_type_id: int,
    material_id: int,
    amount: int,
    param1: float,
    param2: float,
    stock_quantity: float = 0.0
) -> Tuple[int, str]:
    """Рассчитывает необходимое количество материала с учётом брака и склада.
    
    Аргументы:
        product_type_id: идентификатор типа продукции
        material_id: идентификатор материала
        amount: количество продукции
        param1: первый параметр (ширина рулона)
        param2: второй параметр (допустимый коэффициент)
        stock_quantity: материал на складе
    
    Возвращает:
        Кортеж (количество материала, сообщение)
    """
    try:
        if any(x <= 0 for x in [amount, param1, param2]) or stock_quantity < 0:
            return -1, "Ошибка: Параметры должны быть положительными."

        conn = sqlite3.connect("decor.db")
        cursor = conn.cursor()

        # Получение коэффициента типа продукции
        cursor.execute("SELECT coefficient FROM Product_types_import WHERE product_type_id = ?", (product_type_id,))
        coeff = cursor.fetchone()
        if not coeff:
            return -1, "Ошибка: Тип продукции не найден."

        # Получение процента брака материала
        cursor.execute("""
            SELECT mt.defect_rate FROM Materials_import m
            JOIN material_types mt ON m.material_type = mt.type_name
            WHERE m.material_id = ?
        """, (material_id,))
        defect_rate = cursor.fetchone()
        if not defect_rate:
            return -1, "Ошибка: Материал не найден."
        defect_rate = defect_rate[0]

        base_consumption = param1 * param2 * coeff[0]
        defect_adjustment = 1 + defect_rate
        total_needed = base_consumption * amount * defect_adjustment
        net_needed = max(0, total_needed - stock_quantity)

        return int(net_needed), "Расчёт выполнен успешно."
    except sqlite3.Error as e:
        return -1, f"Ошибка базы данных: {str(e)}"
    finally:
        conn.close()

def calculate_product_cost(product_id: int, quantity: int) -> Tuple[float, str]:
    """Рассчитывает стоимость продукции на основе материалов.
    
    Аргументы:
        product_id: идентификатор продукции
        quantity: количество единиц
    
    Возвращает:
        Кортеж (стоимость, сообщение)
    """
    try:
        if quantity <= 0:
            return -1.0, "Ошибка: Количество должно быть положительным."

        conn = sqlite3.connect("decor.db")
        cursor = conn.cursor()

        # Получение минимальной стоимости и ширины
        cursor.execute("""
            SELECT min_partner_price, roll_width FROM Products_import WHERE product_id = ?
        """, (product_id,))
        product = cursor.fetchone()
        if not product:
            return -1.0, "Ошибка: Продукт не найден."
        min_price, roll_width = product

        # Расчёт стоимости материалов
        total_material_cost = 0.0
        cursor.execute("""
            SELECT m.unit_price, pm.required_quantity
            FROM product_materials pm
            JOIN Materials_Import m ON pm.material_id = m.material_id
            WHERE pm.product_id = ?
        """, (product_id,))
        materials = cursor.fetchall()
        for unit_price, req_qty in materials:
            material_cost = unit_price * req_qty * quantity
            total_material_cost += material_cost

        # Итоговая стоимость (максимум из минимальной цены и стоимости материалов)
        final_cost = max(min_price * quantity, total_material_cost)
        return round(final_cost, 2), "Стоимость рассчитана успешно."
    except sqlite3.Error as e:
        return -1.0, f"Ошибка базы данных: {str(e)}"
    finally:
        conn.close()