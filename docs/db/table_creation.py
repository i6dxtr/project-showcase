import sqlite3

# Creating connection to database
connection = sqlite3.connect('products.db')
connection.execute("PRAGMA foreign_keys = ON")

# Table Creation for clarity
connection.execute(''' CREATE TABLE products
         (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT NOT NULL,
         cost REAL NOT NULL);
         ''')

connection.execute(''' CREATE TABLE nutritional_info 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    calories INTEGER NOT NULL,
                    total_fat TEXT NOT NULL,
                    cholesterol TEXT NOT NULL,
                    sodium TEXT NOT NULL,
                    total_carbs TEXT NOT NULL,
                    fiber TEXT NOT NULL,
                    sugar TEXT NOT NULL,
                    protein TEXT NOT NULL,
                    allergy TEXT NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products(id));
                   ''')

connection.commit()
connection.close()
