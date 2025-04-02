import streamlit as st
import requests
# from backend import app

# Backend API URL
BACKEND_API_URL = "http://localhost:8000"

# Streamlit UI Setup
st.set_page_config(page_title="Legal AI Assistant", layout="wide")

# Sidebar Navigation
st.sidebar.title("⚖️ Legal AI Assistant")
st.sidebar.markdown("Use AI to analyze legal documents, draft contracts, and answer legal queries.")

menu = st.sidebar.radio("Select a feature:",
                        ["📂 Upload & Analyze Documents", "💬 Legal Chatbot",
                         "✍️ Draft Legal Documents"])

# Function to upload document
def upload_document(file):
    url = f"{BACKEND_API_URL}/upload_document/"
    response = requests.post(url, files={"file": file})
    return response.json().get("text", "")

# Function to summarize document
def summarize_document(text):
    url = f"{BACKEND_API_URL}/summarize_document/"
    response = requests.post(url, json={"text": text})
    return response.json().get("summary", "")

# Function to detect risky clauses
def detect_risk(text):
    url = f"{BACKEND_API_URL}/detect_risk/"
    response = requests.post(url, json={"text": text})
    return response.json().get("risks", "")

# Function to extract named entities
def extract_named_entities(text):
    url = f"{BACKEND_API_URL}/extract_named_entities/"
    response = requests.post(url, json={"text": text})
    return response.json().get("entities", "")

# Function to draft legal document
def draft_document(prompt):
    url = f"{BACKEND_API_URL}/draft_document/"
    response = requests.post(url, json={"prompt": prompt})
    return response.json().get("draft", "")

# Function to interact with Legal Chatbot
def legal_chatbot(query):
    url = f"{BACKEND_API_URL}/legal_chatbot/"
    print(f"query: {query}")
    response = requests.post(url, json={"query": query})
    return response.json().get("response", "")

# Main UI Logic
if menu == "📂 Upload & Analyze Documents":
    st.title("📂 Upload & Analyze Legal Documents")

    uploaded_file = st.file_uploader("Upload a legal document (PDF/TXT)", type=["pdf", "txt"])
    if uploaded_file:
        st.write(f"File name: {uploaded_file.name}")
        text = upload_document(uploaded_file)
        # Send file to backend
        with st.spinner("Uploading and processing document..."):
            response = requests.post(
                f"{BACKEND_API_URL}/upload_document/",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            )

        # Handle response
        if response.status_code == 200:
            text = response.json().get("text", "")
            st.text_area("Extracted Document Content", text, height=300)
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

        if text:
            col1, col2 = st.columns(2)
            with col1:
                # Add searching icon for Summarize Document
                if st.button("📄 Summarize Document"):
                    with st.spinner("🔍 Summarizing document..."):
                        st.write("**Summary:**", summarize_document(text))
                
                # Add searching icon for Detect Risky Clauses
                if st.button("✅ Detect Risky Clauses"):
                    with st.spinner("🔍 Detecting risky clauses..."):
                        st.write("**Risky Clauses:**", detect_risk(text))
            
            with col2:
                # Add searching icon for Extract Named Entities
                if st.button("🔎 Extract Named Entities"):
                    with st.spinner("🔍 Extracting named entities..."):
                        st.write("**Named Entities:**", extract_named_entities(text))

elif menu == "💬 Legal Chatbot":
    st.title("💬 AI-Powered Legal Chatbot")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    user_input = st.chat_input("Ask me any legal question...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.write("**Your Query:**", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.spinner("🔎 Searching..."):
            response = legal_chatbot(user_input)
        
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

elif menu == "✍️ Draft Legal Documents":
    st.title("✍️ Draft Legal Documents")
    prompt = st.text_area("Enter details for the legal document you need:")
    if st.button("📝 Generate Draft"):
        drafted_text = draft_document(prompt)
        st.write("**Generated Document:**", drafted_text)

# elif menu == "🎤 Voice-Based Queries":
#     st.title("🎤 Voice-Based Legal Queries")
#     # Implement voice recognition as needed here.


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
