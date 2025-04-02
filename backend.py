from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
import spacy
from io import BytesIO
from reportlab.pdfgen import canvas
import fitz  # PyMuPDF for PDF parsing
import os

# Load API key from environment variables (replace manually if necessary)
GENAI_API_KEY = st.secrets["general"]["GENAI_API_KEY"]
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Load NLP model for Named Entity Recognition (NER)
nlp = spacy.load("en_core_web_sm")

# Initialize FastAPI app
app = FastAPI()


class QueryRequest(BaseModel):
    query: str

class DocumentRequest(BaseModel):
    text: str

class PromptRequest(BaseModel):
    prompt: str


def generate_response(query: str) -> str:
    print(f"query: {query}")
    """Generates a response using Google Gemini AI."""
    prompt = f"""You are an intelligent Legal advisor chatbot. Follow the below guidelines:
         1. If User greets, greet them back and ask what legal advice they need, if user not great, don't grate by yourself.
         2. If asked a legal question, provide a detailed response like a legal expert.
         3. If asked a non-legal question, inform the user that you only handle legal inquiries.
         4. Don't make any assumptions about the user's knowledge or background. if you don't know the answer, just say I don't know.
            "I can help you with legal questions, but I can't provide information on other topics."

         User Query : {query}
        """
    response = model.generate_content(prompt)
    print(f"response: {response}")
    return response.text if response else "Error generating response."

@app.get("/")
async def home():
    return {"message": "Welcome to the Legal AI Assistant API!"}

@app.post("/legal_chatbot/")
async def legal_chatbot(request: QueryRequest):
    response = generate_response(request.query)
    return {"response": response}

# Helper Functions
def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extracts text from a PDF file."""
    try:
        with fitz.open(stream=BytesIO(pdf_content), filetype="pdf") as doc:
            return "\n".join([page.get_text("text") for page in doc])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")

@app.post("/summarize_document/")
async def summarize_document(request: DocumentRequest): 
    """Summarizes a legal document."""
    summary = generate_response(f"Summarize this legal document:\n{request.text}")
    return {"summary": summary}

@app.post("/detect_risk/")
async def detect_risk(request: DocumentRequest):
    """Detects high-risk clauses in legal text."""
    risks = generate_response(f"Highlight any high-risk clauses in this document:\n{request.text}")
    return {"risks": risks}

@app.post("/extract_named_entities/")
async def extract_entities(request: DocumentRequest):
    """Extracts named entities using spaCy."""
    doc = nlp(request.text)
    return {ent.text: ent.label_ for ent in doc.ents}

@app.post("/upload_document/")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a legal document and extracts text."""
    try:
        # Ensure the file is valid
        print(f"File name: {file.filename}, Content type: {file.content_type}")
        if not file.content_type:
            raise HTTPException(status_code=400, detail="Invalid file type or no file uploaded.")
        
        # Read the file content
        content = await file.read()
        print(f"File name: {file.filename}, Content type: {file.content_type}")
        
        # Handle PDF files
        if file.content_type == 'application/pdf':
            text = extract_text_from_pdf(content)
        # Handle plain text files
        elif file.content_type == 'text/plain':
            text = content.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF or TXT file.")
        
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.post("/draft_document/")
async def draft_legal_document(request: PromptRequest):
    """Generates a legal document draft based on user input."""
    print(f"Drafting document with prompt: {request.prompt}")
    draft = generate_response(f"Draft a legal document based on this prompt:\n{request.prompt}")
    return {"draft": draft} 


@app.post("/generate_pdf/")
async def generate_pdf(text: str):
    """Generates a downloadable legal document in PDF format."""
    try:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.drawString(100, 800, "Generated Legal Document")
        y_position = 780
        for line in text.split("\n"):
            pdf.drawString(100, y_position, line)
            y_position -= 20
        pdf.save()
        buffer.seek(0)
        
        return StreamingResponse(buffer, media_type="application/pdf",
                                 headers={"Content-Disposition": "attachment; filename=document.pdf"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
