import os
import json
from datetime import datetime, timedelta 
from pydantic import BaseModel, Field
from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from openai import OpenAI
import requests
from dotenv import load_dotenv

# Load local environment configurations if present
load_dotenv()

from contextlib import asynccontextmanager, AsyncExitStack
from mcp.server.fastmcp import FastMCP

# Initialize MCP server instance
mcp_server = FastMCP("ICLP MCP Server")

# Example tool: retrieve metrics for an enquiry (placeholder implementation)
@mcp_server.tool()
def get_metrics(enquiry_no: str) -> dict:
    """Return placeholder metrics for the given enquiry number."""
    # In a real implementation, you would query your data store.
    return {"enquiry_no": enquiry_no, "status": "metrics placeholder"}

# Lifespan context manager to start MCP server session manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(mcp_server.session_manager.run())
        yield

# Recreate FastAPI app with lifespan and mount the MCP sub-application
app = FastAPI(
    title="Intelligent Commercial Logistics Platform (ICLP) Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Mount the MCP server at /mcp endpoint
app.mount("/mcp", mcp_server.streamable_http_app())

# Secure Initialization of the AI Gateway Client
# Automatically extracts credentials from the host environment memory
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None
    print("[WARNING] OPENAI_API_KEY not set; OpenAI client disabled. Pipeline will use mock responses.")

# --- 1. SYSTEM DESIGN (SD) DATA CONTRACT MATRIX ---
class ZohoEnquiryPayload(BaseModel):
    Enquiry_No: str = Field(..., description="Unique Zoho record key tracking identifier.")
    Contact_Name: str = Field(..., description="Target contact operator name.")
    Owner_Email: str = Field(..., description="Assigned desk pricing analyst email profile.")
    Total_Enquiry_Received: int = Field(..., description="Historical interaction count total.")
    Confirmed_Bookings: int = Field(..., description="Historical completed booking count.")
    Added_Time: str = Field(..., description="Timestamp record was created: YYYY-MM-DD HH:MM:SS")
    Quoted_Time: str | None = Field(None, description="Timestamp quote was issued: YYYY-MM-DD HH:MM:SS")
    Cut_Off: str | None = Field(None, description="Hard carrier deadline timestamp: YYYY-MM-DD HH:MM:SS")
    POR: str = Field(..., description="Place of Receipt checkpoint.")
    POL: str = Field(..., description="Port of Loading gateway.")
    POD: str = Field(..., description="Port of Discharge gateway.")
    FDC: str = Field(..., description="Final Delivery Place checkpoint.")
    Note_to_Pricing: str = Field("", description="Multi-line unstructured timeline note log text.")
    Closing_Comments: str = Field("", description="Target processing block for synthesized email payload.")
    Management_Support_Reached: bool = Field(False, description="Blueprint verification field indicating stakeholder access.")

# --- 2. DETERMINISTIC LIFECYCLE MATH & BLUEPRINT ENGINE ---
def calculate_operational_metrics(data: ZohoEnquiryPayload) -> dict:
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        added = datetime.strptime(data.Added_Time, fmt)
        
        # Turnaround delay math
        delay_hours = 0.0
        quoted = None
        if data.Quoted_Time:
            quoted = datetime.strptime(data.Quoted_Time, fmt)
            delay_hours = round((quoted - added).total_seconds() / 3600, 2)
            
        # Blueprint cutoff breach validation logic
        cutoff_breach_minutes = 0
        if data.Cut_Off and quoted:
            cutoff = datetime.strptime(data.Cut_Off, fmt)
            if quoted > cutoff:
                cutoff_breach_minutes = round((quoted - cutoff).total_seconds() / 60)
            
        # Baseline conversion win-rate percentage extraction
        win_rate = 0.0
        if data.Total_Enquiry_Received > 0:
            win_rate = round((data.Confirmed_Bookings / data.Total_Enquiry_Received) * 100, 2)
            
        return {
            "delay_hours": delay_hours,
            "cutoff_breach_minutes": cutoff_breach_minutes,
            "historical_win_rate": win_rate,
            "error_flag": False
        }
    except Exception as e:
        return {
            "delay_hours": 0,
            "cutoff_breach_minutes": 0,
            "historical_win_rate": 0,
            "error_flag": True,
            "error_message": str(e)
        }

# --- 3. ARTIFICIAL INTELLIGENCE (AI) DISPATCH CORNERSTONES ---
MODEL_A_SYSTEM_PROMPT = """
You are the ICLP Real-Time Analytics Dashboard Engine.
Analyze the provided freight transaction data packet and return a strict JSON object matching this schema exactly. 
Do not include any markdown code blocks, thoughts, backticks, or trailing prose outside the raw JSON payload.

Expected Strict JSON Schema:
{
  "triage_case": "Case 1 | Case 2 | Case 3 | Case 4",
  "business_factors": {
    "brand_visibility": "High | Medium | Low",
    "engagement_status": "High Volume Engagement | Passive Volume | Critical Idle",
    "product_lane_strength": "Leverage Advantage | Standard | Low Density",
    "enquiry_status": "Pipeline Active | Bottleneck Risk"
  },
  "investigation_insight": "String summary auditing timing risks or profile tracking gaps.",
  "strategy_insight": "String detailing optimal quotation strategies matching corporate lane guidelines from Vani Ma'am and Sharan Sir."
}

Triage Blueprint Rules:
- Case 1 (Lost Account): Total_Enquiry_Received > 3 and Confirmed_Bookings == 0.
- Case 2 (Regular Account): Historical win rate >= 40%.
- Case 3 (Cold Account): Silent/inactive account behavior with extended delays.
- Case 4 (New Enquiry): Total_Enquiry_Received <= 1.
"""

MODEL_B_SYSTEM_PROMPT = """
You are the ICLP Communications Engine.
Generate a professional, highly polished B2B freight quotation response email body based on the client profile, routing parameters, and strategic directions provided.
Ensure core logistics attributes (POR, POL, POD, FDC) are accurately incorporated. Maintain an authoritative, consultative, and direct sales tone. 
Do not generate a subject line, header, signature blocks, or meta-placeholders; output only the clean, raw message body copy text block.
"""

# --- Zoho Creator REST API Client ---
class ZohoClient:
    def __init__(self):
        self.base_url = os.environ.get("ZOHO_CREATOR_API_BASE_URL", "https://creator.zoho.com/api/v2")
        self.owner = os.environ.get("ZOHO_CREATOR_OWNER")
        self.app_link_name = os.environ.get("ZOHO_CREATOR_APP_LINK_NAME")
        self.report_link_name = os.environ.get("ZOHO_CREATOR_REPORT_LINK_NAME")
        
        self.client_id = os.environ.get("ZOHO_CLIENT_ID")
        self.client_secret = os.environ.get("ZOHO_CLIENT_SECRET")
        self.refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN")
        self.accounts_url = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com")
        
        self._access_token = os.environ.get("ZOHO_ACCESS_TOKEN")
        self._token_expiry = None

        # Check if configuration is complete for live API usage
        self.is_dry_run = not all([
            self.owner,
            self.app_link_name,
            self.report_link_name
        ])
        
        # Check if credentials are provided
        has_oauth = all([self.client_id, self.client_secret, self.refresh_token])
        has_direct_token = bool(self._access_token)
        
        if not self.is_dry_run and not (has_oauth or has_direct_token):
            self.is_dry_run = True
            self.dry_run_reason = "Missing Zoho Creator credentials (ZOHO_CLIENT_ID/SECRET/REFRESH_TOKEN or ZOHO_ACCESS_TOKEN)."
        elif self.is_dry_run:
            self.dry_run_reason = "Missing Zoho Creator configuration (ZOHO_CREATOR_OWNER, ZOHO_CREATOR_APP_LINK_NAME, ZOHO_CREATOR_REPORT_LINK_NAME)."
        else:
            self.dry_run_reason = ""

    def get_access_token(self) -> str:
        # If we have client ID, secret, and refresh token, dynamically refresh it
        if self.client_id and self.client_secret and self.refresh_token:
            # Check if token needs refresh
            if not self._access_token or not self._token_expiry or datetime.now() >= self._token_expiry:
                self.refresh_access_token()
        return self._access_token

    def refresh_access_token(self):
        url = f"{self.accounts_url.rstrip('/')}/oauth/v2/token"
        payload = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        print(f"[Zoho Client] Refreshing access token...")
        response = requests.post(url, data=payload)
        response.raise_for_status()
        res_json = response.json()
        self._access_token = res_json["access_token"]
        expires_in = res_json.get("expires_in", 3600)
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
        print(f"[Zoho Client] Token refreshed successfully. Expires in {expires_in} seconds.")

    def find_record_id_by_enquiry_no(self, enquiry_no: str) -> str:
        access_token = self.get_access_token()
        if not access_token:
            raise ValueError("No Zoho access token available.")
            
        url = f"{self.base_url.rstrip('/')}/{self.owner}/{self.app_link_name}/report/{self.report_link_name}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
        }
        params = {
            "criteria": f'Enquiry_No == "{enquiry_no}"'
        }
        
        print(f"[Zoho Client] Searching record for Enquiry_No: {enquiry_no}...")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        res_json = response.json()
        
        records = res_json.get("data", [])
        if not records:
            raise ValueError(f"No Zoho Creator record found matching Enquiry_No: {enquiry_no}")
            
        record_id = records[0].get("ID")
        if not record_id:
            raise ValueError("Record found but is missing the 'ID' field.")
            
        print(f"[Zoho Client] Found matching Zoho Creator Record ID: {record_id}")
        return str(record_id)

    def update_record(self, record_id: str, data: dict):
        access_token = self.get_access_token()
        if not access_token:
            raise ValueError("No Zoho access token available.")
            
        url = f"{self.base_url.rstrip('/')}/{self.owner}/{self.app_link_name}/report/{self.report_link_name}/{record_id}"
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "data": data
        }
        
        print(f"[Zoho Client] Patching record {record_id} at URL: {url}")
        response = requests.patch(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

# Initialize singleton Zoho Creator API client
zoho_client = ZohoClient()

# --- 4. ASYNCHRONOUS ENGINE WORKER COMPONENT ---
def generate_mock_model_a_response(data: ZohoEnquiryPayload, metrics: dict) -> dict:
    win_rate = metrics["historical_win_rate"]
    
    # 1. Triage Case rules
    if data.Total_Enquiry_Received > 3 and data.Confirmed_Bookings == 0:
        triage_case = "Case 1"
    elif win_rate >= 40.0:
        triage_case = "Case 2"
    elif data.Total_Enquiry_Received <= 1:
        triage_case = "Case 4"
    else:
        triage_case = "Case 3"
        
    # 2. Business Factors
    brand_visibility = "High" if data.Total_Enquiry_Received > 10 else ("Medium" if data.Total_Enquiry_Received > 2 else "Low")
    
    if data.Total_Enquiry_Received > 10:
        engagement_status = "High Volume Engagement"
    elif data.Total_Enquiry_Received == 0:
        engagement_status = "Critical Idle"
    else:
        engagement_status = "Passive Volume"
        
    product_lane_strength = "Standard"
    if data.POR in ["Shenzhen", "Shanghai", "Ningbo"]:
        product_lane_strength = "Leverage Advantage"
        
    enquiry_status = "Pipeline Active"
    if metrics["cutoff_breach_minutes"] > 0:
        enquiry_status = "Bottleneck Risk"
        
    # 3. Insights
    investigation_insight = f"Mock Audit: Evaluated account history for {data.Contact_Name}."
    if metrics["cutoff_breach_minutes"] > 0:
        investigation_insight = f"TIMING BREACH: Internal turnaround delay exceeded operational windows. The hard carrier cutoff was missed by {metrics['cutoff_breach_minutes']} minutes. Late-gate space validation required."
        
    strategy_insight = f"Target {triage_case} quotation strategy. Apply corporate lane guidelines from Vani Ma'am and Sharan Sir for route corridor: {data.POR} to {data.POD}."
    
    return {
        "triage_case": triage_case,
        "business_factors": {
            "brand_visibility": brand_visibility,
            "engagement_status": engagement_status,
            "product_lane_strength": product_lane_strength,
            "enquiry_status": enquiry_status
        },
        "investigation_insight": investigation_insight,
        "strategy_insight": strategy_insight
    }

def generate_mock_model_b_response(data: ZohoEnquiryPayload, strategy_insight: str) -> str:
    return f"""Dear {data.Contact_Name},

Thank you for your freight inquiry. Below is our strategic quotation response following our discussions on lane optimizations:

- Place of Receipt: {data.POR}
- Port of Loading: {data.POL}
- Port of Discharge: {data.POD}
- Final Delivery Place: {data.FDC}

Strategic Guidelines: {strategy_insight}

We look forward to partnering with you on this shipment.

Best regards,
Pricing Operations Desk
{data.Owner_Email}"""

def execute_mcp_intelligence_pipeline(data: ZohoEnquiryPayload):
    # Process local deterministic calculations
    metrics = calculate_operational_metrics(data)
    
    # If OpenAI client is not configured, skip remote calls and use mock responses directly
    if client is None:
        # Generate mock Model A response
        insights = generate_mock_model_a_response(data, metrics)
        # Generate mock Model B response
        email_draft = generate_mock_model_b_response(data, insights["strategy_insight"])
        # Push Mock Insight Package back to Zoho Creator (dry‑run or real)
        push_to_zoho_creator(data.Enquiry_No, insights, email_draft)
        return
    
    # Consolidate input state vector for real OpenAI calls
    context_packet = {
        "record_data": data.model_dump(),
        "calculated_metrics": metrics
    }
    
    try:
        # Trigger Model A: Dashboard Analytics Synthesis (Strict JSON Verification Mode)
        response_a = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": MODEL_A_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(context_packet)}
            ],
            temperature=0.1
        )
        insights = json.loads(response_a.choices[0].message.content)
        
        # Hard Structural Override: Safeguard calculated timeline logic breaches
        if metrics["cutoff_breach_minutes"] > 0:
            insights["investigation_insight"] = f"TIMING BREACH: Internal turnaround delay exceeded operational windows. The hard carrier cutoff was missed by {metrics['cutoff_breach_minutes']} minutes. Late‑gate space validation required."
            insights["business_factors"]["enquiry_status"] = "Bottleneck Risk"
        
        # Trigger Model B: Communication Synthesis (Context‑Heavy Narrative Mode)
        response_b = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": MODEL_B_SYSTEM_PROMPT},
                {"role": "user", "content": f"Context: {json.dumps(context_packet)}. Strategy Guidance: {insights.get('strategy_insight')}"}
            ],
            temperature=0.5
        )
        email_draft = response_b.choices[0].message.content
        
        # PUSH INSIGHT PACKAGE BACK TO LIVE PRODUCTION DASHBOARD
        push_to_zoho_creator(data.Enquiry_No, insights, email_draft)
    except Exception as e:
        print(f"[Pipeline Processing Failure] Unable to compute intelligence for record {data.Enquiry_No} via OpenAI API: {str(e)}")
        print(f"⚠️ [API Failure Fallback] Generating local deterministic Mock AI insights for record {data.Enquiry_No}...")
        
        # Generate mock Model A response
        insights = generate_mock_model_a_response(data, metrics)
        # Generate mock Model B response
        email_draft = generate_mock_model_b_response(data, insights["strategy_insight"])
        
        # Push Mock Insight Package back to Zoho Creator logs
        push_to_zoho_creator(data.Enquiry_No, insights, email_draft)
    
def push_to_zoho_creator(enquiry_no: str, insights: dict, email_body: str):
    """
    Handover Point for the SD Team.
    This handles sending the structured AI data package back into Zoho Creator fields via REST APIs.
    """
    print(f"\n--- AI RUN COMPLETE FOR RECORD (Enquiry_No): {enquiry_no} ---")
    print(f"Targeting Update Fields: Investigation_Insight, Strategy_Insight, Closing_Comments")
    print(f"Compiled Payload Metrics:\n{json.dumps(insights, indent=2)}")
    print(f"Generated Mail Body Copy Snippet:\n{email_body[:120]}...\n")
    
    # Prepare update payload
    patch_data = {
        "Investigation_Insight": insights.get("investigation_insight", ""),
        "Strategy_Insight": insights.get("strategy_insight", ""),
        "Closing_Comments": email_body
    }
    
    # Handle dry-run fallback gracefully
    if zoho_client.is_dry_run:
        print(f"ℹ️ [Zoho Creator Integration] Running in DRY-RUN mode. Reason: {zoho_client.dry_run_reason}")
        print("[Zoho Creator Integration] If credentials were provided, the following payload would be PATCHed:")
        print(json.dumps(patch_data, indent=2))
        return

    try:
        # 1. Resolve internal 18-digit Record ID by matching criteria
        internal_id = zoho_client.find_record_id_by_enquiry_no(enquiry_no)
        
        # 2. Patch record in Zoho Creator
        response = zoho_client.update_record(internal_id, patch_data)
        print(f"✅ [Zoho Creator Integration] Record {enquiry_no} (ID: {internal_id}) updated successfully. Response: {response}")
    except Exception as e:
        print(f"❌ [Zoho Creator Integration Failure] Failed to update Zoho Creator for record {enquiry_no}: {str(e)}")

# --- 5. NETWORK WEBHOOK GATEWAY INTERFACES ---
@app.post("/webhooks/v1/enquiry", status_code=status.HTTP_200_OK)
def receive_zoho_webhook(payload: ZohoEnquiryPayload, background_tasks: BackgroundTasks):
    print(f"\n[Webhook Received] Processing inbound transaction tracker for enquiry: {payload.Enquiry_No}")
    
    # Offload the LLM pipeline calls to a background worker.
    # This releases the connection back to Zoho immediately, ensuring an under 2.5-second SLA response.
    background_tasks.add_task(execute_mcp_intelligence_pipeline, payload)
    
    return {
        "status": "queued",
        "message": f"Enquiry {payload.Enquiry_No} successfully passed validation rules and queued for async analytics processing."
    }

@app.get("/health", status_code=status.HTTP_200_OK)
def server_health_check():
    return {"status": "healthy", "engine_version": "1.0.0"}

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    return {
        "message": "Welcome to the Intelligent Commercial Logistics Platform (ICLP) Engine API.",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "enquiry_webhook": "/webhooks/v1/enquiry"
        }
    }