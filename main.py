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
app = FastAPI(title="Enterprise AI Lead Automation PRO")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. SECURITY (API KEY LOCK) ---
# Yeh aapka secret password hai. Frontend ko yeh key bhejni hogi.
API_KEY = "Tabish_Pro_Agent_2026_Secret"
api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    logger.warning(f"⚠️ SECURITY ALERT: Unauthorized access attempt detected!")
    raise HTTPException(status_code=403, detail="Bhai, access denied! Invalid API Key.")

# --- 4. ENVIRONMENT VARIABLES ---
os.environ["GROQ_API_KEY"] = os.getenv("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", "fallback_key_here")

# --- 5. DATA SCHEMAS ---
class LeadInfo(BaseModel):
    customer_name: str = Field(description="Name of the customer. Return 'None' if missing.")
    customer_email: str = Field(description="Email address. Return 'None' if missing.")
    phone_number: str = Field(description="Phone number. Return 'None' if missing.")
    budget: str = Field(description="Budget if mentioned, else 'Not Specified'.")
    lead_score: int = Field(description="Score 1-10. High budget/serious = 8+. Timepass = 1-3.")
    category: str = Field(description="Classify as 'Sales' or 'Support'.")
    summary: str = Field(description="A 1-line summary of the request.")

class IncomingLead(BaseModel):
    raw_text: str

# --- 6. AI BRAIN SETUP ---
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0).with_structured_output(LeadInfo)

# --- 7. THE MAIN ENDPOINT (Now Secured!) ---
@app.post("/capture-lead")
async def capture_and_score_lead(lead: IncomingLead, api_key: str = Depends(get_api_key)):
    logger.info("🔔 Naya Lead Aaya! AI Analyze kar raha hai...")
    
    try:
        # AI Data Extraction
        ai_analysis = llm.invoke(lead.raw_text)
        logger.info(f"✅ AI Analysis Complete. Category: {ai_analysis.category}, Score: {ai_analysis.lead_score}")
        
        # Make.com Webhook URL
        MAKE_WEBHOOK_URL = "https://hook.us1.make.com/5bjeyexi26nbyhxf9e70gn5dpxrrldah"
        
        # Send Data to Make.com
        logger.info("🚀 Data Make.com par bhej rahe hain...")
        webhook_response = requests.post(MAKE_WEBHOOK_URL, json=ai_analysis.dict())
        
        if webhook_response.status_code == 200:
            logger.info("✅ Data Make.com par successfully receive ho gaya!")
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