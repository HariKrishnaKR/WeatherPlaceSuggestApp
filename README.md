# 🌍 TourAI Guide - Elite AI-Powered Travel & Weather Assistant

An **elite-grade**, modern web app that combines **real-time weather data** with **AI-powered travel recommendations** and an **intelligent tour guide chatbot**. Features beautiful glassmorphic UI, animated loading indicators, and formatted AI responses.

## ✨ Features

✨ **Real-time Weather Data** - Live weather from wttr.in API (no authentication needed)  
🎯 **AI-Powered Recommendations** - Gemini 2.5 Flash suggests top 5 attractions  
💬 **Interactive Tour Guide** - Chat with an AI guide about attractions, culture, safety, tips  
🌡️ **Smart City Correction** - Auto-corrects city name typos via Wikipedia  
🎨 **Modern Elite UI** - Glassmorphism design, premium travel background, smooth animations  
🚩 **Animated Loading** - Rotating country flags while AI prepares responses  
📋 **Click-to-Copy Tips** - Copy travel recommendations directly from chat  
📱 **Fully Responsive** - Optimized for desktop, tablet, and mobile  
🌐 **Internet-Ready** - Deployed on Render for worldwide access

## 🚀 Live Deployment

The app is deployed on **Render** and accessible worldwide:
- **URL:** `https://touraid-guide.onrender.com` (deployed after GitHub push)

**See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions.**

## 📦 Local Development

### Prerequisites
- Python 3.8 or higher
- A Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables
Create a `.env` file in the project root and add:
```
GEMINI_API_KEY=your-gemini-api-key-here
```

Replace `your-gemini-api-key-here` with your actual Gemini API key.

### Step 3: Run the Application
```bash
python app.py
```

or use the run script:
```bash
python run.py
```

The app will start at `http://localhost:5000`

## Usage

1. **Search for a City**: Enter any city name in the search box
2. **View Weather**: See current temperature, humidity, wind speed, and more
3. **Get Recommendations**: View AI-suggested places to visit
4. **Chat with Tour Guide**: Ask questions about attractions, activities, and travel tips

### Example Questions for the Chat:
- "What are the best restaurants here?"
- "What activities are suitable for this weather?"
- "What is the best time to visit?"
- "Tell me about local culture and traditions"
- "What are the safety tips for travelers?"

## Project Structure

```
WeatherPlaceSuggestApp/
├── app.py                 # Flask backend with Gemini integration
├── run.py                 # Run script for easy startup
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in repo)
└── templates/
    └── index.html         # HTML frontend with interactive UI
```

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML, CSS, JavaScript
- **Weather API**: wttr.in (free, no API key required)
- **AI**: Google Gemini API (gemini-1.5-flash)
- **HTTP Requests**: requests library

## API Endpoints

### POST /api/weather
Fetches weather data and place recommendations for a city.

**Request:**
```json
{
  "city": "Paris"
}
```

**Response:**
```json
{
  "weather": {
    "city": "Paris",
    "country": "France",
    "temperature": 12.5,
    "feels_like": 11.2,
    "humidity": 75,
    "pressure": 1013,
    "description": "Partly cloudy",
    "wind_speed": 3.5,
    "clouds": 40,
    "coordinates": {"lat": 48.85, "lon": 2.35}
  },
  "places": {
    "places": [
      {
        "name": "Eiffel Tower",
        "description": "...",
        "Best time to visit": "...",
        "Entry fee": "...",
        "Travel tips": "..."
      }
    ]
  }
}
```

### POST /api/chat
Chat with the AI tour guide.

**Request:**
```json
{
  "message": "What are the best restaurants in this city?"
}
```

**Response:**
```json
{
  "response": "Based on the current weather and your interests, I recommend...",
  "city": "Paris"
}
```

### POST /api/clear
Clear chat history.

## Troubleshooting

### "Could not find weather data for [city]"
- Check your internet connection
- Ensure the city name is spelled correctly
- Try a different city

### "GEMINI_API_KEY not configured"
- Make sure the `.env` file exists in the project root
- Verify the API key is correctly copied from Google AI Studio
- Restart the application after updating the .env file

### Port 5000 already in use
Change the port in `app.py` or `run.py`:
```python
app.run(debug=True, port=8000)  # Use port 8000 instead
```

## Future Enhancements

- 🗺️ Interactive map integration
- 📸 Photo gallery of places
- 🌍 Multi-language support
- 🔖 Save favorite destinations
- 📊 Weather forecast for next 7 days
- 🎟️ Integration with booking systems

## License

Open source project

## Support

For issues or suggestions, please open an issue in the repository.

---

**Made with ❤️ using Flask, Gemini AI, and wttr.in**
