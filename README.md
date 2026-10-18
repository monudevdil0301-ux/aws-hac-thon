# OmniCare HealthSync: Autonomous Omnichannel Healthcare Agent

[![AWS Communication Developer Services](https://img.shields.io/badge/AWS%20CDS-EUM%20%7C%20WhatsApp%20%7C%20SES-FF9900?logo=amazon-aws)](https://aws.amazon.com)
[![Amazon Bedrock AgentCore](https://img.shields.io/badge/Amazon%20Bedrock-AgentCore%20%7C%20Claude%203.5-232F3E?logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Devpost Hackathon](https://img.shields.io/badge/Devpost-AWS%20CDS%20Agentic%20AI%20Hackathon-0052CC)](https://aws-cds-partner.devpost.com)

> **Autonomous Clinical Intake, Prescription Triage, and Multi-Channel Handoff built on AWS Communication Developer Services (CDS) and Amazon Bedrock AgentCore.**

---

## 🌟 Executive Summary & Problem Solved

Traditional healthcare outreach relies on disjointed, rigid communication:
- **One-way SMS notifications** that patients ignore or cannot reply to.
- **Isolated email portals** that introduce days of administrative delay.
- **Fragmented customer identity**, forcing patients to repeat their clinical symptoms across channels.

**OmniCare HealthSync** breaks these silos. By coupling **Amazon Bedrock AgentCore** with **AWS Communication Developer Services (CDS)**, OmniCare delivers an autonomous, unified conversational continuum:
1. **Intake on WhatsApp (AWS EUM Social):** Patients upload prescription photos or text acute symptoms. Bedrock Vision extracts dosages and medication entities instantly.
2. **Context-Preserved Handoff to RCS (AWS EUM):** Instead of clunky text typing, the agent dispatches an interactive **RCS Rich Card** with real-time pharmacy inventory and one-tap suggestion chips for instant pick-up reservation.
3. **Discharge & Compliance via Amazon SES:** The moment a slot is confirmed, the agent dispatches a DKIM-signed, clinical discharge summary email containing dosage tables and barcode check-in passes.
4. **Single-Pane Unified Memory (Amazon DynamoDB):** Conversational context is maintained across phone numbers, WhatsApp JIDs, and email addresses.

---

## ⚡ Quick Start — Running in 60 Seconds

### Windows
```powershell
git clone https://github.com/monudevdil0301-ux/aws-hac-thon.git
cd aws-hac-thon
py -3 backend/server.py
# Open http://localhost:8080 in your browser
```

### macOS / Linux
```bash
git clone https://github.com/monudevdil0301-ux/aws-hac-thon.git
cd aws-hac-thon
python3 backend/server.py
# Open http://localhost:8080 in your browser
```

> No dependencies required for demo mode. `boto3` is optional — install it only to connect real AWS credentials.
> To install: `pip install boto3` (or `py -3 -m pip install boto3` on Windows)

### What you'll see in 60 seconds

| Time | What happens |
|------|-------------|
| **0s** | Browser opens to **Command Center** — live KPI counters, animated activity feed, channel stats |
| **5s** | Click **"Watch Live Agent"** → Screen 3 auto-runs all 6 Bedrock AgentCore steps with real tool JSON |
| **20s** | Click **"Unified Inbox"** → find Alex Rivera → tap **CVS Oak St** chip → SES email appears in thread |
| **35s** | Click **"Patient Experience"** → hit **"Play Journey"** → tap phone chip → RCS → SES email shown |
| **50s** | Click **"⚡ API Demo"** in topbar → backend runs real orchestration → toast shows actual run ID |
| **60s** | Click **"Priya Joshi"** in inbox → human approval modal → Approve & Send WhatsApp refund message |

### Live API Endpoints
```
GET  http://localhost:8080/           # Full 4-screen dashboard
GET  http://localhost:8080/api/state  # Patient session state (JSON)
GET  http://localhost:8080/api/inbox  # Conversation list (JSON)
POST http://localhost:8080/api/webhook         # Inbound message (WhatsApp / RCS / SMS)
POST http://localhost:8080/api/demo/run        # Full Bedrock AgentCore execution trace
POST http://localhost:8080/api/approve         # Human approval action
```

### Test the backend right now
```bash
# Trigger a full prescription refill flow
curl -X POST http://localhost:8080/api/demo/run \
  -H "Content-Type: application/json" \
  -d '{"scenario":"prescription_refill"}'
```

---

## 🏗️ Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                           OmniCare HealthSync Architecture                        |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Patient Touchpoints ]                                                          |
|       |                                                                           |
|       +---> AWS EUM Social (WhatsApp)   --> Inbound Rx photos & symptom intake    |
|       |                                                                           |
|       +---> AWS EUM (RCS & SMS Fallback)--> Interactive Pick-up Cards & Chips     |
|       |                                                                           |
|       +---> Amazon SES (Email)         --> Formatted Clinical Packet & QR Pass    |
|                                                                                   |
|                                   |                                               |
|                                   v                                               |
|  [ Ingestion & Event Gateway ]                                                    |
|       Amazon API Gateway HTTP API  -->  AWS Lambda Omnichannel Router             |
|                                                  |                                |
|                                   +--------------+                                |
|                                   |                                               |
|                                   v                                               |
|  [ Agentic AI Core ]                                                              |
|       +--------------------------------------------------------------------+      |
|       | Amazon Bedrock AgentCore (Orchestrator)                            |      |
|       |   - Foundation Model: Anthropic Claude 3.5 Sonnet / AWS Nova Pro   |      |
|       |   - Bedrock Guardrails: Clinical Safety & PII Redaction            |      |
|       +--------------------------------------------------------------------+      |
|                 |                         |                         |             |
|                 v                         v                         v             |
|       [Action Group: Vision]    [Action Group: Geo/Slots]   [Action Group: Dispatch]|
|                 |                         |                         |             |
|                 +-------------------------+-------------------------+             |
|                                           |                                       |
|                                           v                                       |
|  [ Unified Memory & State Store ]                                                 |
|       Amazon DynamoDB Table (OmniCare-Sessions)                                   |
|       - Single-Table Design indexing: E.164 Phone <-> WhatsApp JID <-> Email       |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 🚀 Key AWS CDS Features Demonstrated

| AWS Service | Role in OmniCare | Code Implementation |
| :--- | :--- | :--- |
| **AWS End User Messaging Social (WhatsApp)** | Initial patient engagement, inbound media upload, and interactive quick-reply buttons. | [`backend/services/cds_messaging.py`](backend/services/cds_messaging.py) |
| **AWS End User Messaging (RCS & SMS)** | Interactive Rich Cards, Carousels, and one-tap Suggestion Chips with carrier fallback. | [`backend/services/cds_messaging.py`](backend/services/cds_messaging.py) |
| **Amazon Simple Email Service (SES v2)** | Automated generation and transmission of responsive clinical care instructions. | [`backend/services/cds_messaging.py`](backend/services/cds_messaging.py) |
| **Amazon Bedrock AgentCore** | Autonomous multi-turn reasoning, Action Groups, and OpenAPI-driven tool execution. | [`backend/agent/orchestrator.py`](backend/agent/orchestrator.py) |

---

## ⚡ Quick Start & Reproduction Instructions

### 1. Prerequisites
- Python 3.9+
- AWS CLI configured (optional for simulation mode; required for live cloud deployment)

### 2. Run the Interactive Omnichannel Cockpit Locally
Clone the repository and run:
```bash
# Navigate to project directory
cd omnicare-healthsync

# Start the interactive visual simulator and webhook API
python backend/server.py
```
Open your browser to: **`http://localhost:8080`**

### 3. Running in 100% Live AWS Cloud Mode
OmniCare HealthSync uses the native AWS Python SDK (`boto3`) to communicate directly with AWS APIs. To run in live cloud dispatch mode:

1. **Set your AWS credentials and region:**
   ```powershell
   # Windows PowerShell
   $env:AWS_ACCESS_KEY_ID="your-access-key-id"
   $env:AWS_SECRET_ACCESS_KEY="your-secret-access-key"
   $env:AWS_REGION="us-east-1"
   $env:SIMULATION_MODE="false"
   $env:SES_SENDER_EMAIL="verified-email@yourdomain.com"
   $env:AWS_EUM_WHATSAPP_PHONE_ID="your-whatsapp-phone-id"
   ```
   ```bash
   # macOS / Linux
   export AWS_ACCESS_KEY_ID="your-access-key-id"
   export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
   export AWS_REGION="us-east-1"
   export SIMULATION_MODE="false"
   export SES_SENDER_EMAIL="verified-email@yourdomain.com"
   export AWS_EUM_WHATSAPP_PHONE_ID="your-whatsapp-phone-id"
   ```

2. **Launch the server:**
   ```bash
   py -3 backend/server.py   # Windows
   python3 backend/server.py  # macOS / Linux
   ```

3. **Verify Connected Services:**
   Click the **`AWS CDS Connected`** status pill in the top right of the dashboard, or call:
   ```bash
   curl http://localhost:8080/api/status
   ```
   This returns live client connectivity across:
   - **AWS End User Messaging Social** (`socialmessaging`)
   - **AWS End User Messaging RCS / SMS** (`pinpoint-sms-voice-v2`)
   - **Amazon Simple Email Service** (`sesv2`)
   - **Amazon Bedrock AgentCore & Runtime** (`bedrock-runtime`)
   - **Amazon DynamoDB** (`dynamodb`)

---

## 📦 Cloud Deployment (AWS CloudFormation)

To deploy the production infrastructure to your AWS account:

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation.yaml \
  --stack-name OmniCare-HealthSync-Stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides Environment=prod SESVerifiedEmail=care@yourdomain.com
```

---

## 💼 AWS Partner Central & GTM Packaging

### AWS Marketplace Readiness
OmniCare HealthSync is packaged as an enterprise-ready SaaS accelerator for Healthcare & Life Sciences (HLS) partners:
- **Target Buyers:** Pharmacy Chains, Integrated Delivery Networks (IDNs), and Telehealth Providers.
- **Estimated ROI:** 48% reduction in prescription abandonment; 70% decrease in call center triage volume.
- **Listing Model:** AWS Marketplace AMI / Serverless SaaS contract with per-interaction billing.

### Hackathon Partner Submission Details
- **ACE Marketing Campaign Code:** `AWS CDS Agentic AI Hackathon -Sept. 2026`
- **Partner Opportunity Name:** `OmniCare HealthSync - Omnichannel Clinical Engagement`
