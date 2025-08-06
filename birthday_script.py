import csv
import os
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ─── Configuration ────────────────────────────────────────────────────────────
TEMPLATE_PATH = "template.png"
CSV_PATH = "our_team_details.csv"
IMAGES_DIR = "images"
OUTPUT_DIR = "output"

# Picnie API configuration (for uploading only)
PICNIE_API_KEY = "$U63b6a6bf2d13775853e1dba410ffb4cb"
PICNIE_UPLOAD_URL = "https://picnie.com/api/v1/upload-asset"

# Font files

FONT_NAME_PATH = "arialbd.ttf"
FONT_ADDRESS_PATH = "arial.ttf"
FONT_ROLE_PATH = "arial.ttf"

# Font sizes
SIZE_NAME = 36
SIZE_ADDRESS = 30
SIZE_ROLE = 28

# Profile-photo size & position
PHOTO_W, PHOTO_H = 364, 369
PHOTO_X, PHOTO_Y = 652, 362

# Spacing
LINE_SPACING = 8
TEXT_MARGIN = 15

# ─── Helpers ──────────────────────────────────────────────────────────────────
def format_today():
    now = datetime.now()
    return f"{now.month:02d}/{now.day:02d}/{now.year}"

def download_image(url, dest_path):
    resp = requests.get(url)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(resp.content)

def draw_multiline_centered(draw, lines, x_center, y_start, fonts, spacing):
    y = y_start
    for line, font in zip(lines, fonts):
        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x_center - w / 2, y), line, font=font, fill="black")
        y += h + spacing

def upload_to_picnie(image_path):
    headers = {
        'Authorization': PICNIE_API_KEY
    }
    files = {
        'image': open(image_path, 'rb')
    }
    response = requests.post(PICNIE_UPLOAD_URL, headers=headers, files=files)
    print("Upload Status Code:", response.status_code)
    print("Upload Response:", response.text)
    response_data = response.json()
    return response_data.get('image_url')

def send_whatsapp_message(phone, image_path, name):
    API_URL = "https://app.d4digitalsolutions.com/send-media"
    API_KEY = "w96Yx9YgUxaIfFQPKJNr2HmPTSpIjC"
    SENDER_NUMBER = "919150281224"

    caption = (
        f"Dear *Rtn.{name}*, \n\n"
        "Wishing you a very Happy Anniversary and a wonderful year ahead! "
        "May your special day be filled with joy and cherished moments. \n\n"
        "Rtn.PHF.PP.SRINIVASAN RAMDOSS \n"
        "District Chairman-Greetings\n"
        "Phone No: +91 98940 45150\n"
        "2025-26"
    )

    data = {
        'api_key': API_KEY,
        'sender': SENDER_NUMBER,
        'number': f"91{phone}",
        'media_type': 'image',
        'caption': caption,
        'url': image_path  # must be a valid public image URL
    }

    try:
        response = requests.post(API_URL, data=data)
        response.raise_for_status()
        print(f"✅ WhatsApp message sent to {name}")
        return True
    except Exception as e:
        print(f"❌ WhatsApp send failed for {name}: {e}")
        return False

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    font_name = ImageFont.truetype(FONT_NAME_PATH, SIZE_NAME)
    font_address = ImageFont.truetype(FONT_ADDRESS_PATH, SIZE_ADDRESS)
    font_role = ImageFont.truetype(FONT_ROLE_PATH, SIZE_ROLE)

    today = format_today()

    def normalize_date(date_str):
        parts = date_str.strip().split('/')
        if len(parts) == 3:
            month = str(int(parts[0]))
            day = str(int(parts[1]))
            year = parts[2]
            return f"run{month}/{day}/{year}"
        return date_str.strip()

    print(f"Looking for birthdays on {today}…")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_date = row["Date"].strip()
            if normalize_date(row_date) != normalize_date(today):
                print(f"Skipping {row.get('Name', '[No Name]')} (Date: {row_date})")
                continue

            name = row["Name"].strip()
            club = row["Address"].strip()
            role = row["Roll"].strip()
            img_url = row["image"].strip()

            safe_name = name.replace(" ", "_")
            img_path = os.path.join(OUTPUT_DIR, f"{safe_name}_profile.jpg")

            if 'rotary-logo.png' in img_url:
                print(f"Using noImage.jpg for {name}")
                img_path = "noImage.jpg"
            else:
                try:
                    print(f"Downloading image for {name}")
                    download_image(img_url, img_path)
                except Exception as e:
                    print(f"❌ Failed to download image for {name}: {e}")
                    continue

            # Open template
            try:
                base = Image.open(TEMPLATE_PATH).convert("RGB")
            except Exception as e:
                print(f"❌ Failed to open template: {e}")
                continue

            draw = ImageDraw.Draw(base)

            # Paste profile photo directly
            try:
                profile_img = Image.open(img_path).convert("RGBA")
                profile_img = profile_img.resize((PHOTO_W, PHOTO_H), Image.Resampling.LANCZOS)

                if profile_img.mode == "RGBA":
                    alpha = profile_img.getchannel("A")
                    base.paste(profile_img, (PHOTO_X, PHOTO_Y), mask=alpha)
                else:
                    base.paste(profile_img, (PHOTO_X, PHOTO_Y))
            except Exception as e:
                print(f"❌ Failed to paste profile image for {name}: {e}")
                continue

            # Draw name, club, role
            TEXT_X_CENTER = PHOTO_X + PHOTO_W // 2
            TEXT_Y_START = PHOTO_Y + PHOTO_H + TEXT_MARGIN
            lines = [name.upper(), club.upper(), role.upper()]
            fonts = [font_name, font_address, font_role]
            try:
                draw_multiline_centered(draw, lines, TEXT_X_CENTER, TEXT_Y_START, fonts, LINE_SPACING)
            except Exception as e:
                print(f"❌ Failed to draw text for {name}: {e}")
                continue

            # Save final image
            out_path = os.path.join(OUTPUT_DIR, f"{safe_name}_birthday.jpg")
            try:
                base.save(out_path)
                print(f"✅ Created image: {out_path}")
                out_url = upload_to_picnie(out_path)
                if not out_url:
                    print(f"❌ Upload failed for {name}")
                else:
                    print(f"✅ Uploaded to Picnie: {out_url}")
                   # whatsapp_number = (row.get("WhatsApp") or row.get("Phone") or "").strip()
                    whatsapp_number = row.get("WhatsApp")
                    if whatsapp_number:
                        send_whatsapp_message(whatsapp_number, out_url, name)
                    else:
                        print(f"⚠️ No WhatsApp number for {name}")
            except Exception as e:
                print(f"❌ Failed to save image for {name}: {e}")

    print("🎉 All done!")

if __name__ == "__main__":
    main()
