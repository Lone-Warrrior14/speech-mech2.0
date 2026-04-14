import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(base_dir)
sys.path.extend([
    os.path.join(root_dir, 'authorization'),
    os.path.join(root_dir, 'speech_assistant'),
    os.path.join(root_dir, 'rag_system'),
    os.path.join(root_dir, 'rag_system', 'RAG'),
    os.path.join(root_dir, 'speech_assistant', 'media')
])

try:
    from identity import fuzzy_match_user
    print("identity: OK")
except Exception as e:
    print(f"identity: FAIL ({e})")

try:
    from media_library import get_movies
    print("media_library: OK")
except Exception as e:
    print(f"media_library: FAIL ({e})")

try:
    import rag_answer
    print("rag_answer: OK")
except Exception as e:
    print(f"rag_answer: FAIL ({e})")
