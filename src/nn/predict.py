import torch
from transformers import AutoTokenizer, logging
from sklearn.preprocessing import LabelEncoder
from typing import Union, List, Dict

from .model import CardClassifier

logging.set_verbosity_error()


class Predictor:
    def __init__(self, model_path='./data/card_classifier.pth'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.tokenizer = AutoTokenizer.from_pretrained('DeepPavlov/rubert-base-cased')
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        self.labels = ["duplicate_card", "new_card", "card_message"]
        self.label_encoder = LabelEncoder().fit(self.labels)

        self.model = CardClassifier(num_classes=len(self.labels)).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def predict(self, texts: Union[str, List[str]]) -> Union[Dict, List[Dict]]:
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]

        encodings = self.tokenizer(texts, truncation=True, padding=True, max_length=512, return_tensors='pt')

        with torch.no_grad():
            input_ids = encodings['input_ids'].to(self.device)
            attention_mask = encodings['attention_mask'].to(self.device)
            outputs = self.model(input_ids, attention_mask)
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            confidences = torch.softmax(outputs, dim=1).max(dim=1).values.cpu().numpy()

        decoded_labels = self.label_encoder.inverse_transform(preds)
        results = []
        for i in range(len(decoded_labels)):
            label = decoded_labels[i]
            confidence = confidences[i]
            
            if label == 'new_card':
                message_type = 'NEW_CARD'
            elif label == 'duplicate_card':
                message_type = 'DUPLICATE_CARD'
            else:
                message_type = 'CARD_MESSAGE'

            results.append({
                'type': label,
                'confidence': float(confidence),
                'message_type': message_type
            })

        if is_single:
            return results[0]
        return results


if __name__ == '__main__':
    predictor = Predictor()

    single_msg = """🌟 Карточка «Комару в своем бассейне» ваша!

💎 Редкость • Редкая
✨ Очки • +3,000 [339,000]
💰 Монеты • +7 [1,693]
⚡️ Бустер «удача» помог вам получить эту карточку

🎉 Бонусная карточка каждые 12 часов с командой /bonus"""
    single_result = predictor.predict(single_msg)
    print("--- Single Prediction ---")
    print(single_result)
    print("\n--- Batch Prediction ---")

    test_msgs = [
        single_msg,
        """🔄 Карточка «Много комару» уже у вас!

💎 Редкость • Редкая
✨ Очки • 3,000 [336,000]
💰 Монеты • +3 [1,686]
⚡️ Бустер «удача» помог вам получить эту карточку

Будут начислены только очки

🎁 Получай карточку раз в 12 часов с /bonus!"""
    ]

    batch_results = predictor.predict(test_msgs)
    for result in batch_results:
        print(result)
