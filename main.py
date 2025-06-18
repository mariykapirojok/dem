import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class DecorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Учёт продукции - Наш декор")
        self.geometry("1200x700")
        
        # Настройка стиля
        self.style = ttk.Style()
        self.style.configure("Treeview", font=('Arial', 10), rowheight=25)
        self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        # Главный контейнер
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Таблица
        self.tree = ttk.Treeview(main_frame, 
                               columns=("id", "name", "article", "price", "width"),
                               show="headings")
        
        # Настройка колонок
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Название продукции")
        self.tree.heading("article", text="Артикул")
        self.tree.heading("price", text="Цена (руб)")
        self.tree.heading("width", text="Ширина (м)")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=400)
        self.tree.column("article", width=150, anchor=tk.CENTER)
        self.tree.column("price", width=150, anchor=tk.CENTER)
        self.tree.column("width", width=100, anchor=tk.CENTER)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Обновить", command=self.load_products).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Добавить", command=self.open_add_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Редактировать", command=self.open_edit_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить", command=self.delete_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Материалы", command=self.show_materials).pack(side=tk.LEFT, padx=5)

    def load_products(self):
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            conn = sqlite3.connect('decor.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT product_id, product_name, article, 
                       min_partner_price, roll_width 
                FROM products
                ORDER BY product_name
            """)
            
            for row in cursor.fetchall():
                self.tree.insert("", tk.END, values=(
                    row[0],  # ID
                    row[1],  # Название
                    row[2],  # Артикул
                    f"{row[3]:.2f}" if row[3] else "0.00",  # Цена
                    f"{row[4]:.2f}" if row[4] else "0.00"   # Ширина
                ))
                
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{str(e)}")

    def open_add_window(self):
        self.open_product_window()

    def open_edit_window(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Ошибка", "Выберите продукт для редактирования")
            return
        product_id = self.tree.item(selected_item)["values"][0]
        self.open_product_window(product_id)

    def open_product_window(self, product_id=None):
        add_window = tk.Toplevel(self)
        add_window.title("Добавить продукт" if product_id is None else "Редактировать продукт")
        add_window.geometry("500x400")

        # Поля формы
        ttk.Label(add_window, text="Тип продукта:").pack(pady=5)
        product_type_combobox = ttk.Combobox(add_window, values=self.get_product_types())
        product_type_combobox.pack(pady=5)

        ttk.Label(add_window, text="Название:").pack(pady=5)
        name_entry = ttk.Entry(add_window)
        name_entry.pack(pady=5)

        ttk.Label(add_window, text="Артикул:").pack(pady=5)
        article_entry = ttk.Entry(add_window)
        article_entry.pack(pady=5)

        ttk.Label(add_window, text="Цена (руб):").pack(pady=5)
        price_entry = ttk.Entry(add_window)
        price_entry.pack(pady=5)

        ttk.Label(add_window, text="Ширина (м):").pack(pady=5)
        width_entry = ttk.Entry(add_window)
        width_entry.pack(pady=5)

        # Если редактирование - загружаем данные
        if product_id is not None:
            product_data = self.get_product_by_id(product_id)
            if product_data:
                name_entry.insert(0, product_data["product_name"])
                article_entry.insert(0, product_data["article"])
                price_entry.insert(0, str(product_data["min_partner_price"]))
                width_entry.insert(0, str(product_data["roll_width"]))
                product_type_combobox.set(product_data["type_name"])

        # Кнопка сохранения
        ttk.Button(
            add_window,
            text="Сохранить",
            command=lambda: self.save_product(
                product_id,
                product_type_combobox.get(),
                name_entry.get(),
                article_entry.get(),
                price_entry.get(),
                width_entry.get(),
            ),
        ).pack(pady=10)

    def get_product_types(self):
        conn = sqlite3.connect('decor.db')
        cursor = conn.cursor()
        cursor.execute("SELECT type_name FROM product_types")
        types = [row[0] for row in cursor.fetchall()]
        conn.close()
        return types

    def get_product_by_id(self, product_id):
        conn = sqlite3.connect('decor.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, pt.type_name 
            FROM products p
            JOIN product_types pt ON p.product_type_id = pt.product_type_id
            WHERE p.product_id = ?
        """, (product_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "product_id": row[0],
                "product_type_id": row[1],
                "product_name": row[2],
                "article": row[3],
                "min_partner_price": row[4],
                "roll_width": row[5],
                "type_name": row[6],
            }
        return None

    def save_product(self, product_id, product_type, name, article, price, width):
        try:
            conn = sqlite3.connect('decor.db')
            cursor = conn.cursor()
            
            # Получаем ID типа продукта
            cursor.execute("SELECT product_type_id FROM product_types WHERE type_name = ?", (product_type,))
            type_id = cursor.fetchone()[0]
            
            # Проверяем, что цена и ширина - числа
            price = float(price)
            width = float(width)
            if price < 0 or width < 0:
                raise ValueError("Цена и ширина не могут быть отрицательными")
            
            if product_id is None:  # Добавление
                cursor.execute("""
                    INSERT INTO products (product_type_id, product_name, article, min_partner_price, roll_width)
                    VALUES (?, ?, ?, ?, ?)
                """, (type_id, name, article, price, width))
            else:  # Редактирование
                cursor.execute("""
                    UPDATE products 
                    SET product_type_id=?, product_name=?, article=?, min_partner_price=?, roll_width=?
                    WHERE product_id=?
                """, (type_id, name, article, price, width, product_id))
            
            conn.commit()
            conn.close()
            self.load_products()  # Обновляем таблицу
            messagebox.showinfo("Успех", "Продукт успешно сохранён")
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректные данные: {e}")
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось сохранить продукт: {e}")

    def delete_product(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Ошибка", "Выберите продукт для удаления")
            return
        
        product_id = self.tree.item(selected_item)["values"][0]
        if messagebox.askyesno("Подтверждение", "Удалить выбранный продукт?"):
            try:
                conn = sqlite3.connect('decor.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
                conn.commit()
                conn.close()
                self.load_products()
                messagebox.showinfo("Успех", "Продукт успешно удалён")
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить продукт: {e}")

    def show_materials(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Ошибка", "Выберите продукт")
            return
        
        product_id = self.tree.item(selected_item)["values"][0]
        
        materials_window = tk.Toplevel(self)
        materials_window.title("Материалы продукта")
        materials_window.geometry("800x400")
        
        # Таблица материалов
        tree = ttk.Treeview(materials_window, columns=("material", "quantity"), show="headings")
        tree.heading("material", text="Материал")
        tree.heading("quantity", text="Количество")
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Загрузка данных
        try:
            conn = sqlite3.connect('decor.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.material_name, pm.required_quantity
                FROM product_materials pm
                JOIN materials m ON pm.material_id = m.material_id
                WHERE pm.product_id = ?
            """, (product_id,))
            
            for row in cursor.fetchall():
                tree.insert("", tk.END, values=(row[0], row[1]))
            
            conn.close()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить материалы: {e}")

    def calculate_product_cost(self, product_id):
        try:
            conn = sqlite3.connect('decor.db')
            cursor = conn.cursor()
            
            # Получаем все материалы продукта
            cursor.execute("""
                SELECT m.material_name, m.unit_price, pm.required_quantity
                FROM product_materials pm
                JOIN materials m ON pm.material_id = m.material_id
                WHERE pm.product_id = ?
            """, (product_id,))
            
            total_cost = 0.0
            for material_name, unit_price, quantity in cursor.fetchall():
                total_cost += unit_price * quantity
            
            conn.close()
            return round(total_cost, 2)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось рассчитать стоимость: {e}")
            return 0.0

if __name__ == "__main__":
    app = DecorApp()
    app.mainloop()