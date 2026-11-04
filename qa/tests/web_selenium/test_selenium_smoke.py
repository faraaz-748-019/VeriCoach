"""Cross-browser Selenium smoke test suite for VeriCoach web application.

Executed across Chrome and Firefox in headless CI mode.
Strictly uses explicit waits (WebDriverWait) and zero sleep() calls.
"""

from __future__ import annotations

import allure
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

TIMEOUT = 15.0


@pytest.mark.smoke
@pytest.mark.web
@allure.feature("Selenium Web Smoke")
@allure.story("Initial Application Load and Structural Integrity")
def test_smoke_page_load_and_elements(
    driver: webdriver.Remote, web_server_url: str
) -> None:
    """Verify primary layout components load properly across browsers."""
    wait = WebDriverWait(driver, TIMEOUT)

    with allure.step(f"Navigate to {web_server_url}"):
        driver.get(web_server_url)

    with allure.step("Wait explicitly for main chat window container"):
        chat_window = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='chat-window']")
            )
        )
        assert chat_window.is_displayed()

    with allure.step("Wait explicitly for header banner and title"):
        app_header = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='app-header']")
            )
        )
        assert app_header.is_displayed()
        assert "VeriCoach" in driver.title

    with allure.step("Wait explicitly for chat input field to be interactive"):
        chat_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='chat-input']"))
        )
        assert chat_input.is_enabled()


@pytest.mark.smoke
@pytest.mark.web
@allure.feature("Selenium Web Smoke")
@allure.story("Multilingual Language Switching")
def test_smoke_multilingual_language_switch(
    driver: webdriver.Remote, web_server_url: str
) -> None:
    """Verify switching language dropdown dynamically updates UI localization."""
    wait = WebDriverWait(driver, TIMEOUT)

    with allure.step(f"Navigate to {web_server_url}"):
        driver.get(web_server_url)

    with allure.step("Wait explicitly for language selector dropdown"):
        select_elem = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='language-select']")
            )
        )
        lang_select = Select(select_elem)

    with allure.step("Switch language to Hindi (hi)"):
        lang_select.select_by_value("hi")
        # Explicit wait for input placeholder to transition to Hindi
        wait.until(
            lambda d: "पूछें"
            in (
                d.find_element(
                    By.CSS_SELECTOR, "[data-testid='chat-input']"
                ).get_attribute("placeholder")
                or ""
            )
            or "प्रश्न"
            in (
                d.find_element(
                    By.CSS_SELECTOR, "[data-testid='chat-input']"
                ).get_attribute("placeholder")
                or ""
            )
        )

    with allure.step("Switch language to Telugu (te)"):
        select_elem = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='language-select']")
            )
        )
        lang_select = Select(select_elem)
        lang_select.select_by_value("te")
        # Explicit wait for input placeholder to transition to Telugu
        wait.until(
            lambda d: "అడగండి"
            in (
                d.find_element(
                    By.CSS_SELECTOR, "[data-testid='chat-input']"
                ).get_attribute("placeholder")
                or ""
            )
            or "ప్రశ్నను"
            in (
                d.find_element(
                    By.CSS_SELECTOR, "[data-testid='chat-input']"
                ).get_attribute("placeholder")
                or ""
            )
        )


@pytest.mark.smoke
@pytest.mark.web
@allure.feature("Selenium Web Smoke")
@allure.story("Chat Message Dispatch and Receipt")
def test_smoke_send_chat_message(driver: webdriver.Remote, web_server_url: str) -> None:
    """Verify inputting query dispatches request and renders assistant response."""
    wait = WebDriverWait(driver, TIMEOUT)

    with allure.step(f"Navigate to {web_server_url}"):
        driver.get(web_server_url)

    with allure.step("Input financial query"):
        chat_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='chat-input']"))
        )
        chat_input.clear()
        chat_input.send_keys("What is the difference between debt and equity funds?")

    with allure.step("Click submit button explicitly when enabled"):
        send_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='send-button']"))
        )
        send_btn.click()

    with allure.step("Explicitly wait for assistant response element"):
        assistant_msg = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='message-assistant']")
            )
        )
        assert assistant_msg.is_displayed()
        assert len(assistant_msg.text.strip()) > 0


@pytest.mark.smoke
@pytest.mark.web
@allure.feature("Selenium Web Smoke")
@allure.story("Citations Disclosure Toggle")
def test_smoke_citations_disclosure(
    driver: webdriver.Remote, web_server_url: str
) -> None:
    """Verify citations toggle disclosures and panel visibility."""
    wait = WebDriverWait(driver, TIMEOUT)

    with allure.step(f"Navigate to {web_server_url}"):
        driver.get(web_server_url)

    with allure.step("Send query mapped to indexed financial corpus"):
        chat_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='chat-input']"))
        )
        chat_input.clear()
        chat_input.send_keys("Explain tax savings under Section 80C.")

        send_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='send-button']"))
        )
        send_btn.click()

    with allure.step("Explicitly wait for assistant response to render"):
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='message-assistant']")
            )
        )

    with allure.step("Explicitly check for citations disclosure toggle"):
        # Locate toggle button if citations were retrieved
        toggles = driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='citations-toggle']"
        )
        if toggles:
            toggle_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-testid='citations-toggle']")
                )
            )
            toggle_btn.click()

            citations_panel = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "[data-testid='citations-panel']")
                )
            )
            assert citations_panel.is_displayed()
        else:
            # If mock assistant returned response without sources, verify message structure is valid
            assistant_elem = driver.find_element(
                By.CSS_SELECTOR, "[data-testid='message-assistant']"
            )
            assert assistant_elem.is_displayed()


@pytest.mark.smoke
@pytest.mark.web
@allure.feature("Selenium Web Smoke")
@allure.story("Feedback Submission Interaction")
def test_smoke_feedback_submission(
    driver: webdriver.Remote, web_server_url: str
) -> None:
    """Verify feedback rating interaction using explicit waits."""
    wait = WebDriverWait(driver, TIMEOUT)

    with allure.step(f"Navigate to {web_server_url}"):
        driver.get(web_server_url)

    with allure.step(
        "Send financial question to populate assistant response with feedback buttons"
    ):
        chat_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='chat-input']"))
        )
        chat_input.clear()
        chat_input.send_keys("How do liquid funds work?")

        send_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='send-button']"))
        )
        send_btn.click()

    with allure.step("Explicitly wait for assistant response and feedback button"):
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='message-assistant']")
            )
        )

    with allure.step("Click thumbs up button explicitly"):
        thumbs_up = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-testid='feedback-thumbs-up']")
            )
        )
        thumbs_up.click()

    with allure.step("Explicitly wait for feedback status confirmation to appear"):
        status_elem = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='feedback-status']")
            )
        )
        assert status_elem.is_displayed()
        assert len(status_elem.text.strip()) > 0
