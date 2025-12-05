
"""
Canvas Login Test Case Implementation
Tests the Canvas account connection flow in VT Calendar application.

Test Case: Canvas Login Check
Preconditions: None
Steps:
1. Navigate to the calendar login page
2. Click connect Canvas button  
3. Enter Canvas details
4. Click login
Expected Result: Success message appears verifying account connection was successful
AI use:
Claude Sonnet was used to better understand the requirements and set up the test case structure using the following prompt:
Implement a skeleton for the following testcase:
Canvas Login Check
Preconditions:
None
Steps:
1. Navigate to the calendar login page
2. Click connect Canvas button
3. Enter Canvas details
4. Click login
Expected result - Success message appears verifying account connection was successful.

Explain what information is relevant to determine pass or failure. Where do you get that information from? How do you get it?
"""

import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time


class CanvasLoginTest(unittest.TestCase):
    """Test case for Canvas account connection"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        # Initialize Chrome driver (you can use other browsers)
        cls.driver = webdriver.Chrome()
        cls.driver.maximize_window()
        cls.base_url = "http://127.0.0.1:3001"
        cls.wait = WebDriverWait(cls.driver, 10)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        cls.driver.quit()
    
    def test_canvas_login_success(self):
        
        print("\n=== Starting Canvas Login Test ===\n")
        
        # Step 1: Navigate to the calendar login page
        print("Step 1: Navigate to login page")
        self.driver.get(f"{self.base_url}/auth.html")
        
        # Verify page loaded correctly
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.assertIn("VT Calendar", self.driver.title)
        print("✓ Login page loaded successfully")
        
        # First, register/login to get to dashboard
        print("\nStep 1a: Register/Login to VT Calendar")
        self._perform_login()
        
        # Step 2: Click connect Canvas button (or navigate to link section)
        print("\nStep 2: Click 'Link Canvas' button")
        try:
            link_canvas_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "linkCanvasBtn"))
            )
            link_canvas_btn.click()
            print("✓ Link Canvas button clicked")
        except TimeoutException:
            # Might already be on link section or dashboard
            print("⚠ Link Canvas button not found, checking current state...")
        
        # Step 3: Enter Canvas details (API token)
        print("\nStep 3: Enter Canvas API token")
        
        # Wait for Canvas token input field
        canvas_token_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "canvasToken"))
        )
        
        # Get test Canvas token from environment or use test token
        # In real test, you'd use a valid Canvas API token
        test_canvas_token = "test_canvas_token_12345"  # Replace with valid token
        
        canvas_token_input.clear()
        canvas_token_input.send_keys(test_canvas_token)
        print(f"✓ Canvas token entered: {test_canvas_token[:10]}...")
        
        # Step 4: Click login (submit Canvas link form)
        print("\nStep 4: Submit Canvas connection form")
        
        link_canvas_submit = self.driver.find_element(
            By.CSS_SELECTOR, "#linkCanvasForm button[type='submit']"
        )
        link_canvas_submit.click()
        print("✓ Canvas link form submitted")
        
        # Expected Result: Verify success message appears
        print("\n=== Verifying Expected Results ===\n")
        
        # CRITICAL: Check for success notification
        success_message = self._check_for_success_notification()
        
        if success_message:
            print(f"✓ SUCCESS: {success_message}")
            
            # Additional verification: Check Canvas connection status
            self._verify_canvas_connection_status()
            
            # Log final test result
            print("\n" + "="*50)
            print("TEST RESULT: PASS ✓")
            print("Canvas account connection successful")
            print("="*50 + "\n")
            
        else:
            # Check for error message
            error_message = self._check_for_error_notification()
            
            print("\n" + "="*50)
            print("TEST RESULT: FAIL ✗")
            if error_message:
                print(f"Error message appeared: {error_message}")
            else:
                print("No success or error message appeared within timeout")
            print("="*50 + "\n")
            
            self.fail("Canvas login test failed - success message not found")
    
    def _perform_login(self):
        """Helper method to login/register before Canvas connection"""
        try:
            # Check if already logged in
            dashboard = self.driver.find_element(By.ID, "dashboardSection")
            if dashboard.is_displayed():
                print("✓ Already logged in")
                return
        except:
            pass
        
        # Switch to register tab
        register_tab = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".tab-btn[data-tab='register']"))
        )
        register_tab.click()
        time.sleep(0.5)
        
        # Fill registration form
        test_email = f"test{int(time.time())}@vt.edu"
        test_password = "TestPass123"
        
        email_input = self.driver.find_element(By.ID, "registerEmail")
        password_input = self.driver.find_element(By.ID, "registerPassword")
        
        email_input.send_keys(test_email)
        password_input.send_keys(test_password)
        
        # Submit registration
        register_btn = self.driver.find_element(
            By.CSS_SELECTOR, "#registerFormContent button[type='submit']"
        )
        register_btn.click()
        
        time.sleep(1)
        
        # Now login with same credentials
        login_tab = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".tab-btn[data-tab='login']"))
        )
        login_tab.click()
        time.sleep(0.5)
        
        login_email = self.driver.find_element(By.ID, "loginEmail")
        login_password = self.driver.find_element(By.ID, "loginPassword")
        
        login_email.send_keys(test_email)
        login_password.send_keys(test_password)
        
        login_btn = self.driver.find_element(
            By.CSS_SELECTOR, "#loginFormContent button[type='submit']"
        )
        login_btn.click()
        
        # Wait for dashboard to appear
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "dashboardSection"))
        )
        print("✓ Logged in successfully")
    
    def _check_for_success_notification(self):
        
        try:
            # Wait for notification to appear (max 10 seconds)
            notification = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "notification"))
            )
            
            # Get notification text
            message_text = notification.text
            
            # Check if it's a success notification
            notification_classes = notification.get_attribute("class")
            is_success = "success" in notification_classes
            
            # Verify message contains Canvas-related success keywords
            success_keywords = ["linked", "canvas", "course", "success"]
            contains_keywords = any(
                keyword in message_text.lower() 
                for keyword in success_keywords
            )
            
            if is_success and contains_keywords:
                return message_text
            
            return None
            
        except TimeoutException:
            print("✗ No notification appeared within timeout period")
            return None
    
    def _check_for_error_notification(self):
        """Check if error notification appeared instead"""
        try:
            notification = self.driver.find_element(By.CLASS_NAME, "notification")
            notification_classes = notification.get_attribute("class")
            
            if "error" in notification_classes:
                return notification.text
            
        except:
            pass
        
        return None
    
    def _verify_canvas_connection_status(self):
        
        try:
            # Wait for dashboard to be visible
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "dashboardSection"))
            )
            
            # Find Canvas status element
            canvas_status = self.driver.find_element(By.ID, "canvasStatus")
            status_text = canvas_status.text
            
            # Verify it shows connected
            if "Connected" in status_text or "✓" in status_text:
                print("✓ Canvas status updated to 'Connected'")
                
                # Optional: Verify icon color
                status_icon = canvas_status.find_element(By.CLASS_NAME, "status-icon")
                icon_color = status_icon.value_of_css_property("color")
                print(f"  Status icon color: {icon_color}")
                
                return True
            else:
                print(f"✗ Canvas status not updated correctly: {status_text}")
                return False
                
        except Exception as e:
            print(f"✗ Could not verify Canvas status: {str(e)}")
            return False


def run_test_with_detailed_reporting():
    
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(CanvasLoginTest)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST EXECUTION SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run test with detailed reporting
    success = run_test_with_detailed_reporting()
    
    # Exit with appropriate code
    exit(0 if success else 1)