import sqlite3

# Creating connection to database
connection = sqlite3.connect('products.db')
connection.execute("PRAGMA foreign_keys = ON")

# Inserting data into table

# Peanut Butter
connection.execute('''
INSERT INTO products (name, cost)
VALUES (?, ?)
''', ('Kroger Creamy Peanut Butter', 6.49))

# Peanut Butter Nutrition
connection.execute('''
INSERT INTO nutritional_info (
    product_id,
    calories,
    total_fat,
    cholesterol,
    sodium,
    total_carbs,
    fiber,
    sugar,
    protein,
    allergy
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    1,                   # product_id
    180,                 # calories
    '15g',               # total_fat
    '0mg',               # cholesterol
    '150mg',             # sodium
    '7g',                # total_carbs
    '2g',                # fiber
    '4g',                # sugar
    '7g',                # protein
    'Peanuts'            # allergy
))

# GV Cookies
connection.execute('''
INSERT INTO products (name, cost)
VALUES (?, ?)
''', ('Great Value Twist and Shout Cookies', 3.37))

# GV Cookies Nutrition
connection.execute('''
INSERT INTO nutritional_info (
    product_id,
    calories,
    total_fat,
    cholesterol,
    sodium,
    total_carbs,
    fiber,
    sugar,
    protein,
    allergy
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    2,           # product_id
    160,         # calories
    '7g',        # total_fat
    '0mg',       # cholesterol
    '160mg',     # sodium
    '24g',       # total_carbs
    '1g',        # fiber
    '12g',       # sugar
    '2g',        # protein
    'Wheat and Soy. May contain traces of milk, eggs, almonds, coconut, pecans, and peanuts.'
))

# Morton Kosher Salt
connection.execute('''
INSERT INTO products (name, cost)
VALUES (?, ?)
''', ('Morton Coarse Kosher Salt', 2.12))

# Morton Kosher Salt Nutrition Info
connection.execute('''
INSERT INTO nutritional_info (
    product_id,
    calories,
    total_fat,
    cholesterol,
    sodium,
    total_carbs,
    fiber,
    sugar,
    protein,
    allergy
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    3,           # product_id
    0,           # calories
    '0g',        # total_fat
    '0mg',       # cholesterol
    '480mg',     # sodium
    '0g',        # total_carbs
    '0g',        # fiber
    '0g',        # sugar
    '0g',        # protein
    'None'          # allergy (since you said put 0 if missing)
))

# Kroger Olive Oil
connection.execute('''
INSERT INTO products (name, cost)
VALUES (?, ?)
''', ('Kroger Extra Virgin Olive Oil', 2.12))

# Olive Oil Nutrition
connection.execute('''
INSERT INTO nutritional_info (
    product_id,
    calories,
    total_fat,
    cholesterol,
    sodium,
    total_carbs,
    fiber,
    sugar,
    protein,
    allergy
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    4,           # product_id
    120,         # calories
    '14g',       # total_fat
    '0mg',       # cholesterol
    '0mg',       # sodium
    '0g',        # total_carbs
    '0g',        # fiber
    '0g',        # sugar
    '0g',        # protein
    'None'          # allergy
))

print("All data in product table\n")

# Cursor for selection query
result = connection.execute('''
SELECT products.*, nutritional_info.*
FROM products
JOIN nutritional_info
ON products.id = nutritional_info.product_id
''')

# Display all data in table
for row in result:
    print(row)

connection.commit()
connection.close()