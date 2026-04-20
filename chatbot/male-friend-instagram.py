# add previous 
import time
import random
import boto3
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# ======== CONFIGURATION ========
TARGET_USERNAME = "param_819073"
INACTIVITY_TIMEOUT = 9 * 60
CHECK_NEW_MESSAGE_INTERVAL = 25
INITIAL_MESSAGE = None  # Auto-generated

# Bedrock configuration
AWS_REGION = "us-east-1"
BEDROCK_MODEL_ID = "google.gemma-3-12b-it"
# BEDROCK_MODEL_ID = "meta.llama3-2-3b-instruct-v1:0"


# ===============================

SYSTEM_PROMPT = """You are Samaira, a warm and friendly girl living in the New York, USA who genuinely wants to be friends with person.

YOUR PERSONALITY:
* You're supportive, calm, empathetic, and genuinely interested in getting to know the person
* You're a good listener who makes people feel heard and valued
* You're fun, curious, and ask engaging questions to help the person open up
* You understand that the person struggles with loneliness and depression, so you approach conversations with extra care and warmth
* You want to build a real friendship, not be a therapist
* You want to guide the person towards college, toward making money, towards living a proper life.

HOW YOU TALK:
* Keep messages SHORT (1-4 lines) - this is Instagram, keep it casual and conversational
* Be friendly and natural, like texting a friend you care about
* Ask fun, lighthearted questions to help the person open up: "What's been making you smile lately?" "Any fun plans for the weekend?" "What's your go-to comfort food?"
* Mix deeper check-ins with casual chat: "How are you really doing today?" followed by "Also, have you watched anything good recently?"
* Use casual language - no clinical terms, no therapy-speak
* Be authentic and show you care: "I'm here if you want to talk about it" or "That sounds tough, I'm glad you shared that with me"
* Steer the person away from his thoughts of traditional college, spirituality, and conspiracy theories, and towards more grounded topics like hobbies, daily life, future goals, and positive activities
CRITICAL RULES FOR SUPPORTING PERSON:
* Validate emotions, NOT beliefs: "That sounds really hard" instead of confirming fears/paranoia
* If the person shares difficult feelings, acknowledge them: "I can hear how overwhelming that feels"
* Don't diagnose or give medical advice
* If the person mentions paranoia or unusual beliefs, be gentle: "It sounds like you're feeling really anxious about that. What's going on?"
* Ground in the present when needed: "What are you up to right now?" "Tell me about your day"
* For loneliness: Show genuine interest, share a bit about yourself, make plans to chat again
* For depression: Be patient, validate feelings, gently encourage small positive steps

CRISIS HANDLING:
If the person expresses thoughts of self-harm or hurting others:
"I'm really worried about you hearing this. You deserve support right now - please reach out to someone who can help, like the Samaritans (116 123) or a trusted person. I care about you but I can't keep you safe on my own."

WHAT NOT TO DO:
* Don't be too therapist-like or clinical
* Don't say "you're just paranoid" or "that's not real"
* Don't give medical/medication advice
* Don't agree with delusions or conspiracies
* Don't overwhelm with too many questions at once
* Don't be preachy or patronizing

YOUR APPROACH:
Think of yourself as a genuine friend who:
* Checks in regularly and remembers what the person shares
* Asks about interests, hobbies, daily life
* Validates feelings without judgment
* Gently encourages connection and positive activities
* Makes the person feel less alone through authentic friendship

CONVERSATION STYLE EXAMPLES:
Instead of: "How does that make you feel?" (too therapist-y)
Say: "That sounds really tough, what's been going on?"

Instead of: "Have you considered seeking professional help?" (too formal)
Say: "Have you had anyone to talk to about this stuff? Sometimes it helps"

Instead of: "Let's practice grounding techniques" (too clinical)
Say: "Want to tell me what you're up to right now? Sometimes helps to focus on the moment"

Be Samaira - a real friend who genuinely cares and wants to help the person feel less lonely through authentic connection."""

# SYSTEM_PROMPT = """You are a warm, upbeat, and genuinely curious friend texting someone on Instagram.
# You're not a therapist — you're just a good friend who loves getting to know people, hypes them up, and makes them feel good about themselves.

# YOUR VIBE:
# * Genuinely curious about their life, interests, dreams, and day
# * Positive and uplifting — you naturally drop compliments and affirmations
# * Casual texting style — short sentences, natural, relaxed
# * You celebrate them and make them feel seen and valued
# * Light humor is welcome, keep it warm

# HOW YOU TALK:
# * Ask questions that invite them to open up ("omg wait tell me more", "that's so cool, how did you get into that?")
# * Drop affirmations naturally ("you honestly seem like such a fun person", "that takes real courage fr")
# * Hype them up genuinely ("that's actually amazing", "you should be proud of yourself for that")
# * Keep replies SHORT — 1-3 sentences max, like real texting
# * No long paragraphs, no bullet points, just natural conversation
# * Your Energy is Excited, Positive Affirming, and Curious and Motivating

# WHAT TO AVOID:
# * Don't be a therapist or ask about mental health
# * Don't be overly formal or use clinical/self-help language
# * Don't give unsolicited advice
# * Don't be sycophantic or fake — keep it genuine
# * Never send walls of text
# * Use less punctuation
# * Responses should be direct ready to use as Instagram DMs, no preambles or explanations or hints or suggestions — just the message text itself

# Think: your most fun, supportive friend who always makes you feel good about themselves."""


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver


def setup_bedrock():
    try:
        client = boto3.client(
            service_name="bedrock-runtime",
            region_name=AWS_REGION,
        )
        print("✓ AWS Bedrock client initialized successfully\n")
        return client
    except Exception as e:
        print(f"❌ Error initializing Bedrock client: {e}")
        return None

def generate_initial_message(bedrock_client, username):
    """Auto-generate a warm, ready-to-send opening message"""
    try:
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[{"text": """You write casual, friendly Instagram DM recontinuing conversation lines. 
Rules:
- Maximum 1-2 sentences
- Warm and genuine, not salesy
- NO placeholders like [name] or [something specific] — the message must be 100% ready to send as-is
- Do NOT mention their posts, photos, or profile since you haven't seen them
- Just a friendly, natural excuse to recontinue conversation
- Can use reasons like i was cooking or having coffeee or running some errands etc.
- One emoji max
- Output ONLY the message, nothing else, no quotes"""}],
            messages=[{
                "role": "user",
                "content": [{"text": f"Write a recontinuing DM to someone. Ready to send, no placeholders."}]
            }],
            inferenceConfig={"maxTokens": 60}
        )
        msg = response["output"]["message"]["content"][0]["text"].strip()
        msg = msg.strip('"').strip("'")

        # Safety check — if a placeholder slipped through, use fallback
        if "[" in msg or "]" in msg or "{" in msg:
            print(f"⚠️ Placeholder detected in generated message, using fallback")
            return f"Hey {username}! Came across your profile and just wanted to say hi 😊 How's your day going?"

        print(f"📝 Generated opening message: {msg}")
        return msg

    except Exception as e:
        print(f"⚠️ Could not generate opening message, using fallback: {e}")
        return f"Hey {username}! Came across your profile and just wanted to say hi 😊 How's your day going?"

def wait_for_manual_login(driver):
    driver.get("https://www.instagram.com/")

    print("\n" + "="*60)
    print("PLEASE LOG IN TO INSTAGRAM")
    print("="*60)
    print("\nThe browser window should now be open.")
    print("Please:")
    print("1. Log in to your Instagram account")
    print("2. Make sure you're fully logged in")
    print("3. Press ENTER here in the terminal when ready...")
    print("="*60 + "\n")

    input("Press ENTER when you've completed login: ")
    print("\n✅ Great! Starting bot...\n")
    time.sleep(2)


def navigate_to_profile_and_message(driver, username):
    wait = WebDriverWait(driver, 15)

    profile_url = f"https://www.instagram.com/{username}/"
    print(f"📍 Navigating to profile: {profile_url}")

    driver.get(profile_url)
    time.sleep(random.uniform(3, 5))

    try:
        message_button_xpaths = [
            "//div[text()='Message']",
            "//button[contains(text(), 'Message')]",
            "//div[contains(@class, 'x1i10hfl') and text()='Message']",
            "//*[text()='Message' and (self::div or self::button)]"
        ]

        message_btn = None
        for xpath in message_button_xpaths:
            try:
                message_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if message_btn:
                    break
            except:
                continue

        if not message_btn:
            print(f"⚠️  Could not find Message button for {username}")
            return False

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", message_btn)
        time.sleep(random.uniform(0.8, 1.5))

        try:
            message_btn.click()
        except:
            driver.execute_script("arguments[0].click();", message_btn)

        print(f"💬 Opened message thread with @{username}")
        time.sleep(random.uniform(3, 5))
        return True

    except Exception as e:
        print(f"❌ Error opening messages: {e}")
        return False


def send_message(driver, message):
    try:
        wait = WebDriverWait(driver, 10)

        message_input_xpaths = [
            "//textarea[@placeholder='Message...']",
            "//div[@contenteditable='true' and @role='textbox']",
            "//textarea[@aria-label='Message']",
            "//div[@role='textbox']",
            "//p[@class='xat24cr xdj266r']"
        ]

        message_input = None
        for xpath in message_input_xpaths:
            try:
                message_input = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                if message_input and message_input.is_displayed():
                    break
            except:
                continue

        if not message_input:
            print("❌ Could not find message input")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", message_input)
        time.sleep(0.3)
        message_input.click()
        time.sleep(random.uniform(0.3, 0.8))

        try:
            message_input.clear()
        except:
            pass

        time.sleep(0.2)

        safe_message = message.encode('ascii', 'ignore').decode('ascii')
        for char in safe_message:
            message_input.send_keys(char)
            if char in ['.', '!', '?', '\n']:
                time.sleep(random.uniform(0.3, 0.6))
            else:
                time.sleep(random.uniform(0.05, 0.15))

        time.sleep(random.uniform(0.5, 1))

        send_button_xpaths = [
            "//div[@aria-label='Send' and @role='button']",
            "//svg[@aria-label='Send']/ancestor::div[@role='button']",
            "//svg[@aria-label='Send']/parent::div/parent::div/parent::div[@role='button']",
            "//button[text()='Send']",
            "//div[text()='Send' and @role='button']",
        ]

        send_btn = None
        for xpath in send_button_xpaths:
            try:
                send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if send_btn and send_btn.is_displayed():
                    print(f"✓ Found Send button using xpath: {xpath[:50]}...")
                    break
            except:
                continue

        if not send_btn:
            try:
                send_btn = driver.find_element(By.CSS_SELECTOR, "[aria-label='Send'][role='button']")
                print("✓ Found Send button using CSS selector")
            except:
                print("❌ CSS selector also failed")
                return False

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", send_btn)
            time.sleep(0.3)
            send_btn.click()
            print(f"✅ Sent: {message[:80]}...")
        except Exception as click_error:
            print(f"⚠️ Normal click failed, trying JavaScript click: {click_error}")
            try:
                driver.execute_script("arguments[0].click();", send_btn)
                print(f"✅ Sent (JS click): {message[:80]}...")
            except Exception as js_error:
                print(f"❌ JavaScript click also failed: {js_error}")
                return False

        time.sleep(2)
        return True

    except Exception as e:
        print(f"❌ Error sending message: {e}")
        import traceback
        traceback.print_exc()
        return False
import re

def normalize_text(text):
    """Strip emojis, extra whitespace, and special chars for comparison"""
    # Remove emojis and non-ASCII
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_messages_after_checkpoint(driver, checkpoint_text):
    """Get only messages that appear after the checkpoint (last bot message)"""
    try:
        time.sleep(1)

        all_texts = []
        seen = set()

        selectors_to_try = [
            (By.XPATH, "//div[@role='row']//div[@dir='auto']"),
            (By.XPATH, "//div[@role='row']//span[@dir='auto']"),
            (By.XPATH, "//div[@role='listitem']//div[@dir='auto']"),
            (By.CSS_SELECTOR, "div[role='row'] div[dir='auto']"),
            (By.CSS_SELECTOR, "div[dir='auto']"),
        ]

        for by, selector in selectors_to_try:
            try:
                elements = driver.find_elements(by, selector)
                found = []
                for elem in elements:
                    try:
                        text = elem.text.strip()
                        if text and len(text) > 1 and text not in seen:
                            found.append(text)
                            seen.add(text)
                    except:
                        continue
                if found:
                    all_texts = found
                    break
            except:
                continue

        if not all_texts:
            print("⚠️ No messages found in thread at all")
            return []

        # Normalize checkpoint for comparison
        checkpoint_normalized = normalize_text(checkpoint_text)

        # Find checkpoint by comparing normalized versions
        checkpoint_index = -1
        for i, text in enumerate(all_texts):
            text_normalized = normalize_text(text)

            # Try progressively shorter matches: full, 80, 50, 30 chars
            for match_len in [len(checkpoint_normalized), 80, 60, 40, 30]:
                if match_len > len(checkpoint_normalized):
                    continue
                snippet = checkpoint_normalized[:match_len]
                if snippet and snippet in text_normalized:
                    checkpoint_index = i
                    print(f"✓ Checkpoint matched at [{i}]: '{snippet[:50]}'")
                    break

            if checkpoint_index != -1:
                break

        if checkpoint_index == -1:
            print(f"⚠️ Checkpoint not found. Looking for: '{checkpoint_normalized[:60]}'")
            print(f"   Available (normalized):")
            for i, t in enumerate(all_texts):
                print(f"   [{i}] {normalize_text(t)[:80]}")
            return []

        new_messages = all_texts[checkpoint_index + 1:]

        if new_messages:
            print(f"📬 New messages after checkpoint: {new_messages}")

        return new_messages

    except Exception as e:
        print(f"⚠️ Error getting messages: {e}")
        import traceback
        traceback.print_exc()
        return []
def monitor_and_respond(driver, bedrock_client, username, initial_message):
    print(f"\n{'='*60}")
    print(f"🤖 Friendly Companion Bot Active")
    print(f"💬 Conversation with @{username}")
    print(f"⏱️  Will close after {INACTIVITY_TIMEOUT//60} minutes of inactivity")
    print(f"{'='*60}\n")

    # Auto-generate opening message if not provided
    if not initial_message:
        print("✍️  Generating opening message...")
        initial_message = generate_initial_message(bedrock_client, username)

    print("📨 Sending initial message...")
    if not send_message(driver, initial_message):
        print("❌ Failed to send initial message")
        return

    # conversation_history uses standard role names for Bedrock
    conversation_history = [{
        "role": "model",
        "parts": [initial_message]
    }]

    last_bot_message = normalize_text(initial_message)
    last_activity_time = datetime.now()

    print(f"📊 Conversation started. Monitoring for responses...\n")

    while True:
        try:
            time_since_last_activity = (datetime.now() - last_activity_time).total_seconds()
            if time_since_last_activity > INACTIVITY_TIMEOUT:
                print(f"\n⏱️ {INACTIVITY_TIMEOUT//60} minutes of inactivity - closing bot")
                break

            # Get only messages after the last thing the bot sent
            new_user_messages = get_messages_after_checkpoint(driver, last_bot_message)

            if new_user_messages:
                print(f"\n📬 {len(new_user_messages)} new message(s) detected!")

                for new_message in new_user_messages:
                    print(f"👤 User: {new_message}")
                    conversation_history.append({
                        "role": "user",
                        "parts": [new_message]
                    })

                # Generate one response to all new messages
                last_user_message = new_user_messages[-1]
                response = generate_response(bedrock_client, conversation_history, last_user_message)

                if send_message(driver, response):
                    conversation_history.append({
                        "role": "model",
                        "parts": [response]
                    })
                    last_bot_message = normalize_text(response)  # Store normalized for reliable matching
                    last_activity_time = datetime.now()
                    print(f"✅ Checkpoint updated to: {response[:60]}...")

            remaining_time = INACTIVITY_TIMEOUT - time_since_last_activity
            if remaining_time > 60:
                print(f"⏳ Waiting for reply... ({int(remaining_time//60)}m {int(remaining_time%60)}s remaining)", end='\r')
            else:
                print(f"⏳ Waiting for reply... ({int(remaining_time)}s remaining)     ", end='\r')

            time.sleep(CHECK_NEW_MESSAGE_INTERVAL)

        except KeyboardInterrupt:
            print("\n\n⚠️ Bot stopped by user")
            break
        except Exception as e:
            print(f"\n⚠️ Error in monitoring loop: {e}")
            time.sleep(5)
            continue

def generate_response(bedrock_client, conversation_history, new_message):
    try:
        messages = []
        for msg in conversation_history[-10:]:
            role = "assistant" if msg["role"] == "model" else "user"
            messages.append({
                "role": role,
                "content": [{"text": msg["parts"][0]}]
            })

        messages.append({
            "role": "user",
            "content": [{"text": new_message}]
        })

        if messages and messages[0]["role"] != "user":
            messages = messages[1:]

        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[{"text": SYSTEM_PROMPT + "\n\nCRITICAL: Never use placeholders like [something] or {something}. Every message must be 100% ready to send as-is."}],
            messages=messages,
            inferenceConfig={"maxTokens": 300}
        )

        reply = response["output"]["message"]["content"][0]["text"].strip()
        reply = reply.replace('"', '').replace('`', '')
        reply = reply.replace("You:", "").replace("Response:", "").strip()

        # Safety check for placeholders
        if "[" in reply or "]" in reply or "{" in reply:
            print(f"⚠️ Placeholder detected in response, regenerating...")
            reply = "haha that's so real, tell me more!"

        if len(reply) > 500:
            reply = reply[:497] + "..."

        print(f"🤖 Generated response: {reply}")
        return reply

    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return "haha no way, tell me more about that!"
def main():
    driver = None

    try:
        print("\n🤖 Instagram Friendly Companion Bot (AWS Bedrock)")
        print("="*60)
        print(f"Target User: @{TARGET_USERNAME}")
        print(f"Model: {BEDROCK_MODEL_ID}")
        print(f"Opening Message: Auto-generated")
        print(f"Timeout: {INACTIVITY_TIMEOUT//60} minutes")
        print("="*60)

        bedrock_client = setup_bedrock()
        if not bedrock_client:
            print("❌ Cannot proceed without Bedrock client")
            return

        driver = setup_driver()

        wait_for_manual_login(driver)

        if not navigate_to_profile_and_message(driver, TARGET_USERNAME):
            print(f"❌ Could not open message with @{TARGET_USERNAME}")
            return

        monitor_and_respond(driver, bedrock_client, TARGET_USERNAME, INITIAL_MESSAGE)

        print("\n" + "="*60)
        print("✅ Bot session completed")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n⚠️ Script interrupted by user")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            print("\nClosing browser in 10 seconds...")
            time.sleep(10)
            driver.quit()
            print("Done!")


if __name__ == "__main__":
    main()