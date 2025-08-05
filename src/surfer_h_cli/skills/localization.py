import base64
import io
import re

import openai
from PIL import Image

from surfer_h_cli.utils import smart_resize

LOCALIZATION_PROMPT: str = "Localize an element on the GUI image according to my instructions and return `NOT_FOUND`\n{component}"


def localization_request(
    image: Image.Image, element_name: str, model: str, temperature: float = 0.0
) -> dict:
    """Creates a localization prompt to send to an openai-compatible LLM."""

    # create prompt text
    localization_prompt = LOCALIZATION_PROMPT.format(component=element_name)

    # convert image to JPEG saved as base64
    width, height = image.size
    new_height, new_width = smart_resize(
        height,
        width,
        factor=14 * 2,  # patch size * patch merge
        min_pixels=4 * 28 * 28,  # n_token * patch size * patch size
        max_pixels=1280 * 28 * 28,  # n_pixel * patch size * patch size
    )
    image = image.resize(
        (new_width, new_height), resample=Image.Resampling.LANCZOS
    ).convert("RGB")
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="JPEG", quality=90)
    image_base64 = base64.b64encode(image_bytes.getvalue()).decode("utf-8")
    # create openai request
    openai_request = {
        "messages": [
            {
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "detail": "auto",
                            "url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    },
                    {"type": "text", "text": localization_prompt},
                ],
                "role": "user",
            }
        ],
        "model": model,
        "temperature": temperature,
    }
    return openai_request


def parse_localization_response(
    completion: openai.types.chat.ChatCompletion, image: Image.Image | None = None
) -> tuple[int, int]:
    if image is not None:
        width, height = image.size
        new_height, new_width = smart_resize(
            height,
            width,
            factor=14 * 2,  # patch size * patch merge
            min_pixels=4 * 28 * 28,  # n_token * patch size * patch size
            max_pixels=1280 * 28 * 28,  # n_pixel * patch size * patch size
        )
    else:
        width, height, new_width, new_height = 1.0, 1.0, 1.0, 1.0

    response = completion.choices[0].message.content
    match = re.search(
        r".*?(?<!\d)(\d+(?:\.\d+)?)(?!\d).*?(?<!\d)(\d+(?:\.\d+)?)(?!\d)", response
    )
    if match is None:
        raise ValueError("Coordinates not found in completion content")
    x = float(match.group(1))
    y = float(match.group(2))
    normalized_x, normalized_y = x / new_width, y / new_height
    if (
        normalized_x > 1.0
        or normalized_y > 1.0
        or normalized_x < 0.0
        or normalized_y < 0.0
    ):
        # put the click in the image
        normalized_x, normalized_y = 0.25, 0.25
    resized_x, resized_y = int(normalized_x * width), int(normalized_y * height)
    return (resized_x, resized_y)


def localize_element(
    image: Image.Image,
    element_name: str,
    openai_client: openai.OpenAI,
    model: str,
    temperature: float = 0.0,
) -> tuple[float, float]:
    prompt = localization_request(
        image=image, element_name=element_name, model=model, temperature=temperature
    )
    response = openai_client.chat.completions.create(**prompt)
    return parse_localization_response(response, image)
