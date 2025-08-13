# TIA Hardware OCR Extractor

Use OCR to extract device data from **TIA Portal** hardware configuration screenshots and prepare it for database storage.  
> **Internal use only. Not intended for public distribution.** 
---

## Why

TIA Portal does not provide a standalone export of the **hardware configuration**, yet a custom event/alerting system developed by the company I work for needs a list of devices with their IP addresses and names.  
This tool processes screenshots of the hardware configuration, runs OCR, extracts relevant fields, normalizes them, and generates a text file ready for later import into a database.

---

## What it does

1. Accepts a screenshot of the TIA Portal hardware configuration.
2. Pre-processes the image (deskew, denoise, contrast/threshold).
3. Runs OCR to read IP addresses, device names and related labels.
4. Parses and validates extracted entities (e.g., IPv4 format).
5. Generates a text file with results (and optional JSON/CSV).
6. **Prepares** the data for a future database write/integration (DB write is optional and can be disabled; by default, no write is performed).

---

## Features

- Image preprocessing
- OCR pipeline
- Parsing heuristics tailored to TIA Portal screenshots
- Outputs `devices.txt` (optional JSON/CSV — planned)
- Optional database integration hook (planned)

---

> The tool relies on TIA Portal as the **source of truth** (via screenshots).

---
