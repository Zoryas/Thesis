import sys, traceback
sys.path.insert(0, r'd:\xampp\htdocs\readwise')
try:
    import importlib
    importlib.import_module('routes.teacher_routes')
    print('import ok')
except Exception:
    traceback.print_exc()
