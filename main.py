import os
import requests
import logging
from fastapi import FastAPI, Depends, HTTPException, Security
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader

# --- 1. SYSTEM LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- 2. INITIALIZE APP & CORS ---
app = FastAPI(title="Tabish Enterprise AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. SECURITY (API KEY LOCK) ---
API_KEY = "Tabish_Pro_Agent_2026_Secret"
api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    logger.warning(f"⚠️ SECURITY ALERT: Unauthorized access attempt detected!")
    raise HTTPException(status_code=403, detail="Access denied! Invalid API Key.")

# --- 4. ENVIRONMENT VARIABLES ---
# Vercel Settings se automatically key uthayega
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "fallback_key_here")

# --- 5. DATA SCHEMAS (With Phase 7 Memory) ---
class LeadInfo(BaseModel):
    customer_name: str = Field(description="Name of the customer. Return 'None' if missing.")
    customer_email: str = Field(description="Email address. Return 'None' if missing.")
    phone_number: str = Field(description="Phone number. Return 'None' if missing.")
    budget: str = Field(description="Budget if mentioned, else 'Not Specified'.")
    lead_score: str = Field(description="Score 1 to 10. MUST be a string value like '8' or '3'.")
    category: str = Field(description="Classify as 'Sales' or 'Support'.")
    summary: str = Field(description="A 1-line summary of the request.")

class IncomingLead(BaseModel):
    raw_text: str
    chat_history: str = ""  # AI KI NAYI DIARY (MEMORY)

# --- 6. AI BRAIN SETUP ---
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0).with_structured_output(LeadInfo)

# --- 7. THE MAIN ENDPOINT ---
@app.post("/capture-lead")
async def capture_and_score_lead(lead: IncomingLead, api_key: str = Depends(get_api_key)):
    logger.info("🔔 Naya Message Aaya! AI Analyze kar raha hai...")
    
    try:
        # Phase 7: AI ko purani baatein aur naya message ek sath dena
        full_prompt = f"""
        Previous Conversation Context (if any):
        {lead.chat_history}
        
        Latest Message:
        {lead.raw_text}
        
        Now, combining all the information above, extract the lead details.
        """
        
        # AI Data Extraction
        ai_analysis = llm.invoke(full_prompt)
        logger.info(f"✅ AI Analysis Complete. Category: {ai_analysis.category}, Score: {ai_analysis.lead_score}")
        
        # Make.com Webhook URL (Aapka latest working link)
        MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/5b3eqexi26nbyhxf9e70gn5dpxrrldah"
        
        # Send Data to Make.com
        webhook_response = requests.post(MAKE_WEBHOOK_URL, json=ai_analysis.dict())
        
        if webhook_response.status_code == 200:
            logger.info("✅ Data Make.com par bhej diya gaya!")
        else:
            logger.error(f"❌ Make.com Error: {webhook_response.text}")
            
        return {
            "status": "success",
            "make_status": webhook_response.status_code,
            "data": ai_analysis
        }
        
    except Exception as e:
        logger.error(f"❌ System Crash/Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
