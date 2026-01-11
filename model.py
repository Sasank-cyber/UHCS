import numpy as np
from scipy.special import softmax
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TFAutoModelForSequenceClassification,
)
from transformers import pipeline

# Zero-shot classifier
classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli"
)

CATEGORIES = [
    "Mess / Food",
    "Water Supply",
    "Electricity",
    "Internet / WiFi",
    "Cleanliness",
    "Room / Furniture",
    "Security",
    "Administration",
    "Other"
]


# Preprocess text (username and link placeholders)
def preprocess(text):
    new_text = []
    for t in text.split(" "):
        t = "@user" if t.startswith("@") and len(t) > 1 else t
        t = "http" if t.startswith("http") else t
        new_text.append(t)
    return " ".join(new_text)
MODEL = f"cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
config = AutoConfig.from_pretrained(MODEL)
        # PT
model = AutoModelForSequenceClassification.from_pretrained(MODEL)

def output(text):

    # model.save_pretrained(MODEL)
    # text = input("text please\n")
    # text = preprocess(text)
    encoded_input = tokenizer(text, return_tensors="pt")
    output = model(**encoded_input)
    scores = output[0][0].detach().numpy()
    scores = softmax(scores)
    return scores
def ranking(scores):

    ranking = np.argsort(scores)
    ranking = ranking[::-1]
    for i in range(scores.shape[0]):
        l = config.id2label[ranking[i]]
        s = scores[ranking[i]]
        print(f"{i + 1}) {l} {np.round(float(s), 4)}")

def predict_category(text):
    result = classifier(text, CATEGORIES)
    return {
        "category": result["labels"][0],
        "confidence": round(result["scores"][0], 3)
    }
