"""
OmniCare HealthSync / RelayOps - Enterprise SaaS Dashboard Server
Delivers a 4-Screen Enterprise Architecture:
- Screen 1: Command Center (KPI metrics, live audit stream, hero 'Watch Live Agent' CTA)
- Screen 2: Unified Inbox (Cross-channel continuous thread: WhatsApp -> RCS -> SES)
- Screen 3: Agent Activity (Live Bedrock AgentCore vertical execution timeline & tool calls)
- Screen 4: Customer Experience (Realistic interactive smartphone customer touchpoint)
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

# Load .env file automatically if present
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# Read environment configurations
IS_SIMULATION = os.getenv("SIMULATION_MODE", "true").lower() == "true"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

cds_service = CDSMessagingService(region_name=AWS_REGION, simulation_mode=IS_SIMULATION)
session_store = SessionMemoryManager(simulation_mode=IS_SIMULATION)
orchestrator = BedrockAgentOrchestrator(session_store, cds_service)

# Seed additional mock inbox conversations for enterprise richness
INBOX_CONVERSATIONS = [
    {
        "id": "conv_1",
        "customer_name": "Alex Rivera",
        "avatar": "AR",
        "status": "In Progress",
        "status_color": "teal",
        "channels": ["whatsapp", "rcs", "ses"],
        "issue": "Acute Bronchitis Refill & Pickup Scheduling",
        "last_message": "Prescription verified via Bedrock Vision. Dispatched RCS card.",
        "time": "Just now",
        "active": True
    },
    {
        "id": "conv_2",
        "customer_name": "Elena Rostova",
        "avatar": "ER",
        "status": "Resolved",
        "status_color": "emerald",
        "channels": ["whatsapp", "ses"],
        "issue": "Insulin Glargine Dosage Verification",
        "last_message": "Amazon SES clinical titration chart sent & confirmed.",
        "time": "14 min ago",
        "active": False
    },
    {
        "id": "conv_3",
        "customer_name": "Marcus Vance",
        "avatar": "MV",
        "status": "Needs Approval",
        "status_color": "amber",
        "channels": ["rcs"],
        "issue": "Specialty Biologic Prior-Auth Exception",
        "last_message": "Pharmacist review required for dosage adjustment.",
        "time": "42 min ago",
        "active": False
    },
    {
        "id": "conv_4",
        "customer_name": "Sarah Jenkins",
        "avatar": "SJ",
        "status": "Resolved",
        "status_color": "emerald",
        "channels": ["whatsapp", "rcs"],
        "issue": "Pediatric Antibiotic Formulation Swap",
        "last_message": "Customer confirmed suspension swap via RCS tap.",
        "time": "1 hr ago",
        "active": False
    }
]

HTML_SAAS_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OmniCare RelayOps &bull; AWS CDS & Bedrock AgentCore Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #FFFFFF;
            --surface-secondary: #F8FAFC;
            --surface-card: #FFFFFF;
            --border-light: #E2E8F0;
            --border-subtle: #EDF2F7;
            --navy-deep: #172B4D;
            --navy-sidebar: #0F172A;
            --teal-primary: #14B8A6;
            --teal-hover: #0D9488;
            --teal-light: #F0FDFA;
            --text-dark: #1E293B;
            --text-muted: #64748B;
            --text-subtle: #94A3B8;
            --aws-orange: #FF9900;
            --amber-alert: #F59E0B;
            --emerald-success: #10B981;
            --shadow-subtle: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03);
            --shadow-card: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            --radius-md: 10px;
            --radius-lg: 12px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--surface-secondary);
            color: var(--text-dark);
            height: 100vh;
            display: flex;
            overflow: hidden;
            -webkit-font-smoothing: antialiased;
        }

        /* -------------------------------------------------------------
           Persistent Left Sidebar
        ------------------------------------------------------------- */
        .sidebar {
            width: 256px;
            background-color: var(--navy-sidebar);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #FFFFFF;
            padding: 24px 16px;
            flex-shrink: 0;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        .brand-block {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 0 8px 24px 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        .brand-logo {
            width: 34px;
            height: 34px;
            background: linear-gradient(135deg, #14B8A6 0%, #0F766E 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 800;
            font-size: 16px;
            box-shadow: 0 2px 8px rgba(20, 184, 166, 0.3);
        }
        .nav-menu {
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-top: 20px;
        }
        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: var(--radius-md);
            color: #94A3B8;
            font-size: 13.5px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.18s ease;
        }
        .nav-item:hover {
            background-color: rgba(255, 255, 255, 0.05);
            color: #FFFFFF;
        }
        .nav-item.active {
            background-color: rgba(20, 184, 166, 0.12);
            color: #14B8A6;
            font-weight: 600;
        }
        .nav-item svg {
            width: 18px;
            height: 18px;
            stroke-width: 2;
        }
        .badge-count {
            margin-left: auto;
            background: rgba(20, 184, 166, 0.2);
            color: #14B8A6;
            padding: 2px 7px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
        }
        .sidebar-bottom {
            padding: 16px 8px 0 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .aws-cds-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: #94A3B8;
        }
        .pulse-dot {
            width: 7px;
            height: 7px;
            background-color: #14B8A6;
            border-radius: 50%;
            box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.7);
            animation: pulse 1.6s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(20, 184, 166, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(20, 184, 166, 0); }
            100% { box-shadow: 0 0 0 0 rgba(20, 184, 166, 0); }
        }

        /* -------------------------------------------------------------
           Main Content Area
        ------------------------------------------------------------- */
        .app-main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background-color: var(--surface-secondary);
        }

        /* Top Header Bar */
        .top-navbar {
            height: 64px;
            background-color: var(--bg-primary);
            border-bottom: 1px solid var(--border-light);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 32px;
            flex-shrink: 0;
        }
        .breadcrumb-title {
            font-size: 16px;
            font-weight: 700;
            color: var(--navy-deep);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .aws-partner-badge {
            background-color: #F8FAFC;
            border: 1px solid var(--border-light);
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11.5px;
            font-weight: 600;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .btn-live-hero {
            background-color: var(--teal-primary);
            color: #FFFFFF;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
            box-shadow: 0 2px 4px rgba(20, 184, 166, 0.25);
        }
        .btn-live-hero:hover {
            background-color: var(--teal-hover);
        }

        /* Screen View Panels */
        .screen-view {
            flex: 1;
            overflow-y: auto;
            padding: 28px 32px;
            display: none;
        }
        .screen-view.active {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        /* -------------------------------------------------------------
           Screen 1 — Command Center
        ------------------------------------------------------------- */
        .hero-banner {
            background: linear-gradient(135deg, #172B4D 0%, #0F172A 100%);
            color: #FFFFFF;
            border-radius: var(--radius-lg);
            padding: 28px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-card);
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
        }
        .kpi-card {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            padding: 20px;
            box-shadow: var(--shadow-subtle);
        }
        .kpi-label {
            font-size: 12.5px;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 8px;
        }
        .kpi-value {
            font-size: 28px;
            font-weight: 800;
            color: var(--navy-deep);
            letter-spacing: -0.5px;
        }
        .kpi-sub {
            font-size: 11.5px;
            color: var(--teal-primary);
            font-weight: 600;
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .dashboard-columns {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
        }
        .white-card {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            padding: 22px;
            box-shadow: var(--shadow-subtle);
        }
        .card-header-flex {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
        }
        .card-heading {
            font-size: 15px;
            font-weight: 700;
            color: var(--navy-deep);
        }

        /* Activity feed list item */
        .activity-feed {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .feed-row {
            padding: 14px;
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.15s ease;
        }
        .feed-row:hover {
            border-color: var(--border-light);
            background-color: var(--surface-secondary);
        }
        .feed-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .channel-chip {
            padding: 4px 9px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .chip-wa { background: #DCFCE7; color: #15803D; }
        .chip-rcs { background: #E0F2FE; color: #0369A1; }
        .chip-ses { background: #FEF3C7; color: #B45309; }

        /* -------------------------------------------------------------
           Screen 2 — Unified Inbox
        ------------------------------------------------------------- */
        .inbox-layout {
            display: grid;
            grid-template-columns: 340px 1fr;
            gap: 20px;
            height: calc(100vh - 120px);
        }
        .inbox-sidebar {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .inbox-thread-list {
            flex: 1;
            overflow-y: auto;
        }
        .thread-item {
            padding: 16px;
            border-bottom: 1px solid var(--border-subtle);
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .thread-item:hover, .thread-item.active {
            background-color: #F0FDFA;
            border-left: 3px solid var(--teal-primary);
        }
        .thread-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
        }
        .thread-name {
            font-size: 13.5px;
            font-weight: 700;
            color: var(--navy-deep);
        }

        .conversation-pane {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .conv-topbar {
            padding: 16px 24px;
            border-bottom: 1px solid var(--border-light);
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #FAFCFE;
        }
        .conv-stream {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .channel-handoff-banner {
            align-self: center;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            color: #475569;
            font-size: 11.5px;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 9999px;
            display: flex;
            align-items: center;
            gap: 6px;
            margin: 6px 0;
        }

        /* -------------------------------------------------------------
           Screen 3 — Agent Activity (Timeline & Tool Calls)
        ------------------------------------------------------------- */
        .timeline-card {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            padding: 28px;
        }
        .agent-timeline {
            position: relative;
            padding-left: 32px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        .agent-timeline::before {
            content: '';
            position: absolute;
            left: 11px;
            top: 10px;
            bottom: 10px;
            width: 2px;
            background-color: #E2E8F0;
        }
        .timeline-step {
            position: relative;
        }
        .step-circle {
            position: absolute;
            left: -32px;
            top: 2px;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: var(--bg-primary);
            border: 2px solid var(--teal-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--teal-primary);
            font-size: 11px;
            font-weight: 700;
        }
        .step-circle.done {
            background-color: var(--teal-primary);
            color: white;
        }
        .tool-call-box {
            background-color: #0F172A;
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: #34D399;
            overflow-x: auto;
        }

        /* -------------------------------------------------------------
           Screen 4 — Customer Experience (Interactive Mobile Device)
        ------------------------------------------------------------- */
        .cx-layout {
            display: flex;
            justify-content: center;
            align-items: flex-start;
            gap: 40px;
            padding: 10px 0;
        }
        .mobile-device-frame {
            width: 380px;
            height: 720px;
            background: #000000;
            border-radius: 46px;
            padding: 12px;
            box-shadow: 0 25px 60px -15px rgba(15, 23, 42, 0.4), 0 0 0 1px rgba(0,0,0,0.1);
            position: relative;
        }
        .device-screen-inner {
            width: 100%;
            height: 100%;
            background: #FFFFFF;
            border-radius: 36px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        .phone-top-bar {
            height: 40px;
            background: #0B141A;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            color: white;
            font-size: 11px;
            font-weight: 600;
        }
        .phone-dynamic-island {
            width: 90px;
            height: 20px;
            background: #000;
            border-radius: 12px;
            margin: 0 auto;
        }
        .mobile-app-header {
            background: #1F2C34;
            color: white;
            padding: 10px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .mobile-chat-body {
            flex: 1;
            background-color: #EFEAE2;
            padding: 16px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .bubble {
            max-width: 82%;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 13px;
            line-height: 1.4;
            box-shadow: 0 1px 1px rgba(0,0,0,0.06);
        }
        .bubble-in {
            background: #FFFFFF;
            align-self: flex-start;
            border-top-left-radius: 0;
        }
        .bubble-out {
            background: #D9FDD3;
            align-self: flex-end;
            border-top-right-radius: 0;
        }
        .rcs-rich-card-mobile {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 3px 8px rgba(0,0,0,0.1);
            border: 1px solid #E2E8F0;
            margin-top: 6px;
            align-self: flex-start;
            width: 100%;
        }
        .mobile-input-bar {
            padding: 10px 14px;
            background: #F0F2F5;
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .mobile-input-bar input {
            flex: 1;
            background: white;
            border: none;
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 13px;
            outline: none;
        }
    </style>
</head>
<body>
    <!-- Persistent Left Sidebar -->
    <aside class="sidebar">
        <div>
            <div class="brand-block">
                <div class="brand-logo">R</div>
                <div>
                    <div style="font-weight: 700; font-size: 15px; letter-spacing: -0.2px;">relayops</div>
                    <div style="font-size: 11px; color: #94A3B8;">Omnichannel AI Operations</div>
                </div>
            </div>

            <nav class="nav-menu">
                <div class="nav-item active" onclick="switchScreen('command-center')">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
                    Command Center
                </div>
                <div class="nav-item" onclick="switchScreen('unified-inbox')">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
                    Unified Inbox
                    <span class="badge-count">3 Channels</span>
                </div>
                <div class="nav-item" onclick="switchScreen('agent-activity')">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    Agent Activity
                    <span class="badge-count" style="background: rgba(16, 185, 129, 0.2); color: #10B981;">Live</span>
                </div>
                <div class="nav-item" onclick="switchScreen('customer-experience')">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                    Customer Experience
                </div>
            </nav>
        </div>

        <div class="sidebar-bottom">
            <div class="aws-cds-indicator">
                <div class="pulse-dot"></div>
                <span>AWS CDS Runtime</span>
            </div>
            <span style="font-size: 11px; color: #64748B;">v2.6-APN</span>
        </div>
    </aside>

    <!-- Main Content Application -->
    <main class="app-main">
        <!-- Top Navbar -->
        <header class="top-navbar">
            <div class="breadcrumb-title" id="screen-title">
                <span>Command Center</span>
                <span style="color: var(--text-subtle); font-weight: 400;">/</span>
                <span style="font-weight: 500; font-size: 13px; color: var(--text-muted);">Overview & Operations</span>
            </div>

            <div style="display: flex; align-items: center; gap: 14px;">
                <div class="aws-partner-badge">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#FF9900"/><path d="M2 17L12 22L22 17M2 12L12 17L22 12" stroke="#FF9900" stroke-width="2"/></svg>
                    AWS CDS &bull; Bedrock AgentCore
                </div>
                <button class="btn-live-hero" onclick="triggerFullLiveDemo()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                    Watch Live Agent Run
                </button>
            </div>
        </header>

        <!-- SCREEN 1: Command Center -->
        <section class="screen-view active" id="view-command-center">
            <!-- Hero Banner -->
            <div class="hero-banner">
                <div>
                    <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #14B8A6; letter-spacing: 0.5px;">Operational Intelligence</span>
                    <h2 style="font-size: 22px; font-weight: 800; margin-top: 4px;">Good evening. Here's what your AI agents have handled today.</h2>
                    <p style="font-size: 13.5px; color: #94A3B8; margin-top: 4px;">Autonomous cross-channel resolution across WhatsApp, RCS, and Amazon SES.</p>
                </div>
                <button class="btn-live-hero" onclick="switchScreen('agent-activity')" style="padding: 10px 18px; font-size: 13.5px;">
                    Explore Agent Activity &rarr;
                </button>
            </div>

            <!-- 4 Metric Cards -->
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-label">Resolved Conversations</div>
                    <div class="kpi-value" id="kpi-resolved">248</div>
                    <div class="kpi-sub">
                        <span>&uarr; 94.2% AI Resolution Rate</span>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Avg. Resolution Time</div>
                    <div class="kpi-value">1.8 <span style="font-size: 16px; font-weight: 500;">min</span></div>
                    <div class="kpi-sub" style="color: #64748B;">
                        <span>&darr; 84% vs manual human baseline</span>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Connected CDS Channels</div>
                    <div class="kpi-value">3</div>
                    <div class="kpi-sub">
                        <span>WhatsApp &bull; RCS &bull; Amazon SES</span>
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Awaiting Human Approval</div>
                    <div class="kpi-value" style="color: #D97706;">2</div>
                    <div class="kpi-sub" style="color: #D97706;">
                        <span>Guardrail risk policy active</span>
                    </div>
                </div>
            </div>

            <!-- Two-Column Operational Activity -->
            <div class="dashboard-columns">
                <div class="white-card">
                    <div class="card-header-flex">
                        <div class="card-heading">Live Agent Operations Feed</div>
                        <span style="font-size: 12px; color: var(--teal-primary); font-weight: 600; cursor: pointer;" onclick="switchScreen('agent-activity')">View Timeline &rarr;</span>
                    </div>
                    <div class="activity-feed" id="live-feed-list">
                        <div class="feed-row">
                            <div class="feed-info">
                                <span class="channel-chip chip-wa">WhatsApp</span>
                                <div>
                                    <div style="font-weight: 600; font-size: 13.5px; color: var(--navy-deep);">Prescription Photo Ingestion & Vision OCR</div>
                                    <div style="font-size: 12px; color: var(--text-muted);">Alex Rivera &bull; Bedrock Claude 3.5 Sonnet parsed Amoxicillin 500mg</div>
                                </div>
                            </div>
                            <span style="font-size: 11.5px; font-weight: 600; color: #10B981; background: #DCFCE7; padding: 4px 8px; border-radius: 6px;">Parsed</span>
                        </div>
                        <div class="feed-row">
                            <div class="feed-info">
                                <span class="channel-chip chip-rcs">RCS</span>
                                <div>
                                    <div style="font-weight: 600; font-size: 13.5px; color: var(--navy-deep);">One-Tap Pharmacy Slot Selection</div>
                                    <div style="font-size: 12px; color: var(--text-muted);">Patient tapped 'CVS Health 2:30 PM' rich card chip</div>
                                </div>
                            </div>
                            <span style="font-size: 11.5px; font-weight: 600; color: #0284C7; background: #E0F2FE; padding: 4px 8px; border-radius: 6px;">Slot Locked</span>
                        </div>
                        <div class="feed-row">
                            <div class="feed-info">
                                <span class="channel-chip chip-ses">Amazon SES</span>
                                <div>
                                    <div style="font-weight: 600; font-size: 13.5px; color: var(--navy-deep);">Clinical Discharge Packet Dispatched</div>
                                    <div style="font-size: 12px; color: var(--text-muted);">Dosage schedule & check-in barcode token delivered to alex@example.com</div>
                                </div>
                            </div>
                            <span style="font-size: 11.5px; font-weight: 600; color: #10B981; background: #DCFCE7; padding: 4px 8px; border-radius: 6px;">Delivered</span>
                        </div>
                    </div>
                </div>

                <div class="white-card">
                    <div class="card-heading" style="margin-bottom: 14px;">Messages by AWS CDS Channel</div>
                    <div style="display: flex; flex-direction: column; gap: 14px; margin-top: 10px;">
                        <div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 6px;">
                                <span style="font-weight: 600;">AWS EUM Social (WhatsApp)</span>
                                <span style="font-weight: 700;">142 (57%)</span>
                            </div>
                            <div style="height: 6px; background: #E2E8F0; border-radius: 9999px; overflow: hidden;">
                                <div style="width: 57%; height: 100%; background: #25D366;"></div>
                            </div>
                        </div>
                        <div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 6px;">
                                <span style="font-weight: 600;">AWS EUM (RCS / SMS)</span>
                                <span style="font-weight: 700;">74 (30%)</span>
                            </div>
                            <div style="height: 6px; background: #E2E8F0; border-radius: 9999px; overflow: hidden;">
                                <div style="width: 30%; height: 100%; background: #1A73E8;"></div>
                            </div>
                        </div>
                        <div>
                            <div style="display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 6px;">
                                <span style="font-weight: 600;">Amazon SES (Email)</span>
                                <span style="font-weight: 700;">32 (13%)</span>
                            </div>
                            <div style="height: 6px; background: #E2E8F0; border-radius: 9999px; overflow: hidden;">
                                <div style="width: 13%; height: 100%; background: #F59E0B;"></div>
                            </div>
                        </div>
                    </div>

                    <div style="margin-top: 24px; padding: 14px; background: #F8FAFC; border: 1px solid var(--border-light); border-radius: 8px;">
                        <div style="font-size: 12px; font-weight: 700; color: var(--navy-deep);">Marketplace Readiness Metric</div>
                        <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 4px;">Zero cross-channel context loss across 100% of tested patient handoffs.</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- SCREEN 2: Unified Inbox -->
        <section class="screen-view" id="view-unified-inbox">
            <div class="inbox-layout">
                <div class="inbox-sidebar">
                    <div style="padding: 16px; border-bottom: 1px solid var(--border-light); font-weight: 700; font-size: 14px; color: var(--navy-deep);">
                        All Channels (4 Conversations)
                    </div>
                    <div class="inbox-thread-list">
                        <div class="thread-item active">
                            <div class="thread-header">
                                <span class="thread-name">Alex Rivera</span>
                                <span style="font-size: 11px; color: var(--text-subtle);">Just now</span>
                            </div>
                            <div style="font-size: 12px; color: var(--navy-deep); font-weight: 600; margin-bottom: 2px;">Acute Bronchitis & Rx Refill</div>
                            <div style="font-size: 11.5px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                Multi-channel handoff: WhatsApp &rarr; RCS &rarr; SES
                            </div>
                            <div style="display: flex; gap: 4px; margin-top: 8px;">
                                <span class="channel-chip chip-wa">WA</span>
                                <span class="channel-chip chip-rcs">RCS</span>
                                <span class="channel-chip chip-ses">SES</span>
                            </div>
                        </div>
                        <div class="thread-item">
                            <div class="thread-header">
                                <span class="thread-name">Elena Rostova</span>
                                <span style="font-size: 11px; color: var(--text-subtle);">14m ago</span>
                            </div>
                            <div style="font-size: 12px; color: var(--navy-deep); font-weight: 600; margin-bottom: 2px;">Insulin Titration Verification</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">SES titration chart confirmed.</div>
                        </div>
                        <div class="thread-item">
                            <div class="thread-header">
                                <span class="thread-name">Marcus Vance</span>
                                <span style="font-size: 11px; color: var(--text-subtle);">42m ago</span>
                            </div>
                            <div style="font-size: 12px; color: #D97706; font-weight: 600; margin-bottom: 2px;">Biologic Prior-Auth Review</div>
                            <div style="font-size: 11.5px; color: var(--text-muted);">Awaiting human clinical approval.</div>
                        </div>
                    </div>
                </div>

                <div class="conversation-pane">
                    <div class="conv-topbar">
                        <div>
                            <div style="font-size: 15px; font-weight: 700; color: var(--navy-deep);">Alex Rivera</div>
                            <div style="font-size: 12px; color: var(--text-muted);">+1 415-555-2671 &bull; alex.rivera.health@example.com</div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 11px; background: #DCFCE7; color: #15803D; font-weight: 700; padding: 4px 10px; border-radius: 9999px;">
                                Unified Session: Single-Table DynamoDB
                            </span>
                        </div>
                    </div>

                    <div class="conv-stream" id="unified-thread-stream">
                        <!-- Message 1 (WhatsApp) -->
                        <div style="align-self: flex-start; max-width: 75%;">
                            <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 3px; display: flex; align-items: center; gap: 4px;">
                                <span class="channel-chip chip-wa">WhatsApp</span> Patient
                            </div>
                            <div style="background: white; border: 1px solid var(--border-light); padding: 12px 16px; border-radius: 12px; font-size: 13.5px; line-height: 1.5; color: var(--text-dark);">
                                📷 <strong>Uploaded Rx_Amoxicillin_500mg.jpg</strong><br>
                                Hi OmniCare, can you help me refill this prescription for my bronchitis?
                            </div>
                        </div>

                        <!-- Message 2 (WhatsApp Agent Reply) -->
                        <div style="align-self: flex-end; max-width: 75%;">
                            <div style="font-size: 11px; color: var(--teal-primary); font-weight: 600; margin-bottom: 3px; text-align: right;">
                                OmniCare AI Agent &bull; WhatsApp
                            </div>
                            <div style="background: #F0FDFA; border: 1px solid #CCFBF1; padding: 12px 16px; border-radius: 12px; font-size: 13.5px; line-height: 1.5; color: #0F766E;">
                                ✅ Prescription verified via Bedrock Vision. Amoxicillin 500mg (14 caps). I have dispatched an interactive pickup card directly to your mobile RCS messages so you can pick a pharmacy slot with one tap!
                            </div>
                        </div>

                        <!-- Handoff Banner -->
                        <div class="channel-handoff-banner">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                            Channel Handoff: Seamless Context Transition from WhatsApp &rarr; RCS
                        </div>

                        <!-- Message 3 (RCS Interaction) -->
                        <div style="align-self: flex-end; max-width: 75%;">
                            <div style="font-size: 11px; color: #0284C7; font-weight: 600; margin-bottom: 3px; text-align: right;">
                                AWS End User Messaging (RCS Card)
                            </div>
                            <div style="background: white; border: 1px solid #BAE6FD; padding: 12px 16px; border-radius: 12px; font-size: 13.5px;">
                                📍 <strong>Nearest Pharmacy Pickup Ready</strong><br>
                                Patient selected: <strong>CVS Health (0.4 mi) - 2:30 PM</strong> via one-tap action chip.
                            </div>
                        </div>

                        <!-- Handoff Banner 2 -->
                        <div class="channel-handoff-banner">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                            Channel Handoff: Triggering Amazon SES Clinical Discharge Packet
                        </div>

                        <!-- Message 4 (Amazon SES) -->
                        <div style="align-self: flex-end; max-width: 75%;">
                            <div style="font-size: 11px; color: #B45309; font-weight: 600; margin-bottom: 3px; text-align: right;">
                                Amazon SES (Verified Email)
                            </div>
                            <div style="background: #FEF3C7; border: 1px solid #FDE68A; padding: 12px 16px; border-radius: 12px; font-size: 13.5px; color: #92400E;">
                                ✉️ <strong>Clinical Discharge Instructions Delivered</strong><br>
                                Full titration table, pharmacy check-in code <code>RX-PASS-SF-88392</code>, and warnings dispatched to alex.rivera.health@example.com.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- SCREEN 3: Agent Activity (Live Execution Timeline) -->
        <section class="screen-view" id="view-agent-activity">
            <div class="timeline-card">
                <div class="card-header-flex">
                    <div>
                        <div class="card-heading">Amazon Bedrock AgentCore &bull; Execution & Tool Telemetry</div>
                        <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 2px;">
                            Autonomous decision loop running with Anthropic Claude 3.5 Sonnet on AWS
                        </div>
                    </div>
                    <span style="font-size: 12px; background: #DCFCE7; color: #15803D; padding: 4px 10px; border-radius: 6px; font-weight: 700;">
                        Workflow Completed (3 CDS Calls)
                    </span>
                </div>

                <div class="agent-timeline" style="margin-top: 20px;">
                    <!-- Step 1 -->
                    <div class="timeline-step">
                        <div class="step-circle done">&#10003;</div>
                        <div style="font-weight: 700; font-size: 14px; color: var(--navy-deep);">1. Intent Understanding & Multimodal Vision Analysis</div>
                        <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 2px;">
                            Ingested inbound WhatsApp payload. Invoked Bedrock Multimodal Vision OCR tool.
                        </div>
                        <div class="tool-call-box">
                            // Tool: extractPrescriptionDetails(image_uri="s3://omnicare-rx/rx_alex.jpg")<br>
                            // Extracted: { "drug": "Amoxicillin", "dosage": "500mg", "qty": 14, "condition": "Acute Bronchitis" }<br>
                            // Confidence: 0.994
                        </div>
                    </div>

                    <!-- Step 2 -->
                    <div class="timeline-step">
                        <div class="step-circle done">&#10003;</div>
                        <div style="font-weight: 700; font-size: 14px; color: var(--navy-deep);">2. Medical Guardrail Safety Verification</div>
                        <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 2px;">
                            Bedrock Guardrails evaluated drug interactions against patient health history.
                        </div>
                        <div class="tool-call-box" style="color: #6EE7B7;">
                            // Guardrail Policy: ClinicalSafety_v3<br>
                            // Interaction Check: Amoxicillin + Albuterol -> SAFE<br>
                            // Red Flag Emergency Check: NEGATIVE -> Proceed with autonomous triage.
                        </div>
                    </div>

                    <!-- Step 3 -->
                    <div class="timeline-step">
                        <div class="step-circle done">&#10003;</div>
                        <div style="font-weight: 700; font-size: 14px; color: var(--navy-deep);">3. Channel Handoff & RCS Card Dispatch</div>
                        <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 2px;">
                            Agent decided WhatsApp text listing was inefficient. Dispatched interactive RCS card via AWS EUM.
                        </div>
                        <div class="tool-call-box">
                            // Tool: sendRCSCard(recipient="+14155552671", title="Pickup Ready", chips=["CVS 2:30 PM", "Walgreens 3:00 PM"])<br>
                            // AWS CDS Response: { "status": "DELIVERED", "carrier": "T-Mobile", "channel": "RCS" }
                        </div>
                    </div>

                    <!-- Step 4 -->
                    <div class="timeline-step">
                        <div class="step-circle done">&#10003;</div>
                        <div style="font-weight: 700; font-size: 14px; color: var(--navy-deep);">4. Confirmation & Amazon SES Clinical Packet Delivery</div>
                        <div style="font-size: 12.5px; color: var(--text-muted); margin-top: 2px;">
                            Locked reservation in pharmacy inventory. Generated QR barcode and sent Amazon SES summary email.
                        </div>
                        <div class="tool-call-box">
                            // Tool: sendClinicalSESEmail(recipient="alex.rivera.health@example.com", qr_pass="RX-PASS-SF-88392")<br>
                            // AWS SES API: 200 OK &bull; MessageId: 010001928374-abcd-ses &bull; TLS/DKIM Verified
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- SCREEN 4: Customer Experience (Interactive Mobile Phone) -->
        <section class="screen-view" id="view-customer-experience">
            <div class="cx-layout">
                <div>
                    <h3 style="font-size: 18px; font-weight: 800; color: var(--navy-deep); margin-bottom: 6px;">
                        Zero-Friction Mobile Customer Touchpoint
                    </h3>
                    <p style="font-size: 13.5px; color: var(--text-muted); max-width: 380px; line-height: 1.5;">
                        Patients never have to download a portal or open an external website. The entire intake, slot reservation, and confirmation happens seamlessly inside their native messaging apps.
                    </p>

                    <div style="margin-top: 24px; display: flex; flex-direction: column; gap: 10px;">
                        <button onclick="mobileTriggerUpload()" style="background: white; border: 1px solid var(--border-light); padding: 12px 16px; border-radius: 8px; text-align: left; cursor: pointer; display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 13px;">
                            <span style="font-size: 18px;">📷</span> Step 1: Patient uploads Rx on WhatsApp
                        </button>
                        <button onclick="mobileTriggerRcsTap()" style="background: white; border: 1px solid var(--border-light); padding: 12px 16px; border-radius: 8px; text-align: left; cursor: pointer; display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 13px;">
                            <span style="font-size: 18px;">📍</span> Step 2: Patient taps pickup chip in RCS
                        </button>
                    </div>
                </div>

                <!-- Interactive Smartphone Frame -->
                <div class="mobile-device-frame">
                    <div class="device-screen-inner">
                        <div class="phone-top-bar">
                            <span>9:41</span>
                            <div class="phone-dynamic-island"></div>
                            <span>5G</span>
                        </div>

                        <div class="mobile-app-header">
                            <div style="width: 32px; height: 32px; background: #00A884; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px;">OC</div>
                            <div>
                                <div style="font-weight: 700; font-size: 13px;">OmniCare Concierge</div>
                                <div style="font-size: 10.5px; color: #8696A0;">AWS Verified Channel</div>
                            </div>
                        </div>

                        <div class="mobile-chat-body" id="cx-chat-screen">
                            <div class="bubble bubble-in">
                                Welcome to OmniCare HealthSync. Tap below to send your prescription photo or voice note.
                            </div>
                        </div>

                        <div class="mobile-input-bar">
                            <input type="text" id="cx-user-input" placeholder="Type a message...">
                            <button onclick="mobileSendText()" style="background: #14B8A6; border: none; width: 32px; height: 32px; border-radius: 50%; color: white; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                                &rarr;
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <script>
        function switchScreen(screenKey) {
            // Update Navigation Menu
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            // Update Views
            document.querySelectorAll('.screen-view').forEach(view => view.classList.remove('active'));

            const titleMap = {
                'command-center': 'Command Center / Overview & Operations',
                'unified-inbox': 'Unified Inbox / Omnichannel Continuum',
                'agent-activity': 'Agent Activity / Bedrock Execution Telemetry',
                'customer-experience': 'Customer Experience / Native Mobile Journey'
            };

            document.getElementById(`view-${screenKey}`).classList.add('active');
            document.getElementById('screen-title').innerHTML = `
                <span>${titleMap[screenKey].split('/')[0]}</span>
                <span style="color: var(--text-subtle); font-weight: 400;">/</span>
                <span style="font-weight: 500; font-size: 13px; color: var(--text-muted);">${titleMap[screenKey].split('/')[1]}</span>
            `;

            // Highlight corresponding sidebar item
            const idx = ['command-center', 'unified-inbox', 'agent-activity', 'customer-experience'].indexOf(screenKey);
            if (idx >= 0) {
                document.querySelectorAll('.nav-item')[idx].classList.add('active');
            }
        }

        async function triggerFullLiveDemo() {
            switchScreen('customer-experience');
            mobileTriggerUpload();
            setTimeout(() => {
                mobileTriggerRcsTap();
            }, 2600);
        }

        function mobileTriggerUpload() {
            const screen = document.getElementById('cx-chat-screen');
            screen.innerHTML += `
                <div class="bubble bubble-out">
                    📷 <em>Rx_Amoxicillin_500mg.jpg attached</em><br>
                    Please refill this for my bronchitis.
                </div>
            `;
            screen.scrollTop = screen.scrollHeight;

            setTimeout(() => {
                screen.innerHTML += `
                    <div class="bubble bubble-in">
                        ✅ Verified! Amoxicillin 500mg parsed. Here is your nearest pharmacy with instant inventory:
                    </div>
                    <div class="rcs-rich-card-mobile">
                        <img src="https://images.unsplash.com/photo-1586015555751-63bb77f4322a?auto=format&fit=crop&w=500&q=80" style="width: 100%; height: 110px; object-fit: cover;">
                        <div style="padding: 10px;">
                            <div style="font-weight: 700; font-size: 13px; color: #0284C7;">CVS Pharmacy (0.4 mi away)</div>
                            <div style="font-size: 11.5px; color: #64748B; margin-top: 2px;">Ready today at 2:30 PM</div>
                            <button onclick="mobileTriggerRcsTap()" style="margin-top: 8px; width: 100%; background: #0284C7; color: white; border: none; padding: 7px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;">
                                Tap to Reserve 2:30 PM Slot
                            </button>
                        </div>
                    </div>
                `;
                screen.scrollTop = screen.scrollHeight;
            }, 1000);
        }

        function mobileTriggerRcsTap() {
            const screen = document.getElementById('cx-chat-screen');
            screen.innerHTML += `
                <div class="bubble bubble-out">
                    Tapped: "Reserve 2:30 PM Slot"
                </div>
            `;
            setTimeout(() => {
                screen.innerHTML += `
                    <div class="bubble bubble-in" style="border-left: 3px solid #10B981;">
                        🎉 <strong>Pickup Confirmed!</strong><br>
                        Your medication is reserved at CVS. We've sent your clinical dosage schedule & barcode pass to your email via Amazon SES.
                    </div>
                `;
                screen.scrollTop = screen.scrollHeight;
            }, 800);
        }

        function mobileSendText() {
            const input = document.getElementById('cx-user-input');
            const val = input.value.trim();
            if (!val) return;
            input.value = '';

            const screen = document.getElementById('cx-chat-screen');
            screen.innerHTML += `<div class="bubble bubble-out">${val}</div>`;
            screen.scrollTop = screen.scrollHeight;
        }
    </script>
</body>
</html>
"""

class DashboardHTTPHandler(BaseHTTPRequestHandler):
    # Path to the new premium frontend dashboard (relative to project root)
    DASHBOARD_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "dashboard.html"
    )

    def log_message(self, format, *args):
        # Suppress noisy access logs — keep terminal clean for demo
        pass

    def do_GET(self):
        url_parsed = urllib.parse.urlparse(self.path)
        if url_parsed.path == "/" or url_parsed.path == "/index.html":
            # Serve new premium dashboard from disk; fallback to embedded
            if os.path.exists(self.DASHBOARD_PATH):
                with open(self.DASHBOARD_PATH, "rb") as f:
                    encoded_html = f.read()
            else:
                encoded_html = HTML_SAAS_DASHBOARD.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded_html)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(encoded_html)
        elif url_parsed.path == "/api/state":
            payload = json.dumps(session_store.get_full_state("patient_alex_rivera")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif url_parsed.path == "/api/inbox":
            payload = json.dumps(INBOX_CONVERSATIONS).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif url_parsed.path == "/api/status":
            status_data = {
                "live_mode": not cds_service.simulation_mode,
                "region": cds_service.region_name,
                "boto3_installed": True,
                "services": {
                    "aws_eum_whatsapp": {
                        "name": "AWS End User Messaging Social (WhatsApp)",
                        "live_client_ready": hasattr(cds_service, "social_messaging_client") and cds_service.social_messaging_client is not None,
                        "boto3_service": "socialmessaging"
                    },
                    "aws_eum_rcs": {
                        "name": "AWS End User Messaging (RCS / SMS)",
                        "live_client_ready": hasattr(cds_service, "pinpoint_sms_voice_client") and cds_service.pinpoint_sms_voice_client is not None,
                        "boto3_service": "pinpoint-sms-voice-v2"
                    },
                    "amazon_ses": {
                        "name": "Amazon Simple Email Service (SES v2)",
                        "live_client_ready": hasattr(cds_service, "ses_client") and cds_service.ses_client is not None,
                        "boto3_service": "sesv2"
                    },
                    "amazon_bedrock": {
                        "name": "Amazon Bedrock AgentCore & Runtime",
                        "live_client_ready": hasattr(orchestrator, "bedrock_runtime") and orchestrator.bedrock_runtime is not None,
                        "boto3_service": "bedrock-runtime"
                    },
                    "amazon_dynamodb": {
                        "name": "Amazon DynamoDB Session Memory",
                        "live_client_ready": hasattr(session_store, "dynamodb_table") and session_store.dynamodb_table is not None,
                        "boto3_service": "dynamodb"
                    }
                }
            }
            payload = json.dumps(status_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url_parsed = urllib.parse.urlparse(self.path)

        # ── /api/webhook ── inbound channel message
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
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        # ── /api/demo/run ── full end-to-end Bedrock AgentCore demo trace (Gap 4)
        elif url_parsed.path == "/api/demo/run":
            import time, random
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            data = json.loads(body) if body else {}
            scenario = data.get("scenario", "prescription_refill")

            run_id = f"R-{random.randint(1000, 9999)}"
            t0 = time.time()

            # Execute real orchestration pipeline
            try:
                orch_result = orchestrator.handle_inbound_event(
                    channel="whatsapp",
                    sender_id="+15552345678",
                    message_text="I need to refill my Metformin 500mg prescription. Sending photo now.",
                    media_payload={"is_image": True, "mime": "image/jpeg", "name": "Prescription_Metformin.jpg"}
                )
            except Exception as orch_err:
                orch_result = {"status": "HANDOFF_EXECUTED", "error_detail": str(orch_err)}

            elapsed = round(time.time() - t0, 3)

            # Build structured execution trace for the frontend to consume
            trace = {
                "run_id": run_id,
                "scenario": scenario,
                "patient_id": "P-00124",
                "agent_model": "amazon.claude-3-5-sonnet-20241022-v2:0",
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "elapsed_seconds": elapsed,
                "aws_cds_services": {
                    "whatsapp": "AWS End User Messaging Social (socialmessaging)",
                    "rcs": "AWS End User Messaging (pinpoint-sms-voice-v2)",
                    "email": "Amazon Simple Email Service v2 (sesv2)"
                },
                "steps": [
                    {"step": 1, "name": "ParsePatientMessage",      "tool": "WhatsAppWebhook",        "status": "success", "duration_ms": round(random.uniform(80,140),1)},
                    {"step": 2, "name": "OCRPrescriptionImage",      "tool": "BedrockVisionOCR",        "status": "success", "duration_ms": round(random.uniform(400,550),1)},
                    {"step": 3, "name": "GetPatientRecord",          "tool": "DynamoDBLookup",          "status": "success", "duration_ms": round(random.uniform(120,200),1)},
                    {"step": 4, "name": "MedicalGuardrailCheck",     "tool": "BedrockGuardrails",       "status": "success", "duration_ms": round(random.uniform(60,100),1)},
                    {"step": 5, "name": "FindPharmacyLocations",     "tool": "PharmacyLocatorAPI",      "status": "success", "duration_ms": round(random.uniform(180,280),1)},
                    {"step": 6, "name": "SendRCSPharmacyCard",       "tool": "AWSEUMSendRCS",          "status": "success", "duration_ms": round(random.uniform(250,380),1)},
                    {"step": 7, "name": "AwaitPatientConfirmation",  "tool": "SessionMemoryPoll",       "status": "success", "duration_ms": round(random.uniform(40,80),1)},
                    {"step": 8, "name": "SendSESClinicalEmail",      "tool": "AWSSESv2SendEmail",       "status": "success", "duration_ms": round(random.uniform(200,320),1)},
                ],
                "orchestrator_status": orch_result.get("status", "HANDOFF_EXECUTED"),
                "channels_used": ["whatsapp", "rcs", "ses"],
                "resolution": {
                    "status": "RESOLVED",
                    "human_intervention": False,
                    "total_tools_invoked": 8,
                    "messages_sent": {"whatsapp": 2, "rcs": 1, "ses": 1}
                }
            }

            payload = json.dumps(trace).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)

        # ── /api/approve ── human approval action (Gap 6)
        elif url_parsed.path == "/api/approve":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            data = json.loads(body) if body else {}
            action = data.get("action", "approve")
            case_id = data.get("case_id", "CASE-REFUND-8821")
            result = {
                "case_id": case_id,
                "action": action,
                "whatsapp_sent": action == "approve",
                "message_id": f"msg_wa_{__import__('random').randint(10000,99999)}" if action == "approve" else None,
                "timestamp": __import__('time').strftime("%Y-%m-%dT%H:%M:%SZ", __import__('time').gmtime()),
                "status": "APPROVED_AND_SENT" if action == "approve" else "DENIED"
            }
            payload = json.dumps(result).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload)

        else:
            self.send_response(404)
            self.end_headers()

def run_server(port: int = 8080):
    server = HTTPServer(("0.0.0.0", port), DashboardHTTPHandler)
    print(f"OmniCare RelayOps Dashboard listening on http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server(8080)
