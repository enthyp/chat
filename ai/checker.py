import pickle
from keras.preprocessing.sequence import pad_sequences
from keras.models import model_from_json
from ai.model import Model


class Checker(Model):
    def load(self, architecture, weights, tokenizer, maxlen):
        self.maxlen = maxlen

        with open(tokenizer, 'rb') as handle:
            self.tokenizer = pickle.load(handle)

        with open(architecture, 'r') as f:
            self.model = model_from_json(f.read())
        self.model.load_weights(weights)

    def load_from_package(self, maxlen):
        self.maxlen = maxlen

        from pkg_resources import resource_filename
        tokenizer = resource_filename('ai', 'models/tokenizer.pickle')
        architecture = resource_filename('ai', 'models/model_architecture.json')
        weights = resource_filename('ai', 'models/model_weights.h5')

        with open(tokenizer, 'rb') as handle:
            self.tokenizer = pickle.load(handle)

        with open(architecture, 'r') as f:
            self.model = model_from_json(f.read())
        self.model.load_weights(weights)

    def process(self, msg):
        tokenized_msg = self.tokenizer.texts_to_sequences([msg])
        x_s = pad_sequences(tokenized_msg, self.maxlen)
        predictions = self.model.predict([x_s])

        return predictions.squeeze().tolist()
