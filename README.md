# 🧠 TDS Virtual TA – Jan 2025

This project is a Virtual Teaching Assistant for the "Tools in Data Science - Jan 2025" course from IIT Madras. It uses a Retrieval-Augmented Generation (RAG) pipeline to answer student queries using course material and Discourse forum discussions.

---


### 1. 📥 Source Data

- **Course Data from GitHub**  
  Official markdown files from:  
  [`sanand0/tools-in-data-science-public`](https://github.com/sanand0/tools-in-data-science-public/tree/tds-2025-01)



- **Discourse Data via API**  
  Collect posts and replies using the JSON API responses from:  
  [https://discourse.onlinedegree.iitm.ac.in](https://discourse.onlinedegree.iitm.ac.in)

  

---

### 2. 🔧 Preparing the Data

- **Convert to Markdown**  
  Normalize all data into clean markdown.  


- **Chunk and Embed Text**  
  - Use overlapping chunks to retain context.
  - Generate embeddings using `OpenAI`’s `text-embedding-3-small` model.
  - Store efficiently using `.npz` format.  


- **Rate Limit Awareness**

---

### 3. ⚙️ Application Development

- **Framework:** `FastAPI`
- **Features:**
  - Accepts question (and optionally image)
  - Retrieves top relevant chunks using cosine similarity on precomputed embeddings
  - Calls OpenAI's `gpt-4o-mini` (or configurable model) with system prompt and top chunks
  - Returns concise, Markdown-formatted answers

---

### 4. 🚀 Deployment

- **Platform:** [Vercel](https://vercel.com)  
  > ✅ *Advantage:* Always-on with seamless HTTPS  

---

### 5. ✅ Testing & Validation

- **Framework:** [Promptfoo](https://promptfoo.dev)
- **Evaluation Strategy:**
  - Create a YAML test config
  - Compare answers against known good patterns
  - Validate `output.answer` and links for relevance and quality

---

## 📦 Requirements

```txt
fastapi
uvicorn
openai
python-dotenv
numpy
scipy
pytesseract
pillow

To get started, set your OPENAI_API_KEY environment variable, or other required keys for the providers you selected.

Next, edit promptfooconfig.yaml.

Then run:
```
promptfoo eval
```

Afterwards, you can view the results by running `promptfoo view`
