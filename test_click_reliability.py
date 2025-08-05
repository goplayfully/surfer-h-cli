import os
import time
from pathlib import Path

from PIL import Image, ImageDraw
from src.surfer_h_cli.simple_browser import SimpleWebBrowserTools
from src.surfer_h_cli.skills.localization import localize_element
from src.surfer_h_cli.surferh import get_env_or_cli, parse_args, setup_client


def draw_circle_on_image(
    image: Image.Image, x: int, y: int, radius: int = 20, color: str = "red"
) -> Image.Image:
    """Draw a circle on the image at the specified coordinates."""
    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius), outline=color, width=3
    )
    return image


def run_test():
    """Run the click reliability test."""
    cli_args = parse_args()
    browser = SimpleWebBrowserTools()
    browser.open_browser(
        headless=cli_args.headless_browser,
        width=cli_args.browser_width,
        height=cli_args.browser_height,
        action_timeout=cli_args.action_timeout,
    )

    # Set up only the localization client, as it's the only one needed for this test.
    openai_api_key = get_env_or_cli("OPENAI_API_KEY", cli_args.openai_api_key)
    model_name_localization = get_env_or_cli(
        "MODEL_NAME_LOCALIZATION", cli_args.model_name_localization, "HCompany/Holo1-7B"
    )
    base_url_localization = get_env_or_cli(
        "BASE_URL_LOCALIZATION", cli_args.base_url_localization
    )
    api_key_localization = get_env_or_cli(
        "API_KEY_LOCALIZATION", cli_args.api_key_localization
    )

    assert model_name_localization is not None, "Localization model name not set."
    print(f"Localization Model Name: {model_name_localization}")
    assert base_url_localization is not None, (
        "Localization base URL not set. Please set BASE_URL_LOCALIZATION env var or --base_url_localization arg."
    )
    print(f"Localization Model URL: {base_url_localization}")

    openai_client_localization = setup_client(
        name="localization",
        base_url=base_url_localization,
        openai_api_key=openai_api_key,
        custom_api_key=api_key_localization or "EMPTY",
    )

    test_page_path = (
        Path(__file__).parent / "debug" / "www.soundroom.org" / "events.html"
    )
    browser.goto(f"file://{test_page_path.resolve()}")

    time.sleep(2)

    elements_to_test = ["Click on the 'Tickets at Camille Kerani Group' link"]
    # elements_to_test = ["Camille Kerani Group"]
    max_scrolls = 5

    for i, element_name in enumerate(elements_to_test):
        print(f"--- Testing '{element_name}' ---")
        found_element = False
        for scroll_attempt in range(max_scrolls):
            # 1. Take a screenshot in the current view
            screenshot = browser.screenshot()
            before_path = f"debug/test_{scroll_attempt}_before.png"
            screenshot.save(before_path)

            # 2. Try to localize the element
            try:
                x, y = localize_element(
                    image=screenshot,
                    element_name=element_name,
                    openai_client=openai_client_localization,
                    model=model_name_localization,
                    temperature=0.0,
                )
                print(
                    f"Localized '{element_name}' at ({x}, {y}) on scroll attempt {scroll_attempt + 1}"
                )

                # 3. Visualize the click
                annotated_image = draw_circle_on_image(screenshot.copy(), x, y)
                annotated_image_path = (
                    f"debug/test_{i}_annotated_scroll_{scroll_attempt}.png"
                )
                annotated_image.save(annotated_image_path)
                print(f"Saved annotated screenshot to {annotated_image_path}")

                # 4. Execute the click
                browser.click_at(x, y)
                print("Executed click.")
                time.sleep(1)

                # 5. Save "after" screenshot to verify click
                after_screenshot = browser.screenshot()
                after_screenshot_path = f"debug/test_{i}_after_click.png"
                after_screenshot.save(after_screenshot_path)
                print(f"Saved 'after' screenshot to {after_screenshot_path}")

                found_element = True
                break  # Exit the scroll loop since we found and clicked the element

            except ValueError as e:
                print(
                    f"Could not find '{element_name}' in current view. {e} Scrolling down..."
                )
                browser.scroll("down")
                time.sleep(1)  # Wait for scroll to settle

        if not found_element:
            print(f"Could not find '{element_name}' after {max_scrolls} scrolls.")

        print("-" * (len(element_name) + 14))

    browser.quit()
    print("Test complete. Check the 'debug' directory for results.")


if __name__ == "__main__":
    run_test()
