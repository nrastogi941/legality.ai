import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF for PDF parsing
import spacy
import speech_recognition as sr
from io import BytesIO
from reportlab.pdfgen import canvas

# Configure Google Gemini API (Replace with your actual API Key)
GENAI_API_KEY = st.secrets["general"]["GENAI_API_KEY"]
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Load NLP model for Named Entity Recognition (NER)
nlp = spacy.load("en_core_web_sm")

# Streamlit UI Setup
st.set_page_config(page_title="Legal AI Assistant", layout="wide")

# Sidebar Navigation
st.sidebar.title("⚖️ Legal AI Assistant")
st.sidebar.markdown("Use AI to analyze legal documents, draft contracts, and answer legal queries.")

menu = st.sidebar.radio("Select a feature:",
                        ["📂 Upload & Analyze Documents", "💬 Legal Chatbot",
                         "✍️ Draft Legal Documents", "🎤 Voice-Based Queries"])


# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    return "\n".join([page.get_text("text") for page in doc])


def generate_response(query: str) -> str:
    prompt = f"""You are an intelligent Legal advisor chatbot. Follow some below given guideline to give response
         to user:
         1. If User greets then greet user back and ask what legal advice should they except.
         2. If user asks any legal question then explain the response to user just like a highly qualified 
            legal advisor.
         3. If the user asks any generic question which does not falls in legal category just response back 
            back to user that asks only legal question and everything else is out of your scope.

         User Query : {query}
        """
    response = model.generate_content(prompt)
    return response.text if response else "Error generating response."


# Function to summarize text
def summarize_text(text: str) -> str:
    return generate_response(f"Summarize this legal document:\n{text}")

def answer_question(question: str, context: str) -> str:
    prompt = f"Answer the question based on the provided legal context.\n\nQuestion: {question}\nContext: {context}"
    return generate_response(prompt)


# Function to detect risky clauses
def detect_clause_risks(text: str) -> str:
    return generate_response(f"Highlight any high-risk clauses in this document:\n{text}")


# Function to extract named entities
def extract_named_entities(text: str):
    doc = nlp(text)
    return {ent.text: ent.label_ for ent in doc.ents}


# Function to compare two documents
def compare_documents(text1: str, text2: str) -> str:
    return generate_response(f"Compare these legal documents:\nDoc1: {text1}\nDoc2: {text2}")


# Function to draft a legal document
def draft_document(prompt: str) -> str:
    return generate_response(f"Draft a legal document based on this prompt:\n{prompt}")


# Function for speech recognition
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError:
        return "Speech recognition service unavailable."


# Function to create a downloadable PDF
def download_pdf(text, filename="output.pdf"):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 800, "Generated Legal Document")
    y_position = 780
    for line in text.split("\n"):
        pdf.drawString(100, y_position, line)
        y_position -= 20
    pdf.save()
    buffer.seek(0)
    return buffer


# Main UI Logic
if menu == "📂 Upload & Analyze Documents":
    st.title("📂 Upload & Analyze Legal Documents")

    uploaded_files = st.file_uploader("Upload legal documents (PDF/TXT)", type=["txt", "pdf"],
                                      accept_multiple_files=True)
    all_text = ""
    document_texts = {}

    if uploaded_files:
        for uploaded_file in uploaded_files:
            text = extract_text_from_pdf(
                uploaded_file) if uploaded_file.type == "application/pdf" else uploaded_file.read().decode("utf-8")
            document_texts[uploaded_file.name] = text
            all_text += text + "\n\n"
            st.text_area(f"📜 {uploaded_file.name}", text, height=150)

        if all_text:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Summarize Documents"):
                    with st.spinner("🔎 Summarizing document..."):
                        st.write("**Summary:**", summarize_text(all_text))
                if st.button("✅ Detect Risky Clauses"):
                    with st.spinner("🔍 Detecting risky clauses..."):
                        st.write("**Risks:**", detect_clause_risks(all_text))
            with col2:
                if st.button("🔎 Extract Named Entities"):
                    with st.spinner("🔍 Extracting named entities..."):
                        st.write("**Entities:**", extract_named_entities(all_text))

        # Document Comparison
        if len(document_texts) >= 2:
            doc1, doc2 = st.selectbox("Select First Document", list(document_texts.keys())), st.selectbox(
                "Select Second Document", list(document_texts.keys()))
            if st.button("🔍 Compare Documents"):
                st.write("**Comparison:**", compare_documents(document_texts[doc1], document_texts[doc2]))

        question = st.text_input("Ask a legal question based on the documents")
        if question:
            answer = answer_question(question, all_text)
            st.write("**Answer:**", answer)

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
            response = generate_response(user_input)
        
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)


elif menu == "✍️ Draft Legal Documents":
    st.title("✍️ Draft Legal Documents")
    prompt = st.text_area("Enter details for the legal document you need:")

    if st.button("📝 Generate Draft"):
        drafted_text = draft_document(prompt)
        st.write("**Generated Document:**", drafted_text)
        pdf_file = download_pdf(drafted_text)
        st.download_button("📥 Download as PDF", pdf_file, "drafted_document.pdf", "application/pdf")

elif menu == "🎤 Voice-Based Queries":
    st.title("🎤 Voice-Based Legal Queries")

    if st.button("🎤 Start Voice Query"):
        spoken_query = recognize_speech()
        st.write("**Recognized Query:**", spoken_query)
        if spoken_query:
            response = generate_response(spoken_query)
            st.write("**Answer:**", response)
