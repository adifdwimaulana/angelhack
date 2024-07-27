# app.py
import os
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

# Set your OpenAI API key here
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

sessionChat: dict[str, list] = {}


@app.route('/chat', methods=['POST'])
def create_chat_session():
    session_id = uuid.uuid4().hex
    sessionChat[session_id] = [
        {
            'role': 'system',
            'content': 'You are assistant to help customer choose the food they want to eat and avoid indecisiveness.'
        }
    ]
    return jsonify({'session_id': session_id})


@app.route('/chat/<session_id>', methods=['POST'])
def chat(session_id):
    message = request.json.get('message', '')
    if session_id not in sessionChat:
        return jsonify({'error': 'Session not found'})
    if message == '':
        return jsonify({'error': 'Message cannot be empty'})

    sessionChat[session_id].append({
        'role': 'human',
        'content': message
    })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=sessionChat[session_id],
        temperature=0.6,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    sessionChat[session_id].append({
        'role': 'assistant',
        'content': response.choices[0].message.content
    })

    return jsonify({'response': response.choices[0].message.content})


@app.route('/chat/<session_id>', methods=['GET'])
def get_chat(session_id):
    if session_id not in sessionChat:
        return jsonify({'error': 'Session not found'})
    return jsonify(sessionChat[session_id])


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
