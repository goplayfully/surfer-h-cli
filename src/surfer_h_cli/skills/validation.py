import json

import openai

from surfer_h_cli.skills.validation_models import WebRetrievalEvaluation

SYSTEM_PROMPT = """As an evaluator, you will be presented with three primary components to assist you in your role:

1. Web Task Instruction: This is a clear and specific directive provided in natural language, detailing the online activity to be carried out. These requirements may include conducting searches, verifying information, comparing prices, checking availability, or any other action relevant to the specified web service (such as Amazon, Apple, ArXiv, BBC News, Booking etc).

2. Result Screenshots: This is a visual representation of the screen showing the result or intermediate state of performing a web task. It serves as visual proof of the actions taken in response to the instruction.

3. Result Response: This is a textual response obtained after the execution of the web task. It serves as textual result in response to the instruction.

-- You DO NOT NEED to interact with web pages or perform actions such as booking flights or conducting searches on websites.
-- You SHOULD NOT make assumptions based on information not presented in the screenshot when comparing it to the instructions.
-- Your primary responsibility is to conduct a thorough assessment of the web task instruction against the outcome depicted in the screenshot and in the response, evaluating whether the actions taken align with the given instructions.
-- NOTE that the instruction may involve more than one task, for example, locating the garage and summarizing the review. Failing to complete either task, such as not providing a summary, should be considered unsuccessful.
-- NOTE that the screenshot is authentic, but the response provided by LLM is generated at the end of web browsing, and there may be discrepancies between the text and the screenshots.
-- Note the difference: 1) Result response may contradict the screenshot, then the content of the screenshot prevails, 2) The content in the Result response is not mentioned on the screenshot, choose to believe the content


You should elaborate on how you arrived at your final evaluation and then provide a definitive verdict on whether the task has been successfully accomplished, either as 'SUCCESS' or 'NOT SUCCESS'."""


USER_PROMPT = """TASK: {task}
Result Response: {answer}
{num} screenshots at the end: """


def build_validation_messages(
    task: str, answer: str, screenshots: list[str]
) -> list[dict]:
    """Build messages compatible with OpenAI API format"""
    user_content: list[dict] = [
        {
            "type": "text",
            "text": USER_PROMPT.format(task=task, answer=answer, num=len(screenshots)),
        }
    ]

    for image_b64 in screenshots:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "detail": "auto",
                    "url": f"data:image/png;base64,{image_b64}",
                },
            }
        )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_validation_request(task: str, answer: str, screenshots: list[str]) -> dict:
    request: dict = {"messages": build_validation_messages(task, answer, screenshots)}
    return request


def validate_web_voyager_answer(
    task: str,
    answer: str,
    screenshots: list[str],
    is_answer: bool,
    openai_client: openai.OpenAI,
    openai_args: dict,
) -> WebRetrievalEvaluation:
    metrics = WebRetrievalEvaluation(task=task, screenshots=screenshots, answer=answer)

    if not is_answer:
        metrics.success = False
        metrics.why = "No answer"
        return metrics

    if len(screenshots) == 0:
        metrics.success = False
        metrics.why = "No screenshots"
        return metrics

    try:
        request = build_validation_request(task, answer, screenshots)
        request.update(openai_args)
        response = openai_client.chat.completions.create(**request)
        content = response.choices[0].message.content

        if not content:
            raise Exception("Problem with the LLM")

        try:
            data = json.loads(content)
            if isinstance(data, dict) and "success" in data:
                success = bool(data["success"])
            else:
                # Fallback to string search (original code) if JSON is not in the expected format
                success = "SUCCESS" in content and "NOT SUCCESS" not in content
        except (json.JSONDecodeError, TypeError):
            # If it's not JSON, use the original string search logic
            success = "SUCCESS" in content and "NOT SUCCESS" not in content

        metrics.success = success
        metrics.why = content
        return metrics

    except Exception as e:
        return WebRetrievalEvaluation(
            task=task, success=False, why="Problem during evaluation: " + str(e)
        )
