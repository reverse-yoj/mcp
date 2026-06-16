import os
import json
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from openai import OpenAI

app = FastAPI(title="ICLP Master MCP Control Engine")

# Initialize the OpenAI Client
# It will automatically look for an Environment Variable named 'OPENAI_API_KEY'
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "mock-key-for-testing"))

# ==========================================
# 1. THE DATA CONTRACT (Pydantic Schema)
# ==========================================
class ZohoEnquiryPayload(BaseModel):
    Enquiry_No: str
    Enquiry_Date: str
    Account: str
    Contact_Name: Optional[str] = "UNKNOWN"
    Department: Optional[str] = "UNKNOWN"
    POR: str
    POL: str
    POD: str
    FDC: str
    Total_Enquiry_Received: int = 0
    Confirmed_Bookings: int = 0
    Last_Booking_Received_Date: Optional[str] = "UNKNOWN"
    Note_to_Pricing: Optional[str] = "No notes provided."
    Added_Time: str
    Quoted_Time: Optional[str] = None

# ==========================================
# 2. THE MASTER SYSTEM PROMPT
# ==========================================
MASTER_SYSTEM_PROMPT = """
You are acting as the Core Intelligence Engine of the Intelligent Commercial Logistics Platform (ICLP). 
Your role is to analyze structured container shipping data packets and translate them into real-time pricing strategies, operational risk flags, and communication tracks for our Zoho Creator Dashboard.

### 1. OPERATIONAL GUARDRAILS
- Response Format: You must respond ONLY as a strict, single JSON object. Do not include conversational filler, prefaces, or markdown code blocks (such as ```json) outside the pure data payload.
- Data Gap Resilience (Case 4 Handling): If fields are marked "UNKNOWN", do not hallucinate metrics. Instead, immediately pivot your "investigation_insight" output to flag the exact profile gap and generate a data-gathering checklist for the rep.

### 2. THE 4-CASE TRIAGE MANDATE
Evaluate incoming historical volume metrics to tag the record's operational track:
- Case 1: Lost Account -> Set if Total_Enquiry_Received > 3 but Confirmed_Bookings == 0.
- Case 2: Regular Account -> Set if win rate >= 40%.
- Case 3: Cold Account -> Set if Last_Booking_Received_Date is older than 60 days from June 2026.
- Case 4: New Enquiry -> Set if Total_Enquiry_Received <= 1.

### 3. THE ANALYTICAL OUTPUT SCHEMA
Your JSON response must map precisely to these keys:
{
  "triage_case": "Case 1 | Case 2 | Case 3 | Case 4",
  "business_factors": {
    "engagement_status": "High | Passive Volume | Critical Idle",
    "brand_visibility": "Strong | Minimal",
    "management_support": "High Executive | Procurement Tier | Unmapped",
    "enquiry_status": "Processing | Bottleneck Risk",
    "product_lane_strength": "Leverage Advantage | Market Match | High Cost Tier"
  },
  "investigation_insight": "A professional paragraph auditing profile data gaps, timing risks, or shipping anomalies.",
  "strategy_insight": "Actionable, direct instructions guiding the pricing analyst on margin application, rate sensitivity, or specialized routing options."
}
"""

# ==========================================
# 3. THE WEBHOOK GATEWAY (Listens to Zoho)
# ==========================================
@app.post("/webhooks/v1/enquiry")
def receive_zoho_webhook(raw_data: dict, background_tasks: BackgroundTasks):
    print(f"\n⚡ [Webhook Alert] Received update from Zoho Creator Form.")
    try:
        validated_data = ZohoEnquiryPayload(**raw_data)
    except Exception as e:
        return {"status": "error", "message": f"Data contract validation failed: {str(e)}"}
    
    background_tasks.add_task(execute_mcp_intelligence_pipeline, validated_data)
    return {"status": "queued", "message": f"Enquiry {validated_data.Enquiry_No} is processing."}

# ==========================================
# 4. THE AI LIVE CONNECTION CORE
# ==========================================
def execute_mcp_intelligence_pipeline(data: ZohoEnquiryPayload):
    print(f"⚙️ [Processing Worker] Running live AI analysis for {data.Account}...")
    
    # Calculate baseline metrics for the AI input window
    win_rate = 0.0
    if data.Total_Enquiry_Received > 0:
        win_rate = (data.Confirmed_Bookings / data.Total_Enquiry_Received) * 100

    # Package the Master Contract Object
    ai_context_packet = {
        "meta": {
            "enquiry_id": data.Enquiry_No,
            "shipper": data.Account,
            "route_corridor": f"{data.POR} ({data.POL}) -> {data.POD} ({data.FDC})"
        },
        "historical_metrics": {
            "historical_win_rate_percent": round(win_rate, 2),
            "total_past_enquiries": data.Total_Enquiry_Received,
            "last_active_booking_date": data.Last_Booking_Received_Date
        },
        "operational_insights": {
            "user_notes": data.Note_to_Pricing,
            "buyer_department": data.Department
        }
    }

    try:
        # Connect Live to OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"}, # STRICT DATABASE GUARDRAIL
            messages=[
                {"role": "system", "content": MASTER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this freight transaction: {json.dumps(ai_context_packet)}"}
            ],
            temperature=0.2 # Keep answers stable and realistic
        )
        
        # Extract the raw JSON string from the AI's reply
        ai_raw_json = response.choices[0].message.content
        structured_insights = json.loads(ai_raw_json)
        
        print("\n--- 🎉 Live AI Response Stream Received Successfully ---")
        print(json.dumps(structured_insights, indent=2))
        print("--------------------------------------------------------\n")
        
        # TODO: requests.put("[https://www.zohoapis.com/creator/](https://www.zohoapis.com/creator/)...", json=structured_insights)
        
    except Exception as e:
        print(f"❌ [API Error] Failed to process live AI loop: {str(e)}")