# Phase 7.5 — End-to-End SIH Demo Script

This document provides a minute-by-minute walkthrough to demonstrate the full End-to-End clinical flow of MediPlatform using Mock Data (mimicking the PostgreSQL DB contracts).

## Pre-requisites
Ensure both Next.js applications are running:
1. Patient Kiosk: `http://localhost:3000`
2. Doctor Dashboard: `http://localhost:3001`

---

## 0:00 - The Registration (Patient Kiosk)
**Action**: Patient approaches the Kiosk at `http://localhost:3000/`.
**Script**: "Welcome to MediPlatform. The patient starts their journey by selecting their preferred language (Hindi) and providing consent for AI processing."
**Action**: Click 'Hindi' ➔ 'Consent' ➔ Enter name 'Raj Kumar' and basic demographics. 
**Verification**: The system registers the patient (mock ID: `pat_raj_123`) and generates a secure session (`mock-session-raj-123`).

## 1:00 - Clinical Voice Intake (Patient Kiosk)
**Action**: Patient enters the Clinical Conversation view.
**Script**: "Our AI immediately begins the clinical interview in the patient's language. The patient can use voice or touch to describe their symptoms."
**Action**: Click the Microphone icon, type `Chest pain` into the Mock input, and submit.
**Verification**: The structured clinical history extracts `Chief Complaint: Chest pain` and records it locally against the encounter (`enc_raj_001`). 

## 1:40 - Red Flag Detection (Patient Kiosk)
**Action**: The system processes the answer.
**Script**: "Instantly, our determinist clinical rule engine detects a high-priority Red Flag."
**Action**: The UI displays the red `PRIORITY ALERT` banner.
**Verification**: The RedFlag `CHEST_PAIN_SUDDEN_ONSET` is generated and tied to the encounter. 

## 2:00 - Medical Document Ingestion (Patient Kiosk)
**Action**: The patient continues to the Document Upload screen.
**Script**: "Before seeing the doctor, Raj uploads his previous medical documents to provide context."
**Action**: Upload any dummy PDF and click 'Process'.
**Verification**: The OCR engine (mocked) extracts `Amlodipine 5mg` and `Hb: 10.2` and links them to the timeline via `doc_raj_01`.

## 3:00 - Doctor Receives Patient (Doctor Dashboard)
**Action**: Switch to the Doctor Dashboard `http://localhost:3001/queue`.
**Script**: "Meanwhile, on the physician's workspace, Raj Kumar automatically appears at the top of the queue with a HIGH priority alert."
**Action**: Observe the Queue. Click on `Raj Kumar`.

## 3:40 - The Encounter Workspace (Doctor Dashboard)
**Action**: The Doctor enters the Workspace for `enc_raj_001`.
**Script**: "The doctor is presented with an AI-generated clinical summary, completely synthesized from the kiosk conversation and the OCR documents."
**Action**: Observe the AI Summary Panel and the Red Flag panel.

## 4:00 - Source Provenance (Doctor Dashboard)
**Action**: Navigate to the Document Timeline on the right.
**Script**: "To ensure absolute clinical safety, the doctor can verify every piece of extracted information. Let's look at the Amlodipine extraction."
**Action**: Click on the Document icon. 
**Verification**: The UI explicitly shows the mapping between the structured `Amlodipine 5mg` and the source text `Tab Amlodipine 5mg OD`.

## 4:20 - Summary Edit & Verify (Doctor Dashboard)
**Action**: Click `Edit Summary` in the AI Summary Panel.
**Script**: "The AI assists, but the doctor decides. The physician edits the summary, adding their own observations, and seals the record."
**Action**: Modify text and save. 
**Verification**: The status updates to `DOCTOR_EDITED`.
**Action**: Click `Verify Summary`.
**Verification**: The status updates to `DOCTOR_VERIFIED` and the record is sealed.

## 5:00 - End Demo
**Script**: "In just 5 minutes, we turned a waiting room experience into a highly structured, prioritized, and verified clinical asset for the physician."
