# app.py (improved resilient version)
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
import threading
import traceback

load_dotenv()

# Config
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./reviews.db"  # default: sqlite file in project folder
)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)
PORT = int(os.getenv("PORT", 5000))

# Flask app
app = Flask(__name__)
CORS(app)

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    review_text = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=False)
    confidence = Column(String(20), nullable=True)
    key_points = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# NLP models (lazy-loaded)
_sentiment_model = None
_summary_model = None
_gemini_client = None
_model_lock = threading.Lock()

def load_transformers_sentiment():
    global _sentiment_model
    try:
        from transformers import pipeline
    except Exception as e:
        app.logger.warning("transformers not available: %s", e)
        return None
    with _model_lock:
        if _sentiment_model is None:
            try:
                # small sentiment model
                _sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
            except Exception as e:
                app.logger.exception("Failed loading sentiment model: %s", e)
                _sentiment_model = None
    return _sentiment_model

def load_transformers_summarizer():
    global _summary_model
    try:
        from transformers import pipeline
    except Exception as e:
        app.logger.warning("transformers not available: %s", e)
        return None
    with _model_lock:
        if _summary_model is None:
            try:
                # try a reasonably small summarizer (may still be large)
                _summary_model = pipeline("summarization")
            except Exception as e:
                app.logger.exception("Failed loading summarizer model: %s", e)
                _summary_model = None
    return _summary_model

def load_gemini():
    global _gemini_client
    if not GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
    except Exception as e:
        app.logger.warning("google.generativeai not installed: %s", e)
        return None
    with _model_lock:
        if _gemini_client is None:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # keep module reference - use genai.GenerativeModel when needed
                _gemini_client = genai
            except Exception as e:
                app.logger.exception("Failed to configure Gemini: %s", e)
                _gemini_client = None
    return _gemini_client

# Simple fallback sentiment (keyword based)
_positive_words = {"baik", "enak", "lezat", "mantap", "bagus", "recommended", "rekomendasi", "love", "liked", "penuh", "worth"}
_negative_words = {"tidak", "buruk", "sepi", "buruk", "kecewa", "asin", "pahit", "lambat", "mahal", "murah", "kurang"}

def fallback_sentiment(text: str):
    text_lower = text.lower()
    pos = sum(1 for w in _positive_words if w in text_lower)
    neg = sum(1 for w in _negative_words if w in text_lower)
    if pos > neg:
        return "positive", "fallback"
    if neg > pos:
        return "negative", "fallback"
    return "neutral", "fallback"

def analyze_sentiment(text: str):
    model = load_transformers_sentiment()
    if model:
        try:
            res = model(text[:512])[0]
            label = res.get("label", "").lower()
            score = res.get("score", 0.0)
            if "pos" in label:
                return "positive", f"{score:.2%}"
            if "neg" in label:
                return "negative", f"{score:.2%}"
            return "neutral", f"{score:.2%}"
        except Exception as e:
            app.logger.exception("Error running sentiment model: %s", e)
            return fallback_sentiment(text)
    else:
        return fallback_sentiment(text)

def extract_key_points(text: str, max_points=5):
    # Try Gemini first (if configured)
    gem = load_gemini()
    if gem:
        try:
            model = gem.GenerativeModel("gemini-pro")
            prompt = f"Extract up to {max_points} concise bullet points (in Indonesian) from the following restaurant/food review. Focus on food quality, portion, price, service, ambience, and other concrete observations.\n\nReview:\n{text}\n\nRespond as bullet points starting with '- '"
            resp = model.generate_content(prompt)
            # some gemini responses have .text
            kp = getattr(resp, "text", str(resp))
            return kp.strip()
        except Exception as e:
            app.logger.exception("Gemini extraction failed: %s", e)
            # fallback to transformers or simple method below

    # If summarizer available, use it
    summarizer = load_transformers_summarizer()
    if summarizer:
        try:
            out = summarizer(text, max_length=80, min_length=20, do_sample=False)
            summary = out[0].get("summary_text", "")
            bullets = [s.strip() for s in summary.split(".") if s.strip()]
            return "\n".join(f"- {b}" for b in bullets[:max_points])
        except Exception as e:
            app.logger.exception("Summarizer failed: %s", e)

    # Final fallback: naive extraction - split sentences and pick first few
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    picks = sentences[:max_points]
    return "\n".join(f"- {s.strip()}" for s in picks if s.strip())

# Routes
@app.route("/")
def home():
    return jsonify({
        "message": "Food Review Analyzer API (Flask)",
        "status": "running",
        "endpoints": {
            "POST /api/analyze-review": "Analyze a new food review. JSON: {\"review_text\":\"...\"}",
            "GET /api/reviews": "Get all saved reviews"
        }
    })

@app.route("/api/analyze-review", methods=["POST"])
def analyze_review():
    try:
        payload = request.get_json(silent=True) or {}
        review_text = payload.get("review_text") or payload.get("content") or ""
        if not isinstance(review_text, str) or not review_text.strip():
            return jsonify({"error": "Field 'review_text' is required"}), 400

        sentiment, confidence = analyze_sentiment(review_text)
        key_points = extract_key_points(review_text)

        # Save
        db = SessionLocal()
        new = Review(
            review_text=review_text.strip(),
            sentiment=sentiment,
            confidence=confidence,
            key_points=key_points
        )
        db.add(new)
        db.commit()
        db.refresh(new)
        db.close()

        return jsonify({"success": True, "data": {
            "id": new.id,
            "review_text": new.review_text,
            "sentiment": new.sentiment,
            "confidence": new.confidence,
            "key_points": new.key_points,
            "created_at": new.created_at.isoformat()
        }})
    except Exception as e:
        app.logger.exception("analyze_review error: %s", e)
        return jsonify({"error": "internal server error", "detail": str(e)}), 500

@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    try:
        db = SessionLocal()
        rows = db.query(Review).order_by(Review.created_at.desc()).all()
        db.close()
        data = []
        for r in rows:
            data.append({
                "id": r.id,
                "review_text": r.review_text,
                "sentiment": r.sentiment,
                "confidence": r.confidence,
                "key_points": r.key_points,
                "created_at": r.created_at.isoformat()
            })
        return jsonify({"success": True, "count": len(data), "data": data})
    except Exception as e:
        app.logger.exception("get_reviews error: %s", e)
        return jsonify({"error": "internal server error", "detail": str(e)}), 500

if __name__ == "__main__":
    app.logger.info("Starting Food Review Analyzer (Flask)")
    app.logger.info("Database: %s", DATABASE_URL)
    if GEMINI_API_KEY:
        app.logger.info("Gemini API key available - Gemini will be used for keypoints if configured")
    else:
        app.logger.info("Gemini API key NOT set - using local summarizer / fallback for key points")
    app.run(debug=True, host="0.0.0.0", port=PORT)
