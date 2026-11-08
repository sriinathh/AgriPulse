'''Lightweight stub for joblib used in ModelManager when the real package is unavailable.'''

class DummyModel:
    def predict(self, df):
        return [0.0]

def load(path):
    # Return a dummy payload mimicking the expected joblib artifact structure.
    return {
        "model": DummyModel(),
        "columns": []
    }
