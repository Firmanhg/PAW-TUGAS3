# Product Review Analyzer

Aplikasi web untuk menganalisis sentiment review produk menggunakan AI (Hugging Face & Gemini)

## 👨‍💻 Dibuat Oleh
- **Nama**: Firman H Gultom
- **NIM**: 123140171
- **GitHub**: [https://github.com/Firmanhg/PAW-TUGAS3.git]

## 📋 Fitur

1. ✅ Input review produk (text)
2. ✅ Analisis sentiment (positive/negative/neutral) menggunakan Hugging Face
3. ✅ Extract key points menggunakan Gemini AI
4. ✅ Display hasil analysis di React frontend
5. ✅ Simpan hasil ke PostgreSQL database
6. ✅ Lihat semua review yang pernah dianalisis

## 🛠️ Teknologi yang Digunakan

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **Hugging Face Transformers** - Sentiment analysis
- **Google Gemini AI** - Key points extraction
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database

### Frontend
- **React.js** - UI framework
- **Axios** - HTTP client
- **CSS3** - Styling

## 📦 Instalasi

### Prerequisites
- Node.js (v16+)
- Python (v3.8+)
- PostgreSQL (v12+)
- Gemini API Key

### 1. Clone Repository

```bash
git clone [your-github-repo-url]
cd product-review-analyzer
```

### 2. Setup Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Buat file .env
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/review_db" > .env
echo "GEMINI_API_KEY=your_gemini_api_key_here" >> .env

# Jalankan backend
python app.py
```

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Jalankan frontend
npm start
```

### 4. Setup Database

```sql
-- Buat database di PostgreSQL
CREATE DATABASE review_db;
```

## 🚀 Cara Menggunakan

1. Buka browser di `http://localhost:3000`
2. Ketik review produk di form input
3. Klik tombol "Analisis Review"
4. Lihat hasil analisis sentiment dan key points
5. Scroll ke bawah untuk melihat semua review yang pernah dianalisis

## 📡 API Endpoints

### POST `/api/analyze-review`
Menganalisis review baru

**Request Body:**
```json
{
  "review_text": "Produk bagus, pengiriman cepat!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "review_text": "Produk bagus, pengiriman cepat!",
    "sentiment": "positive",
    "confidence": "99.87%",
    "key_points": "- Kualitas produk memuaskan\n- Pengiriman cepat...",
    "created_at": "2025-12-12T10:30:00"
  }
}
```

### GET `/api/reviews`
Mengambil semua review

**Response:**
```json
{
  "success": true,
  "count": 10,
  "data": [...]
}
```

## 📊 Database Schema

**Table: reviews**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| review_text | TEXT | Review dari user |
| sentiment | VARCHAR(20) | positive/negative/neutral |
| confidence | VARCHAR(10) | Confidence score |
| key_points | TEXT | Key points dari Gemini |
| created_at | DATETIME | Timestamp |
<img width="888" height="297" alt="image" src="https://github.com/user-attachments/assets/3ef0a095-3613-4c91-bd3a-2e79dbb925e6" />


## 🎯 Error Handling

- ✅ Loading states saat proses analisis
- ✅ Error messages untuk input kosong
- ✅ Error handling untuk API failures
- ✅ Database connection error handling

## 📸 Screenshots
## Negative Review
<img width="1896" height="975" alt="image" src="https://github.com/user-attachments/assets/45ae861f-95ce-4b09-b21b-f460205fa304" />
## Positive Review
<img width="996" height="787" alt="image" src="https://github.com/user-attachments/assets/47360a2f-71ae-414c-93de-92bd3d6e9786" />
## Neutral Review
<img width="987" height="563" alt="image" src="https://github.com/user-attachments/assets/f061fc1e-376c-4aae-a96a-1d3c56a1ed93" />


## 🔮 Future Improvements

- [ ] Export hasil analisis ke PDF
- [ ] Filter review berdasarkan sentiment
- [ ] Grafik statistik sentiment
- [ ] Support multiple languages
- [ ] User authentication

## 📄 License

MIT License

## 📞 Contact

Untuk pertanyaan atau saran, silakan hubungi:
- GitHub: [https://github.com/Firmanhg/PAW-TUGAS3.git]

---
