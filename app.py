from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import joblib
import os
import re
from typing import Dict, List, Any
import uuid

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False

# Import your real dataset model
from model import AdvancedCropRecommendationModel  

app = Flask(__name__)
CORS(app)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Store OTPs temporarily
OTP_STORE = {}

# Crop profit data (same as before)
CROP_PROFIT_DATA = {
    'rice': {'cost_per_ha': 45000, 'yield_per_ha': 4500, 'price_per_kg': 25, 'season': 'Monsoon (June - October)', 'growth_period': '120-150 days'},
    'wheat': {'cost_per_ha': 40000, 'yield_per_ha': 3500, 'price_per_kg': 30, 'season': 'Winter (November - April)', 'growth_period': '110-130 days'},
    'corn': {'cost_per_ha': 35000, 'yield_per_ha': 5000, 'price_per_kg': 22, 'season': 'Monsoon / Winter (Jun - Nov)', 'growth_period': '90-120 days'},
    'maize': {'cost_per_ha': 35000, 'yield_per_ha': 5000, 'price_per_kg': 22, 'season': 'Monsoon / Winter (Jun - Nov)', 'growth_period': '90-120 days'},
    'cotton': {'cost_per_ha': 65000, 'yield_per_ha': 600, 'price_per_kg': 85, 'season': 'Monsoon (May - June sowing)', 'growth_period': '160-200 days'},
    'sugarcane': {'cost_per_ha': 85000, 'yield_per_ha': 80000, 'price_per_kg': 4, 'season': 'Winter / Spring (Jan - March)', 'growth_period': '10-12 months'},
    'tomato': {'cost_per_ha': 75000, 'yield_per_ha': 30000, 'price_per_kg': 20, 'season': 'Winter / Summer (Oct - March)', 'growth_period': '90-110 days'},
    'potato': {'cost_per_ha': 60000, 'yield_per_ha': 25000, 'price_per_kg': 15, 'season': 'Winter (October - November sowing)', 'growth_period': '90-120 days'},
    'onion': {'cost_per_ha': 55000, 'yield_per_ha': 18000, 'price_per_kg': 22, 'season': 'Winter / Monsoon (Oct - July)', 'growth_period': '120-150 days'},
    'barley': {'cost_per_ha': 38000, 'yield_per_ha': 3000, 'price_per_kg': 28, 'season': 'Winter (October - November)', 'growth_period': '100-120 days'},
    'mustard': {'cost_per_ha': 32000, 'yield_per_ha': 1500, 'price_per_kg': 55, 'season': 'Winter (September - October)', 'growth_period': '100-120 days'},
    'groundnut': {'cost_per_ha': 48000, 'yield_per_ha': 2200, 'price_per_kg': 60, 'season': 'Monsoon (June - July)', 'growth_period': '120-150 days'},
    'soybean': {'cost_per_ha': 44000, 'yield_per_ha': 2500, 'price_per_kg': 48, 'season': 'Monsoon (June - July)', 'growth_period': '90-110 days'},
    'pigeonpeas': {'cost_per_ha': 32000, 'yield_per_ha': 1800, 'price_per_kg': 75, 'season': 'Monsoon (June - July)', 'growth_period': '150-180 days'},
    'kidneybeans': {'cost_per_ha': 35000, 'yield_per_ha': 1500, 'price_per_kg': 80, 'season': 'Winter (Oct - Nov)', 'growth_period': '90-110 days'},
    'chickpea': {'cost_per_ha': 30000, 'yield_per_ha': 2000, 'price_per_kg': 65, 'season': 'Winter (October - November)', 'growth_period': '100-120 days'},
    'banana': {'cost_per_ha': 110000, 'yield_per_ha': 65000, 'price_per_kg': 12, 'season': 'Monsoon / Summer (Year-round)', 'growth_period': '12-14 months'},
    'mango': {'cost_per_ha': 130000, 'yield_per_ha': 12000, 'price_per_kg': 45, 'season': 'Summer (Harvest: April - July)', 'growth_period': '3-5 years for maturity'},
    'tea': {'cost_per_ha': 160000, 'yield_per_ha': 2800, 'price_per_kg': 180, 'season': 'Monsoon / Autumn', 'growth_period': 'Perennial crop'},
    'coffee': {'cost_per_ha': 190000, 'yield_per_ha': 2200, 'price_per_kg': 250, 'season': 'Winter (Nov - Feb)', 'growth_period': 'Perennial crop'},
    'jute': {'cost_per_ha': 52000, 'yield_per_ha': 2700, 'price_per_kg': 45, 'season': 'Spring / Monsoon (March - May)', 'growth_period': '120-150 days'},
    'sunflower': {'cost_per_ha': 38000, 'yield_per_ha': 2000, 'price_per_kg': 60, 'season': 'Summer / Winter / Monsoon', 'growth_period': '90-110 days'},
    'sesame': {'cost_per_ha': 32000, 'yield_per_ha': 1000, 'price_per_kg': 100, 'season': 'Monsoon / Summer', 'growth_period': '80-100 days'},
    'lentil': {'cost_per_ha': 30000, 'yield_per_ha': 1500, 'price_per_kg': 70, 'season': 'Winter (October - November)', 'growth_period': '100-120 days'},
    'blackgram': {'cost_per_ha': 34000, 'yield_per_ha': 1300, 'price_per_kg': 75, 'season': 'Monsoon / Summer', 'growth_period': '80-100 days'},
    'greengram': {'cost_per_ha': 32000, 'yield_per_ha': 1100, 'price_per_kg': 80, 'season': 'Monsoon / Summer', 'growth_period': '70-90 days'},
    'cashew': {'cost_per_ha': 110000, 'yield_per_ha': 2500, 'price_per_kg': 130, 'season': 'Summer (Harvest: Feb - May)', 'growth_period': '3-5 years'},
    'grapes': {'cost_per_ha': 150000, 'yield_per_ha': 30000, 'price_per_kg': 40, 'season': 'Winter / Summer', 'growth_period': '150-180 days'},
    'apple': {'cost_per_ha': 180000, 'yield_per_ha': 15000, 'price_per_kg': 100, 'season': 'Autumn (Harvest: Aug - Oct)', 'growth_period': 'Perennial (5-8 years)'},
    'papaya': {'cost_per_ha': 95000, 'yield_per_ha': 45000, 'price_per_kg': 15, 'season': 'Monsoon / Winter', 'growth_period': '9-11 months'},
    'pineapple': {'cost_per_ha': 120000, 'yield_per_ha': 35000, 'price_per_kg': 25, 'season': 'Monsoon (May - July)', 'growth_period': '15-18 months'},
    'cabbage': {'cost_per_ha': 45000, 'yield_per_ha': 35000, 'price_per_kg': 12, 'season': 'Winter (Oct - Nov sowing)', 'growth_period': '90-120 days'},
    'cauliflower': {'cost_per_ha': 50000, 'yield_per_ha': 28000, 'price_per_kg': 15, 'season': 'Winter (September - October)', 'growth_period': '90-120 days'},
    'brinjal': {'cost_per_ha': 65000, 'yield_per_ha': 22000, 'price_per_kg': 20, 'season': 'Monsoon / Winter / Summer', 'growth_period': '120-150 days'},
    'chili': {'cost_per_ha': 75000, 'yield_per_ha': 3000, 'price_per_kg': 150, 'season': 'Monsoon / Summer', 'growth_period': '150-180 days'},
    'coconut': {'cost_per_ha': 120000, 'yield_per_ha': 15000, 'price_per_kg': 25, 'season': 'Monsoon / Summer (Year-round)', 'growth_period': '5-7 years for first yield'},
    'muskmelon': {'cost_per_ha': 40000, 'yield_per_ha': 15000, 'price_per_kg': 15, 'season': 'Summer (Jan - March)', 'growth_period': '80-100 days'},
    'watermelon': {'cost_per_ha': 45000, 'yield_per_ha': 25000, 'price_per_kg': 10, 'season': 'Summer (Jan - March)', 'growth_period': '80-100 days'},
    'mungbean': {'cost_per_ha': 30000, 'yield_per_ha': 1000, 'price_per_kg': 85, 'season': 'Monsoon / Summer', 'growth_period': '65-75 days'},
    'mothbeans': {'cost_per_ha': 25000, 'yield_per_ha': 800, 'price_per_kg': 60, 'season': 'Monsoon', 'growth_period': '75-90 days'},
    'orange': {'cost_per_ha': 140000, 'yield_per_ha': 18000, 'price_per_kg': 40, 'season': 'Winter (Harvest: Oct - March)', 'growth_period': '4-5 years'},
    'pomegranate': {'cost_per_ha': 160000, 'yield_per_ha': 12000, 'price_per_kg': 80, 'season': 'Monsoon / Summer (Year-round)', 'growth_period': '2-3 years'}
}

class CropChatbot:
    def __init__(self, profit_data):
        # Enhanced crop database combining your profit data with additional information
        self.crop_data = {}
        self.init_crop_database(profit_data)
        
        # Dynamic Generative AI Setup
        self.api_key = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
        self.gemini_model = None
        
        if GENAI_AVAILABLE and self.api_key and self.api_key != "YOUR_GEMINI_API_KEY_HERE":
            try:
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash',
                    system_instruction="You are an expert AI agricultural assistant. Answer all questions about farming, crops, soil, climate, and plant diseases concisely and accurately. Respond using basic clean Markdown.")
            except Exception as e:
                print(f"Gemini Init Error: {e}")
                
    def init_crop_database(self, profit_data):
        """Initialize comprehensive crop database"""
        # Additional crop information to supplement profit data
        crop_details = {
            'rice': {
                "scientific_name": "Oryza sativa",
                "type": "Cereal grain",
                "climate": "Tropical and subtropical, requires high humidity",
                "soil": "Clay or loamy soil with good water retention",
                "water_requirement": "High - requires flooded fields",
                "temperature": "20-35°C optimal",
                "major_diseases": ["Blast", "Brown spot", "Bacterial blight"],
                "pests": ["Rice stem borer", "Brown planthopper", "Rice weevil"],
                "nutrients": "Rich in carbohydrates, provides energy",
                "care_tips": [
                    "Maintain water level 2-5cm in fields",
                    "Apply nitrogen fertilizer in split doses",
                    "Monitor for pest infestations regularly"
                ]
            },
            'wheat': {
                "scientific_name": "Triticum aestivum",
                "type": "Cereal grain",
                "climate": "Temperate climate with cool winters",
                "soil": "Well-drained loamy soil",
                "water_requirement": "Moderate - avoid waterlogging",
                "temperature": "15-25°C optimal",
                "major_diseases": ["Rust", "Powdery mildew", "Septoria leaf blotch"],
                "pests": ["Aphids", "Armyworm", "Hessian fly"],
                "nutrients": "Rich in protein, fiber, and B vitamins",
                "care_tips": [
                    "Ensure proper drainage",
                    "Apply balanced fertilizers",
                    "Practice crop rotation"
                ]
            },
            'tomato': {
                "scientific_name": "Solanum lycopersicum",
                "type": "Vegetable/Fruit",
                "climate": "Warm temperate climate",
                "soil": "Well-drained, fertile soil with pH 6.0-6.8",
                "water_requirement": "Regular watering, avoid overwatering",
                "temperature": "18-25°C optimal",
                "major_diseases": ["Early blight", "Late blight", "Fusarium wilt"],
                "pests": ["Tomato hornworm", "Whitefly", "Aphids"],
                "nutrients": "Rich in lycopene, vitamin C, and potassium",
                "care_tips": [
                    "Provide support for vining varieties",
                    "Mulch to retain moisture",
                    "Prune suckers for better fruit development"
                ]
            },
            'corn': {
                "scientific_name": "Zea mays",
                "type": "Cereal grain",
                "climate": "Warm climate with adequate rainfall",
                "soil": "Well-drained, fertile soil",
                "water_requirement": "Moderate to high",
                "temperature": "21-27°C optimal",
                "major_diseases": ["Corn smut", "Gray leaf spot", "Corn rust"],
                "pests": ["Corn borer", "Fall armyworm", "Corn earworm"],
                "nutrients": "Rich in carbohydrates and dietary fiber",
                "care_tips": [
                    "Plant in blocks for better pollination",
                    "Side-dress with nitrogen fertilizer",
                    "Control weeds early in growth"
                ]
            },
            'cotton': {
                "scientific_name": "Gossypium hirsutum",
                "type": "Fiber crop",
                "climate": "Warm climate with long frost-free period",
                "soil": "Deep, well-drained black cotton soil",
                "water_requirement": "Moderate to high",
                "temperature": "21-30°C optimal",
                "major_diseases": ["Fusarium wilt", "Verticillium wilt", "Cotton leaf curl virus"],
                "pests": ["Bollworm", "Aphids", "Thrips", "Whitefly"],
                "nutrients": "Seeds rich in protein and oil",
                "care_tips": [
                    "Maintain proper plant spacing",
                    "Regular monitoring for bollworm",
                    "Adequate irrigation during flowering"
                ]
            },
            'potato': {
                "scientific_name": "Solanum tuberosum",
                "type": "Vegetable/Tuber",
                "climate": "Cool temperate climate",
                "soil": "Well-drained, sandy loam soil",
                "water_requirement": "Moderate, consistent moisture",
                "temperature": "15-20°C optimal",
                "major_diseases": ["Late blight", "Early blight", "Potato virus Y"],
                "pests": ["Colorado potato beetle", "Aphids", "Wireworms"],
                "nutrients": "Rich in carbohydrates, potassium, and vitamin C",
                "care_tips": [
                    "Hill soil around plants as they grow",
                    "Avoid overwatering to prevent rot",
                    "Harvest when foliage dies back"
                ]
            },
            'mango': {
                "scientific_name": "Mangifera indica",
                "type": "Fruit (Orchard crop)",
                "climate": "Tropical and subtropical",
                "soil": "Deep, well-drained alluvial or loamy soil",
                "water_requirement": "Moderate (Requires dry spell for flowering)",
                "temperature": "24-30°C optimal",
                "major_diseases": ["Powdery mildew", "Anthracnose", "Mango malformation"],
                "pests": ["Mango hopper", "Fruit fly", "Mealy bug"],
                "nutrients": "High in Vitamin A, C, and dietary fiber",
                "care_tips": [
                    "Prune regularly for better sunlight penetration",
                    "Apply organic mulch to retain moisture",
                    "Monitor for floral malformation early"
                ]
            },
            'banana': {
                "scientific_name": "Musa acuminata",
                "type": "Fruit",
                "climate": "Tropical, humid climate",
                "soil": "Rich, well-drained loamy soil",
                "water_requirement": "High - requires consistent moisture",
                "temperature": "25-30°C optimal",
                "major_diseases": ["Panama wilt", "Sigatoka leaf spot", "Bunchy top"],
                "pests": ["Banana weevil", "Aphids", "Thrips"],
                "nutrients": "Excellent source of potassium and Vitamin B6",
                "care_tips": [
                    "De-suckering to maintain plant vigor",
                    "Provide windbreaks for protection",
                    "Heavy mulching is beneficial"
                ]
            },
            'sugarcane': {
                "scientific_name": "Saccharum officinarum",
                "type": "Cash crop / Grass",
                "climate": "Tropical to subtropical",
                "soil": "Deep, rich loamy soil",
                "water_requirement": "Very High",
                "temperature": "32-38°C optimal",
                "major_diseases": ["Red rot", "Smut", "Grassy shoot"],
                "pests": ["Top borer", "Early shoot borer", "Pyrilla"],
                "nutrients": "Main source of sucrose (sugar)",
                "care_tips": [
                    "Earthing up to prevent lodging",
                    "Timely irrigation during tillering",
                    "Ensure proper drainage during monsoon"
                ]
            }
        }
        
        # Merge profit data with detailed crop information
        for crop_name, profit_info in profit_data.items():
            self.crop_data[crop_name] = {
                **profit_info,
                **(crop_details.get(crop_name, {
                    "scientific_name": f"{crop_name.title()} species",
                    "type": "Agricultural crop",
                    "climate": "Varies based on variety",
                    "soil": "Well-drained fertile soil",
                    "water_requirement": "Moderate",
                    "temperature": "Optimal range varies",
                    "major_diseases": ["Common fungal diseases", "Bacterial infections"],
                    "pests": ["Common agricultural pests"],
                    "nutrients": "Nutritional benefits vary",
                    "care_tips": ["Follow good agricultural practices", "Regular monitoring", "Proper fertilization"]
                }))
            }

    def normalize_input(self, user_input: str) -> str:
        """Normalize user input for better matching"""
        return user_input.lower().strip()

    def find_crop(self, user_input: str) -> str:
        """Find crop mentioned in user input"""
        normalized_input = self.normalize_input(user_input)
        
        # Direct crop name matching
        for crop_key in self.crop_data.keys():
            if crop_key in normalized_input:
                return crop_key
        
        # Alternative names matching
        alternatives = {
            "maize": "corn",
            "paddy": "rice",
            "tomatoes": "tomato",
            "potatoes": "potato",
            "onions": "onion",
            "chillies": "chili",
            "chillies": "chili",
            "brinjals": "brinjal",
            "eggplant": "brinjal",
            "ladyfinger": "okra",
            "bhindi": "okra",
            "arhar": "pigeonpea",
            "tur": "pigeonpea"
        }
        
        # Word-based matching to avoid partial overlaps
        words = normalized_input.split()
        
        # 1. Check direct matches with word boundaries
        for crop_key in self.crop_data.keys():
            if f" {crop_key} " in f" {normalized_input} ":
                return crop_key
        
        # 2. Check alternatives
        for alt_name, crop_key in alternatives.items():
            if f" {alt_name} " in f" {normalized_input} " and crop_key in self.crop_data:
                return crop_key
        
        # 3. Fallback to simple substring for messy inputs
        for crop_key in self.crop_data.keys():
            if crop_key in normalized_input:
                return crop_key
        
        return None

    def get_crop_info(self, crop: str, info_type: str = "general") -> dict:
        """Get specific information about a crop"""
        if crop not in self.crop_data:
            return {"error": "Sorry, I don't have information about that crop."}
        
        crop_info = self.crop_data[crop]
        
        if info_type == "general":
            return {
                "type": "general_info",
                "crop_name": crop.title(),
                "scientific_name": crop_info.get('scientific_name', 'N/A'),
                "type_category": crop_info.get('type', 'Agricultural crop'),
                "season": crop_info.get('season', 'N/A'),
                "growth_period": crop_info.get('growth_period', 'N/A'),
                "climate": crop_info.get('climate', 'N/A'),
                "temperature": crop_info.get('temperature', 'N/A'),
                "soil": crop_info.get('soil', 'N/A'),
                "water_requirement": crop_info.get('water_requirement', 'N/A'),
                "nutrients": crop_info.get('nutrients', 'N/A')
            }
        
        elif info_type == "diseases":
            return {
                "type": "diseases",
                "crop_name": crop.title(),
                "diseases": crop_info.get('major_diseases', [])
            }
        
        elif info_type == "pests":
            return {
                "type": "pests",
                "crop_name": crop.title(),
                "pests": crop_info.get('pests', [])
            }
        
        elif info_type == "care":
            return {
                "type": "care_tips",
                "crop_name": crop.title(),
                "care_tips": crop_info.get('care_tips', [])
            }
        
        elif info_type == "profit":
            return {
                "type": "profit_analysis",
                "crop_name": crop.title(),
                "cost_per_ha": crop_info.get('cost_per_ha', 0),
                "yield_per_ha": crop_info.get('yield_per_ha', 0),
                "price_per_kg": crop_info.get('price_per_kg', 0),
                "revenue": crop_info.get('yield_per_ha', 0) * crop_info.get('price_per_kg', 0),
                "profit": (crop_info.get('yield_per_ha', 0) * crop_info.get('price_per_kg', 0)) - crop_info.get('cost_per_ha', 0)
            }
        
        elif info_type == "season":
            return {
                "type": "season",
                "crop_name": crop.title(),
                "season": crop_info.get('season', 'N/A'),
                "growth_period": crop_info.get('growth_period', 'N/A')
            }
            
        elif info_type == "soil":
            return {
                "type": "soil",
                "crop_name": crop.title(),
                "soil": crop_info.get('soil', 'N/A')
            }
            
        elif info_type == "water":
            return {
                "type": "water",
                "crop_name": crop.title(),
                "water_requirement": crop_info.get('water_requirement', 'N/A')
            }
            
        elif info_type == "nutrition":
            return {
                "type": "nutrition",
                "crop_name": crop.title(),
                "nutrients": crop_info.get('nutrients', 'N/A')
            }
            
        elif info_type == "live_weather":
            return {
                "type": "live_weather",
                "crop_name": crop.title(),
                "climate": crop_info.get('climate', 'N/A'),
                "water_req": crop_info.get('water_requirement', 'N/A'),
                "temp": crop_info.get('temperature', 'N/A')
            }
            
        elif info_type == "market":
            # Mocking a dynamic market trend based on profit margins
            rev = crop_info.get('yield_per_ha', 0) * crop_info.get('price_per_kg', 0)
            cost = crop_info.get('cost_per_ha', 0)
            margin = ((rev - cost) / rev) if rev > 0 else 0
            trend = "High Demand 📈" if margin > 0.4 else ("Stable ⚖️" if margin > 0.2 else "Volatile 📉")
            
            return {
                "type": "market",
                "crop_name": crop.title(),
                "price": crop_info.get('price_per_kg', 0),
                "trend": trend,
                "demand": "Increasing globally" if margin > 0.3 else "Steady local demand"
            }
        
        return {"error": "I couldn't find that specific information."}

    def identify_query_type(self, user_input: str) -> str:
        """Identify what type of information user is asking for"""
        normalized_input = self.normalize_input(user_input)
        
        if any(word in normalized_input for word in ["disease", "diseases", "sick", "infection", "spots", "fungus", "mold", "rot", "blight", "wilt", "die"]):
            return "diseases"
        elif any(word in normalized_input for word in ["pest", "pests", "insect", "bugs", "worm", "aphid", "mite", "caterpillar", "infestation"]):
            return "pests"
        elif any(word in normalized_input for word in ["care", "tips", "how to grow", "growing", "maintain", "manage", "cultivation", "practice", "method", "guide", "training", "pruning"]):
            return "care"
        elif any(word in normalized_input for word in ["profit", "cost", "revenue", "money", "economics", "income", "expense", "budget", "investment", "return", "roi"]):
            return "profit"
        elif any(word in normalized_input for word in ["season", "when", "time", "plant", "month", "sowing", "harvest", "calendar"]):
            return "season"
        elif any(word in normalized_input for word in ["soil", "ground", "earth", "land", "field", "texture", "ph"]):
            return "soil"
        elif any(word in normalized_input for word in ["water", "irrigation", "watering", "drip", "sprinkler", "moisture", "drought"]):
            return "water"
        elif any(word in normalized_input for word in ["weather", "temperature", "rain", "rainy", "hot", "cold", "climate", "monsoon", "summer", "winter"]):
            return "live_weather"
        elif any(word in normalized_input for word in ["market", "price", "trend", "cost", "sell", "buy", "worth", "value", "demand", "supply", "mandi"]):
            return "market"
        else:
            return "general"

    def get_greeting(self) -> dict:
        """Return greeting message"""
        available_crops = list(self.crop_data.keys())
        return {
            "type": "greeting",
            "message": "Welcome to the Agricultural Crop Information Chatbot!",
            "available_crops": available_crops,
            "capabilities": [
                "General information about crops",
                "Growing conditions and seasons", 
                "Common diseases and pests",
                "Care tips and farming practices",
                "Profit analysis and economics",
                "Soil and water requirements"
            ]
        }

    def process_response(self, user_input: str, session_data: dict = None) -> dict:
        """Process user input and return appropriate response"""
        if session_data is None:
            session_data = {}
            
        normalized_input = self.normalize_input(user_input)
        
        # Use Dynamic Generative AI (Gemini) if configured!
        if self.gemini_model:
            try:
                # Add context about the platform if helpful
                prompt = f"User asks: {user_input}"
                response = self.gemini_model.generate_content(prompt)
                return {
                    "type": "llm",
                    "message": response.text
                }
            except Exception as e:
                print(f"Gemini Response Error: {e}")
                # Falls back to local database if network error occurs!

        # Try API Key activation notice
        if any(word in normalized_input for word in ["api", "gemini", "ai", "smart"]):
            return {
                "type": "error",
                "message": "To unlock advanced, dynamic AI answers for ALL crops & diseases, please `pip install google-generativeai` and insert your free Gemini API key at line 46 inside `app.py`!"
            }

        # Handle exit commands
        if any(exit_word in normalized_input for exit_word in ["bye", "exit", "quit", "goodbye"]) and len(normalized_input.split()) < 4:
            return {
                "type": "goodbye",
                "message": "Thank you for using the Crop Information Chatbot! Happy farming!"
            }
        
        # Handle help requests
        if "help" in normalized_input and len(normalized_input.split()) < 5:
            return {
                "type": "help",
                "message": "I can provide information about these crops",
                "available_crops": list(self.crop_data.keys()),
                "example_questions": [
                    "What is rice?",
                    "Rice diseases", 
                    "How to grow tomatoes?",
                    "Cotton pests",
                    "Wheat profit analysis"
                ]
            }
        
        # Find crop in user input
        crop = self.find_crop(user_input)
        
        if crop:
            session_data["current_crop"] = crop
            query_type = self.identify_query_type(user_input)
            return self.get_crop_info(crop, query_type)
        
        # If no crop found, check if user is asking about current crop
        elif session_data.get("current_crop"):
            query_type = self.identify_query_type(user_input)
            # If a specific query type is found, answer it
            if query_type != "general":
                return self.get_crop_info(session_data["current_crop"], query_type)
        
        # Handle greetings (Now AFTER crop check, so "hi, tell me about mango" works)
        if any(greeting == word for greeting in ["hi", "hello", "hey", "start", "greetings"] for word in normalized_input.split()):
            # Only greet if the sentence is simple or no crop found
            return self.get_greeting()
        
        # Default response for unrecognized input
        else:
            # 1. Hardcoded Farming "Training" for common questions
            faqs = {
                "npk": "NPK stands for Nitrogen (N), Phosphorus (P), and Potassium (K). These are the three primary macronutrients essential for plant growth.",
                "nitrogen": "Nitrogen is crucial for leaf growth and gives plants their green color. It is a major component of chlorophyll.",
                "phosphorus": "Phosphorus helps in root development, flower and fruit production, and overall plant energy transfer.",
                "potassium": "Potassium (K) is vital for overall plant health, disease resistance, and water regulation in the plant.",
                "ph": "Soil pH measures how acidic or alkaline the soil is (0-14). Most crops prefer a slightly acidic to neutral pH of 6.0 to 7.0.",
                "fertilizer": "Fertilizers are natural or synthetic materials applied to soil or plant tissues to supply one or more plant nutrients essential to the growth of plants.",
                "irrigation": "Irrigation is the artificial application of water to land to assist in the production of crops. Types include drip, sprinkler, and surface irrigation.",
                "pesticide": "Pesticides are substances meant for attracting, seducing, and then destroying, or mitigating any pest. Use them judiciously to avoid soil degradation.",
                "organic": "Organic farming relies on fertilizers of organic origin such as compost manure, green manure, and bone meal and places emphasis on techniques such as crop rotation and companion planting.",
                "soil": "Soil is a mixture of organic matter, minerals, gases, liquids, and organisms that together support life. Testing your soil helps determine its nutrient deficiencies.",
                "farming": "Farming is the practice of cultivating plants and livestock. It is the key development in the rise of sedentary human civilization.",
                "agriculture": "Agriculture encompasses crop and livestock production, aquaculture, fisheries and forestry for food and non-food products."
            }
            
            for key, answer in faqs.items():
                if key in normalized_input:
                    return {
                        "type": "llm",
                        "message": f"**🌱 Agricultural Knowledge Base:**\n\n{answer}"
                    }
                    
            # 2. Wikipedia Fallback
            if WIKIPEDIA_AVAILABLE:
                try:
                    # Append farming context implicitly to narrow down searches
                    search_query = f"{user_input} agriculture farming" if len(user_input.split()) < 3 else user_input
                    search_results = wikipedia.search(search_query)
                    
                    if not search_results:
                        search_results = wikipedia.search(user_input)
                        
                    if search_results:
                        # Grab the top factual result
                        top_page = wikipedia.page(search_results[0], auto_suggest=False)
                        summary = wikipedia.summary(search_results[0], sentences=4, auto_suggest=False)
                        return {
                            "type": "llm",
                            "message": f"**🌐 Live Web Intelligence:**\n\n{summary}\n\n*[Source: Wikipedia]({top_page.url})*"
                        }
                except Exception as e:
                    print(f"Wikipedia Fallback Error: {e}")
                    pass # Silently drop into standard failure error message

            return {
                "type": "error",
                "message": f"I don't have detailed information on '{user_input}' in my local database yet. \n\n**To get smarter answers:**\n1. Install dependencies: `pip install google-generativeai` \n2. Set your `GEMINI_API_KEY` in environment variables.\n\nAlternatively, try asking about: {', '.join(list(self.crop_data.keys())[:5])}"
            }


# Initialize and train/load model
DATASET_PATH = "Crop_recommendation.csv"
MODEL_PATH = "crop_recommendation_model.pkl"

if os.path.exists(MODEL_PATH):
    crop_model = AdvancedCropRecommendationModel(DATASET_PATH)
    crop_model.load_model(MODEL_PATH)
else:
    crop_model = AdvancedCropRecommendationModel(DATASET_PATH)
    crop_model.train_model()
    crop_model.save_model(MODEL_PATH)

# Initialize chatbot
chatbot = CropChatbot(CROP_PROFIT_DATA)

def calculate_profit_analysis(crop_name):
    """Calculate detailed profit analysis for a crop"""
    data = CROP_PROFIT_DATA.get(crop_name.lower())
    if not data:
        return None
    
    revenue = data['yield_per_ha'] * data['price_per_kg']
    profit = revenue - data['cost_per_ha']
    profit_margin = (profit / revenue) * 100 if revenue > 0 else 0
    
    return {
        'crop_name': crop_name,
        'cost_per_ha': data['cost_per_ha'],
        'yield_per_ha': data['yield_per_ha'],
        'price_per_kg': data['price_per_kg'],
        'season': data['season'],
        'growth_period': data['growth_period'],
        'revenue': revenue,
        'profit': profit,
        'profit_margin': round(profit_margin, 1)
    }

def calculate_fertilizer_prescription(crop_name, input_n, input_p, input_k):
    """Calculates Smart Fertilizer requirements per hectare (Urea, DAP, MOP)"""
    # Standards based on Indian Agricultural Research Institute (IARI) recommended doses (kg/ha)
    crop_reqs = {
        'rice': {'N': 120, 'P': 60, 'K': 40},
        'wheat': {'N': 120, 'P': 60, 'K': 40},
        'maize': {'N': 120, 'P': 60, 'K': 40},
        'corn': {'N': 120, 'P': 60, 'K': 40},
        'cotton': {'N': 120, 'P': 60, 'K': 60},
        'sugarcane': {'N': 250, 'P': 100, 'K': 100},
        'tomato': {'N': 150, 'P': 100, 'K': 100},
        'potato': {'N': 150, 'P': 100, 'K': 120},
        'onion': {'N': 100, 'P': 50, 'K': 50},
        'banana': {'N': 200, 'P': 100, 'K': 300},
        'mango': {'N': 100, 'P': 50, 'K': 100},
        'grapes': {'N': 150, 'P': 100, 'K': 150},
        'orange': {'N': 120, 'P': 60, 'K': 80},
        'papaya': {'N': 250, 'P': 250, 'K': 500},
        'pigeonpeas': {'N': 20, 'P': 50, 'K': 20},
        'chickpea': {'N': 20, 'P': 50, 'K': 20},
        'kidneybeans': {'N': 30, 'P': 60, 'K': 30},
        'lentil': {'N': 20, 'P': 40, 'K': 20},
        'mungbean': {'N': 20, 'P': 40, 'K': 20},
        'mothbeans': {'N': 20, 'P': 40, 'K': 20},
        'blackgram': {'N': 20, 'P': 40, 'K': 20},
        'pomegranate': {'N': 120, 'P': 60, 'K': 60},
        'watermelon': {'N': 100, 'P': 50, 'K': 50},
        'muskmelon': {'N': 100, 'P': 50, 'K': 50},
        'apple': {'N': 100, 'P': 50, 'K': 100},
        'coconut': {'N': 150, 'P': 100, 'K': 250},
        'mustard': {'N': 80, 'P': 40, 'K': 40},
        'soybean': {'N': 20, 'P': 60, 'K': 40},
        'groundnut': {'N': 25, 'P': 50, 'K': 75},
        'jute': {'N': 60, 'P': 30, 'K': 30},
        'coffee': {'N': 160, 'P': 120, 'K': 160},
        'tea': {'N': 150, 'P': 50, 'K': 100},
        'default': {'N': 100, 'P': 50, 'K': 50}
    }
    
    req = crop_reqs.get(crop_name.lower(), crop_reqs['default'])
    
    # Calculate pure N-P-K deficits
    def_p = max(0, req['P'] - input_p)
    def_k = max(0, req['K'] - input_k)
    
    # DAP required for Phosphorus (DAP provides 46% P, 18% N)
    dap_needed = def_p / 0.46 if def_p > 0 else 0
    
    # MOP required for Potassium (MOP provides 60% K)
    mop_needed = def_k / 0.60 if def_k > 0 else 0
    
    # Calculate N provided by the DAP fertilizer
    n_from_dap = dap_needed * 0.18
    def_n = max(0, req['N'] - input_n - n_from_dap)
    
    # Urea required for remaining Nitrogen (Urea provides 46% N)
    urea_needed = def_n / 0.46 if def_n > 0 else 0
    
    return {
        'Urea': round(urea_needed, 1),
        'DAP': round(dap_needed, 1),
        'MOP': round(mop_needed, 1),
        'N_req': req['N'],
        'P_req': req['P'],
        'K_req': req['K']
    }

@app.route('/')
def login_page():
    """Serve the login page as default"""
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Serve the main dashboard page"""
    return render_template('index.html')

@app.route('/service-worker.js')
def service_worker():
    from flask import send_from_directory
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    from flask import send_from_directory
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/chatbot')
def chatbot_page():
    """Serve the chatbot page"""
    return render_template('chatbot.html')

# Original endpoints (unchanged)
@app.route('/api/predict', methods=['POST'])
def predict_crops():
    """API endpoint for crop prediction"""
    try:
        data = request.get_json()
        required_fields = ['nitrogen', 'phosphorus', 'potassium', 'temperature', 'humidity', 'ph', 'rainfall']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Format input for model
        input_features = [
            data['nitrogen'],
            data['phosphorus'],
            data['potassium'],
            data['temperature'],
            data['humidity'],
            data['ph'],
            data['rainfall']
        ]
        
        predictions = crop_model.predict_with_confidence(input_features)
        
        # Add profit and fertilizer analysis
        for pred in predictions[:3]:  # keep top 3
            pred['profit_analysis'] = calculate_profit_analysis(pred['crop'])
            pred['fertilizer_plan'] = calculate_fertilizer_prescription(
                pred['crop'], 
                data['nitrogen'], 
                data['phosphorus'], 
                data['potassium']
            )
        
        return jsonify({
            'success': True,
            'predictions': predictions[:3],
            'input_data': data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crop-info/<crop_name>')
def get_crop_info(crop_name):
    """Get detailed information about a specific crop"""
    profit_analysis = calculate_profit_analysis(crop_name)
    if profit_analysis:
        return jsonify({'success': True, 'crop_info': profit_analysis})
    else:
        return jsonify({'error': 'Crop not found'}), 404

@app.route('/api/model-info')
def get_model_info():
    """Get information about the trained model"""
    return jsonify({
        'success': True,
        'model_info': {
            'algorithm': 'Random Forest Classifier',
            'features': crop_model.feature_names,
            'supported_crops': crop_model.crop_names.tolist() if crop_model.crop_names is not None else [],
            'model_trained': crop_model.model is not None
        }
    })

@app.route('/api/weather', methods=['POST'])
def get_live_weather():
    """Fetch real-time weather data for a given city or coordinates"""
    import urllib.request
    import json
    import urllib.parse
    
    try:
        data = request.get_json()
        city = data.get('city', '').strip()
        lat = data.get('lat')
        lon = data.get('lon')
        
        # Geocode city if lat/lon not provided
        if city and not (lat and lon):
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
            with urllib.request.urlopen(geo_url) as response:
                geo_data = json.loads(response.read().decode())
                if not geo_data.get('results'):
                    return jsonify({'error': f'City "{city}" not found.'}), 404
                lat = geo_data['results'][0]['latitude']
                lon = geo_data['results'][0]['longitude']
                city = geo_data['results'][0]['name']

        if not (lat and lon):
            return jsonify({'error': 'Please provide a city or coordinates.'}), 400

        # Fetch live weather (temp, humidity, and daily precipitation sum)
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m&daily=precipitation_sum&timezone=auto&forecast_days=1"
        with urllib.request.urlopen(weather_url) as response:
            weather_data = json.loads(response.read().decode())
            
        current = weather_data.get('current', {})
        daily = weather_data.get('daily', {})
        
        # For agricultural rainfall, a single day of rain is usually 0. We'll extrapolate a monthly average for the model, or just use a baseline 100 + daily * 10
        daily_rain = daily.get('precipitation_sum', [0])[0]
        estimated_rainfall = max(20, min(300, 50 + (daily_rain * 15))) # Artificial scaling for demonstration of ML model limits
        
        return jsonify({
            'success': True,
            'city': city or 'Current Location',
            'temperature': current.get('temperature_2m', 25),
            'humidity': current.get('relative_humidity_2m', 70),
            'rainfall': round(estimated_rainfall, 2),
            'lat': lat,
            'lon': lon
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch weather: {str(e)}'}), 500

@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    """Send real OTP via TextBelt"""
    import random
    import urllib.request
    import urllib.parse
    import json
    
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        if not phone or len(phone) < 7:
            return jsonify({'success': False, 'error': 'Valid mobile number required'}), 400
            
        otp = str(random.randint(100000, 999999))
        OTP_STORE[phone] = otp
        
        # TextBelt free SMS
        textbelt_url = "https://textbelt.com/text"
        req_data = urllib.parse.urlencode({
            'phone': phone,
            'message': f"Your Farm Dashboard Login OTP is: {otp}",
            'key': 'textbelt'
        }).encode('utf-8')
        
        req = urllib.request.Request(textbelt_url, data=req_data)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if result.get('success'):
                return jsonify({'success': True, 'message': 'Real OTP Sent!'})
            else:
                return jsonify({'success': False, 'error': result.get('error', 'Textbelt Error')}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    """Verify OTP"""
    data = request.get_json()
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    
    if phone in OTP_STORE and OTP_STORE[phone] == code:
        del OTP_STORE[phone]
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Invalid OTP code'}), 400

@app.route('/api/subscribe_alerts', methods=['POST'])
def subscribe_alerts():
    """Mock Twilio Route for SMS Weather/Price Alerts with 3-Day Forecast"""
    import urllib.request
    import json
    import urllib.parse
    
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        location_city = data.get('location', '').strip()
        
        if not phone or len(phone) < 7:
            return jsonify({'success': False, 'error': 'Please enter a valid mobile number!'}), 400
            
        if not location_city or location_city.lower() in ['auto-detected location', 'your farm']:
            location_city = 'Delhi' # Fallback default
            
        # 1. Geocode the city
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location_city)}&count=1&language=en&format=json"
        
        try:
            with urllib.request.urlopen(geo_url) as response:
                geo_data = json.loads(response.read().decode())
                if not geo_data.get('results'):
                    raise Exception(f"City {location_city} not found")
                lat = geo_data['results'][0]['latitude']
                lon = geo_data['results'][0]['longitude']
                actual_city = geo_data['results'][0]['name']
                
            # 2. Get 5-day forecast
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto&forecast_days=5"
            with urllib.request.urlopen(weather_url) as response:
                weather_data = json.loads(response.read().decode())
                
            dates = weather_data['daily']['time']
            max_temps = weather_data['daily']['temperature_2m_max']
            min_temps = weather_data['daily']['temperature_2m_min']
            rain = weather_data['daily']['precipitation_sum']
            
            sms_body = f"AgriAlert for {actual_city} (5-Day Weather):\n\n"
            for i in range(5):
                sms_body += f"{dates[i]}:\nTemp: {min_temps[i]}C to {max_temps[i]}C\nRain: {rain[i]}mm\n\n"
            sms_body += "Reply STOP to unsubscribe."
                
        except Exception as e:
            sms_body = f"AgriAlert for {location_city}: Unable to fetch precise 5-day data at this moment. Stay tuned!"

        # REAL SMS API EXECUTION using TextBelt (Sends 1 Free Real SMS per day without API Keys)
        print("\n" + "="*50)
        print("[PREPARING REAL SMS DISPATCH VIA TEXTBELT]")
        print(f"TO: {phone}")
        print(f"MESSAGE:\n{sms_body}")
        
        is_real_sms_sent = False
        api_error_reason = ""
        
        try:
            # Requires international format e.g. adding country code if missing
            # But textbelt attempts to route it automatically based on origin IP if missing
            textbelt_url = "https://textbelt.com/text"
            req_data = urllib.parse.urlencode({
                'phone': phone,
                'message': sms_body,
                'key': 'textbelt' # Public key, allows 1 free SMS per day
            }).encode('utf-8')
            
            req = urllib.request.Request(textbelt_url, data=req_data)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                
                if result.get('success'):
                    print(f"REAL SMS SENT SUCCESSFULLY! Quota remaining: {result.get('quotaRemaining', 0)}")
                    is_real_sms_sent = True
                else:
                    api_error_reason = result.get('error', 'Unknown Error')
                    print(f"Textbelt Real SMS failed: {api_error_reason}")
                    
        except Exception as e:
            api_error_reason = str(e)
            print(f"Textbelt API connection error: {api_error_reason}")

        print("="*50 + "\n")
        
        if is_real_sms_sent:
            status_msg = f"✅ Success! A REAL text message was sent to {phone}!\n(Note: The free API limits you to 1 real message per day. Don't spam it!)"
        else:
            status_msg = f"✅ Request processed, but the Free SMS failed to send because: '{api_error_reason}'\n\nYou might have hit the 1-SMS-per-day IP limit. Try again tomorrow or use an actual paid provider like Twilio.\n\nPreview of SMS:\n\n{sms_body}"
            
        return jsonify({
            'success': True,
            'message': status_msg,
            'sms_sent': is_real_sms_sent,
            'sms_body': sms_body,
            'phone': phone
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# New Chatbot endpoints
def dict_to_markdown(response_dict: dict) -> str:
    """Converts structured dictionaries into clean markdown text for translation."""
    t = response_dict.get('type')
    if t == "error":
        return response_dict.get("message", "Error occurred.")
    elif t == "llm":
        return response_dict.get("message", "")
    elif t == "help":
        crops = ", ".join(response_dict.get('available_crops', [])[:6])
        example_q = ", ".join(response_dict.get('example_questions', [])[:3])
        return f"I can help with:\n{crops}\n\nExample questions: {example_q}"
    elif t == "greeting":
        caps = "\n".join([f"- {c}" for c in response_dict.get('capabilities', [])])
        return f"{response_dict.get('message')}\n\nI can provide information about:\n{caps}"
    elif t == "goodbye":
        return response_dict.get("message", "Goodbye!")
    
    crop = response_dict.get("crop_name", "Crop").title()
    if t == "general_info":
        return f"### {crop}\n*{response_dict.get('scientific_name', '')}*\n\n**Type:** {response_dict.get('type_category', '')}\n**Season:** {response_dict.get('season', '')}\n**Climate:** {response_dict.get('climate', '')}\n**Soil:** {response_dict.get('soil', '')}\n**Water:** {response_dict.get('water_requirement', '')}"
    elif t == "diseases":
        return f"### Diseases - {crop}\n" + "\n".join([f"- {d}" for d in response_dict.get('diseases', [])])
    elif t == "pests":
        return f"### Pests - {crop}\n" + "\n".join([f"- {p}" for p in response_dict.get('pests', [])])
    elif t == "care_tips":
        return f"### Care Tips - {crop}\n" + "\n".join([f"- {c}" for c in response_dict.get('care_tips', [])])
    elif t == "profit_analysis":
        return f"### Profit Analysis - {crop}\n- **Cost:** ₹{response_dict.get('cost_per_ha', '0'):,}/ha\n- **Yield:** {response_dict.get('yield_per_ha', '0'):,} kg/ha\n- **Profit:** ₹{response_dict.get('profit', '0'):,}/ha"
    elif t == "season":
        return f"### Seasonality - {crop}\n- **Season:** {response_dict.get('season', '')}\n- **Growth Period:** {response_dict.get('growth_period', '')}"
    elif t == "live_weather" or t == "climate":
        return f"### Climate Profile - {crop}\n- **Temp:** {response_dict.get('temperature', 'Optimal')}\n- **Climate:** {response_dict.get('climate', '')}"
    elif t == "market":
        return f"### Market Trends - {crop}\n- **Price:** ₹{response_dict.get('price', '')}/kg\n- **Trend:** {response_dict.get('trend', '')}\n- **Demand:** {response_dict.get('demand', '')}"
        
    return response_dict.get("message", "I received your message.")

@app.route('/api/chatbot/message', methods=['POST'])
def chatbot_message():
    """Handle chatbot messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        selected_language = data.get('language', 'english').lower()
        
        language_map = {
            'hindi': 'hi',
            'marathi': 'mr',
            'punjabi': 'pa',
            'telugu': 'te',
            'english': 'en'
        }
        lang_code = language_map.get(selected_language, 'en')
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
            
        # 1. Input Translation Pipeline (Native Lang -> English)
        actual_input = user_message
        if TRANSLATOR_AVAILABLE and lang_code != 'en':
            try:
                # We translate to English so internal keyword/LLM engines understand safely
                actual_input = GoogleTranslator(source=lang_code, target='en').translate(user_message)
                print(f"[TRANSLATION ENGINE] {selected_language} -> {actual_input}")
            except Exception as e:
                print(f"Translation Error (Input): {e}")
        
        # Get or create session ID
        session_id = session.get('chatbot_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['chatbot_session_id'] = session_id
        
        # Get session data
        session_data = session.get('chatbot_data', {})
        
        # Process message natively in English
        if hasattr(chatbot, 'gemini_model') and chatbot.gemini_model:
            # If using LLM, inject language instruction directly for best results
            lang_instruction = f" You MUST format your response strictly in {selected_language}." if lang_code != 'en' else ""
            
            # Use detected crop and intent to provide context to Gemini
            local_context = ""
            detected_crop = chatbot.find_crop(actual_input)
            if detected_crop:
                detected_intent = chatbot.identify_query_type(actual_input)
                local_info = chatbot.get_crop_info(detected_crop, detected_intent)
                if "error" not in local_info:
                    local_context = f"Context from our database for {detected_crop}: {local_info}. Use this as a reference but answer naturally. "
            
            try:
                prompt_text = f"{local_context}User asks: {actual_input}.{lang_instruction}"
                gemini_resp = chatbot.gemini_model.generate_content(prompt_text)
                response = {"type": "llm", "message": gemini_resp.text}
            except Exception as e:
                 print(f"Gemini fallback initiated: {e}")
                 response = chatbot.process_response(actual_input, session_data)
        else:
            response = chatbot.process_response(actual_input, session_data)
            
        # 2. Output Translation Pipeline (English -> Native Lang)
        if response.get("type") != "llm":
            # Consolidate standard objects into unified Markdown for reliable unified translation
            md_response = dict_to_markdown(response)
            if TRANSLATOR_AVAILABLE and lang_code != 'en':
                try:
                    md_response = GoogleTranslator(source='en', target=lang_code).translate(md_response)
                except Exception as e:
                    print(f"Translation Error (Output): {e}")
            
            # Repackage completely as Markdown LLM-type so frontend safely blindly renders it
            response = {"type": "llm", "message": md_response}
        
        # Add current crop context to session if found
        if 'crop_name' in response:
             session_data['current_crop'] = response['crop_name'].lower()
        
        # Update session data
        session['chatbot_data'] = session_data
        session.modified = True
        
        return jsonify({
            'success': True,
            'response': response,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot/reset', methods=['POST'])
def reset_chatbot():
    """Reset chatbot session"""
    try:
        session.pop('chatbot_session_id', None)
        session.pop('chatbot_data', None)
        
        return jsonify({
            'success': True,
            'message': 'Chatbot session reset successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot/crops')
def get_available_crops():
    """Get list of available crops for chatbot"""
    return jsonify({
        'success': True,
        'crops': list(CROP_PROFIT_DATA.keys())
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'model_ready': crop_model.model is not None,
        'chatbot_ready': True
    })

@app.route('/api/chatbot/vision', methods=['POST'])
def chatbot_vision():
    """Handle image uploads for disease recognition (Mock)"""
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
            
        # Use Gemini Vision if available
        if hasattr(chatbot, 'gemini_model') and chatbot.gemini_model:
            try:
                import base64
                from io import BytesIO
                # Header usually like "data:image/jpeg;base64,..."
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                
                img_bytes = base64.b64decode(image_data)
                
                # Use Gemini 1.5 Flash for specialized agricultural vision analysis
                vision_prompt = """
                Analyze this agricultural image with high precision.
                1. **Identify Crop**: What plant is this?
                2. **Identify Health Status**: Is it healthy? If not, name the specific disease or pest (e.g., 'Tomato Late Blight').
                3. **Diagnostic Details**: Brief cause of the issue.
                4. **Actionable Care Plan**: 3-4 clear, professional steps to fix the issue or maintain health.
                
                Format the response with bold headers and clear bullet points. Use basic clean Markdown.
                """
                
                # The google-generativeai library handles bytes for images
                response = chatbot.gemini_model.generate_content([
                    vision_prompt, 
                    {'mime_type': 'image/jpeg', 'data': img_bytes}
                ])
                
                # Consolidate response
                full_message = f"### 📷 Vision AI Analysis\n\n{response.text}"
                
                return jsonify({
                    'success': True,
                    'response': {
                        'type': 'llm',
                        'message': full_message
                    }
                })
            except Exception as e:
                print(f"Gemini Vision Error: {e}")
                # Fallback to mock

        import random
        import time
        
        time.sleep(2) # Simulate Deep Learning processing delay
        
        # MOCK A.I. DIAGNOSTICS DB
        diagnoses = [
            {
                "disease": "Tomato Early Blight",
                "cause": "Fungal infection (*Alternaria solani*) caused by prolonged wetness.",
                "action": "Remove affected leaves. Apply Copper-based fungicides. Ensure proper spacing for airflow."
            },
            {
                "disease": "Rice Leaf Smut",
                "cause": "Fungal disease (*Entyloma oryzae*) surviving in soil residue.",
                "action": "Use disease-free seeds. Treat with appropriate fungicides containing Propiconazole."
            },
            {
                "disease": "Cotton Aphid Warning",
                "cause": "Pest infestation visible on leaf undersides causing curling.",
                "action": "Apply Neem oil immediately. Introduce natural predators like Ladybugs. Use Imidacloprid if severe."
            },
            {
                "disease": "Healthy Leaf",
                "cause": "Optimal Nitrogen, Phosphorus, and Climate parameters.",
                "action": "No action needed! Keep up your current irrigation and fertilizer schedule."
            }
        ]
        
        result = random.choice(diagnoses)
        
        return jsonify({
            'success': True,
            'response': {
                'type': 'vision',
                'diagnosis': result['disease'],
                'cause': result['cause'],
                'action': result['action']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred processing the image: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting Crop Recommendation System with Integrated Chatbot...")
    print("Available endpoints:")
    print("- / : Main crop recommendation interface")
    print("- /chatbot : Chatbot interface") 
    print("- /api/predict : Crop prediction")
    print("- /api/chatbot/message : Chatbot messaging")
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)