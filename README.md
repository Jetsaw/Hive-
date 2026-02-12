# 🐝 HIVE - MMU Engineering Academic Advisor

An AI-powered chatbot with dual-layer RAG (Retrieval-Augmented Generation) system for academic advising at MMU Engineering Faculty.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+ (for frontend tooling)

### Backend Setup
```bash
cd hive-backend
pip install -r requirements.txt
cp .env.example .env  # Configure your environment
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd hive-frontend
python -m http.server 8080
```

Visit http://localhost:8080 to use the application.

---

## 📁 Project Structure

```
Hive/
├── docs/                       # All documentation
│   ├── guides/                 # Integration & architecture guides
│   ├── testing/                # Testing documentation
│   ├── troubleshooting/        # Troubleshooting guides
│   └── reports/                # Analysis & completion reports
│
├── hive-backend/               # Backend application
│   ├── app/                    # Application code
│   │   ├── agents/             # AI agents (chatbot, retriever, reflection)
│   │   ├── advisor/            # Advisory system (alias resolver, session mgmt)
│   │   ├── api/                # FastAPI routes
│   │   ├── core/               # Core configurations
│   │   ├── memory/             # Conversation memory
│   │   └── rag/                # RAG system (indexer, retriever, router)
│   ├── data/                   # Knowledge base & indices
│   │   ├── indexes/            # FAISS vector indices
│   │   └── kb/                 # Knowledge base files
│   ├── tests/                  # All test files
│   ├── scripts/                # Utility scripts
│   └── test-results/           # Test outputs (gitignored)
│
├── hive-frontend/              # Frontend application
│   ├── index.html              # Main HTML
│   ├── app.js                  # JavaScript logic  
│   └── styles.css              # Styling
│
└── deploy/                     # Deployment configurations
```

---

## 🎯 Features

### Dual-Layer RAG Architecture
- **Structure Layer**: Programme overviews, term structures (76 entries)
- **Details Layer**: Course Q&A pairs (1,270 entries)

### Intelligent Query Routing
- Course code detection (e.g., "ACE6313")
- Alias resolution (e.g., "machine learning" → ACE6313)
- Structure queries (e.g., "Year 2 Trimester 1 subjects")
- Mixed queries (combining structure & details)

### Voice Interaction
- **Speech-to-Text**: Whisper AI
- **Text-to-Speech**: Browser Web Speech API
- Conditional voice playback (text input = no voice, voice input = voice response)

### Session Management
- Programme tracking
- Conversation history
- Context-aware responses

---

## 📚 Documentation

### Guides
- [RAG Integration Guide](docs/guides/rag-integration.md) - How the RAG system works
- [Manual Testing Guide](docs/testing/manual-testing-guide.md) - Comprehensive testing instructions

### Reports
- [Implementation Complete](docs/reports/implementation-complete.md) - Final implementation summary
- [Chatbot Analysis](docs/reports/chatbot-analysis.md) - Accuracy test results
- [Knowledge Base Analysis](docs/reports/kb-files-analysis.md) - KB file comparison

### Troubleshooting
- [Browser Cache Fix](docs/troubleshooting/browser-cache-fix.md) - Fixing cached JavaScript issues

---

## 🧪 Testing

Run tests from the `hive-backend/tests/` directory:

```bash
# Run all component tests
python tests/test_all_components.py

# Run chatbot accuracy tests
python tests/test_chatbot_accuracy.py

# Run RAG system tests
python tests/test_rag_system.py

# Run diagnostic
python tests/run_diagnostic.py
```

---

## 🛠️ Tech Stack

**Backend**:
- FastAPI - Web framework
- DeepSeek - LLM provider
- FAISS - Vector similarity search
- Whisper - Speech-to-text

**Frontend**:
- Vanilla JavaScript
- Web Speech API - Text-to-speech
- CSS3 - Modern styling

**Knowledge Base**:
- 76 programme structure entries
- 1,270 course Q&A pairs
- 282 alias mappings
- 110 routing rules

---

## 📊 System Performance

- **RAG Accuracy**: 98% (verified via automated tests)
- **Alias Resolution**: 100% accuracy
- **Query Routing**: All types handled correctly
- **Structure Index**: 76 vectors
- **Details Index**: 1,270 vectors

---

## 🔑 Environment Variables

Create a `.env` file in `hive-backend/`:

```env
# LLM Configuration
DEEPSEEK_API_KEY=your_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Knowledge Base Paths
KB_DIR=data/kb
INDEX_DIR=data/indexes
```

---

## 🚀 Deployment

See the `deploy/` directory for deployment configurations.

---

## 📝 License

[Add your license here]

---

## 👥 Contributors

[Add contributors here]

---

## 🆘 Support

For issues and questions:
1. Check [troubleshooting guides](docs/troubleshooting/)
2. Review [test results](hive-backend/test-results/)
3. Consult [implementation docs](docs/reports/)

---

**System Status**: 🟢 Production Ready
