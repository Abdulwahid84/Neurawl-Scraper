# 🧠 Neurawl Scraper

An AI-powered web scraper that can extract **structured data from any website using natural language prompts**.

> 🚧 This project is currently in early development.

---

## ✨ Overview

Neurawl Scraper combines traditional web scraping with AI to make data extraction easier and more flexible.

Instead of manually writing selectors (like XPath or CSS), you can:

1. Provide a website URL
2. Describe what data you want
3. Let AI handle the extraction

This approach makes scraping more adaptable to modern websites.

---

## ⚙️ How It Works

The project follows a simple pipeline:

### 1. Fetch Website Content

* Uses a browser automation tool (like Selenium)
* Loads the full webpage (including JavaScript)
* Extracts raw DOM/text content

### 2. Process the Content

* Cleans and structures the scraped HTML
* Splits large content into manageable chunks

### 3. AI-Based Extraction

* User provides a prompt (e.g., *"Get all product names and prices"*)
* The content + prompt is sent to an LLM
* The AI understands the page and extracts relevant data

👉 Unlike traditional scrapers, AI focuses on **meaning, not just HTML structure**, making it more resilient to layout changes ([GoProxy][1])

### 4. Output

* Returns structured data (JSON/table/text)
* Can be extended to save results or integrate APIs

---

## 🧩 Tech Stack (Planned / Current)

* Python
* Selenium (for scraping dynamic sites)
* Streamlit (for UI)
* LLM APIs (for intelligent parsing)

---

## 🚀 Current Status

* [x] Basic scraping setup
* [x] DOM extraction
* [ ] AI parsing integration
* [ ] Output formatting
* [ ] Error handling & scaling

---

## 📌 Example Flow

```bash
1. Enter URL → https://example.com
2. Click "Scrape"
3. Enter prompt → "Extract all product titles and prices"
4. Get structured output
```

---

## 🎯 Goals

* Make scraping **simpler and more intuitive**
* Reduce dependency on fragile selectors
* Enable scraping of **any site using plain English**

---

## ⚠️ Notes

* Some websites may block scraping (CAPTCHAs, rate limits, etc.)
* Future versions may include proxy support and scaling tools

---

## 📖 Inspiration

This project is inspired by modern AI scraping approaches where:

* AI analyzes page structure
* Understands content semantically
* Extracts data based on user intent

---

## 🤝 Contributing

Still early-stage — contributions, ideas, and feedback are welcome!
