from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import google.generativeai as genai
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gemini_model = genai.GenerativeModel('gemini-pro')

# Configure Database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/review_db')
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Load Hugging Face sentiment analysis model
print("Loading sentiment analysis model...")
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print("Model loaded successfully!")

# Database Model
class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    review_text = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=False)
    confidence = Column(String(10), nullable=False)
    key_points = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(engine)

@app.route('/')
def home():
    return jsonify({
        "message": "Product Review Analyzer API",
        "status": "running",
        "endpoints": {
            "POST /api/analyze-review": "Analyze a new review",
            "GET /api/reviews": "Get all reviews"
        }
    })

@app.route('/api/analyze-review', methods=['POST'])
def analyze_review():
    try:
        # Get review text from request
        data = request.get_json()
        review_text = data.get('review_text', '')
        
        if not review_text:
            return jsonify({"error": "Review text is required"}), 400
        
        # Step 1: Analyze sentiment using Hugging Face
        print(f"Analyzing sentiment for: {review_text[:50]}...")
        sentiment_result = sentiment_analyzer(review_text[:512])[0]  # Limit to 512 chars for model
        
        # Map sentiment
        sentiment_label = sentiment_result['label'].lower()
        if sentiment_label == 'positive':
            sentiment = 'positive'
        elif sentiment_label == 'negative':
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        confidence = f"{sentiment_result['score']:.2%}"
        
        # Step 2: Extract key points using Gemini
        print("Extracting key points with Gemini...")
        prompt = f"""Analyze this product review and extract 3-5 key points in Indonesian language.
Review: {review_text}

Format your response as bullet points starting with - 
Be concise and focus on the most important aspects mentioned."""
        
        gemini_response = gemini_model.generate_content(prompt)
        key_points = gemini_response.text
        
        # Step 3: Save to database
        session = Session()
        new_review = Review(
            review_text=review_text,
            sentiment=sentiment,
            confidence=confidence,
            key_points=key_points
        )
        session.add(new_review)
        session.commit()
        review_id = new_review.id
        session.close()
        
        # Return results
        return jsonify({
            "success": True,
            "data": {
                "id": review_id,
                "review_text": review_text,
                "sentiment": sentiment,
                "confidence": confidence,
                "key_points": key_points,
                "created_at": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        session = Session()
        reviews = session.query(Review).order_by(Review.created_at.desc()).all()
        
        reviews_list = []
        for review in reviews:
            reviews_list.append({
                "id": review.id,
                "review_text": review.review_text,
                "sentiment": review.sentiment,
                "confidence": review.confidence,
                "key_points": review.key_points,
                "created_at": review.created_at.isoformat()
            })
        
        session.close()
        
        return jsonify({
            "success": True,
            "count": len(reviews_list),
            "data": reviews_list
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n🚀 Starting Product Review Analyzer API...")
    print("📊 Database connected")
    print("🤖 AI models loaded")
    print("✅ Server running on http://localhost:5000\n")
    app.run(debug=True, port=5000)