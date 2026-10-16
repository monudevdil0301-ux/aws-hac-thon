# OmniCare HealthSync: Devpost Submission & Video Pitch Kit

## 1. Devpost Submission Fields

### Project Title
**OmniCare HealthSync: Autonomous Omnichannel Healthcare Agent on AWS CDS & Bedrock AgentCore**

### Elevator Pitch (One-sentence summary)
OmniCare HealthSync transforms patient care by connecting AWS End User Messaging (WhatsApp & RCS) and Amazon SES with Amazon Bedrock AgentCore into an autonomous, context-preserving clinical concierge.

---

### Inspiration
Customer engagement in healthcare is plagued by fragmented channels: critical alerts are lost in SMS silos, while patients struggle with confusing medication instructions. We took inspiration directly from the hackathon challenge: building a truly conversational, multi-channel agent where a patient can start an intake on WhatsApp with a photo of their prescription, seamlessly transition to an interactive RCS card to select their pharmacy pickup slot with one tap, and automatically receive clinical dosage guidelines via Amazon SES—without ever losing conversational state.

---

### What It Does
OmniCare HealthSync is an enterprise clinical communication agent:
1. **Intake on WhatsApp (AWS EUM Social):** Patients text symptoms or upload photos of their prescription. Amazon Bedrock Vision (Claude 3.5 Sonnet) extracts medication names, dosages, and refill parameters.
2. **Context-Preserved RCS Handoff (AWS EUM):** Instead of making patients type addresses, Bedrock AgentCore dispatches an interactive RCS Rich Card with nearby pharmacy pickup times and one-tap suggestion chips.
3. **Clinical Compliance via Amazon SES:** Once a reservation is confirmed, Amazon SES automatically dispatches a secure, styled clinical care packet featuring medication tables, safety precautions, and a check-in QR code pass.
4. **Unified Patient Memory (DynamoDB):** A single-table architecture unifies phone numbers, WhatsApp JIDs, and email addresses so the agent maintains persistent clinical context regardless of where the patient responds.

---

### How We Built It
- **AWS End User Messaging Social:** Integrated native WhatsApp messaging for intake, quick replies, and prescription image parsing.
- **AWS End User Messaging (RCS & SMS):** Built interactive Rich Cards and suggestion chips with automatic SMS fallback for older devices.
- **Amazon Simple Email Service (SES v2):** Designed responsive clinical summary templates with encrypted check-in tokens.
- **Amazon Bedrock AgentCore:** Orchestrated autonomous multi-step reasoning, Action Groups, and OpenAPI-defined clinical tools.
- **Amazon DynamoDB:** Implemented cross-channel session tracking and state machine synchronization.
- **Infrastructure as Code:** Built CloudFormation templates for one-click deployment.

---

### Challenges We Ran Into & How We Overcame Them
- **Telecom Provisioning Latency:** Securing 10DLC carrier approvals and WhatsApp Business Account (WABA) verification can take weeks. We developed a dual-mode engine: native AWS SDK clients (`boto3`) alongside an interactive Omnichannel Simulator Cockpit that enables live verification and webhook replay.
- **Cross-Channel Identity Linking:** Patients use different identifiers (phone on WhatsApp vs. email for medical packets). We resolved this using a DynamoDB single-table design that indexes multiple E.164 identities and emails to a single patient partition key.

---

### Accomplishments That We're Proud Of
- Complete execution of the hackathon prompt's vision: an end-to-end multi-channel loop transitioning across WhatsApp, RCS, and SES.
- Real-time agent reasoning telemetry showing every Bedrock tool invocation.
- Fully packaged for AWS Marketplace with a clear partner GTM trajectory.

---

### What's Next for OmniCare HealthSync
- Publishing OmniCare as an AWS Marketplace Consulting Offering for health systems.
- Integrating EHR standards (FHIR / HL7) via Amazon HealthLake.
- Expanding multi-language voice integration via Amazon Polly and AWS CDS Voice.

---

## 2. 3-Minute Demo Video Script & Storyboard

### [0:00 - 0:35] The Problem & Introduction
- **Visual:** Speaker on camera + title slide "OmniCare HealthSync: Powered by AWS CDS & Bedrock AgentCore".
- **Audio:** *"Healthcare communication is broken. Patients receive static SMS reminders they can't reply to, lose critical instructions in email portals, and repeat their history at every step. We built OmniCare HealthSync to deliver true agentic, omnichannel care using AWS Communication Developer Services."*

### [0:35 - 1:30] Live Demo Part 1: WhatsApp Intake & Bedrock Vision
- **Visual:** Screen recording showing the WhatsApp panel. Patient uploads prescription image. Bedrock Telemetry displays Claude 3.5 Sonnet extracting Amoxicillin 500mg.
- **Audio:** *"Here on WhatsApp powered by AWS End User Messaging Social, Alex uploads a photo of his prescription. Amazon Bedrock AgentCore analyzes the image with multimodal vision and verifies the dosage. Notice what happens next: instead of forcing Alex to type out pharmacy addresses, Bedrock decides that an interactive mobile card is a better user experience."*

### [1:30 - 2:15] Live Demo Part 2: RCS Handoff & One-Tap Reservation
- **Visual:** Screen switches to the RCS Messages panel. An interactive Rich Card appears with a picture of CVS, distance, and two suggestion chips: `[CVS Health (0.4 mi) - 2:30 PM]`. The user clicks the chip.
- **Audio:** *"Instantly, on RCS through AWS End User Messaging, Alex receives an interactive card with verified inventory at his local pharmacy. With a single tap, he confirms his 2:30 PM pickup slot. The Bedrock Agent locks the reservation and updates our DynamoDB omnichannel session state."*

### [2:15 - 2:45] Live Demo Part 3: Amazon SES Clinical Packet
- **Visual:** Screen transitions to the SES Inbox. The email arrives containing the styled clinical summary, complete dosage schedule, and QR pass code.
- **Audio:** *"Immediately, Amazon SES dispatches a formatted clinical discharge packet to Alex's email with clear dosage schedules, warnings, and his check-in pass. Three channels, zero repeated questions, complete clinical continuity."*

### [2:45 - 3:00] Conclusion & Partner Value
- **Visual:** Architecture diagram and AWS Marketplace listing mock-up.
- **Audio:** *"OmniCare HealthSync demonstrates the true power of AWS CDS combined with agentic AI—driving down prescription abandonment and scaling partner solutions on AWS. Thank you!"*

---

## 3. How to Create the ACE Opportunity ID (Partner Central)

1. Log into your **AWS Partner Central** account ([partnercentral.awspartner.com](https://partnercentral.awspartner.com/)).
2. Navigate to **Customer Engagement (ACE)** $\rightarrow$ **Opportunities** $\rightarrow$ **Create New Opportunity**.
3. Fill in the following:
   - **Customer Name:** `OmniCare HealthSync Demo` (or your pilot customer / internal practice name).
   - **Primary AWS Service:** `Amazon Bedrock` and `AWS End User Messaging (EUM)`.
   - **Expected Launch Date:** Any date within the current or next quarter.
   - **Marketing Campaign Code (CRITICAL):** Copy and paste exactly:
     `AWS CDS Agentic AI Hackathon -Sept. 2026`
4. Submit the opportunity.
5. Copy the generated **Opportunity ID** (format: `O-XXXXXXX` or numeric ID) and paste it into your Devpost submission form.
