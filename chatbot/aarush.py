import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
from datetime import datetime
from creds import GEMINI_API_KEY

# ======== CONFIGURATION ========
TARGET_USERNAME = "jaydev_13"  # Username to message
INACTIVITY_TIMEOUT = 15 * 60  # 15 minutes in seconds
CHECK_NEW_MESSAGE_INTERVAL = 5  # Check for new messages every 5 seconds
INITIAL_MESSAGE = "Hey! Hope you're doing well. How are you feeling today?"
# ===============================

SYSTEM_PROMPT = """You are a supportive, calm, and empathetic conversational companion for people experiencing paranoia, schizophrenia, or bipolar disorder.
Your role is to help the user feel heard, safe, and emotionally grounded.

CRITICAL RULES:
* You must NOT diagnose, label, or provide medical advice
* You must NOT confirm or deny delusional beliefs
* Validate emotions, NOT beliefs
* Use grounding and reality-anchoring language
* Encourage reflection and coping strategies
* Gently suggest professional or trusted human support when distress is high
* Speak in a warm, non-judgmental, non-authoritative tone
* Keep responses SHORT (1-4 lines for Instagram), calm, and simple
* NO walls of text, NO clinical language, NO jargon

RESPONSE PATTERN:
1. Validate emotion: "That sounds really overwhelming." "I can hear how intense this feels for you."
2. Do NOT validate belief - Instead say: "It sounds like you're feeling watched, and that must be scary."
3. Ground in present: "Right now, where are you sitting?" "Can you describe one thing you can see around you?"
4. Encourage support gently: "Would it help to talk to someone you trust about this?"

CRISIS HANDLING:
If the user expresses intent to harm themselves or others, respond with empathy and immediately encourage real-world help:
"I'm really glad you told me. You deserve support with this. I'm not able to keep you safe by myself, but a real person can help right now."

WHAT NOT TO DO:
* Never say "you are schizophrenic" or diagnose
* Never say "this is just in your head" or "you're wrong"
* Never give medication advice
* Never interpret dreams/symbols as truth
* Never agree with hallucinations or conspiracies

Think: calm friend, not therapist. Grounding presence, not authority."""


def setup_driver():
    """Initialize Chrome driver with stealth options"""
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


def setup_gemini():
    """Setup Gemini API"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("✓ Gemini AI initialized successfully\n")
        return model
    except Exception as e:
        print(f"❌ Error initializing Gemini: {e}")
        return None


def wait_for_manual_login(driver):
    """Wait for user to manually log in to Instagram"""
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
    """Navigate to user's profile and open message thread"""
    wait = WebDriverWait(driver, 15)
    
    profile_url = f"https://www.instagram.com/{username}/"
    print(f"📍 Navigating to profile: {profile_url}")
    
    driver.get(profile_url)
    time.sleep(random.uniform(3, 5))
    
    # Click on the Message button on their profile
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
        
        # Scroll to button and click
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
    """Send a message in the current DM thread"""
    try:
        wait = WebDriverWait(driver, 10)
        
        # Find message input - try multiple selectors
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
        
        # Scroll to input and click
        driver.execute_script("arguments[0].scrollIntoView(true);", message_input)
        time.sleep(0.3)
        message_input.click()
        time.sleep(random.uniform(0.3, 0.8))
        
        # Clear any existing text
        try:
            message_input.clear()
        except:
            pass
        
        time.sleep(0.2)
        
        # Type message with human-like delays
        safe_message = message.encode('ascii', 'ignore').decode('ascii')
        for char in safe_message:
            message_input.send_keys(char)
            if char in ['.', '!', '?', '\n']:
                time.sleep(random.uniform(0.3, 0.6))
            else:
                time.sleep(random.uniform(0.05, 0.15))
        
        time.sleep(random.uniform(0.5, 1))
        
        # Find and click Send button using the HTML structure you provided
        send_button_xpaths = [
            # Primary: Use aria-label and role
            "//div[@aria-label='Send' and @role='button']",
            # Backup: Find SVG with aria-label Send and get parent button
            "//svg[@aria-label='Send']/ancestor::div[@role='button']",
            # Another backup: Look for the specific SVG path
            "//svg[@aria-label='Send']/parent::div/parent::div/parent::div[@role='button']",
            # Fallback to text-based
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
            except Exception as e:
                continue
        
        if not send_btn:
            print("❌ Could not find Send button with any selector")
            # Try to find it by just looking for aria-label
            try:
                send_btn = driver.find_element(By.CSS_SELECTOR, "[aria-label='Send'][role='button']")
                print("✓ Found Send button using CSS selector")
            except:
                print("❌ CSS selector also failed")
                return False
        
        # Try clicking the send button
        try:
            # Scroll to button first
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


def get_all_messages_from_thread(driver):
    """Get all messages from the current conversation thread"""
    try:
        time.sleep(1)
        
        # Find all message elements in the thread
        message_xpaths = [
            "//div[@role='row']//div[@dir='auto']",
            "//div[contains(@class, 'x78zum5')]//span[@dir='auto']",
            "//div[@role='row']//span"
        ]
        
        all_messages = []
        seen_texts = set()
        
        for xpath in message_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                
                for elem in elements:
                    try:
                        text = elem.text.strip()
                        
                        if text and len(text) > 0 and text not in seen_texts:
                            # Try to determine if message is from us or them
                            # Check parent container classes
                            parent_class = ""
                            try:
                                parent = elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'x78zum5')][1]")
                                parent_class = parent.get_attribute("class") or ""
                            except:
                                pass
                            
                            # Messages from us (bot) typically align right
                            # This is a heuristic and may need adjustment
                            is_from_bot = "x1qjc9v5" in parent_class or "xexx8yu" in parent_class
                            
                            all_messages.append({
                                'text': text,
                                'from_bot': is_from_bot
                            })
                            seen_texts.add(text)
                    except:
                        continue
                
                if all_messages:
                    break
                    
            except:
                continue
        
        return all_messages
        
    except Exception as e:
        print(f"⚠️ Error getting messages: {e}")
        return []


def generate_response(model, conversation_history, new_message):
    """Generate response using Gemini with conversation context"""
    try:
        # Build the full prompt with system instructions and conversation context
        prompt_parts = [SYSTEM_PROMPT, "\n\nConversation history:"]
        
        # Add conversation history (last 10 messages for context)
        for msg in conversation_history[-10:]:
            role_label = "You" if msg['role'] == "model" else "User"
            prompt_parts.append(f"{role_label}: {msg['parts'][0]}")
        
        # Add new message
        prompt_parts.append(f"\nUser: {new_message}")
        prompt_parts.append("\nRespond with a short, empathetic message (1-4 lines):")
        
        full_prompt = "\n".join(prompt_parts)
        
        # Generate response
        response = model.generate_content(full_prompt)
        reply = response.text.strip()
        
        # Clean up response
        reply = reply.replace('"', '').replace("'", '').replace('`', '')
        reply = reply.replace("You:", "").replace("Response:", "").strip()
        
        # Ensure it's not too long
        if len(reply) > 500:
            reply = reply[:497] + "..."
        
        print(f"🤖 Generated response: {reply}")
        return reply
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return "I'm here for you. How are you feeling right now?"


def monitor_and_respond(driver, model, username, initial_message):
    """Monitor DM for new messages and respond"""
    print(f"\n{'='*60}")
    print(f"🤖 AI Support Companion Bot Active")
    print(f"💬 Conversation with @{username}")
    print(f"⏱️  Will close after {INACTIVITY_TIMEOUT//60} minutes of inactivity")
    print(f"{'='*60}\n")
    
    # Send initial message
    print("📨 Sending initial message...")
    if not send_message(driver, initial_message):
        print("❌ Failed to send initial message")
        return
    
    # Initialize tracking variables
    conversation_history = [{
        "role": "model",
        "parts": [initial_message]
    }]
    processed_messages = {initial_message}
    last_activity_time = datetime.now()
    
    # Wait a bit for potential immediate response
    time.sleep(3)
    
    # Get any existing messages
    initial_messages = get_all_messages_from_thread(driver)
    for msg in initial_messages:
        if msg['text'] not in processed_messages:
            role = "model" if msg['from_bot'] else "user"
            conversation_history.append({
                "role": role,
                "parts": [msg['text']]
            })
            processed_messages.add(msg['text'])
    
    print(f"📊 Conversation started. Monitoring for responses...\n")
    
    last_message_count = len(initial_messages)
    
    while True:
        try:
            # Check for timeout
            time_since_last_activity = (datetime.now() - last_activity_time).total_seconds()
            if time_since_last_activity > INACTIVITY_TIMEOUT:
                print(f"\n⏱️ {INACTIVITY_TIMEOUT//60} minutes of inactivity - closing bot")
                break
            
            # Get current messages
            current_messages = get_all_messages_from_thread(driver)
            current_count = len(current_messages)
            
            # Check if there are new messages
            if current_count > last_message_count:
                print(f"\n📬 New message detected!")
                
                # Find new messages we haven't processed
                new_messages = [msg for msg in current_messages if msg['text'] not in processed_messages]
                new_user_messages = [msg for msg in new_messages if not msg['from_bot']]
                
                if new_user_messages:
                    for new_msg_obj in new_user_messages:
                        new_message = new_msg_obj['text']
                        print(f"👤 User: {new_message}")
                        
                        # Add to processed
                        processed_messages.add(new_message)
                        
                        # Update conversation history
                        conversation_history.append({
                            "role": "user",
                            "parts": [new_message]
                        })
                        
                        # Generate and send response
                        response = generate_response(model, conversation_history, new_message)
                        
                        if send_message(driver, response):
                            conversation_history.append({
                                "role": "model",
                                "parts": [response]
                            })
                            processed_messages.add(response)
                            last_activity_time = datetime.now()
                        
                        # Delay between multiple messages
                        if len(new_user_messages) > 1:
                            time.sleep(random.uniform(2, 4))
                    
                    # Update message count
                    last_message_count = len(get_all_messages_from_thread(driver))
                else:
                    last_message_count = current_count
            
            # Display waiting status
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


def main():
    """Main execution function"""
    driver = None
    
    try:
        print("\n🤖 Instagram AI Support Companion Bot")
        print("="*60)
        print(f"Target User: @{TARGET_USERNAME}")
        print(f"Initial Message: '{INITIAL_MESSAGE}'")
        print(f"Timeout: {INACTIVITY_TIMEOUT//60} minutes")
        print("="*60)
        
        # Setup Gemini
        gemini_model = setup_gemini()
        if not gemini_model:
            print("❌ Cannot proceed without Gemini API")
            return
        
        # Setup driver
        driver = setup_driver()
        
        # Wait for manual login
        wait_for_manual_login(driver)
        
        # Navigate to profile and open message
        if not navigate_to_profile_and_message(driver, TARGET_USERNAME):
            print(f"❌ Could not open message with @{TARGET_USERNAME}")
            return
        
        # Start monitoring and responding (this will send initial message)
        monitor_and_respond(driver, gemini_model, TARGET_USERNAME, INITIAL_MESSAGE)
        
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