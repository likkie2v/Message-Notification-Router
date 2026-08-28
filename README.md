# AI-Powered Multimodal Message Notification Router

An AI-powered, context-aware notification routing system built for the **HackerRank Orchestrate Hackathon**.

The system analyzes WhatsApp-style messages and determines whether they should trigger an immediate notification, be included in a digest, or be muted.

## 🎯 Problem Statement

Modern messaging platforms generate a large number of notifications every day. Not every message deserves the same level of attention.

This project builds an intelligent notification routing system that classifies incoming messages into three actions:

- 🔔 **Notify** — Important messages requiring immediate attention
- 📥 **Digest** — Messages that can be reviewed later
- 🔇 **Mute** — Spam, scams, unwanted promotions, repetitive forwards, or low-value messages

The system supports **multimodal messages**, including text, images, and voice notes.

---

## ✨ Features

- Context-aware message classification
- Multimodal processing for text, images, and voice notes
- OCR-based text extraction from images
- Speech-to-text processing for voice notes
- Scam and credential theft detection
- Prompt injection detection
- Spam detection
- Promotion and marketing message detection
- Urgency detection
- Event detection
- Payment-related message detection
- Business update detection
- Greeting and forwarded-message detection
- Risk scoring
- Urgency scoring
- Source trust scoring
- Historical engagement analysis
- Negative interaction history analysis
- Notification overload handling
- Context-based evidence selection

---

## 🧠 Routing Actions

| Action | Meaning |
|---|---|
| `notify` | The message is important and should immediately notify the user |
| `digest` | The message is useful but can be reviewed later |
| `mute` | The message is spam, scam, unwanted, or low priority |

---

## 🏷️ Supported Message Types

The system detects multiple message categories:

- `urgent`
- `event`
- `payment`
- `business_update`
- `promotion`
- `greeting`
- `forward`
- `spam`
- `scam`
- `personal`
- `unknown`

---

## 🏗️ Project Architecture

```text
Incoming Message
       │
       ▼
┌───────────────────────┐
│ Multimodal Processor  │
│ Text / Image / Voice  │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Context Builder       │
│ History / Business /  │
│ Group Context         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Decision Engine       │
│                       │
│ • Message Type        │
│ • Risk Score          │
│ • Urgency Score       │
│ • Trust Score         │
│ • Engagement Score    │
│ • History Analysis    │
└───────────┬───────────┘
            │
            ▼
    Notify / Digest / Mute
