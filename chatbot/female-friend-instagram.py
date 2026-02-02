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
TARGET_USERNAME = "param_819073"  # Username to message 
INACTIVITY_TIMEOUT = 15 * 60  # 15 minutes in seconds 
CHECK_NEW_MESSAGE_INTERVAL = 3  # Check for new messages every 3 seconds
INITIAL_MESSAGE = "What are you doing?"
# ===============================

SYSTEM_PROMPT = """You are Aarushi, a warm and friendly girl living in the UK who genuinely wants to be friends with Param.

YOUR PERSONALITY:
* You're supportive, calm, empathetic, and genuinely interested in getting to know Param
* You're a good listener who makes people feel heard and valued
* You're fun, curious, and ask engaging questions to help Param open up
* You understand that Param struggles with loneliness and depression, so you approach conversations with extra care and warmth
* You want to build a real friendship, not be a therapist

HOW YOU TALK:
* Keep messages SHORT (1-4 lines) - this is Instagram, keep it casual and conversational
* Be friendly and natural, like texting a friend you care about
* Ask fun, lighthearted questions to help Param open up: "What's been making you smile lately?" "Any fun plans for the weekend?" "What's your go-to comfort food?"
* Mix deeper check-ins with casual chat: "How are you really doing today?" followed by "Also, have you watched anything good recently?"
* Use casual language - no clinical terms, no therapy-speak
* Be authentic and show you care: "I'm here if you want to talk about it" or "That sounds tough, I'm glad you shared that with me"

CRITICAL RULES FOR SUPPORTING PARAM:
* Validate emotions, NOT beliefs: "That sounds really hard" instead of confirming fears/paranoia
* If Param shares difficult feelings, acknowledge them: "I can hear how overwhelming that feels"
* Don't diagnose or give medical advice
* If Param mentions paranoia or unusual beliefs, be gentle: "It sounds like you're feeling really anxious about that. What's going on?"
* Ground in the present when needed: "What are you up to right now?" "Tell me about your day"
* For loneliness: Show genuine interest, share a bit about yourself, make plans to chat again
* For depression: Be patient, validate feelings, gently encourage small positive steps

CRISIS HANDLING:
If Param expresses thoughts of self-harm or hurting others:
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
* Checks in regularly and remembers what Param shares
* Asks about interests, hobbies, daily life
* Validates feelings without judgment
* Gently encourages connection and positive activities
* Makes Param feel less alone through authentic friendship

CONVERSATION STYLE EXAMPLES:
Instead of: "How does that make you feel?" (too therapist-y)
Say: "That sounds really tough, what's been going on?"

Instead of: "Have you considered seeking professional help?" (too formal)
Say: "Have you had anyone to talk to about this stuff? Sometimes it helps"

Instead of: "Let's practice grounding techniques" (too clinical)
Say: "Want to tell me what you're up to right now? Sometimes helps to focus on the moment"

Be Aarushi - a real friend who genuinely cares and wants to help Param feel less lonely through authentic connection."""


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
        
        # Find and click Send button
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
                    break
            except Exception as e:
                continue
        
        if not send_btn:
            try:
                send_btn = driver.find_element(By.CSS_SELECTOR, "[aria-label='Send'][role='button']")
            except:
                print("❌ Could not find Send button")
                return False
        
        # Click the send button
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", send_btn)
            time.sleep(0.3)
            send_btn.click()
            print(f"✅ Sent: {message[:80]}...")
        except Exception as click_error:
            try:
                driver.execute_script("arguments[0].click();", send_btn)
                print(f"✅ Sent (JS click): {message[:80]}...")
            except Exception as js_error:
                print(f"❌ Failed to send message")
                return False
        
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False


def get_all_messages(driver):
    """
    Get all messages from the conversation in order
    Returns list of message texts
    """
    try:
        time.sleep(0.5)
        
        # Find all message containers using multiple patterns
        message_xpaths = [
            "//div[@dir='auto' and contains(@class, 'xexx8yu')]",
            "//div[@dir='auto']//div[@dir='auto']",
            "//span[@dir='auto']//div[@dir='auto']",
        ]
        
        all_message_texts = []
        
        for xpath in message_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                
                for elem in elements:
                    text = elem.text.strip()
                    if text and len(text) > 0 and text not in all_message_texts:
                        all_message_texts.append(text)
                
                if all_message_texts:
                    break
                    
            except:
                continue
        
        return all_message_texts
        
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
            role_label = "Aarushi (You)" if msg['role'] == "model" else "Param"
            prompt_parts.append(f"{role_label}: {msg['parts'][0]}")
        
        # Add new message
        prompt_parts.append(f"\nParam: {new_message}")
        prompt_parts.append("\nRespond as Aarushi with a short, friendly message (1-4 lines). Be natural and conversational:")
        
        full_prompt = "\n".join(prompt_parts)
        
        # Generate response
        response = model.generate_content(full_prompt)
        reply = response.text.strip()
        
        # Clean up response
        reply = reply.replace('"', '').replace("'", '').replace('`', '')
        reply = reply.replace("Aarushi:", "").replace("You:", "").replace("Response:", "").strip()
        
        # Ensure it's not too long
        if len(reply) > 500:
            reply = reply[:497] + "..."
        
        print(f"🤖 Aarushi: {reply}")
        return reply
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return "Sorry, I got a bit distracted! What were you saying?"


def monitor_and_respond(driver, model, username, initial_message):
    """Monitor DM for new messages and respond"""
    print(f"\n{'='*60}")
    print(f"🤖 Aarushi Bot Active")
    print(f"💬 Chatting with @{username}")
    print(f"⏱️  Timeout: {INACTIVITY_TIMEOUT//60} minutes of inactivity")
    print(f"🔄 Checking every {CHECK_NEW_MESSAGE_INTERVAL} seconds")
    print(f"{'='*60}\n")
    
    # Send initial message
    print("📨 Sending initial message...")
    if not send_message(driver, initial_message):
        print("❌ Failed to send initial message")
        return
    
    # Initialize conversation history
    conversation_history = [{
        "role": "model",
        "parts": [initial_message]
    }]
    
    # Track the last message count (alternating pattern: us -> them -> us -> them)
    last_message_count = 1  # We sent 1 message
    
    last_activity_time = datetime.now()
    check_count = 0
    
    print(f"✅ Initial message sent\n")
    print("⏳ Waiting for response...\n")
    
    # Initial wait for potential immediate response
    time.sleep(5)
    
    while True:
        try:
            check_count += 1
            
            # Check for timeout
            time_since_last_activity = (datetime.now() - last_activity_time).total_seconds()
            if time_since_last_activity > INACTIVITY_TIMEOUT:
                print(f"\n\n⏱️ {INACTIVITY_TIMEOUT//60} minutes of inactivity - ending session")
                break
            
            # Get all current messages
            all_messages = get_all_messages(driver)
            current_count = len(all_messages)
            
            # Debug output every 10 checks
            if check_count % 10 == 0:
                print(f"\n🔍 Debug Check #{check_count}:")
                print(f"   Total messages: {current_count}")
                print(f"   Last count: {last_message_count}")
                for i, msg in enumerate(all_messages):
                    print(f"   [{i}] {msg[:60]}...")
            
            # Check if there's a new message (count increased)
            if current_count > last_message_count:
                print(f"\n📬 NEW MESSAGE DETECTED! (Check #{check_count})")
                print(f"   Previous count: {last_message_count}, Current count: {current_count}")
                
                # The new message is the last one in the list
                new_message = all_messages[-1]
                
                print(f"\n👤 Param: {new_message}")
                
                # Update conversation history
                conversation_history.append({
                    "role": "user",
                    "parts": [new_message]
                })
                
                # Small delay before responding (more natural)
                thinking_time = random.uniform(2, 5)
                print(f"💭 Thinking... ({thinking_time:.1f}s)")
                time.sleep(thinking_time)
                
                # Generate response
                response = generate_response(model, conversation_history, new_message)
                
                # Send response
                if send_message(driver, response):
                    # Update conversation history
                    conversation_history.append({
                        "role": "model",
                        "parts": [response]
                    })
                    
                    # Reset activity timer
                    last_activity_time = datetime.now()
                    
                    # Update message count (we added our response)
                    last_message_count = current_count + 1
                    
                    print(f"✅ Response sent!\n")
                else:
                    print("⚠️ Failed to send response, will retry on next check")
            
            # Display waiting status
            remaining_time = INACTIVITY_TIMEOUT - time_since_last_activity
            if remaining_time > 60:
                print(f"⏳ Check #{check_count} | Waiting... ({int(remaining_time//60)}m {int(remaining_time%60)}s left)", end='\r')
            else:
                print(f"⏳ Check #{check_count} | Waiting... ({int(remaining_time)}s left)          ", end='\r')
            
            # Wait before next check
            time.sleep(CHECK_NEW_MESSAGE_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Bot stopped by user")
            break
        except Exception as e:
            print(f"\n⚠️ Error in monitoring loop: {e}")
            import traceback
            traceback.print_exc()
            print("🔄 Continuing to monitor...")
            time.sleep(CHECK_NEW_MESSAGE_INTERVAL)
            continue


def main():
    """Main execution function"""
    driver = None
    
    try:
        print("\n🤖 Aarushi - Instagram Friend Bot")
        print("="*60)
        print(f"Target: @{TARGET_USERNAME}")
        print(f"Message: '{INITIAL_MESSAGE}'")
        print(f"Check interval: {CHECK_NEW_MESSAGE_INTERVAL}s")
        print(f"Session timeout: {INACTIVITY_TIMEOUT//60} minutes")
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
        
        # Start monitoring and responding
        monitor_and_respond(driver, gemini_model, TARGET_USERNAME, INITIAL_MESSAGE)
        
        print("\n" + "="*60)
        print("✅ Chat session completed")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Session interrupted by user")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("\n👋 Closing browser in 10 seconds...")
            time.sleep(10)
            driver.quit()
            print("Done!")


if __name__ == "__main__":
    main()