import os, sys
# Make this package a namespace that points to the actual backend/app directory
package_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app"))
# Extend this package's __path__ so imports like app.database find modules in backend/app
if os.path.isdir(package_path):
    __path__.append(package_path)
else:
    raise RuntimeError(f"Backend app path not found: {package_path}")
