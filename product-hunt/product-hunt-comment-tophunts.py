#!/usr/bin/env python3
"""
Product Hunt Automation Script with AWS Bedrock (Qwen)
Automates browsing, upvoting, and commenting on top products of the day.
Uses AWS Bedrock + Qwen model to generate personalized comments.

Requirements:
    pip install selenium boto3
    AWS credentials configured via environment variables or ~/.aws/credentials
"""

import os
import time
import json
import random

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AWS_CONFIG = {
    "region_name": os.getenv("AWS_REGION", "us-east-1"),
    "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    # Optional – only needed when assuming a role / using temporary credentials
    "aws_session_token": os.getenv("AWS_SESSION_TOKEN"),
}

# Qwen model available on AWS Bedrock
# See: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "qwen.qwen2-5-72b-instruct-v1:0")

DELAY_BETWEEN_PRODUCTS = (30, 45)   # seconds (min, max)
COMMENT_MAX_CHARS = 500
FALLBACK_COMMENT = "This is so good. Exactly what I needed."


# ---------------------------------------------------------------------------
# Browser helpers
# ---------------------------------------------------------------------------

def setup_driver() -> webdriver.Chrome:
    """Initialise a Chrome WebDriver with anti-detection options."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=options)

def wait_for_manual_login(driver: webdriver.Chrome) -> None:
    """Pause execution and let the user log in manually."""
    print("\n" + "=" * 60)
    print("PLEASE LOG IN TO PRODUCT HUNT")
    print("=" * 60)
    print("\n1. Log in to your Product Hunt account in the browser window.")
    print("2. Make sure you are fully logged in.")
    print("3. Press ENTER here when ready.")
    print("=" * 60 + "\n")
    input("Press ENTER after completing login: ")
    print("\nGreat! Starting automation…\n")


# ---------------------------------------------------------------------------
# AWS Bedrock / Qwen helpers
# ---------------------------------------------------------------------------

def create_bedrock_client() -> boto3.client:
    """Create and return a boto3 Bedrock Runtime client."""
    kwargs = {
        "service_name": "bedrock-runtime",
        "region_name": AWS_CONFIG["region_name"],
    }
    # Only pass explicit credentials when they are set; otherwise boto3 will
    # fall back to the credential chain (~/.aws/credentials, IAM role, etc.)
    if AWS_CONFIG["aws_access_key_id"]:
        kwargs["aws_access_key_id"] = AWS_CONFIG["aws_access_key_id"]
    if AWS_CONFIG["aws_secret_access_key"]:
        kwargs["aws_secret_access_key"] = AWS_CONFIG["aws_secret_access_key"]
    if AWS_CONFIG["aws_session_token"]:
        kwargs["aws_session_token"] = AWS_CONFIG["aws_session_token"]

    client = boto3.client(**kwargs)
    print("✓ AWS Bedrock client created")
    return client


def call_qwen(client: boto3.client, prompt: str) -> str:
    """
    Call the Qwen model via AWS Bedrock converse API and return the text reply.

    Bedrock's converse() is the recommended unified API for chat models.
    """
    try:
        response = client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            inferenceConfig={
                "maxTokens": 300,
                "temperature": 0.8,
                "topP": 0.9,
            },
        )

        # Extract the assistant's text from the response
        output_message = response["output"]["message"]
        text_parts = [
            block["text"]
            for block in output_message["content"]
            if "text" in block
        ]
        return " ".join(text_parts).strip()

    except (BotoCoreError, ClientError) as exc:
        print(f"  ⚠ Bedrock API error: {exc}")
        return ""


# ---------------------------------------------------------------------------
# Product page helpers
# ---------------------------------------------------------------------------

def get_product_info(driver: webdriver.Chrome) -> dict:
    """Extract name, tagline, and extra details from the current product page."""
    info = {"name": "this product", "description": "An innovative product"}

    # Product name
    try:
        info["name"] = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
    except NoSuchElementException:
        pass

    # Tagline / description
    description_selectors = [
        "h2",
        "p.text-secondary",
        "div.text-secondary",
        "[data-test='product-description']",
        "meta[name='description']",
        "meta[property='og:description']",
    ]
    for sel in description_selectors:
        try:
            if sel.startswith("meta"):
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                text = elem.get_attribute("content") or ""
            else:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                text = elem.text.strip()
            if len(text) > 10:
                info["description"] = text
                break
        except NoSuchElementException:
            continue

    # Extra body copy (first few paragraphs)
    try:
        paragraphs = driver.find_elements(By.CSS_SELECTOR, "p, div.text-16")
        snippets = [
            p.text.strip()
            for p in paragraphs[:5]
            if 20 < len(p.text.strip()) < 500
        ]
        if snippets:
            info["details"] = " ".join(snippets[:3])
    except Exception:
        pass

    print(f"  📝 Product  : {info['name']}")
    print(f"  📄 Tagline  : {info['description'][:100]}…")
    return info


def generate_comment(client: boto3.client, product_info: dict) -> str:
    """Use Qwen via Bedrock to craft a personalised Product Hunt comment."""
    name = product_info.get("name", "this product")
    description = product_info.get("description", "")
    details = product_info.get("details", "")

    prompt = (
        "You are an enthusiastic Product Hunt community member who just discovered "
        "an exciting new product.\n\n"
        f"Product Name: {name}\n"
        f"Product Description: {description}\n"
        f"{'Additional Details: ' + details if details else ''}\n\n"
        "Write a short, authentic comment (2-3 sentences, under 280 characters) that:\n"
        "1. Shows genuine excitement about the product.\n"
        "2. Highlights one specific feature or aspect that caught your attention.\n"
        "3. Ends with one thoughtful, niche question about a use case or how it works.\n\n"
        "Keep it conversational and human. Avoid corporate buzzwords and excessive emoji. "
        "Do NOT use quotation marks in your response."
    )

    comment = call_qwen(client, prompt)

    if not comment:
        print("  ⚠ Empty response from Qwen, using fallback comment.")
        return FALLBACK_COMMENT

    # Sanitise
    comment = comment.replace('"', "").replace("'", "")
    if len(comment) > COMMENT_MAX_CHARS:
        comment = comment[: COMMENT_MAX_CHARS - 3] + "…"

    print(f"  🤖 Comment  : {comment[:100]}…")
    return comment


def upvote_product(driver: webdriver.Chrome) -> bool:
    """Click the upvote button on the current product page."""
    try:
        wait = WebDriverWait(driver, 10)
        btn = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "button[data-test='vote-button']")
            )
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        time.sleep(1)
        btn.click()
        print("  ✓ Upvoted!")
        time.sleep(2)
        return True
    except (TimeoutException, NoSuchElementException) as exc:
        print(f"  ⚠ Could not upvote: {exc}")
        return False


def post_comment(driver: webdriver.Chrome, message: str) -> bool:
    """Find the comment textarea, type the message, and submit it."""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
    time.sleep(2)

    textarea_selectors = [
        "textarea[placeholder*='comment' i]",
        "textarea[placeholder*='Add a comment' i]",
        "textarea[name='comment']",
        "div[contenteditable='true']",
        "textarea",
    ]

    for sel in textarea_selectors:
        try:
            field = driver.find_element(By.CSS_SELECTOR, sel)
            if not field.is_displayed():
                continue

            driver.execute_script("arguments[0].scrollIntoView(true);", field)
            time.sleep(1)
            field.click()
            time.sleep(0.5)
            field.send_keys(message)
            time.sleep(1)

            # Try finding the submit button via parent <form>
            submitted = False
            try:
                form = field.find_element(By.XPATH, "./ancestor::form")
                submit_btn = form.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_btn.click()
                submitted = True
            except NoSuchElementException:
                pass

            # Fallback: any visible submit button on the page
            if not submitted:
                for btn in driver.find_elements(By.CSS_SELECTOR, "button[type='submit']"):
                    if btn.is_displayed():
                        btn.click()
                        submitted = True
                        break

            if submitted:
                print(f"  ✓ Comment posted: '{message[:80]}…'")
                time.sleep(2)
                return True

        except NoSuchElementException:
            continue

    print("  ⚠ Could not find comment field or submit button.")
    return False


# ---------------------------------------------------------------------------
# Scraping helpers
# ---------------------------------------------------------------------------

def get_top_products(driver: webdriver.Chrome) -> list[str]:
    """Return URLs for all top-launching products listed today."""
    print("Fetching today's top products…")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "section[data-test^='post-item']")
            )
        )
        time.sleep(2)

        seen: set[str] = set()
        links: list[str] = []

        for section in driver.find_elements(
            By.CSS_SELECTOR, "section[data-test^='post-item']"
        ):
            try:
                href = section.find_element(
                    By.CSS_SELECTOR, "a[href*='/products/']"
                ).get_attribute("href")
                if href and href not in seen:
                    seen.add(href)
                    links.append(href)
            except NoSuchElementException:
                continue

        print(f"Found {len(links)} product(s).\n")
        return links

    except TimeoutException as exc:
        print(f"Timed out waiting for products: {exc}")
        return []


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def process_product(
    driver: webdriver.Chrome,
    client: boto3.client,
    url: str,
    index: int,
    total: int,
) -> None:
    """Navigate to a product, upvote it, generate a comment, and post it."""
    print(f"\n[{index}/{total}] {url}")
    driver.get(url)
    time.sleep(3)

    product_info = get_product_info(driver)
    upvote_product(driver)
    comment = generate_comment(client, product_info)
    post_comment(driver, comment)

    if index < total:
        delay = random.randint(*DELAY_BETWEEN_PRODUCTS)
        print(f"\n⏱  Waiting {delay}s before the next product…")
        time.sleep(delay)


def main() -> None:
    driver = None
    try:
        print("\n🚀 Product Hunt Automation — AWS Bedrock / Qwen")
        print("=" * 60)
        print(f"  Region  : {AWS_CONFIG['region_name']}")
        print(f"  Model   : {BEDROCK_MODEL_ID}")
        print("=" * 60)

        # Initialise AWS Bedrock client once; reuse for all products
        bedrock_client = create_bedrock_client()

        # Launch browser and log in
        driver = setup_driver()
        driver.get("https://www.producthunt.com")
        time.sleep(2)
        wait_for_manual_login(driver)

        # Return to home page to scrape products
        driver.get("https://www.producthunt.com")
        time.sleep(2)

        product_urls = get_top_products(driver)
        if not product_urls:
            print("⚠ No products found. Check the page structure and try again.")
            return

        print(f"🎯 Processing {len(product_urls)} product(s)…")
        print("=" * 60)

        for idx, url in enumerate(product_urls, start=1):
            process_product(driver, bedrock_client, url, idx, len(product_urls))

        print("\n" + "=" * 60)
        print("✅ Automation complete!")
        print("=" * 60)
        time.sleep(10)

    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user.")

    except Exception as exc:
        print(f"\n✗ Unexpected error: {exc}")

    finally:
        if driver:
            print("\nClosing browser…")
            driver.quit()
            print("Done.")


if __name__ == "__main__":
    main()