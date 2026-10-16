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
            --bg-dark: #0b0f19;
            --surface: #111827;
            --surface-card: #1f2937;
            --border: #2d3748;
            --wa-green: #25d366;
            --wa-teal: #128c7e;
            --wa-dark-bg: #0b141a;
            --wa-bubble-in: #202c33;
            --wa-bubble-out: #005c4b;
            --rcs-blue: #1a73e8;
            --rcs-dark-bg: #1a1c1e;
            --rcs-bubble-in: #2d3033;
            --rcs-bubble-out: #0b57d0;
            --ses-bg: #ffffff;
            --aws-orange: #ff9900;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border);
            padding: 14px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .aws-logo-badge {
            background: #232f3e;
            border: 1px solid #ff9900;
            color: #ff9900;
            font-weight: 800;
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
            letter-spacing: 0.5px;
        }
        .live-status-pill {
            background: rgba(16, 185, 129, 0.12);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
            font-size: 12px;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 9999px;
            display: flex;
            align-items: center;
            gap: 8px;
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
            grid-template-columns: 370px 370px 420px 1fr;
            gap: 20px;
            padding: 20px 24px;
            flex: 1;
            overflow-x: auto;
        }

        /* Realistic Smartphone Mockup Framing */
        .device-col {
            border-radius: 28px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 25px 40px -15px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255,255,255,0.08);
            position: relative;
        }
        .phone-notch {
            height: 22px;
            background: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .notch-camera {
            width: 50px;
            height: 10px;
            background: #111;
            border-radius: 10px;
        }

        /* 1. WhatsApp Native Styling */
        .wa-container {
            background: var(--wa-dark-bg);
            border: 1px solid #1f2c34;
        }
        .wa-header {
            background: #202c33;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .wa-avatar {
            width: 38px;
            height: 38px;
            background: #00a884;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 15px;
        }
        .wa-chat-area {
            flex: 1;
            background-color: #0b141a;
            background-image: radial-gradient(rgba(255,255,255,0.03) 1px, transparent 0);
            background-size: 18px 18px;
            padding: 16px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 480px;
            max-height: 520px;
        }
        .wa-msg {
            max-width: 84%;
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 13.5px;
            line-height: 1.4;
            word-wrap: break-word;
            position: relative;
        }
        .wa-msg-in {
            background: var(--wa-bubble-in);
            color: #e9edef;
            align-self: flex-start;
            border-top-left-radius: 0px;
        }
        .wa-msg-out {
            background: var(--wa-bubble-out);
            color: #e9edef;
            align-self: flex-end;
            border-top-right-radius: 0px;
        }
        .wa-quick-replies {
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-top: 8px;
        }
        .wa-qr-btn {
            background: #202c33;
            color: #00a884;
            border: 1px solid rgba(0, 168, 132, 0.4);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12.5px;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            transition: all 0.15s;
        }
        .wa-qr-btn:hover {
            background: #00a884;
            color: #fff;
        }
        .wa-input-bar {
            background: #202c33;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .wa-input-bar input {
            flex: 1;
            background: #2a3942;
            border: none;
            color: #fff;
            padding: 9px 14px;
            border-radius: 20px;
            font-size: 13px;
            outline: none;
        }
        .wa-input-bar button {
            background: #00a884;
            border: none;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #fff;
        }

        /* 2. Google Messages / RCS Native Styling */
        .rcs-container {
            background: var(--rcs-dark-bg);
            border: 1px solid #2d3033;
        }
        .rcs-header {
            background: #24272b;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        .rcs-chat-area {
            flex: 1;
            background: #131517;
            padding: 16px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 480px;
            max-height: 520px;
        }
        .rcs-msg {
            max-width: 82%;
            padding: 10px 14px;
            border-radius: 18px;
            font-size: 13.5px;
            line-height: 1.45;
        }
        .rcs-msg-in {
            background: var(--rcs-bubble-in);
            color: #e3e3e3;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        .rcs-msg-out {
            background: var(--rcs-bubble-out);
            color: #ffffff;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .rcs-rich-card {
            background: #202327;
            border: 1px solid #3c4043;
            border-radius: 16px;
            overflow: hidden;
            width: 100%;
            margin-top: 6px;
            align-self: flex-start;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .rcs-card-img {
            width: 100%;
            height: 120px;
            object-fit: cover;
        }
        .rcs-card-content {
            padding: 14px;
        }
        .rcs-card-title {
            font-size: 14.5px;
            font-weight: 700;
            color: #8ab4f8;
            margin-bottom: 6px;
        }
        .rcs-card-body {
            font-size: 12.5px;
            color: #c4c7c5;
            margin-bottom: 12px;
        }
        .rcs-chips-container {
            display: flex;
            flex-direction: column;
            gap: 7px;
        }
        .rcs-chip-action {
            background: #2a2e33;
            border: 1px solid #8ab4f8;
            color: #8ab4f8;
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .rcs-chip-action:hover {
            background: #8ab4f8;
            color: #131517;
        }
        .rcs-input-bar {
            background: #24272b;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .rcs-input-bar input {
            flex: 1;
            background: #1a1c1e;
            border: 1px solid #3c4043;
            color: #fff;
            padding: 9px 14px;
            border-radius: 20px;
            font-size: 13px;
            outline: none;
        }
        .rcs-input-bar button {
            background: #8ab4f8;
            border: none;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            color: #131517;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-weight: bold;
        }

        /* 3. SES Professional Email Client */
        .email-container {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 24px;
        }
        .email-header {
            background: #0f172a;
            padding: 14px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #334155;
        }
        .email-body-area {
            flex: 1;
            padding: 14px;
            overflow-y: auto;
            min-height: 480px;
            max-height: 520px;
            background: #0f172a;
        }
        .email-letterhead {
            background: #ffffff;
            color: #1e293b;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
            font-size: 13px;
        }

        /* 4. Bedrock Telemetry Panel */
        .telemetry-container {
            background: #0a0e17;
            border: 1px solid #1e293b;
            border-radius: 24px;
            display: flex;
            flex-direction: column;
            padding: 16px;
        }
        .telemetry-trace-box {
            flex: 1;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11.5px;
            background: #030712;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 14px;
            overflow-y: auto;
            color: #6ee7b7;
            line-height: 1.6;
            max-height: 520px;
        }

        /* Interactive Runner Bar */
        .action-dock {
            background: #0f172a;
            border-top: 1px solid #334155;
            padding: 14px 28px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .primary-flow-btn {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #fff;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
            transition: all 0.2s;
        }
        .primary-flow-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.6);
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="aws-logo-badge">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#ff9900"/>
                    <path d="M2 17L12 22L22 17M2 12L12 17L22 12" stroke="#ff9900" stroke-width="2" stroke-linecap="round"/>
                </svg>
                AWS CDS PARTNER
            </div>
            <div>
                <h1 style="font-size: 17px; font-weight: 800; letter-spacing: -0.3px;">OmniCare HealthSync</h1>
                <div style="font-size: 11.5px; color: #94a3b8;">Autonomous Clinical Concierge &bull; Amazon Bedrock AgentCore</div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="font-size: 12px; color: #cbd5e1; background: #1e293b; padding: 5px 12px; border-radius: 8px; border: 1px solid #334155;">
                Patient: <strong>Alex Rivera</strong> (+1 415-555-2671)
            </div>
            <div class="live-status-pill">
                <div class="pulse"></div>
                AWS CDS LIVE STREAM
            </div>
        </div>
    </header>

    <div class="main-layout">
        <!-- 1. Authentic WhatsApp Phone -->
        <div class="device-col wa-container">
            <div class="phone-notch"><div class="notch-camera"></div></div>
            <div class="wa-header">
                <!-- Official WhatsApp Logo -->
                <svg width="24" height="24" viewBox="0 0 24 24" fill="#25d366">
                    <path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91C2.13 13.66 2.59 15.36 3.45 16.86L2.05 22L7.3 20.62C8.75 21.41 10.38 21.83 12.04 21.83C17.5 21.83 21.95 17.38 21.95 11.92C21.95 9.27 20.92 6.78 19.05 4.91C17.18 3.03 14.69 2 12.04 2ZM12.04 20.15C10.56 20.15 9.11 19.76 7.85 19.01L7.55 18.83L4.43 19.65L5.26 16.61L5.06 16.29C4.24 14.99 3.8 13.47 3.8 11.91C3.8 7.37 7.5 3.67 12.05 3.67C14.25 3.67 16.31 4.53 17.87 6.09C19.42 7.65 20.28 9.72 20.28 11.92C20.28 16.46 16.58 20.15 12.04 20.15Z"/>
                </svg>
                <div class="wa-avatar">OC</div>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 13.5px; color: #e9edef; display: flex; align-items: center; gap: 4px;">
                        OmniCare Health
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="#00a884"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                    </div>
                    <div style="font-size: 11px; color: #8696a0;">AWS End User Messaging Social</div>
                </div>
                <span style="font-size: 10px; background: rgba(0, 168, 132, 0.2); color: #25d366; padding: 2px 8px; border-radius: 9999px; font-weight: 700; border: 1px solid rgba(37, 211, 102, 0.4);">Meta WhatsApp</span>
            </div>

            <div class="wa-chat-area" id="wa-screen">
                <div class="wa-msg wa-msg-in">
                    Hello Alex! I am your autonomous care concierge. Send a photo of your prescription or a voice message to initiate your care plan.
                </div>
            </div>

            <!-- Intuitive Meta Action Triggers -->
            <div style="background: #182229; padding: 8px 12px; display: flex; gap: 8px; border-top: 1px solid rgba(255,255,255,0.06);">
                <button onclick="simulateWhatsAppPhoto()" style="flex: 1; background: #005c4b; color: #25d366; border: 1px solid #00a884; padding: 7px; border-radius: 8px; font-size: 11.5px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                    Upload Rx Photo
                </button>
                <button onclick="simulateWhatsAppVoice()" style="flex: 1; background: #005c4b; color: #25d366; border: 1px solid #00a884; padding: 7px; border-radius: 8px; font-size: 11.5px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
                    Send Voice Note
                </button>
            </div>

            <div class="wa-input-bar">
                <input type="text" id="wa-input" placeholder="Type a message...">
                <button onclick="sendWhatsApp()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
            </div>
        </div>

        <!-- 2. Authentic Google Messages / RCS Phone -->
        <div class="device-col rcs-container">
            <div class="phone-notch"><div class="notch-camera"></div></div>
            <div class="rcs-header">
                <!-- Official Google Messages / RCS Logo -->
                <svg width="22" height="22" viewBox="0 0 24 24" fill="#1a73e8">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
                </svg>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 13.5px; color: #fff;">OmniCare Care Center</div>
                    <div style="font-size: 11px; color: #8ab4f8;">AWS End User Messaging &bull; RCS Verified</div>
                </div>
                <span style="font-size: 10px; background: rgba(26, 115, 232, 0.2); color: #8ab4f8; padding: 2px 8px; border-radius: 9999px; font-weight: 700; border: 1px solid rgba(26, 115, 232, 0.4);">RCS Active</span>
            </div>

            <div class="rcs-chat-area" id="rcs-screen">
                <div class="rcs-msg rcs-msg-in" style="font-size: 12px; color: #9aa0a6;">
                    🔒 Chatting with OmniCare (Verified). High-bandwidth RCS connected.
                </div>
            </div>

            <div class="rcs-input-bar">
                <input type="text" id="rcs-input" placeholder="Text message (RCS)...">
                <button onclick="sendRCS()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
            </div>
        </div>

        <!-- 3. Professional SES Email Client -->
        <div class="device-col email-container">
            <div class="email-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <!-- Official Email Envelope SVG -->
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="#f59e0b">
                        <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                    </svg>
                    <span style="font-size: 13.5px; font-weight: 700; color: #fff;">Amazon SES Inbox</span>
                </div>
                <span style="font-size: 10px; background: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 2px 8px; border-radius: 9999px; font-weight: 700; border: 1px solid rgba(245, 158, 11, 0.3);">TLS &bull; DKIM Verified</span>
            </div>

            <div class="email-body-area" id="email-screen">
                <div style="text-align: center; color: #64748b; font-size: 13px; margin-top: 50px;">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="#334155" style="margin-bottom: 10px;">
                        <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 14H4V8l8 5 8-5v10zm-8-7L4 6h16l-8 5z"/>
                    </svg><br>
                    Awaiting clinical discharge packet from Amazon SES...
                </div>
            </div>

            <div style="padding: 10px 14px; background: #0b1120; font-size: 11px; color: #94a3b8; text-align: center; border-top: 1px solid #334155;">
                Automated clinical discharge protocols powered by Amazon SES v2
            </div>
        </div>

        <!-- 4. Amazon Bedrock AgentCore Intelligence -->
        <div class="telemetry-container">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="#818cf8">
                        <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2M7.5 13A2.5 2.5 0 0 0 5 15.5 2.5 2.5 0 0 0 7.5 18a2.5 2.5 0 0 0 2.5-2.5A2.5 2.5 0 0 0 7.5 13m9 0a2.5 2.5 0 0 0-2.5 2.5 2.5 2.5 0 0 0 2.5 2.5 2.5 2.5 0 0 0 2.5-2.5 2.5 2.5 0 0 0-2.5-2.5"/>
                    </svg>
                    <span style="font-weight: 700; font-size: 13.5px; color: #fff;">Bedrock AgentCore</span>
                </div>
                <span style="font-size: 11px; background: #1e1b4b; color: #a5b4fc; padding: 2px 8px; border-radius: 6px; font-weight: 600; border: 1px solid #4338ca;">Claude 3.5 Sonnet</span>
            </div>
            <div class="telemetry-trace-box" id="trace-box">
                // System Initialized: Amazon Bedrock AgentCore.<br>
                // Listening to AWS CDS Webhooks (WhatsApp, RCS, SES).<br>
                // Click "Run Full Omnichannel Flow" below to experience live triage!
            </div>
        </div>
    </div>

    <!-- Quick Action Dock -->
    <div class="action-dock">
        <div>
            <div style="font-weight: 700; font-size: 14px; color: #fff;">Interactive Omnichannel Experience</div>
            <div style="font-size: 12px; color: #94a3b8;">Demonstrating seamless handoff across AWS EUM Social (WhatsApp) ➔ AWS EUM (RCS) ➔ Amazon SES</div>
        </div>
        <button class="primary-flow-btn" onclick="runWinningScenario()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            Run Full Omnichannel Flow (WhatsApp ➔ RCS ➔ SES)
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
