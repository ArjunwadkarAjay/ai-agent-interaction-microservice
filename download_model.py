from chromadb.utils import embedding_functions
import os
import sys

print("--- [download_model.py] STARTED ---")
try:
    # Initialize the default embedding function to trigger the download
    # This will download 'all-MiniLM-L6-v2' to the default cache directory
    print("--- [download_model.py] Triggering DefaultEmbeddingFunction to download model... ---")
    ef = embedding_functions.DefaultEmbeddingFunction()
    
    # Force download by encoding a sample
    print("--- [download_model.py] Encoding sample to force download... ---")
    ef(["test"])
    
    print("--- [download_model.py] Download command executed successfully. ---")
    
    # Verify file existence
    cache_dir = os.path.expanduser("~/.cache")
    print(f"--- [download_model.py] Checking cache directory: {cache_dir} ---")
    
    found = False
    for root, dirs, files in os.walk(cache_dir):
        for name in files:
            if "onnx" in name:
                print(f"--- [download_model.py] FOUND MODEL: {os.path.join(root, name)}")
                found = True
                
    if not found:
        print("--- [download_model.py] ERROR: No ONNX model files found in cache! ---")
        sys.exit(1)

except Exception as e:
    print(f"--- [download_model.py] EXCEPTION: {e} ---")
    sys.exit(1)

print("--- [download_model.py] FINISHED ---")
