# app.py
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from openai import OpenAI
load_dotenv()

app = Flask(__name__)


# Set your OpenAI API key here
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

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

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv('PORT', 8000)))
