# Surfer-H CLI Architectural Overview

This document provides a high-level overview of the Surfer-H CLI agent's architecture. The agent is designed to navigate the web to complete tasks, using a combination of AI models for decision-making and browser automation for execution.

## Core Components

The agent's logic is primarily located in the `src/surfer_h_cli` directory. Here's a breakdown of the key components:

-   **`surferh.py` (Main Loop & Orchestrator):** This is the main entry point of the application. It contains the `agent_loop` function, which orchestrates the entire process. The loop initializes the agent's state, continuously calls the navigation model, executes the returned action, and updates the agent's state. It also handles the maximum number of steps and timeout settings.

-   **`simple_browser.py` (Browser Interaction):** This file provides a `SimpleWebBrowserTools` class that wraps a Selenium WebDriver. It offers a simplified interface for performing web browser actions like clicking, typing, scrolling, and taking screenshots. Navigation methods dynamically wait for the page to be fully loaded before proceeding to prevent errors from interacting with a partially-rendered page.

-   **`skills/navigation_step.py` (Navigation Model):** This component is the "brain" of the agent. The `navigation_step` function constructs a prompt with the current task, the current URL, previous actions, notes, and recent screenshots. It then sends this information to a multimodal LLM (the "navigator model") to decide the next action.

-   **`skills/localization.py` (Element Localization):** When the navigation model decides to click or type on an element, it only provides a text description of the element. The `localize_element` function takes this description and the current screenshot and uses another AI model (the "localizer model") to find the precise (x, y) coordinates of the element on the page.

-   **`skills/navigation_models.py` (Action Definitions):** This file defines the set of possible actions the agent can take, such as `click_element`, `write_element`, `scroll`, and `answer`. These are defined using Pydantic models, which ensures that the output from the navigation model is well-structured.

-   **`skills/validation.py` (Answer Validation):** When the agent believes it has completed the task, it outputs an `answer` action. The `validate_web_voyager_answer` function can then be used to have another AI model (the "validator model") review the final answer and screenshots to determine if the task was actually successful.
