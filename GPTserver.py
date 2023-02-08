from flask import Flask
from flask import jsonify
from flask import request
from revChatGPT.Unofficial import Chatbot

def set_token_available(session_list, token_available):
    for session in session_list:
        token_available[session]=True
    return token_available

def get_session_list(path) -> list:
    ##SESSION
    with open(path, 'r') as f:
      # Read the contents of the file
      contents = f.read()

    # Split the contents into a list of lines
    lines = contents.split('\n')
    return lines

def set_session(token_available) -> str:
    for token in enumerate(token_available):
        if token[0]==False:session=token[1]
    return session

app = Flask(__name__)

session_list=get_session_list('D:/ChatGPT_Flask/session.txt')
chatbot = Chatbot(config={"session_token": session_list[0]}, no_refresh=True)

now_session=session_list[0]
token_available = {}
token_available=set_token_available(session_list, token_available)

def verify_request_data(data: dict) -> bool:
    """
    Verifies that the required fields are present in the data.
    """
    # Required fields: "prompt", "session_token"
    if "prompt" not in data:
        return False
    return True


@app.route("/chat", methods=["POST"])
def chat():
    """
    The main chat endpoint.
    """

    now_session=set_session(token_available)

    data = request.get_json()
    if not verify_request_data(data):
        return jsonify({"error": "Invalid data."}), 400

    # Return rate limit if token_available is false
    if token_available[now_session] is False:
        return jsonify({"error": "Rate limited"}), 429

    token_available[now_session] = False

    try:
        response = chatbot.ask(
            prompt=data["prompt"],
            session_token=now_session,
            parent_id=data.get("parent_id"),
            conversation_id=data.get("conversation_id"),
        )
    except Exception as exc:
        token_available[now_session] = True
        return jsonify({"error": str(exc)}), 500

    response["session_token"] = chatbot.session_token
    token_available[now_session] = True

    return jsonify(response), 200


@app.route("/refresh", methods=["POST"])
def refresh():
    """
    The refresh endpoint.
    """
    data = request.get_json()
    if "session_token" not in data:
        return jsonify({"error": "Invalid data."}), 400

    if data.get("session_token") not in token_available:
        return jsonify({"error": "Invalid token."}), 400

    chatbot.session_token = data["session_token"]
    try:
        chatbot.refresh_session()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"session_token": chatbot.session_token}), 200


def main():
    app.run(host="0.0.0.0" , port=8080)
