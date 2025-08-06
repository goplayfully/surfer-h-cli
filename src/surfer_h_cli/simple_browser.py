from io import BytesIO

from PIL import Image
from pydantic import BaseModel
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def chrome_viewport_size(driver: Chrome) -> tuple[int, int]:
    """Get viewport size of chrome browser"""

    return tuple(
        driver.execute_script("return [window.innerWidth, window.innerHeight];")
    )


def resize_chrome(driver: Chrome, width: int, height: int):
    """Resize a selenium chromedriver window."""
    current_width, current_height = chrome_viewport_size(driver)
    if width != current_width or height != current_height:
        driver.set_window_size(width, height)
        current_width, current_height = chrome_viewport_size(driver)
        driver.set_window_size(
            width + width - current_width, height + height - current_height
        )


class page_is_loaded:
    """An expectation for checking that the page is fully loaded."""

    def __call__(self, driver):
        state = driver.execute_script("return document.readyState")
        print(f"document.readyState is '{state}'")
        return state == "complete"




class Tab:
    """Tab object."""

    def __init__(self, index: str) -> None:
        """Build a tab with an index."""
        self.index = index


class WebTabs(BaseModel):
    titles: list[str]


class WebException(Exception):
    """Custom exception for web-related errors"""

    pass


class SimpleWebBrowserTools:
    """Selenium-based web environment for executing web actions"""

    def __init__(self):
        """
        Initialize the Selenium web environment

        Args:
            headless: Whether to run browser in headless mode
            wait_timeout: Default timeout for waiting operations
        """

    def open_browser(
        self, headless: bool, width: int, height: int, action_timeout: int, **kwargs
    ):
        """Setup the Selenium WebDriver"""
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(f"--window-size={width},{height}")
        options.add_argument("--force-device-scale-factor=1")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")

        try:
            self.driver = Chrome(options=options)
            self.wait = WebDriverWait(self.driver, action_timeout)
            self.headless = headless
            self.width = width
            self.height = height
            self.action_timeout = action_timeout

            resize_chrome(self.driver, self.width, self.height)

        except Exception as e:
            raise WebException(f"Failed to initialize WebDriver: {e}")

    def get_screenshot_size(self) -> tuple[int, int]:
        """Get the size of the current screenshot/viewport"""
        assert self.driver

        size = self.driver.get_window_size()
        return size["width"], size["height"]

    def get_tab_url(self) -> str:
        return self.driver.current_url

    def get_tabs(self) -> list[Tab]:
        """Return description of the tabs   opened with the current tab being focused."""
        return [Tab(index=handle) for handle in self.driver.window_handles]

    def get_tabs_titles(self) -> WebTabs:
        return WebTabs(titles=self.driver.window_handles)

    @staticmethod
    def find_newer_tab(previous_tabs: list[Tab], new_tabs: list[Tab]) -> Tab:
        """Find one newer tab from the previous tabs"""
        assert len(new_tabs) > len(previous_tabs)
        previous_indexes = [tab.index for tab in previous_tabs]
        for tab in new_tabs[-1::-1]:
            if tab.index not in previous_indexes:
                return tab
        raise WebException("No newer tab found")

    def click_at(self, x: int, y: int):
        """Click at specific coordinates"""
        assert self.driver
        actions = ActionChains(self.driver)
        actions.move_by_offset(x, y).click().perform()
        actions.reset_actions()

    def write(self, text: str, n_backspaces: int = 0):
        """Write text, optionally clearing with backspaces first"""
        assert self.driver
        active_element = self.driver.switch_to.active_element
        if active_element is None:
            return
        if n_backspaces > 0:
            active_element.send_keys(Keys.BACKSPACE * n_backspaces)

        active_element.send_keys(text)

    def scroll(self, direction: str):
        """Scroll the page in the specified direction"""

        assert self.driver
        body = self.driver.find_element(By.TAG_NAME, "body")
        if direction == "down":
            body.send_keys(Keys.PAGE_DOWN)
        elif direction == "up":
            body.send_keys(Keys.PAGE_UP)
        elif direction == "left":
            body.send_keys(Keys.ARROW_LEFT)
        elif direction == "right":
            body.send_keys(Keys.ARROW_RIGHT)
        else:
            raise WebException(f"Invalid scroll direction: {direction}")

    def goback(self):
        """Navigate back to previous page"""
        assert self.driver
        self.driver.back()
        self.wait.until(page_is_loaded())

    def goto(self, url: str):
        """Navigate to a specific URL"""
        assert self.driver
        self.driver.get(url)
        self.wait.until(page_is_loaded())

    def change_tab(self, title: str):
        """Switch to tab with specific title"""
        assert self.driver

        try:
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if self.driver.title == title:
                    return

        except Exception as e:
            raise WebException(f"Failed to change tab: {e}")

    def focus_tab(self, element: str):
        """Focus on a tab (using element as identifier)"""
        self.change_tab(element)

    def quit(self):
        """Quit the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None

    def refresh(self):
        """Refresh the current page"""
        assert self.driver
        self.driver.refresh()
        self.wait.until(page_is_loaded())

    def restart(self):
        """Restart the browser"""
        self.quit()
        if not hasattr(self, "headless"):
            raise ValueError("Browser not initialized")
        self.open_browser(
            headless=self.headless,
            width=self.width,
            height=self.height,
            action_timeout=self.action_timeout,
        )

    def screenshot(self) -> Image.Image:
        assert self.driver
        screenshot = self.driver.get_screenshot_as_png()

        bytestream = BytesIO(screenshot)
        bytestream.seek(0)
        return Image.open(bytestream)

    def get_webpage(self) -> tuple[str, Image.Image]:
        assert self.driver is not None
        url = self.get_tab_url()
        screenshot = self.screenshot()
        return url, screenshot
