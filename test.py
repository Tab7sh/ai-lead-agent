import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

# 1. Sab se pehle API Key set karein
os.environ["GROQ_API_KEY"] = "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"

# 2. Phir App banayein (Yeh upar hona zaroori tha!)
app = FastAPI(title="Enterprise AI Lead Automation")

# 3. Phir AI ko batayein ke data kaisa chahiye (Schema)
class LeadInfo(BaseModel):
    customer_name: str = Field(description="Customer ka naam")
    phone_number: str = Field(description="Phone number agar diya ho, warna 'None'")
    budget: str = Field(description="Agar budget bataya hai toh nikal lo, warna 'Not Specified'")
    lead_score: int = Field(description="1 se 10 tak score. Serious buyer 8+, timepass 3 se kam")
    summary: str = Field(description="Customer ki requirement 1 line mein")

# User jo raw message bhejega uska schema
class IncomingLead(BaseModel):
    raw_text: str

# 4. Phir AI ka dimaagh set karein
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0).with_structured_output(LeadInfo)

# 5. Aakhir mein hamara Endpoint aayega
@app.post("/capture-lead")
async def capture_and_score_lead(lead: IncomingLead):
    print("🔔 Naya Lead Aaya! AI Analyze kar raha hai...")
    
    # AI Data Extract Karega
    ai_analysis = llm.invoke(lead.raw_text)
    
    # Aapka Make.com ka Webhook URL
    MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/5b3eqexi26nbyhxf9e70gn5dpxrrldah"
    
    # Data ko Make.com par bhej dein!
    print("🚀 Data Make.com par bhej rahe hain...")
    webhook_response = requests.post(MAKE_WEBHOOK_URL, json=ai_analysis.dict())
    
    return {
        "status": "success", 
        "message": "Data extracted and sent to CRM",
        "make_status": webhook_response.status_code,
        "data": ai_analysis
    }