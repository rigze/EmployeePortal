"""
CAPTCHA Generator Module
Generates image-based CAPTCHAs for login security
"""
import random
import string
import base64
import io
import uuid
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# In-memory store for CAPTCHAs: {captcha_id: {"text": "ABC12", "expires": datetime}}
captcha_store = {}

# CAPTCHA settings
CAPTCHA_LENGTH = 5
CAPTCHA_EXPIRY_MINUTES = 5
CAPTCHA_WIDTH = 200
CAPTCHA_HEIGHT = 70


def generate_captcha_text(length: int = CAPTCHA_LENGTH) -> str:
    """Generate random alphanumeric text (excluding confusing chars like 0, O, l, 1)"""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(random.choice(chars) for _ in range(length))


def generate_captcha_image(text: str) -> str:
    """
    Generate a CAPTCHA image with the given text.
    Returns base64-encoded PNG image.
    """
    # Create image with random background color
    bg_color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
    image = Image.new('RGB', (CAPTCHA_WIDTH, CAPTCHA_HEIGHT), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Try to use a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Draw each character with slight rotation and offset
    x_offset = 20
    for char in text:
        # Random color for each character
        char_color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        # Random vertical offset
        y_offset = random.randint(5, 20)
        draw.text((x_offset, y_offset), char, font=font, fill=char_color)
        x_offset += 35
    
    # Add noise lines
    for _ in range(5):
        x1 = random.randint(0, CAPTCHA_WIDTH)
        y1 = random.randint(0, CAPTCHA_HEIGHT)
        x2 = random.randint(0, CAPTCHA_WIDTH)
        y2 = random.randint(0, CAPTCHA_HEIGHT)
        line_color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=2)
    
    # Add noise dots
    for _ in range(100):
        x = random.randint(0, CAPTCHA_WIDTH)
        y = random.randint(0, CAPTCHA_HEIGHT)
        dot_color = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
        draw.point((x, y), fill=dot_color)
    
    # Convert to base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{image_base64}"


def create_captcha() -> dict:
    """
    Create a new CAPTCHA.
    Returns dict with captcha_id and image.
    """
    # Clean expired CAPTCHAs
    cleanup_expired()
    
    # Generate new CAPTCHA
    captcha_id = str(uuid.uuid4())
    text = generate_captcha_text()
    image = generate_captcha_image(text)
    
    # Store for verification
    captcha_store[captcha_id] = {
        "text": text,
        "expires": datetime.now() + timedelta(minutes=CAPTCHA_EXPIRY_MINUTES)
    }
    
    return {
        "captcha_id": captcha_id,
        "image": image
    }


def verify_captcha(captcha_id: str, user_text: str) -> bool:
    """
    Verify user's CAPTCHA input.
    Returns True if correct, False otherwise.
    CAPTCHA is cleared after verification attempt.
    """
    if not captcha_id or captcha_id not in captcha_store:
        return False
    
    stored = captcha_store.pop(captcha_id)  # Remove after use (one-time)
    
    # Check expiry
    if datetime.now() > stored["expires"]:
        return False
    
    # Case-insensitive comparison
    return user_text.upper() == stored["text"].upper()


def cleanup_expired():
    """Remove expired CAPTCHAs from store"""
    now = datetime.now()
    expired = [k for k, v in captcha_store.items() if now > v["expires"]]
    for k in expired:
        del captcha_store[k]
