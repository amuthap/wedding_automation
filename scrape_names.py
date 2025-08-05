
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

URL = "https://rotasmart.club/greetings/w/"
OUTPUT_FILE = "our_team_details.csv"

# Fetch the page
response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")


# Helper function to extract details from a div
def extract_member_details(div):
    name_tag = div.find(["h3", "h4", "h2"])
    name = name_tag.get_text(strip=True) if name_tag else ""
    # Try to extract club name from <p>, <span>, or next sibling after name header
    club = ""
    club_tag = div.find("p")
    if club_tag:
        club = club_tag.get_text(strip=True)
    else:
        # Try <span>
        span_tag = div.find("span")
        if span_tag:
            club = span_tag.get_text(strip=True)
        else:
            # Try next sibling after name header
            if name_tag:
                next_elem = name_tag.find_next_sibling()
                if next_elem and next_elem.name in ["div", "span", "p"]:
                    club = next_elem.get_text(strip=True)
                else:
                    # Try to find text that looks like a club name
                    for elem in div.find_all(text=True):
                        if "RC of" in elem or "RC Of" in elem:
                            club = elem.strip()
                            break
    phone_tag = div.find("a", href=True)
    phone = ""
    whatsapp = ""
    if phone_tag:
        href = phone_tag["href"]
        if href.startswith("tel:"):
            phone = href.replace("tel:", "")
        elif "whatsapp.com" in href:
            whatsapp = href
    whatsapp_tag = div.find("a", href=True, attrs={"target": "_blank"})
    if whatsapp_tag and "whatsapp.com" in whatsapp_tag["href"]:
        whatsapp = whatsapp_tag["href"]
    img_url = ""
    img_tag = div.find("img")
    if img_tag and img_tag.get("src"):
        img_url = img_tag["src"]
        if not img_url.startswith("http"):
            img_url = f"https://rotasmart.club{img_url}" if img_url.startswith("/") else f"https://rotasmart.club/greetings/w/{img_url}"
    # Add current date
    today = datetime.now().strftime("%m/%d/%Y")
    # Now, 'Address' is filled with club, 'Roll' is set to 'member'
    return {
        "Date": today,
        "image": img_url,
        "Name": name,
        "Address": club,
        "Roll": "member",
        "Phone": phone,
        "WhatsApp": whatsapp
    }

# Extract from <div class="our-team">
team_divs = soup.find_all("div", class_="our-team")
data = [extract_member_details(div) for div in team_divs]

# Extract from <div class="member">
member_divs = soup.find_all("div", class_="team-member")
data.extend([extract_member_details(div) for div in member_divs])

# Save to Excel
if data:
    # Ensure column order
    columns = ["Date", "image", "Name", "Address", "Roll", "Phone", "WhatsApp"]
    df = pd.DataFrame(data)
    df = df[columns]
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"Saved {len(data)} team members to {OUTPUT_FILE}")
else:
    print("No team details found. Please check the selector.")
