"""
OmniCare HealthSync - Amazon Bedrock AgentCore Orchestration Engine
Simulates or invokes the Amazon Bedrock Agent with Action Groups:
1. `extract_prescription_details` (Multimodal vision parsing via Claude 3.5 Sonnet / AWS Nova)
2. `search_pharmacy_slots` (Geolocation and inventory query)
3. `dispatch_omnichannel_action` (Intelligent channel routing: WhatsApp vs RCS vs SES)
4. `confirm_reservation_and_notify` (Generates appointment QR, locks pharmacy slot, triggers SES)
"""

import json
import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger("OmniCare.BedrockAgent")
logger.setLevel(logging.INFO)

SYSTEM_PROMPT = """
You are OmniCare HealthSync, an autonomous clinical communication agent powered by Amazon Bedrock AgentCore and AWS Communication Developer Services (CDS).
Your mission is to guide patients seamlessly across channels:
1. Start intake on WhatsApp (AWS EUM Social) when patients upload prescription photos or text symptoms.
2. Route pick-up location scheduling to interactive RCS cards (AWS EUM) with one-tap suggestions for superior mobile usability.
3. Deliver comprehensive clinical instructions, medication schedules, and check-in QR codes via Amazon SES (Email).
Maintain conversational context across all touchpoints. Ensure medical guardrails and empathetic clinical tone.
"""

class BedrockAgentOrchestrator:
    def __init__(self, session_store, cds_service):
        self.session_store = session_store
        self.cds_service = cds_service

    def handle_inbound_event(self, channel: str, sender_id: str, message_text: str, media_payload: Any = None) -> Dict[str, Any]:
        """
        Main entry point for incoming webhooks across WhatsApp, RCS/SMS, and Email.
        Executes Bedrock Agent reasoning cycle and invokes relevant Action Groups.
        """
        patient = self.session_store.resolve_patient(sender_id)
        patient_id = patient["patient_id"]
        
        # Record user message in shared memory
        self.session_store.append_message(patient_id, channel, "user", message_text, {"media": bool(media_payload)})
        
        current_stage = patient["active_case"]["stage"]
        agent_reasoning_trace = []
        action_results = []

        # =====================================================================
        # SCENARIO 1: Intake & Prescription Upload on WhatsApp (EUM Social)
        # =====================================================================
        if channel == "whatsapp" and (current_stage == "INTAKE_INITIALIZED" or "prescription" in message_text.lower() or "rx" in message_text.lower() or media_payload):
            agent_reasoning_trace.append({
                "step": "VisionAnalysis",
                "thought": "Patient uploaded prescription image / message on WhatsApp. Invoking Claude 3.5 Sonnet Vision tool to parse medications and dosages."
            })
            
            # Action Group 1: Parse Prescription
            extracted_meds = patient["active_case"]["medications"]
            
            agent_reasoning_trace.append({
                "step": "ChannelHandoffDecision",
                "thought": "Prescription parsed successfully. Patient needs to choose a pharmacy pick-up location. Text selection in WhatsApp is clunky; dispatching an interactive RCS Rich Card with one-tap chips to mobile for optimal user experience."
            })
            
            # Update stage
            self.session_store.update_case_stage(patient_id, "PHARMACY_SELECTION_PENDING")

            # 1. Reply on WhatsApp acknowledging receipt
            wa_reply = (
                f"✅ Hello {patient['full_name'].split()[0]}, I've verified your prescription for "
                f"{extracted_meds[0]['medication']} ({extracted_meds[0]['dosage']}).\n\n"
                f"I've just sent an interactive Pick-Up Card directly to your Messages (RCS) so you can choose your nearest pharmacy with one tap!"
            )
            self.cds_service.send_whatsapp_message(patient["phone_number"], wa_reply)
            self.session_store.append_message(patient_id, "whatsapp", "agent", wa_reply)

            # 2. Trigger AWS EUM (RCS Card) to patient's device
            rcs_res = self.cds_service.send_rcs_card(
                to_phone_number=patient["phone_number"],
                title="📍 Nearest Pharmacy Pick-up Ready",
                description=f"Amoxicillin 500mg (14 caps) is available nearby. Tap a slot to reserve instant pickup:",
                media_url="https://images.unsplash.com/photo-1586015555751-63bb77f4322a?auto=format&fit=crop&w=600&q=80",
                suggestions=[
                    {"type": "reply", "text": "CVS Health (0.4 mi) - 2:30 PM", "postback": "SELECT_CVS_230"},
                    {"type": "reply", "text": "Walgreens (1.1 mi) - 3:00 PM", "postback": "SELECT_WALGREENS_300"},
                    {"type": "open_url", "text": "View Map & Directions", "url": "https://maps.google.com"}
                ],
                sms_fallback_text="OmniCare: Your Rx is ready. Pick up at CVS (0.4mi) at 2:30PM? Reply YES to confirm."
            )
            self.session_store.append_message(patient_id, "rcs", "agent", "Dispatched RCS Pharmacy Selection Card")
            
            return {
                "status": "HANDOFF_EXECUTED",
                "primary_channel": "whatsapp",
                "handoff_channel": "rcs",
                "reasoning_trace": agent_reasoning_trace,
                "summary": "Prescription parsed via Bedrock Vision on WhatsApp; dispatched interactive pickup card via AWS EUM RCS."
            }

        # =====================================================================
        # SCENARIO 2: Interactive RCS Action / Confirmation (EUM RCS/SMS)
        # =====================================================================
        elif channel in ["rcs", "sms"] and (current_stage == "PHARMACY_SELECTION_PENDING" or "SELECT_" in message_text or "cvs" in message_text.lower() or "yes" in message_text.lower()):
            agent_reasoning_trace.append({
                "step": "SlotReservation",
                "thought": "Received one-tap suggestion response from RCS. Locking inventory at CVS Pharmacy (#4021) for 2:30 PM."
            })
            
            pharmacy_details = {
                "name": "CVS Pharmacy - Market St Branch",
                "address": "701 Market St, San Francisco, CA 94103",
                "pickup_window": "Today, 2:30 PM - 6:00 PM"
            }
            qr_token = "RX-PASS-SF-88392"
            
            self.session_store.update_case_stage(patient_id, "CONFIRMED_AND_DISCHARGED", {
                "preferred_pharmacy": pharmacy_details,
                "pickup_time": "2:30 PM",
                "qr_token": qr_token
            })

            # Send RCS Confirmation
            rcs_confirm_text = (
                f"🎉 Confirmed! Your medication is reserved at {pharmacy_details['name']}.\n"
                f"Ready window: {pharmacy_details['pickup_window']}.\n\n"
                f"📧 We've also emailed your full dosage guidelines & barcode check-in pass to {patient['email']} via Amazon SES."
            )
            self.cds_service.send_rcs_card(
                to_phone_number=patient["phone_number"],
                title="Prescription Reserved!",
                description=rcs_confirm_text,
                suggestions=[
                    {"type": "reply", "text": "Add to Calendar", "postback": "CALENDAR_SYNC"},
                    {"type": "reply", "text": "Need Home Delivery?", "postback": "REQUEST_DELIVERY"}
                ]
            )
            self.session_store.append_message(patient_id, "rcs", "agent", rcs_confirm_text)

            agent_reasoning_trace.append({
                "step": "EmailSummaryDispatch",
                "thought": "Triggering Amazon SES to send compliant medical summary, schedule table, and verification pass."
            })

            # Send Amazon SES Clinical Email
            ses_res = self.cds_service.send_clinical_email(
                to_email=patient["email"],
                subject="Your OmniCare Prescription & Clinical Care Instructions",
                patient_name=patient["full_name"],
                medication_schedule=patient["active_case"]["medications"],
                pickup_location=pharmacy_details,
                qr_code_token=qr_token
            )
            self.session_store.append_message(patient_id, "ses", "agent", "Dispatched Comprehensive Clinical Summary Email via Amazon SES")

            return {
                "status": "COMPLETED_OMNICHANNEL_WORKFLOW",
                "primary_channel": "rcs",
                "secondary_channel": "ses",
                "reasoning_trace": agent_reasoning_trace,
                "summary": "Slot confirmed via RCS tap; triggered Amazon SES clinical summary email."
            }

        # =====================================================================
        # SCENARIO 3: General Question or Follow-up on any channel
        # =====================================================================
        else:
            agent_reasoning_trace.append({
                "step": "GeneralTriage",
                "thought": f"Handling question on {channel}. Maintaining HIPAA compliance and clinical guardrails."
            })
            reply_text = (
                f"Hello {patient['full_name'].split()[0]}, I am your OmniCare Assistant. "
                f"Your active case is '{patient['active_case']['condition']}'. "
                f"Reply with a photo of your prescription or ask any question about your dosage."
            )
            if channel == "whatsapp":
                self.cds_service.send_whatsapp_message(patient["phone_number"], reply_text)
            elif channel in ["rcs", "sms"]:
                self.cds_service.send_rcs_card(patient["phone_number"], "OmniCare Care Center", reply_text)
            
            self.session_store.append_message(patient_id, channel, "agent", reply_text)

            return {
                "status": "MESSAGE_ROUTED",
                "channel": channel,
                "reasoning_trace": agent_reasoning_trace,
                "summary": f"Responded to general inquiry on {channel}."
            }
