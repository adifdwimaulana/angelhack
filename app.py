# app.py
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from openai import OpenAI
from pymongo import MongoClient, DESCENDING
from bson.regex import Regex
import os

app = Flask(__name__)

load_dotenv()

# Set your OpenAI API key here
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# Mongo Config
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["angelhack"]
products_collection = db["product"]

def extract_parameters(messages):
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=256,
        messages=messages
    )

    # Still not working, do here
    message = response.choices[0].message
    return message

@app.route('/order/plan', methods=['POST'])
def plan_order():
    messages = request.json.get('messages', '')
    extracted_params = extract_parameters(messages)

    # Example: Let's assume the extracted parameters are in the form of a dictionary-like string
    # Convert extracted parameters string to dictionary
    extracted_params_dict = eval(extracted_params)

    # filtered_data = [item for item in data if all(item.get(k) == v for k, v in extracted_params_dict.items())]
    # return jsonify(filtered_data)

    print(extracted_params_dict)
    return 'Filter'

@app.route('/suggestion', methods=['GET'])
def get_suggestion():
    prompt = request.json.get('prompt', '')
    extracted_params = extract_parameters(prompt)

    return 'Suggestion'

# Test Read
# @app.route('/products', methods=['GET'])
# def call_products():
#     params = {}
#     params['merchant_area'] = request.args.get('merchant_area')
#     params['merchant_name'] = request.args.get('merchant_name')
#     params['min_price'] = request.args.get('min_price')
#     params['max_price'] = request.args.get('max_price')
#     params['category'] = request.args.getlist('category')
#     params['product_name'] = request.args.get('product_name')
#     params['description'] = request.args.get('description')
#     params['product'] = request.args.get('product')

#     return get_products(params)

def get_products(params = {}):
    query = {}

    merchant_area = params['merchant_area']
    if merchant_area:
        query['merchant_area'] = {'$regex': merchant_area, '$options': 'i'}

    merchant_name = params['merchant_name']
    if merchant_name:
        query['merchant_name'] = {'$regex': merchant_name, '$options': 'i'}

    min_price = params['min_price']
    max_price = params['max_price']
    if min_price and max_price:
        query['price'] = {'$gte': int(min_price), '$lte': int(max_price)}
    elif min_price:
        query['price'] = {'$gte': int(min_price)}
    elif max_price:
        query['price'] = {'$lte': int(max_price)}

    category = params['category']
    if category:
        query['category'] = {'$in': category}

    product_name = params['product_name']
    if product_name:
        query['product'] = {'$regex': product_name, '$options': 'i'}

    description = params['description']
    if description:
        query['description'] = {'$regex': description, '$options': 'i'}

    products = products_collection.find(query).limit(50).sort('rating', DESCENDING)
    result = []
    for product in products:
        product['_id'] = str(product['_id'])  # Convert ObjectId to string
        result.append(product)

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
