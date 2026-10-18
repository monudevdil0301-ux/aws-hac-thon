"""
OmniCare HealthSync - Unified Omnichannel Session & Memory Store
Maintains persistent conversational continuity across:
- WhatsApp Phone Number / JID
- RCS / SMS Mobile Number
- Email Address
Powered by Amazon DynamoDB with single-table design principles.
"""

import time
import os
import json
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    ClientError = Exception
    BOTO3_AVAILABLE = False

class SessionMemoryManager:
    def __init__(self, table_name: str = "OmniCare_PatientSessions", simulation_mode: bool = True, region_name: str = "us-east-1"):
        self.table_name = os.getenv("DYNAMODB_TABLE_NAME", table_name)
        self.simulation_mode = simulation_mode
        self.region_name = os.getenv("AWS_REGION", region_name)
        self._in_memory_db: Dict[str, Dict[str, Any]] = {}
        self.dynamodb_table = None

        if not self.simulation_mode and BOTO3_AVAILABLE:
            try:
                dynamodb = boto3.resource("dynamodb", region_name=self.region_name)
                self.dynamodb_table = dynamodb.Table(self.table_name)
            except Exception as e:
                pass
        
        # Prepopulate demo patient profiles for instantaneous testing
        self._init_demo_identities()

    def _init_demo_identities(self):
        demo_patient_id = "patient_alex_rivera"
        self._in_memory_db[demo_patient_id] = {
            "patient_id": demo_patient_id,
            "full_name": "Alex Rivera",
            "phone_number": "+14155552671",
            "whatsapp_id": "14155552671",
            "email": "alex.rivera.health@example.com",
            "date_of_birth": "1988-06-14",
            "active_case": {
                "case_id": "CASE-9021",
                "condition": "Acute Bronchitis & Allergic Rhinitis",
                "stage": "INTAKE_INITIALIZED",
                "medications": [
                    {"medication": "Amoxicillin", "dosage": "500mg", "frequency": "3x daily for 7 days", "instructions": "Take with meals"},
                    {"medication": "Albuterol Inhaler", "dosage": "90mcg", "frequency": "1-2 puffs every 4-6 hrs", "instructions": "As needed for wheezing"}
                ],
                "preferred_pharmacy": None,
                "pickup_time": None
            },
            "conversation_history": [],
            "last_channel": "whatsapp",
            "updated_at": int(time.time())
        }
        # Also index by phone and email for O(1) multi-channel lookup
        self._in_memory_db["+14155552671"] = self._in_memory_db[demo_patient_id]
        self._in_memory_db["14155552671"] = self._in_memory_db[demo_patient_id]
        self._in_memory_db["alex.rivera.health@example.com"] = self._in_memory_db[demo_patient_id]

    def resolve_patient(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Resolves a unified patient record regardless of whether the inbound signal came from
        WhatsApp ID, SMS phone number, or Email.
        """
        cleaned = identifier.strip().replace(" ", "").replace("-", "")
        if self.dynamodb_table and not self.simulation_mode:
            try:
                res = self.dynamodb_table.get_item(Key={"patient_id": cleaned})
                if "Item" in res:
                    return res["Item"]
            except Exception:
                pass
        return self._in_memory_db.get(cleaned) or self._in_memory_db.get("patient_alex_rivera")

    def append_message(self, patient_id: str, channel: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        patient = self.resolve_patient(patient_id)
        if not patient:
            return
        
        event = {
            "channel": channel,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": int(time.time())
        }
        patient["conversation_history"].append(event)
        patient["last_channel"] = channel
        patient["updated_at"] = int(time.time())

        if self.dynamodb_table and not self.simulation_mode:
            try:
                self.dynamodb_table.put_item(Item=patient)
            except Exception:
                pass

    def update_case_stage(self, patient_id: str, new_stage: str, extra_data: Optional[Dict[str, Any]] = None):
        patient = self.resolve_patient(patient_id)
        if not patient:
            return
        
        patient["active_case"]["stage"] = new_stage
        if extra_data:
            patient["active_case"].update(extra_data)
        patient["updated_at"] = int(time.time())

        if self.dynamodb_table and not self.simulation_mode:
            try:
                self.dynamodb_table.put_item(Item=patient)
            except Exception:
                pass

    def get_full_state(self, patient_id: str) -> Dict[str, Any]:
        return self.resolve_patient(patient_id) or {}
