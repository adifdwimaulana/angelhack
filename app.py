# app.py
import os
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from openai import OpenAI
from pymongo import MongoClient, DESCENDING
from bson.regex import Regex
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

app = Flask(__name__)

# Set your OpenAI API key here
llm = ChatOpenAI(model="gpt-4o")

# Mongo Config
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["angelhack"]
products_collection = db["product"]

sessionChat: dict[str, list] = {}
sessionChatCounter: dict[str, int] = {}


@app.route('/chat', methods=['POST'])
def create_chat_session():
    session_id = str(uuid.uuid4())
    sessionChat[session_id] = [
        SystemMessage('You are assistant to help customer choose the food they want to eat and avoid indecisiveness. '
                      'Help gather what kind of food they want to eat.')
    ]

    sessionChatCounter[session_id] = 0
    return jsonify({'session_id': session_id})


def serialize_session_chat(session_id):
    dictionary = []
    for message in sessionChat[session_id]:
        if message.type == 'system':
            continue  # Skip system messages
        dictionary.append({
            'type': message.type,
            'content': message.content
        })

    return dictionary


def get_suggestions(history):
    chatTemplate = [
        SystemMessage('Generate 3 very brief follow-up questions that the user would likely ask next.'
                      'Enclose the follow-up questions in double angle brackets. Example:'
                      '<<I want something spicy>>',
                      '<<Is there something cheaper>>',
                      'Do no repeat questions that have already been asked.'
                      'Make sure the last question ends with ">>'
                      ),
        HumanMessage(jsonify(history))
    ]

    response = llm.invoke(chatTemplate)
    return response

# Add tools for querying the data and order a product
@app.route('/chat/<session_id>', methods=['POST'])
def chat(session_id):
    message = request.json.get('message', '')
    if session_id not in sessionChat:
        return jsonify({'error': 'Session not found'})
    if message == '':
        return jsonify({'error': 'Message cannot be empty'})

    sessionChat[session_id].append(HumanMessage(message))

    response = llm.invoke(sessionChat[session_id])

    sessionChat[session_id].append(response)

    # Get suggestions
    serialized_chat = serialize_session_chat(session_id)

    return jsonify({'response': response.content})


@app.route('/chat/<session_id>', methods=['GET'])
def get_chat(session_id):
    if session_id not in sessionChat:
        return jsonify({'error': 'Session not found'})
    dictionary = []
    for message in sessionChat[session_id]:
        if message.type == 'system':
            continue  # Skip system messages
        dictionary.append({
            'type': message.type,
            'content': message.content
        })

    return jsonify(dictionary)


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

def get_products(params={}):
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
    app.run(debug=True, port=int(os.getenv('PORT', 8000)))
