"""
OmniCare HealthSync - Interactive Omnichannel Server & Webhook API
Serves both live REST webhooks for AWS API Gateway / AWS CDS callbacks
AND a real-time web simulation cockpit for demonstrating the multi-channel workflow to judges.
"""

import os
import sys
import json

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from backend.services.cds_messaging import CDSMessagingService
from backend.db.session_store import SessionMemoryManager
from backend.agent.orchestrator import BedrockAgentOrchestrator

# Global singletons
cds_service = CDSMessagingService(simulation_mode=True)
session_store = SessionMemoryManager(simulation_mode=True)
orchestrator = BedrockAgentOrchestrator(session_store, cds_service)

HTML_COCKPIT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OmniCare HealthSync &bull; AWS CDS & Bedrock AgentCore</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #090d16;
            --surface: #111827;
            --surface-card: #1f2937;
            --border: #374151;
            --aws-orange: #ff9900;
            --aws-blue: #0073bb;
            --accent-green: #10b981;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 16px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .badge-aws {
            background: linear-gradient(135deg, #ff9900 0%, #d97706 100%);
            color: #000;
            font-weight: 800;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-live {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.3);
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 9999px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .pulse {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        .main-layout {
            display: grid;
            grid-template-columns: 360px 360px 420px 1fr;
            gap: 20px;
            padding: 24px;
            flex: 1;
            overflow-x: auto;
        }

        /* Phone & Device Frames */
        .device-col {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        }
        .device-header {
            padding: 14px 18px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #162032;
        }
        .device-title {
            font-size: 13px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .screen {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 16px;
            gap: 12px;
            overflow-y: auto;
            max-height: 580px;
            min-height: 480px;
            background: #0d131f;
        }
        .msg {
            max-width: 82%;
            padding: 10px 14px;
            border-radius: 14px;
            font-size: 13.5px;
            line-height: 1.45;
            word-wrap: break-word;
        }
        .msg-in {
            background: #1f293d;
            color: #f3f4f6;
            align-self: flex-start;
            border-bottom-left-radius: 2px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .msg-out {
            background: #0284c7;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }
        .msg-wa-out {
            background: #005c4b;
            color: #e9edef;
            align-self: flex-end;
        }
        .msg-wa-in {
            background: #202c33;
            color: #d1d7db;
            align-self: flex-start;
        }

        /* RCS Card */
        .rcs-card {
            background: #1e293b;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #334155;
            margin-top: 6px;
            align-self: flex-start;
            width: 95%;
        }
        .rcs-card img {
            width: 100%;
            height: 120px;
            object-fit: cover;
        }
        .rcs-card-body {
            padding: 12px;
        }
        .rcs-card-title {
            font-size: 14px;
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 4px;
        }
        .rcs-card-desc {
            font-size: 12.5px;
            color: #94a3b8;
            margin-bottom: 12px;
        }
        .rcs-chip-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .rcs-chip {
            background: #0f172a;
            border: 1px solid #38bdf8;
            color: #38bdf8;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .rcs-chip:hover {
            background: #38bdf8;
            color: #0f172a;
        }

        /* Action Input bar */
        .device-input-bar {
            padding: 12px;
            background: #111827;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 8px;
        }
        .device-input-bar input {
            flex: 1;
            background: #1f2937;
            border: 1px solid #374151;
            color: #fff;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 13px;
            outline: none;
        }
        .device-input-bar button {
            background: var(--aws-orange);
            color: #000;
            border: none;
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
        }

        /* Email Panel */
        .email-panel {
            background: #ffffff;
            color: #0f172a;
            border-radius: 8px;
            padding: 14px;
            font-size: 13px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* Telemetry & Bedrock Reasoning Column */
        .telemetry-col {
            background: #0b1120;
            border: 1px solid #1e293b;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            padding: 18px;
        }
        .telemetry-header {
            font-size: 13px;
            font-weight: 700;
            color: #f59e0b;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .trace-box {
            flex: 1;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            background: #030712;
            border: 1px solid #1f2937;
            border-radius: 10px;
            padding: 14px;
            overflow-y: auto;
            color: #a7f3d0;
            line-height: 1.6;
            max-height: 580px;
        }
        .trace-entry {
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .trace-step {
            color: #60a5fa;
            font-weight: 700;
        }

        /* Quick Script Runner */
        .script-bar {
            background: #111827;
            border-top: 1px solid var(--border);
            padding: 14px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }
        .btn-scenario {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .btn-scenario:hover {
            background: #1d4ed8;
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <span class="badge-aws">AWS CDS Hackathon 2026</span>
            <h1 style="font-size: 18px; font-weight: 800;">OmniCare HealthSync</h1>
            <span style="font-size: 12px; color: var(--text-muted);">| Powered by Amazon Bedrock AgentCore</span>
        </div>
        <div style="display: flex; align-items: center; gap: 16px;">
            <span style="font-size: 12px; color: #94a3b8;">Patient: <strong>Alex Rivera</strong> (+1 415-555-2671)</span>
            <div class="badge-live">
                <div class="pulse"></div>
                AWS CDS Connected
            </div>
        </div>
    </header>

    <div class="main-layout">
        <!-- 1. WhatsApp Screen (AWS EUM Social) -->
        <div class="device-col" style="border-color: rgba(37, 211, 102, 0.4);">
            <div class="device-header" style="background: #064e3b;">
                <div class="device-title">
                    <span style="color: #25d366; font-size: 16px;">💬</span>
                    <span>WhatsApp (AWS EUM Social)</span>
                </div>
                <span style="font-size: 10px; background: #047857; color: #a7f3d0; padding: 2px 6px; border-radius: 4px; font-weight: 700;">Meta WhatsApp Prize</span>
            </div>
            <div class="screen" id="wa-screen">
                <div class="msg msg-wa-in">
                    👋 Welcome to OmniCare HealthSync.<br><br>
                    <strong>Meta WhatsApp Features Active:</strong><br>
                    • 📷 Prescription Photo OCR (Bedrock Vision)<br>
                    • 🎙️ Audio Voice Note Triage<br>
                    • 🔘 Interactive Quick-Reply Buttons
                </div>
            </div>
            
            <!-- Quick WhatsApp Meta Action Triggers -->
            <div style="background: #111e18; padding: 6px 10px; display: flex; gap: 6px; border-top: 1px solid #1f3d2f;">
                <button onclick="simulateWhatsAppPhoto()" style="flex: 1; background: #065f46; color: #6ee7b7; border: 1px solid #059669; padding: 6px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer;">
                    📷 Upload Rx Photo
                </button>
                <button onclick="simulateWhatsAppVoice()" style="flex: 1; background: #065f46; color: #6ee7b7; border: 1px solid #059669; padding: 6px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer;">
                    🎙️ Send Voice Note
                </button>
            </div>

            <div class="device-input-bar">
                <input type="text" id="wa-input" placeholder="Type message in WhatsApp...">
                <button onclick="sendWhatsApp()">Send</button>
            </div>
        </div>

        <!-- 2. RCS / SMS Screen (AWS EUM) -->
        <div class="device-col">
            <div class="device-header">
                <div class="device-title">
                    <span style="color: #38bdf8; font-size: 16px;">📱</span>
                    RCS Messages (AWS EUM)
                </div>
                <span style="font-size: 11px; color: #64748b;">Carrier Rich Card</span>
            </div>
            <div class="screen" id="rcs-screen">
                <div class="msg msg-in" style="font-size: 12px; color: #94a3b8;">
                    Encrypted RCS Session &bull; Carrier Fallback to SMS Active
                </div>
            </div>
            <div class="device-input-bar">
                <input type="text" id="rcs-input" placeholder="Reply to RCS...">
                <button onclick="sendRCS()">Send</button>
            </div>
        </div>

        <!-- 3. Clinical Email Inbox (Amazon SES) -->
        <div class="device-col" style="background: #0f172a;">
            <div class="device-header">
                <div class="device-title">
                    <span style="color: #f59e0b; font-size: 16px;">✉️</span>
                    SES Patient Inbox (Amazon SES)
                </div>
                <span style="font-size: 11px; color: #64748b;">TLS / DKIM Verified</span>
            </div>
            <div class="screen" id="email-screen" style="background: #1e293b;">
                <div style="text-align: center; color: #64748b; font-size: 13px; margin-top: 40px;">
                    Awaiting clinical discharge packet dispatch from Amazon SES...
                </div>
            </div>
            <div style="padding: 12px; font-size: 11px; color: #94a3b8; text-align: center; border-top: 1px solid var(--border);">
                Automated clinical summaries are dispatched via Amazon SES v2
            </div>
        </div>

        <!-- 4. AgentCore Brain & Telemetry -->
        <div class="telemetry-col">
            <div class="telemetry-header">
                <span>🧠 Bedrock AgentCore Telemetry</span>
                <span style="font-size: 11px; background: #1e293b; color: #cbd5e1; padding: 3px 8px; border-radius: 4px;">Claude 3.5 Sonnet</span>
            </div>
            <div class="trace-box" id="trace-box">
                // System Initialized.<br>
                // Listening to AWS CDS Webhooks (WhatsApp, RCS, SES).<br>
                // Click "Run Winning Hackathon Scenario" below for full multi-channel flow!
            </div>
        </div>
    </div>

    <!-- Winning Scenario Bar -->
    <div class="script-bar">
        <div>
            <strong style="color: #f59e0b;">Interactive Hackathon Demo Runner:</strong>
            <span style="color: #94a3b8; font-size: 13px; margin-left: 8px;">Trigger the end-to-end multi-channel patient handoff in one click</span>
        </div>
        <button class="btn-scenario" onclick="runWinningScenario()">
            ▶️ Run 1st-Prize Demo Flow (WhatsApp ➔ RCS ➔ SES)
        </button>
    </div>

    <script>
        function logTrace(step, thought) {
            const box = document.getElementById("trace-box");
            const entry = document.createElement("div");
            entry.className = "trace-entry";
            entry.innerHTML = `<span class="trace-step">[Bedrock AgentCore :: ${step}]</span><br>${thought}`;
            box.appendChild(entry);
            box.scrollTop = box.scrollHeight;
        }

        async function triggerBackend(channel, text, media) {
            try {
                const res = await fetch("/api/webhook", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ channel, sender: "+14155552671", text, media })
                });
                return await res.json();
            } catch (e) {
                console.error(e);
            }
        }

        async function sendWhatsApp() {
            const input = document.getElementById("wa-input");
            const val = input.value.trim();
            if (!val) return;
            input.value = "";

            const screen = document.getElementById("wa-screen");
            screen.innerHTML += `<div class="msg msg-wa-out">${val}</div>`;
            screen.scrollTop = screen.scrollHeight;

            const res = await triggerBackend("whatsapp", val, null);
            handleResponse(res);
        }

        async function sendRCS(postbackVal) {
            const input = document.getElementById("rcs-input");
            const val = postbackVal || input.value.trim();
            if (!val) return;
            if (!postbackVal) input.value = "";

            const screen = document.getElementById("rcs-screen");
            screen.innerHTML += `<div class="msg msg-out">${val}</div>`;
            screen.scrollTop = screen.scrollHeight;

            const res = await triggerBackend("rcs", val, null);
            handleResponse(res);
        }

        function handleResponse(res) {
            if (!res) return;
            if (res.reasoning_trace) {
                res.reasoning_trace.forEach(t => logTrace(t.step, t.thought));
            }
            refreshAudit();
        }

        async function refreshAudit() {
            const res = await fetch("/api/state");
            const data = await res.json();

            // Refresh WhatsApp
            const waScreen = document.getElementById("wa-screen");
            const rcsScreen = document.getElementById("rcs-screen");
            const emailScreen = document.getElementById("email-screen");

            waScreen.innerHTML = "";
            rcsScreen.innerHTML = "";

            data.conversation_history.forEach(m => {
                if (m.channel === "whatsapp") {
                    const cls = m.role === "user" ? "msg-wa-out" : "msg-wa-in";
                    waScreen.innerHTML += `<div class="msg ${cls}">${m.content}</div>`;
                } else if (m.channel === "rcs") {
                    if (m.role === "user") {
                        rcsScreen.innerHTML += `<div class="msg msg-out">${m.content}</div>`;
                    } else if (m.content.includes("Dispatched RCS Pharmacy Selection Card") || data.active_case.stage === "PHARMACY_SELECTION_PENDING") {
                        rcsScreen.innerHTML += `
                            <div class="rcs-card">
                                <img src="https://images.unsplash.com/photo-1586015555751-63bb77f4322a?auto=format&fit=crop&w=600&q=80" alt="Pharmacy">
                                <div class="rcs-card-body">
                                    <div class="rcs-card-title">📍 Nearest Pharmacy Pick-up Ready</div>
                                    <div class="rcs-card-desc">Amoxicillin 500mg is available nearby. Tap a slot to reserve instant pickup:</div>
                                    <div class="rcs-chip-group">
                                        <div class="rcs-chip" onclick="sendRCS('CVS Health (0.4 mi) - 2:30 PM')">CVS Health (0.4 mi) - 2:30 PM</div>
                                        <div class="rcs-chip" onclick="sendRCS('Walgreens (1.1 mi) - 3:00 PM')">Walgreens (1.1 mi) - 3:00 PM</div>
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        rcsScreen.innerHTML += `<div class="msg msg-in">${m.content}</div>`;
                    }
                }
            });

            // Update Email
            if (data.active_case.stage === "CONFIRMED_AND_DISCHARGED") {
                emailScreen.innerHTML = `
                    <div class="email-panel">
                        <div style="border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 10px;">
                            <div style="font-weight: 700; color: #0284c7; font-size: 14px;">OmniCare Prescription & Clinical Care Instructions</div>
                            <div style="font-size: 11px; color: #64748b;">From: care@omnicare.aws &bull; To: ${data.email}</div>
                        </div>
                        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 8px; border-radius: 6px; margin-bottom: 10px;">
                            <strong style="color: #166534;">Reservation Confirmed:</strong> ${data.active_case.preferred_pharmacy.name}<br>
                            <span style="font-size: 11px; color: #15803d;">Check-in Code: <code>${data.active_case.qr_token}</code></span>
                        </div>
                        <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                            <tr style="background: #f1f5f9;">
                                <th style="padding: 4px; text-align: left;">Medication</th>
                                <th style="padding: 4px; text-align: left;">Dosage</th>
                                <th style="padding: 4px; text-align: left;">Frequency</th>
                            </tr>
                            ${data.active_case.medications.map(m => `
                                <tr style="border-bottom: 1px solid #f1f5f9;">
                                    <td style="padding: 4px; font-weight: 600;">${m.medication}</td>
                                    <td style="padding: 4px;">${m.dosage}</td>
                                    <td style="padding: 4px; color: #2563eb;">${m.frequency}</td>
                                </tr>
                            `).join('')}
                        </table>
                    </div>
                `;
            }

            waScreen.scrollTop = waScreen.scrollHeight;
            rcsScreen.scrollTop = rcsScreen.scrollHeight;
        }

        async function simulateWhatsAppPhoto() {
            logTrace("MetaWhatsApp_Media", "Patient clicked 'Attach Image' on WhatsApp. Uploading Rx_Amoxicillin_500mg.jpg...");
            const waScreen = document.getElementById("wa-screen");
            waScreen.innerHTML += `
                <div class="msg msg-wa-out">
                    📷 <em>Image attached: Rx_Amoxicillin_500mg.jpg</em><br>
                    Please refill this prescription for my bronchitis.
                </div>
            `;
            waScreen.scrollTop = waScreen.scrollHeight;
            const res = await triggerBackend("whatsapp", "Uploaded Rx_Amoxicillin_500mg.jpg", { is_image: true });
            handleResponse(res);
        }

        async function simulateWhatsAppVoice() {
            logTrace("MetaWhatsApp_Audio", "Patient recorded 12-second WhatsApp voice note (audio/ogg). Uploading to AWS EUM Social...");
            const waScreen = document.getElementById("wa-screen");
            waScreen.innerHTML += `
                <div class="msg msg-wa-out" style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">▶️</span>
                    <div>
                        <div style="font-weight: 600; font-size: 12px;">Voice Note (0:12)</div>
                        <div style="font-size: 11px; opacity: 0.8;">"Persistent cough and wheezing..."</div>
                    </div>
                </div>
            `;
            waScreen.scrollTop = waScreen.scrollHeight;
            const res = await triggerBackend("whatsapp", "Audio note: Persistent cough and wheezing", { is_voice: true });
            handleResponse(res);
        }

        async function runWinningScenario() {
            logTrace("SimulationStarted", "Triggering inbound prescription intake on WhatsApp (AWS EUM Social)...");
            await simulateWhatsAppPhoto();

            // 2. Wait 2.5 seconds, then simulate patient tapping RCS chip
            setTimeout(async () => {
                logTrace("UserInteraction", "Patient received rich RCS card and tapped 'CVS Health (0.4 mi) - 2:30 PM'...");
                const step2 = await triggerBackend("rcs", "CVS Health (0.4 mi) - 2:30 PM", null);
                handleResponse(step2);
            }, 2500);
        }
    </script>
</body>
</html>
"""

class OmnichannelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        if url_parsed.path == "/" or url_parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_COCKPIT.encode("utf-8"))
        elif url_parsed.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            state = session_store.get_full_state("patient_alex_rivera")
            self.wfile.write(json.dumps(state).encode("utf-8"))
        elif url_parsed.path == "/api/audit":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(cds_service.dispatch_audit_trail).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)
        if url_parsed.path == "/api/webhook":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                channel = data.get("channel", "whatsapp")
                sender = data.get("sender", "+14155552671")
                text = data.get("text", "")
                media = data.get("media")
                
                result = orchestrator.handle_inbound_event(channel, sender, text, media)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port: int = 8080):
    server = HTTPServer(("0.0.0.0", port), OmnichannelHandler)
    print(f"OmniCare HealthSync Server listening on http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server(8080)
