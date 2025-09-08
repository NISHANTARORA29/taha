from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import requests
import json
import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import openai
import os
import uuid
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import traceback
import logging
import base64
from io import BytesIO
from PIL import Image


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="build", static_url_path="/")
CORS(app)

@app.route("/")
def serve_react():
    return send_from_directory(app.static_folder, "index.html")

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, "index.html")

class AdvancedGoldGPT:
    def __init__(self, api_key: str = None):
        """Initialize Advanced GoldGPT with OpenAI API"""
        # Updated OpenAI API key
        
        # Metal Price API configuration
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.metal_api_key = os.getenv("METAL_API_KEY")
        
        # CSV file path for products
        self.products_csv_path = "products_with_descriptions.csv"
        
        # Set OpenAI client
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Create images directory if it doesn't exist
        self.images_dir = "generated_images"
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        # Business information
        self.business_info = {
            "name": "Ayar-24 Kuwait",
            "name_ar": "عيار-24 الكويت",
            "website": "https://ayar-24.com/",
            "phone": "00965-98793103",
            "whatsapp": "00965-98793103",
            "email": "info@ayar-24.com",
            "location": "Kuwait",
            "location_ar": "الكويت",
            "specialization": "Precious metals trade, gold bars, exclusive jewelry designs",
            "specialization_ar": "تجارة المعادن الثمينة، سبائك الذهب، تصاميم المجوهرات الحصرية"
        }
        
        # Products and services
        self.products = {
            "gold_bars": {
                "name": "Gold Bars / سبائك الذهب",
                "description": "Pure 24-karat gold bars in various weights",
                "sizes": ["1g", "5g", "10g", "20g", "50g", "100g", "1oz"],
                "purity": "99.99% pure gold"
            },
            "jewelry": {
                "name": "Exclusive Jewelry / مجوهرات حصرية",
                "description": "Custom-designed gold jewelry pieces",
                "types": ["Rings", "Necklaces", "Bracelets", "Earrings", "Chains"],
                "karat_options": ["18K", "21K", "22K", "24K"]
            },
            "coins": {
                "name": "Gold Coins / العملات الذهبية",
                "description": "Investment-grade gold coins",
                "types": ["Krugerrand", "American Eagle", "Canadian Maple Leaf", "Austrian Philharmonic"]
            },
            "silver": {
                "name": "Silver Products / منتجات الفضة",
                "description": "Pure silver bars and coins",
                "types": ["Silver bars", "Silver coins", "Silver jewelry"]
            }
        }
        
        # Load products from CSV
        self.csv_products = self.load_csv_products()
        
        # Enhanced image generation prompts for jewelry and precious metals
        self.jewelry_prompts = {
            "rings": "elegant gold ring with intricate details, luxury jewelry photography, professional lighting, white background",
            "necklaces": "beautiful gold necklace with precious stones, luxury jewelry display, professional photography",
            "bracelets": "sophisticated gold bracelet, premium jewelry design, studio lighting, elegant presentation",
            "earrings": "exquisite gold earrings, luxury jewelry photography, professional lighting, white background",
            "chains": "premium gold chain, luxury jewelry design, professional photography, elegant display",
            "gold_bars": "pure gold bars stacked elegantly, professional precious metals photography, luxury presentation",
            "gold_coins": "collection of gold investment coins, premium numismatic photography, professional lighting",
            "silver_products": "pure silver bars and coins, precious metals photography, professional presentation"
        }

    def enhance_image_prompt(self, user_prompt: str) -> str:
        """Enhance user prompt for better jewelry and precious metals images"""
        try:
            # Detect if user is asking for specific jewelry or precious metals
            prompt_lower = user_prompt.lower()
            
            # Check for jewelry types
            for jewelry_type, enhanced_prompt in self.jewelry_prompts.items():
                if jewelry_type.replace('_', ' ') in prompt_lower:
                    return f"{user_prompt}, {enhanced_prompt}"
            
            # Check for general precious metals terms
            precious_metal_terms = ['gold', 'silver', 'platinum', 'precious metal', 'jewelry', 'jewel']
            if any(term in prompt_lower for term in precious_metal_terms):
                return f"{user_prompt}, luxury precious metals photography, professional lighting, elegant presentation, high quality, detailed"
            
            # For Arabic prompts, add Arabic-specific enhancements
            if self.detect_language(user_prompt) == 'ar':
                return f"{user_prompt}, تصوير مجوهرات فاخرة، إضاءة احترافية، عرض أنيق، جودة عالية"
            
            return user_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing prompt: {str(e)}")
            return user_prompt

    def generate_ai_image(self, prompt: str, filename: str = None) -> Dict:
        """Generate AI image using DALL-E 3 with enhanced prompts"""
        try:
            # Enhance the prompt for better results
            enhanced_prompt = self.enhance_image_prompt(prompt)
            
            logger.info(f"Generating image with prompt: {enhanced_prompt}")
            
            # Generate image using DALL·E 3
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                n=1,
                size="1024x1024",
                quality="standard",  # Can be "standard" or "hd"
                style="vivid"        # Can be "vivid" or "natural"
            )
            
            # Extract image URL
            img_url = response.data[0].url
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"goldgpt_image_{timestamp}.png"
            elif not filename.endswith('.png'):
                filename += '.png'
            
            # Full path for saving
            filepath = os.path.join(self.images_dir, filename)
            
            # Download and save image
            img_response = requests.get(img_url, timeout=30)
            img_response.raise_for_status()
            
            with open(filepath, "wb") as f:
                f.write(img_response.content)
            
            # Convert image to base64 for immediate display
            with open(filepath, "rb") as f:
                img_data = f.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            logger.info(f"Image successfully generated and saved: {filename}")
            
            return {
                'success': True,
                'image_url': img_url,
                'filename': filename,
                'filepath': filepath,
                'base64': img_base64,
                'enhanced_prompt': enhanced_prompt,
                'message': f"Image generated successfully: '{filename}'"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to download image: {str(e)}",
                'message': f"Image generation failed during download: {str(e)}"
            }
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                'success': False,
                'error': f"OpenAI API error: {str(e)}",
                'message': f"Failed to generate image: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error generating AI image: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to generate image: {str(e)}"
            }

    def init_database(self):
        """Initialize SQLite database for chat history"""
        try:
            conn = sqlite3.connect('goldgpt_chats.db')
            cursor = conn.cursor()
            
            # Create chat sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    chart_data TEXT,
                    image_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")

    def save_chat_session(self, session_id: str, messages: list, title: str = None):
        """Save chat session to database"""
        try:
            conn = sqlite3.connect('goldgpt_chats.db')
            cursor = conn.cursor()
            
            if not title and messages:
                first_user_msg = next((msg['content'] for msg in messages if msg['role'] == 'user'), "New Chat")
                title = first_user_msg[:50] + "..." if len(first_user_msg) > 50 else first_user_msg
            
            # Insert or update session
            cursor.execute('''
                INSERT OR REPLACE INTO chat_sessions (id, title, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (session_id, title or "New Chat"))
            
            # Delete existing messages for this session
            cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            
            # Insert new messages
            for message in messages:
                cursor.execute('''
                    INSERT INTO messages (session_id, role, content, chart_data, image_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, message['role'], message['content'], 
                      json.dumps(message.get('chart')) if message.get('chart') else None,
                      json.dumps(message.get('image')) if message.get('image') else None))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving chat session: {str(e)}")

    def load_chat_session(self, session_id: str):
        """Load chat session from database"""
        try:
            conn = sqlite3.connect('goldgpt_chats.db')
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute('SELECT title, created_at FROM chat_sessions WHERE id = ?', (session_id,))
            session_data = cursor.fetchone()
            
            if not session_data:
                conn.close()
                return None
            
            # Get messages
            cursor.execute('''
                SELECT role, content, chart_data, image_data FROM messages 
                WHERE session_id = ? ORDER BY created_at
            ''', (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                message = {
                    'role': row[0],
                    'content': row[1]
                }
                if row[2]:  # chart_data
                    message['chart'] = json.loads(row[2])
                if row[3]:  # image_data
                    message['image'] = json.loads(row[3])
                messages.append(message)
            
            conn.close()
            
            return {
                'messages': messages,
                'title': session_data[0],
                'timestamp': session_data[1]
            }
            
        except Exception as e:
            logger.error(f"Error loading chat session: {str(e)}")
            return None

    def get_chat_history(self):
        """Get all chat sessions"""
        try:
            conn = sqlite3.connect('goldgpt_chats.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, updated_at FROM chat_sessions 
                ORDER BY updated_at DESC
            ''')
            
            sessions = {}
            for row in cursor.fetchall():
                sessions[row[0]] = {
                    'title': row[1],
                    'timestamp': row[2]
                }
            
            conn.close()
            return sessions
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return {}

    def delete_chat_session(self, session_id: str):
        """Delete a chat session"""
        try:
            conn = sqlite3.connect('goldgpt_chats.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error deleting chat session: {str(e)}")

    def load_csv_products(self) -> pd.DataFrame:
        """Load products from CSV file"""
        try:
            if os.path.exists(self.products_csv_path):
                df = pd.read_csv(self.products_csv_path)
                logger.info(f"Loaded {len(df)} products from CSV")
                return df
            else:
                # Create sample data if CSV doesn't exist
                sample_data = {
                    'Product Name': [
                        '0.25 kg BTC Purity 999.9',
                        '0.25 Kg BTC Round Purity 999.9',
                        '1 oz Gold Bar',
                        '10g Gold Bar',
                        '50g Gold Bar'
                    ],
                    'Model': [
                        'ربع كيلو اماراتي نقاوة 999.9',
                        'ربع كيلو اماراتي دائري نقاوة 999.9 BTC',
                        '1 oz Standard Gold Bar',
                        '10g Premium Gold Bar',
                        '50g Investment Gold Bar'
                    ],
                    'Price': [17.0000, 20.0000, 2.1000, 0.6500, 3.2500],
                    'Quantity': [5, 5, 10, 15, 8]
                }
                df = pd.DataFrame(sample_data)
                logger.info("Created sample product data")
                return df
        except Exception as e:
            logger.error(f"Error loading CSV products: {str(e)}")
            return pd.DataFrame()

    def get_metal_prices_api(self) -> Dict:
        """Fetch metal prices from metalpriceapi.com"""
        try:
            params = {
                "api_key": self.metal_api_key,
                "base": "USD",
                "currencies": "XAU,XAG,XPT,XPD"
            }
            
            response = requests.get(self.metal_api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success", False):
                rates = data.get("rates", {})
                
                processed_rates = {}
                for metal, rate in rates.items():
                    if metal == "XAU":
                        processed_rates["gold"] = {
                            "price": round(1/rate, 2) if rate > 0 else 0,
                            "symbol": "XAU",
                            "name": "Gold",
                            "unit": "USD/oz"
                        }
                    elif metal == "XAG":
                        processed_rates["silver"] = {
                            "price": round(1/rate, 2) if rate > 0 else 0,
                            "symbol": "XAG",
                            "name": "Silver",
                            "unit": "USD/oz"
                        }
                    elif metal == "XPT":
                        processed_rates["platinum"] = {
                            "price": round(1/rate, 2) if rate > 0 else 0,
                            "symbol": "XPT",
                            "name": "Platinum",
                            "unit": "USD/oz"
                        }
                    elif metal == "XPD":
                        processed_rates["palladium"] = {
                            "price": round(1/rate, 2) if rate > 0 else 0,
                            "symbol": "XPD",
                            "name": "Palladium",
                            "unit": "USD/oz"
                        }
                
                return {
                    "success": True,
                    "rates": processed_rates,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "base": data.get("base", "USD")
                }
            else:
                return {"success": False, "error": "API returned success=False"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Metal API request failed: {str(e)}")
            return {"success": False, "error": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Metal API unexpected error: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def search_csv_products(self, query: str) -> List[Dict]:
        """Search for products in CSV data"""
        if self.csv_products.empty:
            return []
        
        try:
            query_lower = query.lower()
            
            mask = (
                self.csv_products['Product Name'].str.lower().str.contains(query_lower, na=False) |
                self.csv_products['Model'].str.lower().str.contains(query_lower, na=False)
            )
            
            matching_products = self.csv_products[mask]
            
            products_list = []
            for _, row in matching_products.iterrows():
                products_list.append({
                    'product_name': row['Product Name'],
                    'model': row['Model'],
                    'price': row['Price'],
                    'quantity': row['Quantity']
                })
            
            return products_list
            
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []

    def get_all_csv_products(self) -> List[Dict]:
        """Get all products from CSV"""
        if self.csv_products.empty:
            return []
        
        try:
            products_list = []
            for _, row in self.csv_products.iterrows():
                products_list.append({
                    'product_name': row['Product Name'],
                    'model': row['Model'],
                    'price': row['Price'],
                    'quantity': row['Quantity']
                })
            return products_list
        except Exception as e:
            logger.error(f"Error getting all products: {str(e)}")
            return []

    def detect_language(self, text: str) -> str:
        """Detect if text is Arabic or English"""
        try:
            arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
            total_chars = len(text.strip())
            return 'ar' if arabic_chars > total_chars * 0.3 else 'en'
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return 'en'

    def get_gold_price(self) -> Dict:
        """Fetch current gold price data"""
        try:
            gold_ticker = yf.Ticker("GC=F")
            gold_data = gold_ticker.history(period="2d")
            
            if not gold_data.empty:
                current_price = gold_data['Close'].iloc[-1]
                prev_close = gold_data['Close'].iloc[-2] if len(gold_data) > 1 else current_price
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100
                
                return {
                    'success': True,
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'high_24h': round(gold_data['High'].iloc[-1], 2),
                    'low_24h': round(gold_data['Low'].iloc[-1], 2),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {'success': False, 'error': 'No data available'}
                
        except Exception as e:
            logger.error(f"Error getting gold price: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_kuwait_gold_prices(self) -> Dict:
        """Get Kuwait-specific gold prices"""
        try:
            kuwait_prices = {
                "24k_kwd": 33.78,
                "22k_kwd": 31.01,
                "21k_kwd": 29.56,
                "18k_kwd": 25.34,
                "currency": "KWD",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            return {"success": True, **kuwait_prices}
        except Exception as e:
            logger.error(f"Error getting Kuwait prices: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_market_context(self) -> str:
        """Get current market context for AI"""
        try:
            price_data = self.get_gold_price()
            kuwait_prices = self.get_kuwait_gold_prices()
            metal_prices = self.get_metal_prices_api()
            
            context = f"""
            Current Market Data:
            - Global Gold Price: ${price_data.get('price', 'N/A')}/oz
            - Daily Change: {price_data.get('change', 'N/A')} ({price_data.get('change_pct', 'N/A')}%)
            - Kuwait Gold Prices: 24K={kuwait_prices.get('24k_kwd', 'N/A')} KWD/g, 22K={kuwait_prices.get('22k_kwd', 'N/A')} KWD/g, 18K={kuwait_prices.get('18k_kwd', 'N/A')} KWD/g
            - Market Status: Kuwait gold market showed 142% growth in 2021 and continues strong performance
            """
            
            if metal_prices.get('success'):
                context += "\n\nMetal Prices API Data:\n"
                for metal, data in metal_prices.get('rates', {}).items():
                    context += f"- {data['name']}: ${data['price']}/oz\n"
            
            return context
        except Exception as e:
            logger.error(f"Error getting market context: {str(e)}")
            return "Market data temporarily unavailable."

    def get_products_context(self, user_message: str) -> str:
        """Get products context based on user message"""
        try:
            products_context = ""
            
            product_keywords = ['product', 'price', 'buy', 'purchase', 'available', 'stock', 'منتج', 'سعر', 'شراء', 'متوفر']
            if any(keyword in user_message.lower() for keyword in product_keywords):
                search_results = self.search_csv_products(user_message)
                
                if search_results:
                    products_context = "\n\nAvailable Products (matching your query):\n"
                    for product in search_results:
                        products_context += f"- {product['product_name']}: ${product['price']:.4f}, Quantity: {product['quantity']}\n"
                        products_context += f"  Model: {product['model']}\n"
                else:
                    all_products = self.get_all_csv_products()
                    if all_products:
                        products_context = "\n\nOur Available Products:\n"
                        for product in all_products[:5]:
                            products_context += f"- {product['product_name']}: ${product['price']:.4f}, Quantity: {product['quantity']}\n"
                            products_context += f"  Model: {product['model']}\n"
            
            return products_context
        except Exception as e:
            logger.error(f"Error getting products context: {str(e)}")
            return ""

    def generate_chart_data(self) -> Optional[Dict]:
        """Generate chart data for frontend"""
        try:
            ticker = yf.Ticker("GC=F")
            data = ticker.history(period="1mo")
            
            if data.empty:
                return None
            
            chart_data = {
                'x': [date.strftime('%Y-%m-%d') for date in data.index],
                'y': data['Close'].tolist(),
                'type': 'line',
                'title': 'Gold Price - Last 30 Days',
                'xaxis_title': 'Date',
                'yaxis_title': 'Price (USD/oz)'
            }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating chart data: {str(e)}")
            return None

    def call_openai_api(self, user_message: str, language: str) -> str:
        """Call OpenAI API with optimized context"""
        try:
            market_context = self.get_market_context()
            products_context = self.get_products_context(user_message)
            
            all_products = self.get_all_csv_products()
            product_catalog = ""
            if all_products:
                product_catalog = "\n\nTOP PRODUCTS:\n"
                for product in all_products[:3]:
                    product_catalog += f"- {product['product_name']}: ${product['price']:.2f} (Stock: {product['quantity']})\n"
            
            system_prompt = f"""
            You are GoldGPT, AI precious metals expert for Ayar-24 Kuwait.
            
            Company: Ayar-24 Kuwait | Phone: 00965-98793103 | Email: info@ayar-24.com 
            Website: https://ayar-24.com/ | Location: Kuwait
            
            {market_context}
            {products_context}
            {product_catalog}
            
            COMPREHENSIVE EXPERT CAPABILITIES:
            
            1. UNIVERSAL PRECIOUS METALS KNOWLEDGE:
            - Answer ANY question about gold, silver, platinum, palladium, rhodium, and other precious metals
            - Explain mining processes, refining techniques, and purity standards
            - Discuss historical significance, cultural importance, and industrial applications
            - Provide geological information about metal formation and global reserves
            - Explain metallurgy, alloy compositions, and physical properties
            - Cover jewelry making, craftsmanship techniques, and design principles
            
            2. PERSONALIZED PRODUCT RECOMMENDATIONS:
            - Analyze user's specific needs, budget, and investment goals
            - Recommend exact products from our inventory based on their requirements
            - Suggest optimal product combinations for diversified portfolios
            - Compare different product options (bars vs coins vs jewelry)
            - Explain why specific products suit different investment strategies
            - Provide product alternatives based on availability and pricing
            
            3. INVESTMENT STRATEGY & MARKET ANALYSIS:
            - Comprehensive market trend analysis and forecasting
            - Technical and fundamental analysis of precious metals markets
            - Portfolio allocation strategies for different risk profiles
            - Timing recommendations for buying and selling
            - Economic correlation analysis (inflation, currency, interest rates)
            - Geopolitical impact assessment on precious metals prices
            
            4. EDUCATIONAL & HISTORICAL EXPERTISE:
            - Explain the history of precious metals as currency and store of value
            - Discuss different monetary systems and gold standards
            - Provide educational content about precious metals investing
            - Explain complex financial concepts in simple terms
            - Share interesting facts, stories, and historical events
            - Discuss cultural and religious significance of precious metals
            
            5. PRACTICAL GUIDANCE:
            - Storage solutions and security recommendations
            - Authentication and testing methods for precious metals
            - Tax implications and legal considerations
            - Insurance and documentation requirements
            - Import/export regulations and compliance
            - Best practices for buying, selling, and trading
            
            6. TECHNICAL SPECIFICATIONS:
            - Detailed information about purity, weight, and dimensions
            - Certification and hallmarking standards
            - Manufacturing processes and quality control
            - Packaging and presentation options
            - Shipping and handling procedures
            
            7. AI IMAGE GENERATION CAPABILITY:
            - Can generate stunning AI images of jewelry, precious metals, and investment concepts
            - Enhanced prompts for jewelry: rings, necklaces, bracelets, earrings, chains
            - Professional precious metals photography: gold bars, silver bars, coins
            - Custom jewelry designs and concepts
            - Investment portfolio visualizations
            - If user requests image generation, use keywords like: "generate image", "create visual", "show me picture", "design", "visualize","generate"
            
            RESPONSE STYLE:
            - Language: {'Arabic' if language == 'ar' else 'English'}
            - Use emojis and professional formatting
            - Include specific product suggestions when relevant
            - Provide actionable advice
            - DO NOT include contact information or company details at the end of every response
            - ONLY include contact info when user specifically asks for contact details or wants to make a purchase
            
            IMPORTANT: Do not add footer information (phone, email, website) to every response. Only include it when contextually relevant or when user asks for contact information.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2000,
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"I apologize, but I'm having trouble processing your request right now. Please try again in a moment, or contact our experts directly for assistance."
        
    def generate_response(self, user_message: str) -> Tuple[str, Optional[Dict], Optional[Dict]]:
        """Generate response using OpenAI API - Enhanced with better image generation detection"""
        try:
            language = self.detect_language(user_message)
            
            # Enhanced image generation detection
            image_keywords_en = [
                'generate image', 'create image', 'make image', 'show me picture', 'create visual', 
                'draw', 'design', 'visualize', 'show me', 'create a picture', 'generate visual',
                'make a design', 'create artwork', 'show design', 'picture of', 'image of'
            ]
            
            image_keywords_ar = [
                'صورة', 'رسم', 'اصنع صورة', 'أنشئ صورة', 'اعرض صورة', 'تصميم', 'رسمة',
                'أظهر لي', 'اصنع تصميم', 'صمم', 'مثال بصري'
            ]
            
            all_image_keywords = image_keywords_en + image_keywords_ar
            image_data = None
            
            # Check if user wants to generate an image
            user_message_lower = user_message.lower()
            wants_image = any(keyword in user_message_lower for keyword in all_image_keywords)
            
            if wants_image:
                # Extract image prompt from user message
                image_prompt = user_message
                
                # Remove common image generation keywords to get clean prompt
                for keyword in all_image_keywords:
                    if keyword in user_message_lower:
                        # Remove the keyword but keep the rest
                        image_prompt = re.sub(re.escape(keyword), '', image_prompt, flags=re.IGNORECASE).strip()
                        break
                
                # If no specific prompt remains, create a default based on context
                if not image_prompt or len(image_prompt.strip()) < 5:
                    if language == 'ar':
                        image_prompt = "مجوهرات ذهبية فاخرة وسبائك ذهب"
                    else:
                        image_prompt = "luxury gold jewelry and precious metal bars"
                
                # Generate the image
                logger.info(f"Generating image with extracted prompt: {image_prompt}")
                image_result = self.generate_ai_image(image_prompt)
                
                if image_result['success']:
                    image_data = {
                        'url': image_result['image_url'],
                        'filename': image_result['filename'],
                        'base64': image_result['base64'],
                        'prompt': image_result['enhanced_prompt'],
                        'original_prompt': image_prompt
                    }
                    logger.info(f"Image generated successfully: {image_result['filename']}")
                else:
                    logger.error(f"Image generation failed: {image_result.get('error', 'Unknown error')}")
            
            # Generate chart if requested
            chart_data = None
            chart_keywords = ['chart', 'graph', 'رسم بياني', 'visual', 'trend', 'price chart', 'market chart']
            if any(word in user_message_lower for word in chart_keywords):
                chart_data = self.generate_chart_data()
            
            # Get AI response
            response = self.call_openai_api(user_message, language)
            
            return response, chart_data, image_data
            
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            return "I apologize for the technical difficulty. Please try again.", None, None

# Initialize GoldGPT instance
goldgpt = AdvancedGoldGPT()

# API Routes
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        logger.info(f"Received chat request: {data}")
        
        user_message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Generate response with error handling
        response, chart_data, image_data = goldgpt.generate_response(user_message)
        
        result = {
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if chart_data:
            result['chart'] = chart_data
            
        if image_data:
            result['image'] = image_data
        
        logger.info(f"Sending response with image: {bool(image_data)}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/generate-image', methods=['POST'])
def generate_image_endpoint():
    """Dedicated endpoint for image generation"""
    try:
        data = request.json
        prompt = data.get('prompt', '')
        filename = data.get('filename')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        result = goldgpt.generate_ai_image(prompt, filename)
        
        if result['success']:
            return jsonify({
                'success': True,
                'image_url': result['image_url'],
                'filename': result['filename'],
                'base64': result['base64'],
                'enhanced_prompt': result['enhanced_prompt'],
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }), 500
    
    except Exception as e:
        logger.error(f"Error in generate_image_endpoint: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/images/<filename>')
def serve_image(filename):
    """Serve generated images"""
    try:
        image_path = os.path.join(goldgpt.images_dir, filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        logger.error(f"Error serving image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/images', methods=['GET'])
def list_generated_images():
    """List all generated images"""
    try:
        images = []
        if os.path.exists(goldgpt.images_dir):
            for filename in os.listdir(goldgpt.images_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(goldgpt.images_dir, filename)
                    stat = os.stat(filepath)
                    images.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'url': f'/api/images/{filename}'
                    })
        
        return jsonify({'images': images})
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    try:
        history = goldgpt.get_chat_history()
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/session/<session_id>', methods=['GET'])
def get_chat_session(session_id):
    try:
        session = goldgpt.load_chat_session(session_id)
        if session:
            return jsonify(session)
        else:
            return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        logger.error(f"Error in get_chat_session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/session/<session_id>', methods=['POST'])
def save_chat_session(session_id):
    try:
        data = request.json
        messages = data.get('messages', [])
        title = data.get('title')
        
        goldgpt.save_chat_session(session_id, messages, title)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error in save_chat_session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/session/<session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    try:
        goldgpt.delete_chat_session(session_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error in delete_chat_session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prices', methods=['GET'])
def get_prices():
    try:
        gold_price = goldgpt.get_gold_price()
        kuwait_prices = goldgpt.get_kuwait_gold_prices()
        metal_prices = goldgpt.get_metal_prices_api()
        
        return jsonify({
            'gold': gold_price,
            'kuwait': kuwait_prices,
            'metals': metal_prices
        })
    except Exception as e:
        logger.error(f"Error in get_prices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        query = request.args.get('query', '')
        if query:
            products = goldgpt.search_csv_products(query)
        else:
            products = goldgpt.get_all_csv_products()
        
        return jsonify({'products': products})
    except Exception as e:
        logger.error(f"Error in get_products: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Error in health_check: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        logger.info("Starting Enhanced GoldGPT Flask application with DALL-E 3...")
        app.run(debug=True, host='0.0.0.0', port=5003)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        print(f"Failed to start application: {str(e)}")