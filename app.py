# app.py
import json
import os
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pymongo import MongoClient, DESCENDING

from model.Product import Data, Product
from tools import tool_example_to_messages

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

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert extraction algorithm. "
            "Only extract relevant information from the text. "
            "If you do not know the value of an attribute asked "
            "to extract, return null for the attribute's value.",
        ),
        # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
        MessagesPlaceholder("examples"),  # <-- EXAMPLES!
        # ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
        ("human", "{text}"),
    ]
)

runnable = prompt | llm.with_structured_output(
    schema=Data,
    method="function_calling",
    include_raw=False,
)


def init_prompt_examples():
    examples = [
        (
            "Mike Tyson is so strong",
            Data(product=[]),
        ),
        (
            "Create me a coffee planner for the next 5 days in the morning with price range 30000-70000",
            Data(product=[Product(product_name="Coffee", description="Coffee", min_price=30000, max_price=70000,
                                  category=["drink", "coffee"], merchant_name=None)]),
        ),
        (
            "I want seafood under 100000",
            Data(product=[
                Product(product_name=None, description="Seafood", min_price=None, max_price=100000, category=["food"],
                        merchant_name=None)]),
        ),
        (
            "I want a KFC menu under 100000",
            Data(product=[
                Product(product_name=None, description="Chicken", min_price=None, max_price=100000, category=["food"],
                        merchant_name="KFC")]),
        ),
    ]

    messages = []

    for text, tool_call in examples:
        messages.extend(
            tool_example_to_messages({"input": text, "tool_calls": [tool_call]})
        )

    return messages


def extract_parameters(prompt):
    messages = init_prompt_examples()
    product = runnable.invoke({"text": prompt, "examples": messages})
    return product


### DON'T TOUCH, ITS GOOD (maybe)
language = "Bahasa Indonesia"
cache_bros = {}


def translate_to_language(text):
    if text in cache_bros:
        return cache_bros[text]
    template = [
        SystemMessage('Translate the following text to ' + language + ' translate this don\'t interpret it'),
        HumanMessage(text)
    ]
    response = llm.invoke(template)
    cache_bros[text] = response.content
    return response.content


@app.route('/chat', methods=['POST'])
def create_chat_session():
    session_id = str(uuid.uuid4())

    sessionChat[session_id] = [
        SystemMessage(
            'You are assistant to help customer choose the food they want to eat and avoid indecisiveness. '
            'Help gather what kind of food they want to eat.'
            'Say "Hello what you want to eat" at the beginning of the conversation.'
            'User Language: ' + language
        )
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
        SystemMessage(

            'Generate 3 very brief follow-up questions that the user would likely ask next.'
            'Enclose the follow-up questions in double angle brackets. Example:'
            '<<I want something spicy>>'
            '<<Is there something cheaper>>'
            'Do no repeat questions that have already been asked.'
            'Make sure the last question ends with ">>'
            'User Language: ' + language
        ),
        HumanMessage(json.dumps(history))
    ]

    response = llm.invoke(chatTemplate)
    # Split the response into individual suggestions
    suggestions = response.content.split('<<')
    suggestions = [suggestion.strip() for suggestion in suggestions if suggestion != '']
    suggestions = [suggestion[:-2] for suggestion in suggestions if suggestion[-2:] == '>>']

    return suggestions


# Add tools for querying the data and order a product
@app.route('/chat/<session_id>', methods=['POST'])
def chat(session_id):
    message = request.json.get('message', '')
    if session_id not in sessionChat:
        return jsonify({'error': 'Session not found'})
    if message == '':
        # We don't add empty messages
       pass
    else:
        sessionChat[session_id].append(HumanMessage(message))

    response = llm.invoke(sessionChat[session_id])

    sessionChat[session_id].append(response)

    # Get suggestions
    serialized_chat = serialize_session_chat(session_id)
    suggestions = get_suggestions(serialized_chat)

    return jsonify({
        'response': response.content,
        'suggestions': suggestions
    })


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


### Okay you good

@app.route('/order/plan', methods=['POST'])
def plan_order():
    message = request.json.get('message', '')
    extracted_params = extract_parameters(message)

    if not extracted_params:
        return jsonify({'error': 'Error extracting parameters'}), 500
    
    print(extracted_params.dict())
    
    product_results = query_products(extracted_params.dict())  # Convert Pydantic model to dictionary

    print("products", product_results)

    return jsonify(product_results)


@app.route('/suggestion', methods=['GET'])
def get_suggestion():
    prompt = request.json.get('prompt', '')
    extract_parameters(prompt)

    return 'Suggestion'

def query_products(extracted_params: dict):
    query = {}

    for product in extracted_params["product"]:
        if product['min_price'] is not None:
            query['price'] = {'$gte': product['min_price']}
        if product['max_price'] is not None:
            query.setdefault('price', {}).update({'$lte': product['max_price']})
        # if product['category']:
        #     query['category'] = {'$in': product['category']}
        if product['product_name']:
            query['product'] = {'$regex': product['product_name'], '$options': 'i'}
        # if product['merchant_name']:
        #     query['merchant_name'] = {'$regex': product['merchant_name'], '$options': 'i'}
        # if product['merchant_area']:
        #     query['merchant_area'] = {'$regex': product['merchant_area'], '$options': 'i'}

    try:
        products = products_collection.find(query).limit(10).sort('rating', DESCENDING)
        result = []
        for product in products:
            product['_id'] = str(product['_id'])  # Convert ObjectId to string
            # result.append(Product(**product))  # Create a Product instance
            result.append(product)
        return result
    except Exception as e:
        print(f"Error querying products: {e}")
        return []


if __name__ == '__main__':
    try:
        app.run(debug=os.getenv('DEBUG', 'False') == 'True',
                port=int(os.getenv('PORT', 8000)),
                threaded=False)

    except Exception as e:
        print(f"Error running the server: {e}")
