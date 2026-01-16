import ollama

response = ollama.chat(
    model="qwen3-vl:4b",
    messages=[
        {
            "role": "user",
            "content": "What is happening in this image?, give priorty score and matter of urgency",
            "images": [""".\\images\\jk.png"""],
        }
    ],
)

print(response["message"]["content"])
