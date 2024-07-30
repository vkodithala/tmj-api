import os
import json
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
# We won't have competing threads in this example app
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# entityModel = SpanMarkerModel.from_pretrained(
#     "tomaarsen/span-marker-xlm-roberta-base-multinerd")
# Initialize tokenizer and model for GTE-base
tokenizer = AutoTokenizer.from_pretrained('thenlper/gte-base')
model = AutoModel.from_pretrained('thenlper/gte-base')
# emotionClassification = pipeline(
#     "text-classification", model="SamLowe/roberta-base-go_emotions")


def average_pool(last_hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    last_hidden = last_hidden_states.masked_fill(
        ~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def embed(text, metadata={}):
    combined_text = " ".join(
        [text] + [v for k, v in metadata.items() if isinstance(v, str)])

    inputs = tokenizer(combined_text, return_tensors='pt',
                       max_length=512, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)

    attention_mask = inputs['attention_mask']
    embeddings = average_pool(
        outputs.last_hidden_state, attention_mask)  # type: ignore

    embeddings = F.normalize(embeddings, p=2, dim=1)

    return embeddings.numpy().tolist()[0]


# def emotion(text, metadata={}):
#     combined_text = " ".join(
#         [text] + [v for k, v in metadata.items() if isinstance(v, str)])

#     result = emotionClassification(combined_text)

#     if result and isinstance(result, list):
#         return result[0].get("label")
#     else:
#         raise ValueError("Unexpected result type from emotionClassification.")


# def entity(text, metadata={}):
#     combined_text = " ".join(
#         [text] + [v for k, v in metadata.items() if isinstance(v, str)])

#     entities = entityModel.predict(combined_text)

#     result = []

#     # for entity in entities:
#     #     entity_item = entity['span']
#     #     entity_type = entity['label']

#     # print("\nresult from entity extraction: ", entity_type, ": ", entity_item)

#     return entity_item, entity_type
