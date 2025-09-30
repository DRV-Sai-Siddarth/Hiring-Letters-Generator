from flask import Flask, request, jsonify
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("❌ GROQ_API_KEY is not set in the environment!")

chat = ChatGroq(api_key=groq_api_key, model_name="llama3-8b-8192")

prompt_template = ChatPromptTemplate.from_template(
    """
    Write a formal hiring letter for a candidate with the following details:
    - Candidate Name: {name}
    - Role: {role}
    - Date of Joining: {date}
    - Reason for Hiring: {reason}
    - Responsibilities: {responsibilities}

    From:
    - Sender Name: {sender_name}
    - Sender Position: {sender_position}
    - Company Name: {company_name}

    The tone should be professional, warm, and concise.
    """
)

required_fields = {
    "name", "role", "date", "reason", "responsibilities",
    "sender_name", "company_name", "sender_position"
}

@app.route("/generate", methods=["POST"])
def generate_letter():
    data = request.json

    # Check for missing required fields
    missing = [field for field in required_fields if field not in data]
    if missing:
        error_msg = f"Missing required fields: {', '.join(missing)}"
        logging.warning(error_msg)
        return jsonify({"error": error_msg}), 400

    try:
        # Format prompt messages with data from request
        messages = prompt_template.format_messages(**data)

        # Invoke the Groq Chat model
        response = chat.invoke(messages)

        letter_text = response.content.strip()
        logging.info(f"Generated letter for: {data.get('name')}")

        return jsonify({"text": letter_text})
    except Exception as e:
        logging.error(f"Error generating letter: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
