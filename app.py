import os
import json
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import FastAPI, BackgroundTasks, status
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Intelligent Commercial Logistics Platform (ICLP) Master Engine", 
    version="3.0.0"
)

# Secure Initialization of the AI Gateway Client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --- 1. ENTERPRISE CORE DATA CONTRACT ---
class ZohoEnquiryPayload(BaseModel):
    Enquiry_No: str = Field(..., description="Unique Zoho record key tracking identifier.")
    Contact_Name: str = Field(..., description="Target contact operator name.")
    Owner_Email: str = Field(..., description="Assigned desk pricing analyst email profile.")
    Total_Enquiry_Received: int = Field(..., description="Historical interaction count total.")
    Confirmed_Bookings: int = Field(..., description="Historical completed booking count.")
    Added_Time: str = Field(..., description="Timestamp record was created: YYYY-MM-DD HH:MM:SS")
    Quoted_Time: str = Field(..., description="Timestamp quote was issued: YYYY-MM-DD HH:MM:SS")
    Cut_Off: str = Field(..., description="Hard carrier deadline timestamp: YYYY-MM-DD HH:MM:SS")
    POR: str = Field(..., description="Place of Receipt checkpoint.")
    POL: str = Field(..., description="Port of Loading gateway.")
    POD: str = Field(..., description="Port of Discharge gateway (e.g., Rotterdam, Antwerp, Hamburg).")
    FDC: str = Field(..., description="Final Delivery Place checkpoint.")
    
    # Text History & Centralized Inputs
    Note_to_Pricing: str = Field("", description="Multi-line unstructured follow-up text or CRM loss reasons notes.")
    Brand_Visibility: str = Field(..., description="User enters 'YES' or 'NO' for marketing exposure parameters.")
    Management_Support_Reached: bool = Field(..., description="True/False if an executive or decision-maker was reached.")
    Account_Funnel_Stage: str = Field(..., description="Directly mirrors the current CRM Account Funnel Stage.")

# --- 2. DETERMINISTIC TIMING & CORRIDOR CALCULATIONS ---
def calculate_metrics(data: ZohoEnquiryPayload) -> dict:
    fmt = "%Y-%m-%d %H:%M:%S"
    added = datetime.strptime(data.Added_Time, fmt)
    quoted = datetime.strptime(data.Quoted_Time, fmt)
    cutoff = datetime.strptime(data.Cut_Off, fmt)
    
    delay_hours = round((quoted - added).total_seconds() / 3600, 2)
    cutoff_breach_minutes = max(0, round((quoted - cutoff).total_seconds() / 60))
    win_rate = round((data.Confirmed_Bookings / data.Total_Enquiry_Received * 100), 2) if data.Total_Enquiry_Received > 0 else 0.0
    
    # Rule-Based Engagement Mapping
    if data.Total_Enquiry_Received > 10 and win_rate >= 40.0:
        engagement = "High Volume Engagement"
    elif data.Total_Enquiry_Received > 0 and win_rate == 0.0:
        engagement = "Lost Account Pipeline"
    elif data.Total_Enquiry_Received <= 1:
        engagement = "New Contact / Lead"
    else:
        engagement = "Passive Volume / Critical Idle"
        
    # Standard Corridor Verification Check
    lane_strength = "Standard Density"
    if data.POR in ["Hanoi", "Shenzhen", "Shanghai"]:
        lane_strength = "Leverage Advantage"
        
    return {
        "delay_hours": delay_hours,
        "cutoff_breach_minutes": cutoff_breach_minutes,
        "historical_win_rate": win_rate,
        "engagement_status": engagement,
        "product_lane_strength": lane_strength
    }

# --- 3. MASTER COGNITIVE STRATEGY PROMPT ---
MODEL_A_SYSTEM_PROMPT = """
You are the ICLP Master Pricing Strategy Engine. Your role is to equip the pricing desk with centralized commercial intelligence.

CRITICAL PRICING STRATEGY GUIDELINES:
Analyze the lifecycle data and historical text feedback notes (Note_to_Pricing) to determine the exact strategy:
- If the history shows the account was lost due to pricing ('High Rate', 'Expensive'), direct the user to quote 'Net-to-Net Pricing'.
- If the account is a New Contact/Lead or an active client on a highly sensitive route, direct them to quote 'Thin Margin Strategy'.
- If the route involves a European destination port (POD in Europe like Rotterdam, Antwerp, Genoa, Hamburg, etc.), mark 'is_europe_priority' as true and prioritize premium or aggressive direct vessel routing strategies to protect market share.

You must return a strict JSON object matching this schema exactly with no surrounding text:
{
  "customer_lifecycle_state": "Live Active | Lost Account | New Contact Account | Lead",
  "extracted_historical_loss_reason": "None | High Rate | Transit Delay | Space Constraints | Communication Gap",
  "brand_visibility_status": "YES | NO",
  "management_support_status": "Reached | Not Reached",
  "engagement_level": "High Volume Engagement | Passive Volume | Critical Idle | Lost Account Pipeline",
  "product_lane_leverage": "Leverage Advantage | Standard Density",
  "enquiry_pipeline_stage": "String mirroring Account_Funnel_Stage",
  "is_europe_priority": true,
  "recommended_quoting_strategy": "Net-to-Net Pricing | Thin Margin Strategy | Premium Margin Direct | Value-Added Promotional",
  "investigation_insight": "Summary of data gaps, timestamp audits, or missed carrier cutoffs.",
  "strategy_insight": "Actionable instructions mapping out missed operations and exactly how to construct the freight quote based on history."
}
"""

# --- 4. ENGINE BACKGROUND PIPELINE WORKER ---
def execute_master_pricing_pipeline(data: ZohoEnquiryPayload):
    metrics = calculate_metrics(data)
    
    context_packet = {
        "ui_inputs": data.model_dump(),
        "calculated_metrics": metrics
    }
    
    try:
        # Request strict structured analysis from the model layer
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": MODEL_A_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context_packet)}
            ],
            temperature=0.1
        )
        insights = json.loads(response.choices[0].message.content)
        
        # --- DETERMINISTIC HEURISTIC BOOKING PROBABILITY ALGEBRA ---
        base_probability = (0.4 * metrics["historical_win_rate"]) - (2 * metrics["delay_hours"])
        
        # Strategy weight adjustments
        strategy = insights.get("recommended_quoting_strategy")
        if strategy == "Net-to-Net Pricing": base_probability += 25
        elif strategy == "Thin Margin Strategy": base_probability += 15
        
        # Input state vector weights
        if data.Brand_Visibility.upper() == "YES": base_probability += 10
        if data.Management_Support_Reached: base_probability += 15
        if insights.get("is_europe_priority") is True: base_probability += 10
            
        final_probability = max(0, min(100, round(base_probability, 2)))
        insights["resulting_booking_probability"] = f"{final_probability}%"
        
        # Output the centralized data stream straight to your Zoho Creator dashboard widgets
        push_to_zoho_dashboard_panels(data.Enquiry_No, insights)
        
    except Exception as e:
        print(f"[Pipeline Error] Critical processing failure on background loop: {str(e)}")

def push_to_zoho_dashboard_panels(enquiry_no: str, insights: dict):
    print(f"\n📡 SYNCING CENTRALIZED COMMERCIAL DATA TO ZOHO CREATOR PANELS FOR: {enquiry_no}")
    print(json.dumps(insights, indent=2))

# --- 5. NETWORK ENDPOINT GATEWAY INTERFACE ---
@app.post("/webhooks/v1/enquiry", status_code=status.HTTP_200_OK)
def receive_zoho_webhook(payload: ZohoEnquiryPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(execute_master_pricing_pipeline, payload)
    return {
        "status": "queued", 
        "message": "Enquiry data schema validated. Asynchronous commercial strategy mapping initiated."
    }