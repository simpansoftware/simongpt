from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Define the URL of the Ollama API
OLLAMA_API_URL = 'http://localhost:11434/api/chat'

@app.route('/api/chat', methods=['POST'])
def chat_proxy():
    try:
        # Get the JSON data from the incoming request
        data = request.get_json()

        # Log the incoming request data for debugging
        print(f"Received request data: {json.dumps(data, indent=2)}")

        # Prepare the data to send to the Ollama API
        # Ollama expects a list of messages (including user and AI)
        model = data.get('model', 'llama3.2')  # Default to 'llama3.2' if no model is specified
        data_to_send = {
            'model': model,  # Use the dynamic model selected by the user
            'messages': data.get('messages', [])
        }

        # Log the data being sent to Ollama
        print(f"Sending data to Ollama: {json.dumps(data_to_send, indent=2)}")

        # Forward the request to Ollama
        response = requests.post(OLLAMA_API_URL, json=data_to_send, stream=True)

        # Check if the response from Ollama is OK (status 200)
        if response.status_code == 200:
            # Initialize a variable to accumulate the streamed response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        # Decode and parse each line from the streamed response
                        chunk = line.decode('utf-8')
                        json_data = json.loads(chunk)

                        # Accumulate the message content from Ollama
                        if 'message' in json_data and 'content' in json_data['message']:
                            full_response += json_data['message']['content']

                        # Break when the 'done' flag is set
                        if json_data.get('done', False):
                            break

                    except json.JSONDecodeError as e:
                        print(f"JSONDecodeError: {str(e)}")

            # Return the full response after streaming is complete
            return jsonify({"response": full_response}), 200

        else:
            # If the response from Ollama is not OK, return an error message
            print(f"Error from Ollama API: {response.status_code} - {response.text}")
            return jsonify({"error": "Failed to communicate with Ollama API", "details": response.text}), 500

    except Exception as e:
        # Catch and return any exceptions that occur
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    # Run the Flask server on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
