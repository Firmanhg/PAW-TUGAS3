import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [reviewText, setReviewText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [allReviews, setAllReviews] = useState([]);
  const [error, setError] = useState('');

  // Fetch all reviews on component mount
  useEffect(() => {
    fetchAllReviews();
  }, []);

  const fetchAllReviews = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/reviews');
      setAllReviews(response.data.data);
    } catch (err) {
      console.error('Error fetching reviews:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!reviewText.trim()) {
      setError('Silakan masukkan review produk');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post('http://localhost:5000/api/analyze-review', {
        review_text: reviewText
      });

      setResult(response.data.data);
      setReviewText('');
      fetchAllReviews(); // Refresh the list
    } catch (err) {
      setError('Terjadi kesalahan: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment) => {
    switch(sentiment) {
      case 'positive': return '#22c55e';
      case 'negative': return '#ef4444';
      case 'neutral': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const getSentimentEmoji = (sentiment) => {
    switch(sentiment) {
      case 'positive': return '😊';
      case 'negative': return '😞';
      case 'neutral': return '😐';
      default: return '🤔';
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>🍽️ Food Review Analyzer</h1>
        <p>Analisis sentiment review makanan & restoran menggunakan AI</p>
      </header>

      <main className="main-content">
        {/* Input Form */}
        <div className="card">
          <h2>Masukkan Review Produk</h2>
          <form onSubmit={handleSubmit}>
            <textarea
              className="review-input"
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              placeholder="Contoh: Produk ini sangat bagus, kualitas terbaik dan pengiriman cepat!"
              rows="5"
              disabled={loading}
            />
            
            <button 
              type="submit" 
              className="submit-button"
              disabled={loading}
            >
              {loading ? '⏳ Menganalisis...' : '🔍 Analisis Review'}
            </button>
          </form>

          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}
        </div>

        {/* Analysis Result */}
        {result && (
          <div className="card result-card">
            <h2>📊 Hasil Analisis</h2>
            
            <div className="result-item">
              <strong>Review:</strong>
              <p>{result.review_text}</p>
            </div>

            <div className="sentiment-badge" style={{backgroundColor: getSentimentColor(result.sentiment)}}>
              <span className="sentiment-emoji">{getSentimentEmoji(result.sentiment)}</span>
              <span className="sentiment-text">
                Sentiment: {result.sentiment.toUpperCase()}
              </span>
              <span className="confidence">Confidence: {result.confidence}</span>
            </div>

            <div className="result-item">
              <strong>Key Points:</strong>
              <div className="key-points">
                {result.key_points}
              </div>
            </div>
          </div>
        )}

        {/* All Reviews */}
        <div className="card">
          <h2>📚 Semua Review ({allReviews.length})</h2>
          
          {allReviews.length === 0 ? (
            <p className="no-data">Belum ada review. Silakan analisis review pertama Anda!</p>
          ) : (
            <div className="reviews-list">
              {allReviews.map((review) => (
                <div key={review.id} className="review-item">
                  <div className="review-header">
                    <span 
                      className="sentiment-badge-small" 
                      style={{backgroundColor: getSentimentColor(review.sentiment)}}
                    >
                      {getSentimentEmoji(review.sentiment)} {review.sentiment}
                    </span>
                    <span className="review-date">
                      {new Date(review.created_at).toLocaleString('id-ID')}
                    </span>
                  </div>
                  
                  <p className="review-text">{review.review_text}</p>
                  
                  <details className="key-points-details">
                    <summary>Lihat Key Points</summary>
                    <div className="key-points-content">
                      {review.key_points}
                    </div>
                  </details>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <footer className="footer">
        <p>Dibuat dengan ❤️ menggunakan React, Flask, Hugging Face & Gemini AI</p>
      </footer>
    </div>
  );
}

export default App;