from transformers import pipeline

dialog_model = pipeline("text-generation", model="microsoft/DialoGPT-large")

text = "I will kill you."
result = dialog_model(text, max_length=50)
print(result)


