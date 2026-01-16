import ollama

from score_ import text


def image_verification(image_path):
    response = ollama.chat(
        model="qwen3-vl:4b",
        messages=[
            {
                "role": "user",
                "content": f"What is happening in this image? give a priority score and little overview in a line",
                "images": [f"{image_path}"],
            }
        ],
    )


# print(response["message"]["content"])
