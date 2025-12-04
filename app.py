import os
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")
genai.configure(api_key=GEMINI_API_KEY)

# Weather API - wttr.in (no API key needed)
WEATHER_API_URL = "https://wttr.in"

# Initialize chat history for context
chat_history = []
current_city = None
current_weather = None

def get_weather(city_name):
    """Fetch weather data for a city from wttr.in."""
    try:
        params = {
            "format": "j1"  # JSON format
        }
        response = requests.get(f"{WEATHER_API_URL}/{city_name}", params=params)
        if response.status_code == 200:
            data = response.json()
            
            # Extract current weather data
            current = data['current_condition'][0]
            nearest_area = data['nearest_area'][0]
            
            # Return both the requested city (what user typed) and the resolved area from wttr.in
            weather_info = {
                "requested_city": city_name,
                "resolved_city": nearest_area['areaName'][0]['value'],
                "country": nearest_area['country'][0]['value'],
                "temperature": float(current['temp_C']),
                "feels_like": float(current['FeelsLikeC']),
                "humidity": int(current['humidity']),
                "pressure": int(current['pressure']),
                "description": current['weatherDesc'][0]['value'],
                    "wind_speed": round(float(current['windspeedKmph']) / 3.6, 2),  # Convert to m/s and round to 2 decimals
                "clouds": int(current['cloudcover']),
                "coordinates": {
                    "lat": float(nearest_area['latitude']),
                    "lon": float(nearest_area['longitude'])
                }
            }
            return weather_info
        return None
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None


def _select_model(preferred=None):
    """Try to pick a working generative model. Returns a GenerativeModel instance or None."""
    # If a specific model is provided via environment, try it first
    env_model = os.getenv("GEMINI_MODEL")
    if env_model:
        try:
            return genai.GenerativeModel(env_model)
        except Exception as e:
            print(f"Env GEMINI_MODEL '{env_model}' not available: {e}")

    if preferred is None:
        preferred = [
            "gemini-1.5-flash",
            "gemini-1.5",
            "gemini-1.0",
            "text-bison-001",
            "gpt-4o-mini",
        ]

    # Try preferred names first
    for name in preferred:
        try:
            model = genai.GenerativeModel(name)
            return model
        except Exception:
            continue

    # If preferred list fails, try listing models from the API and pick a likely candidate
    try:
        available = genai.list_models()
        # `available` could be a list of dicts or objects. Normalize.
        for m in available:
            mname = None
            if isinstance(m, dict):
                mname = m.get("name") or m.get("model")
            else:
                mname = getattr(m, "name", None)
            if not mname:
                continue
            # prefer models with known generative names
            lname = mname.lower()
            if any(k in lname for k in ("gemini", "bison", "gpt", "gpt-4", "gpt-4o")):
                try:
                    model = genai.GenerativeModel(mname)
                    return model
                except Exception:
                    continue
    except Exception as e:
        print(f"Error listing models: {e}")

    return None


def _wikipedia_top_places(city_name, limit=5, coords=None):
    """Fetch top candidate places for a city using Wikipedia.
    Prefer geosearch by coordinates when `coords` provided; otherwise use text search
    and favor pages that look like attractions (museum, park, cathedral, tower, temple, beach, garden, market).
    Returns dict {"places": [name1, name2, ...]}.
    """
    try:
        session = requests.Session()
        titles = []

        # Helper to fetch summary for a title
        def fetch_title(title):
            try:
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
                r = session.get(summary_url, timeout=6)
                if r.status_code == 200:
                    data = r.json()
                    return data.get("title") or title
            except Exception:
                return None
            return None

        # If coordinates available, do a geosearch to find nearby notable pages
        if coords and isinstance(coords, dict) and coords.get('lat') and coords.get('lon'):
            lat = coords.get('lat')
            lon = coords.get('lon')
            gs_params = {
                "action": "query",
                "list": "geosearch",
                "gscoord": f"{lat}|{lon}",
                "gsradius": 20000,  # 20 km
                "gslimit": 50,
                "format": "json",
            }
            resp = session.get("https://en.wikipedia.org/w/api.php", params=gs_params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                geolist = data.get('query', {}).get('geosearch', [])
                # Sort by distance and prefer known attraction titles
                attraction_keywords = ('museum', 'park', 'cathedral', 'tower', 'temple', 'church', 'beach', 'garden', 'fort', 'square', 'market', 'palace', 'monument')
                # First pass: collect attraction-like titles
                for g in sorted(geolist, key=lambda x: x.get('dist', 99999)):
                    title = g.get('title')
                    lt = (title or '').lower()
                    if any(k in lt for k in attraction_keywords) and title not in titles:
                        titles.append(title)
                    if len(titles) >= limit:
                        break
                # Second pass: fill with nearby titles if still short
                if len(titles) < limit:
                    for g in sorted(geolist, key=lambda x: x.get('dist', 99999)):
                        title = g.get('title')
                        if title and title not in titles:
                            titles.append(title)
                        if len(titles) >= limit:
                            break

        # If coords didn't produce results, fallback to text search for attractions
        if not titles:
            search_queries = [
                f"things to do in {city_name}",
                f"tourist attractions in {city_name}",
                f"places to visit in {city_name}",
                f"{city_name} attractions",
            ]
            attraction_keywords = ('museum', 'park', 'cathedral', 'tower', 'temple', 'church', 'beach', 'garden', 'fort', 'square', 'market', 'palace', 'monument')
            for q in search_queries:
                params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": q,
                    "format": "json",
                    "srlimit": 20,
                }
                resp = session.get("https://en.wikipedia.org/w/api.php", params=params, timeout=8)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                results = data.get("query", {}).get("search", [])
                for r in results:
                    title = r.get("title")
                    lt = (title or '').lower()
                    if title and title not in titles and any(k in lt for k in attraction_keywords):
                        titles.append(title)
                    if len(titles) >= limit:
                        break
                if len(titles) >= limit:
                    break
            # If still empty, collect generic results
            if not titles:
                for q in search_queries:
                    params = {
                        "action": "query",
                        "list": "search",
                        "srsearch": q,
                        "format": "json",
                        "srlimit": 10,
                    }
                    resp = session.get("https://en.wikipedia.org/w/api.php", params=params, timeout=8)
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    results = data.get("query", {}).get("search", [])
                    for r in results:
                        title = r.get("title")
                        if title and title not in titles:
                            titles.append(title)
                        if len(titles) >= limit:
                            break
                    if len(titles) >= limit:
                        break

        # Fetch readable titles and return up to limit distinct names
        places = []
        for t in titles[:limit]:
            name = fetch_title(t)
            if name and name not in places:
                places.append(name)

        # Final fallback: if still empty, try splitting city into 'City Center' only if nothing else
        if not places:
            return {"places": []}

        return {"places": places}
    except Exception as e:
        print(f"Wikipedia fallback error: {e}")
        return {"places": []}


def resolve_city_name(city_name):
    """Try to resolve/correct the user's city name using Wikipedia search.
    Returns the best-matching title or None if not found."""
    try:
        session = requests.Session()
        params = {
            "action": "query",
            "list": "search",
            "srsearch": city_name,
            "format": "json",
            "srlimit": 1,
        }
        resp = session.get("https://en.wikipedia.org/w/api.php", params=params, timeout=6)
        if resp.status_code != 200:
            return None
        data = resp.json()
        results = data.get("query", {}).get("search", [])
        if not results:
            return None
        best = results[0].get("title")
        return best
    except Exception as e:
        print(f"resolve_city_name error: {e}")
        return None

def get_place_suggestions(city_name, weather_data):
    """Use Gemini to suggest places to visit based on city and weather."""
    try:
        model = _select_model()
        
        prompt = f"""Based on the city '{city_name}' and current weather conditions:
        - Temperature: {weather_data['temperature']}°C
        - Weather: {weather_data['description']}
        - Humidity: {weather_data['humidity']}%
        - Wind Speed: {weather_data['wind_speed']:.2f} m/s
        
        Please suggest 5-7 popular tourist places or attractions to visit in {city_name}. 
        For each place, provide:
        1. Name of the place
        2. What makes it special
        3. Best time to visit (considering current weather)
        4. Entry fee (if known, or "Check locally")
        5. Travel tips
        
        Format your response as a JSON object with a "places" array.
        
        IMPORTANT: Use emojis, bullet points, and numbered lists to make the response visually organized and easy to read.
        Example format for each place:
        - 🏛️ **Place Name**: Brief description
          • Best time: [time info]
          • Fee: [fee info]
          • Tips: [practical tips]"""
        
        # If no model is available, use Wikipedia fallback to return top places
        if model is None:
            print("No generative model available; using Wikipedia fallback for places.")
            return _wikipedia_top_places(city_name, limit=5, coords=weather_data.get('coordinates'))

        # Try generating with the selected model; on failure try alternative models once
        tried = set()
        last_exc = None
        for attempt in range(3):
            try:
                if model is None:
                    model = _select_model()
                if model is None:
                    break
                tried.add(getattr(model, 'name', str(model)))
                response = model.generate_content(prompt)
                response_text = getattr(response, 'text', str(response))
                # Extract JSON from the response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    places_data = json.loads(json_str)
                    # Normalize to list of names (strings) with max length 5
                    if isinstance(places_data, dict) and 'places' in places_data:
                        raw = places_data['places']
                        names = []
                        for item in raw:
                            if isinstance(item, str):
                                names.append(item)
                            elif isinstance(item, dict):
                                nm = item.get('name') or item.get('title')
                                if nm:
                                    names.append(nm)
                        return {'places': names[:5]}
                    # If it's already a list of strings
                    if isinstance(places_data, list):
                        names = []
                        for item in places_data:
                            if isinstance(item, str):
                                names.append(item)
                            elif isinstance(item, dict):
                                nm = item.get('name') or item.get('title')
                                if nm:
                                    names.append(nm)
                        return {'places': names[:5]}
                    return {'places': []}
                else:
                    # If no JSON, try to parse lines for place names
                    lines = [l.strip() for l in response_text.splitlines() if l.strip()]
                    # Build simple place entries from top lines
                    names = []
                    for l in lines[:5]:
                        names.append(l[:120])
                    if names:
                        return {'places': names}
                # if we get here, break and fallback
                break
            except Exception as e:
                print(f"Model generation error (attempt {attempt+1}): {e}")
                last_exc = e
                # try selecting a different model next attempt
                model = _select_model(preferred=None)

        # If generation failed, use Wikipedia fallback
        print(f"All model attempts failed: {last_exc}; using Wikipedia fallback.")
        return _wikipedia_top_places(city_name, limit=5, coords=weather_data.get('coordinates'))
    except Exception as e:
        print(f"Error getting place suggestions: {e}")
        return {"places": [{"error": str(e)}]}

def chat_with_tour_guide(user_message):
    """Chat with the AI tour guide about the city and weather."""
    global chat_history, current_city, current_weather
    
    try:
        model = _select_model()

        # Build context message with current city and weather info
        context = f"""You are an expert tour guide and weather expert. You help users learn about cities, 
        attractions, and travel planning based on weather conditions.
        
        Current City: {current_city}
        Current Weather: {current_weather['description']} at {current_weather['temperature']}°C
        Humidity: {current_weather['humidity']}%, Wind Speed: {current_weather['wind_speed']:.2f} m/s
        
        Answer user questions about:
        - Places to visit in {current_city}
        - Weather and how it affects activities
        - Travel tips and recommendations
        - Local culture and attractions
        - Safety and best practices for visiting
        
        Be conversational, helpful, and provide specific recommendations based on the weather.
        
        FORMATTING REQUIREMENTS:
        📍 Use relevant emojis (🏨 hotel, 🍽️ restaurant, 🎭 culture, 🏛️ museum, 🏖️ beach, 🥾 hiking, 🎪 entertainment, etc.)
        📝 Organize responses with:
           • Numbered lists (1. Item, 2. Item) for main points
           • Bullet points (• Sub-point) for details and tips
           • **Bold text** for emphasis on important locations/times
           • *Italics* for additional context
        ✨ Make responses visually structured and easy to scan"""
        
        # Add user message to chat history
        chat_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Create messages for API
        messages = [{"role": "user", "content": context}]
        
        # Add chat history
        for msg in chat_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Try generating with selected model; if unavailable or errors occur, retry a couple times
        last_exc = None
        if model is None:
            print("No generative model available for chat; will attempt to list models.")

        for attempt in range(3):
            try:
                if model is None:
                    model = _select_model()
                if model is None:
                    break
                response = model.generate_content(
                    [msg["content"] for msg in messages] if len(messages) > 1 else user_message
                )
                assistant_response = getattr(response, 'text', str(response))
                break
            except Exception as e:
                print(f"Chat model generation error (attempt {attempt+1}): {e}")
                last_exc = e
                model = _select_model(preferred=None)

        if not 'assistant_response' in locals() or assistant_response is None:
            print(f"All chat model attempts failed: {last_exc}")
            # Basic fallback reply when model generation fails
            desc = current_weather.get('description') if current_weather else 'current conditions'
            assistant_response = (
                f"I don't have access to the AI model right now. Quick tip: "
                f"Based on {desc} in {current_city}, consider outdoor visits in the morning and "
                f"indoor activities in the afternoon. You can ask more specific questions and I'll help."
            )
        
        # Add assistant response to chat history
        chat_history.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        return assistant_response
    except Exception as e:
        print(f"Error in chat: {e}")
        return f"I apologize, but I encountered an error: {str(e)}"

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/weather', methods=['POST'])
def weather_endpoint():
    """API endpoint to get weather and place suggestions."""
    global current_city, current_weather, chat_history
    
    try:
        data = request.json
        city_name = data.get('city', '').strip()

        if not city_name:
            return jsonify({"error": "City name is required"}), 400

        # Attempt to correct common typos / resolve to canonical city name via Wikipedia
        corrected = resolve_city_name(city_name)
        query_city = corrected if corrected and corrected.lower() != city_name.lower() else city_name

        # Fetch weather using the corrected or original query city
        weather_data = get_weather(query_city)
        if not weather_data:
            return jsonify({"error": f"Could not find weather data for {city_name}"}), 404

        # Store current city (what user typed) and current weather (from wttr.in)
        current_city = city_name
        current_weather = weather_data
        chat_history = []  # Reset chat history for new city

        # Get place suggestions using the corrected/canonical city name
        suggestions = get_place_suggestions(query_city, weather_data)

        response_data = {
            "weather": weather_data,
            "requested_city": city_name,
            "corrected_city": corrected if corrected and corrected.lower() != city_name.lower() else None,
            "places": suggestions.get('places', []) if isinstance(suggestions, dict) else suggestions
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        print(f"Error in weather endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """API endpoint for chatbot interaction."""
    global current_city
    
    try:
        if not current_city:
            return jsonify({"error": "Please enter a city first"}), 400
        
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Get chat response
        response_text = chat_with_tour_guide(message)
        
        return jsonify({
            "response": response_text,
            "city": current_city
        }), 200
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_chat():
    """Clear chat history."""
    global chat_history
    chat_history = []
    return jsonify({"status": "Chat cleared"}), 200

if __name__ == '__main__':
    print("=" * 60)
    print("🌍 TourAI Guide - Weather & Travel Assistant")
    print("=" * 60)
    print("✅ Server starting...")
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("=" * 60)
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    app.run(debug=True, port=5000, use_reloader=False)
