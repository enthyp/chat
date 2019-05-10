from keras.models import model_from_json
from .model import Model
import pickle
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

class Checker(Model):

    def load(self, architectures, weights, tokenizer, maxlen):

        with open(architectures, 'r') as f:
            self.model = model_from_json(f.read())

        self.model.load_weights(weights)

        with open(tokenizer, 'rb') as handle:
            self.t = pickle.load(handle)

        self.maxlen=maxlen

    def process(self, msg):
        list_tokenized_S = self.t.texts_to_sequences([msg])
        X_S = pad_sequences(list_tokenized_S, self.maxlen)
        y_S = self.model.predict([X_S])
        return y_S
    