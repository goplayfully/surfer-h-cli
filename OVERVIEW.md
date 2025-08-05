# Surfer-H CLI Architectural Overview

This document provides a high-level overview of the Surfer-H CLI agent's architecture. The agent is designed to navigate the web to complete tasks, using a combination of AI models for decision-making and browser automation for execution.

## Core Components

The agent's logic is primarily located in the `src/surfer_h_cli` directory. Here's a breakdown of the key components:

- **`surferh.py` (Main Loop & Orchestrator):** This is the main entry point of the application. It contains the `agent_loop` function, which orchestrates the entire process. The loop continuously calls the navigation model, executes the returned action, and updates the agent's state. It also handles the maximum number of steps and timeout settings.

- **`simple_browser.py` (Browser Interaction):** This file provides a `SimpleWebBrowserTools` class that wraps a Selenium WebDriver. It offers a simplified interface for performing web browser actions like clicking, typing, scrolling, and taking screenshots.

- **`skills/navigation_step.py` (Navigation Model):** This component is the "brain" of the agent. The `navigation_step` function constructs a prompt with the current task, previous actions, notes, and recent screenshots. It then sends this information to a multimodal LLM (the "navigator model") to decide the next action.

- **`skills/localization.py` (Element Localization):** When the navigation model decides to click or type on an element, it only provides a text description of the element. The `localize_element` function takes this description and the current screenshot and uses another AI model (the "localizer model") to find the precise (x, y) coordinates of the element on the page.

- **`skills/navigation_models.py` (Action Definitions):** This file defines the set of possible actions the agent can take, such as `click_element`, `write_element`, `scroll`, and `answer`. These are defined using Pydantic models, which ensures that the output from the navigation model is well-structured.

- **`skills/validation.py` (Answer Validation):** When the agent believes it has completed the task, it outputs an `answer` action. The `validate_web_voyager_answer` function can then be used to have another AI model (the "validator model") review the final answer and screenshots to determine if the task was actually successful.

## Answering Your Questions

### a) Why is the model looping after an `answer` action?

The main control flow is in the `agent_loop` function in `surferh.py`. When the `navigation_step` function returns an action, the loop checks if the action is `answer`.

If `use_validator` is `False`, the loop will terminate and return the answer as soon as it receives an `answer` action.

If `use_validator` is `True`, the loop calls the `validate_answer` function. If the validation is successful (`validator_response.success` is `True`), the loop terminates. However, if the validation *fails*, the loop continues to the next iteration. The agent's notes are updated with the validation failure reason, which should guide it to correct its mistake.

**To diagnose looping, check the output of the validation model in the console. It will print "Validation passed" or the reason for failure.** If the validator is being too strict or the navigation model isn't correctly interpreting the feedback, it could lead to a loop.

### b) Why are there so many steps after the task seems done?

This is likely related to the validation process described above. If the agent outputs an `answer` but the validator deems it incorrect or incomplete, the agent will continue trying to complete the task. Each attempt is another "step" in the trajectory.

**Look for the validation feedback in the agent's logs (`"***** Validation passed *****"` or the failure reason).** This will tell you why the agent is continuing to run. You may need to adjust the validation prompt in `skills/validation.py` or the navigation prompt in `skills/navigation_step.py` to improve the agent's performance.

### c) How can I create a new `grep` tool?

Adding a new tool requires a few steps:

1.  **Define the new action:** In `src/surfer_h_cli/skills/navigation_models.py`, create a new Pydantic class for your `grep` action, similar to `ScrollAction` or `GoBackAction`. It should inherit from `BaseAction`.

    ```python
    class GrepAction(BaseAction):
        """Search for a pattern in the current page's text."""
        action: Literal["grep"] = "grep"
        pattern: str
        """The regex pattern to search for."""
    ```

2.  **Add the action to the union type:** Add your new `GrepAction` to the `WebAgentNavigateAction` union type in the same file.

    ```python
    WebAgentNavigateAction = (
        AbsClickElementAction
        | AbsWriteElementAction
        | ScrollAction
        | GoBackAction
        | RefreshAction
        | WaitAction
        | RestartAction
        | AnswerAction
        | GrepAction  # <--- Add your action here
    )
    ```

3.  **Implement the tool's logic:** In `surferh.py`, you'll need to get the page source from Selenium and search for the pattern. You would add a new case to the `execute_navigation_action` function:

    ```python
    def execute_navigation_action(navigation_action: dict, browser: SimpleWebBrowserTools, refresh_url: str):
        action = navigation_action["action"]

        # ... other actions
        elif action == "grep":
            page_source = browser.driver.page_source
            # You'll need to decide how to store and use the results.
            # For example, you could add them to the agent's notes.
            # This part is left as an exercise for the reader.
            pass
        # ... other actions
    ```
    *Note: You would also need to decide how to feed the results of the grep back into the agent's state, likely by updating the `notes` in the `AgentState`.*

4.  **Update the navigation prompt:** Finally, you need to tell the navigation model that it has a new tool. In `src/surfer_h_cli/skills/navigation_step.py`, add a description of your `grep` tool to the `NAVIGATION_PROMPT` string. This will allow the model to learn when to use it.
