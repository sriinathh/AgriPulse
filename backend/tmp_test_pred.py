import sys, traceback
sys.path.append('backend')
try:
    import app.routers.prediction as pred
    print('import ok')
except Exception as e:
    traceback.print_exc()
