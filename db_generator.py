import pandas as pd
import uuid
import random
from pymongo import MongoClient
import re

# Load the dataset from the CSV file
file_path = './grabfood_dataset.csv'  # Update with the correct path to your CSV file
df = pd.read_csv(file_path)

merchant_map = {}

# Function to generate random UUID
def generate_uuid():
    return str(uuid.uuid4())

# Function to generate random rating between 3.0 and 5.0 with a step of 0.1
def generate_random_rating():
    return round(random.uniform(3.0, 5.0), 1)

# Function to generate random review count between 10 and 2000
def generate_random_review_count():
    return random.randint(10, 2000)

def generate_merchant_uuid(merchant_name):
    if merchant_name in merchant_map:
        return merchant_map[merchant_name]
    
    merchant_id = str(uuid.uuid4())
    merchant_map[merchant_name] = merchant_id
    return merchant_id


# Values to check in the category column
directional_values = ['Barat', 'Timur', 'Tengah', 'Utara', 'Selatan', 'Pusat']

# Function to update merchant_area and category columns
def update_merchant_area_category(row):
    category_parts = re.split(r'[\/&]', row['category'])  # Split by / and &
    updated_category_parts = []
    updated_area = row['merchant_area']
    
    for part in category_parts:
        part_stripped = part.strip().capitalize()
        if part_stripped in directional_values:
            updated_area = f"{updated_area} {part_stripped}".strip()
        else:
            updated_category_parts.append(part.strip().lower())

    row['merchant_area'] = ' '.join(word.capitalize() for word in updated_area.split())
    row['category'] = updated_category_parts
    
    return row

# Apply the update function to each row
df = df.apply(update_merchant_area_category, axis=1)
# Apply the merchant UUID generation function to each row
df['merchant_id'] = df['merchant_name'].apply(generate_merchant_uuid)
# Apply the functions to the dataset
df['product_id'] = [generate_uuid() for _ in range(len(df))]
df['rating'] = [generate_random_rating() for _ in range(len(df))]
df['review_count'] = [generate_random_review_count() for _ in range(len(df))]
df['discount_price'] = 0
df['is_discount'] = False

# Display the enriched DataFrame
print(df)

# Save to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB connection string if needed
db = client['angelhack']  # Update with your database name
collection = db['product']  # Update with your collection name

# Convert DataFrame to dictionary and insert into MongoDB
collection.insert_many(df.to_dict('records'))

print("Data saved to MongoDB.")
