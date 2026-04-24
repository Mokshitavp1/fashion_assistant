## Setup

1. Clone the repo
   git clone https://github.com/YOUR_USERNAME/fashion_assistant.git
   cd fashion_assistant

2. Create virtual environment
   python -m venv .venv
   .venv\Scripts\Activate.ps1

3. Install dependencies
   pip install -r requirements.txt

4. Set up environment variables
   copy .env.example .env
   then edit .env and fill in your SECRET_KEY

5. Run backend
   uvicorn backend.main:app --reload

6. Run frontend (new terminal)
   cd frontend
   npm install
   npm run dev
