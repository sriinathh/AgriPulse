import os, joblib, json, sys
model_path = os.path.abspath('ml/models/irrigation_model.joblib')
if not os.path.exists(model_path):
    print('Model file not found', model_path)
    sys.exit(1)
payload = joblib.load(model_path)
print('Keys:', list(payload.keys()))
model = payload.get('model')
cols = payload.get('columns')
print('Model type:', type(model))
print('Number of columns:', len(cols) if cols else 'None')
print('First 5 columns:', cols[:5] if cols else None)
