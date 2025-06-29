from flask import Flask, request, jsonify, render_template
from textblob import TextBlob
import csv
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    ai_response = ask_granite_model(user_message)
    return jsonify({"reply": ai_response})

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        feedback_text = request.form['feedback']
        sentiment = analyze_sentiment(feedback_text)

        with open('data/feedback.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([feedback_text, sentiment])
        
        return render_template('feedback.html', message="Feedback submitted!", sentiment=sentiment)
    
    return render_template('feedback.html')

@app.route('/dashboard')
def dashboard():
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    
    if os.path.exists('data/feedback.csv'):
        with open('data/feedback.csv', 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    sentiment = row[1]
                    if sentiment in sentiment_counts:
                        sentiment_counts[sentiment] += 1
    
    return render_template('dashboard.html', data=sentiment_counts)

def analyze_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

import requests

def ask_granite_model(prompt):
    url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer qDVqlfhedxgka-jsw3y-Uwjsh0x4RIrwf6nUv-jL8w3W"
    }

    payload = {
        "model_id": "ibm-granite/granite-3.3-2b-instruct",
        "project_id": "54964ddf-77ab-4c70-8e35-f402829f3e83",
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 100
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("results", [{}])[0].get("generated_text", "Sorry, no response.")
    except requests.exceptions.RequestException as e:
        return f"API Error: {str(e)}"

def get_iam_token(api_key):
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception("Failed to get IAM token: " + response.text)

def ask_granite_model(prompt):
    api_key = "qDVqlfhedxgka-jsw3y-Uwjsh0x4RIrwf6nUv-jL8w3W"
    token = get_iam_token(api_key)

    url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2024-05-01"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    cm_lookup = {
    "andhra pradesh": "N. Chandrababu Naidu",
    "uttar pradesh": "Yogi Adityanath",
     "tamil nadu": "M. K. Stalin",
        "maharashtra": "Eknath Shinde",
        "delhi": "Arvind Kejriwal"
}

    if "cm of" in prompt.lower():
        for state in cm_lookup:
            if state in prompt.lower():
                return f"The Chief Minister of {state.title()} is {cm_lookup[state]}."
            

        # Hardcoded developer identity fallback
        lower_prompt = prompt.lower().strip()
    if any(q in lower_prompt for q in ["who made you", "who developed you", "who created you"]):
        return "I was developed by Mohammad Abid as part of the Citizen AI project. 😊"

    # system_prompt = (
    #     "You are Citizen AI, an intelligent assistant helping Indian citizens with government-related queries. "
    #     "Provide accurate, polite, and clear answers in a helpful tone. Only talk about government topics like Aadhar, passport, "
    #     "complaints, elections, documents, and services. Don’t reply to casual or off-topic messages. Do not act like a user."
    # )
#     system_prompt = (
#     "You are Citizen AI — a trusted government helpdesk assistant for Indian citizens.\n"
#     "Your job is to provide helpful, accurate, and simple responses to questions about:\n"
#     "- Public services (Aadhar, PAN, passport)\n"
#     "- Government schemes (PMAY, PM-Kisan, etc.)\n"
#     "- Civic issues (electricity, roads, voter ID, etc.)\n"
#     "- State and central services\n\n"
#     "If a question is unclear or unrelated to government, respond politely:\n"
#     "'I'm sorry, I can only assist with Indian government-related services and policies.'\n\n"
#     "Always use polite and supportive language. Avoid vague replies or apologies unless absolutely necessary.\n"
# )
    system_prompt = (
    "You are Citizen AI — a helpful virtual assistant designed to answer questions about Indian governance, development, public services, economics, and related citizen topics.\n\n"
    "Your job is to provide clear, factual, and polite answers to users. When a user asks something complex (e.g., about GDP or development), try to provide an informed response — even if you can't be 100% accurate.\n\n"
    "If something is outside your scope (e.g., celebrity gossip, jokes), politely say: 'I'm here to help with citizen services and public knowledge.'\n\n"
    "Use simple language. Stay helpful, not evasive."
)



    full_prompt = f"{system_prompt}\n\nCitizen: {prompt}\nCitizen AI:"

    payload = {
        "model_id": "ibm/granite-13b-instruct-v2",
        "project_id": "54964ddf-77ab-4c70-8e35-f402829f3e83",
        "input": full_prompt,
        # "parameters": {
        #     "decoding_method": "greedy",
        #     "max_new_tokens": 150
        # }
        "parameters": {
        "decoding_method": "greedy",
        "max_new_tokens": 150,
        "temperature": 0.5,
        "repetition_penalty": 1.1
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["results"][0]["generated_text"]
    else:
        return f"API Error: {response.status_code} - {response.text}"
    

if __name__ == '__main__':
    app.run(debug=True)
