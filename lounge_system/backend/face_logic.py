import numpy as np
try:
    from deepface import DeepFace
    HAS_DEEPFACE = True
except ImportError:
    HAS_DEEPFACE = False
import json
import logging

logger = logging.getLogger(__name__)

# Config
MODEL_NAME = "ArcFace"
SIMILARITY_THRESHOLD = 0.20

def get_embedding(image_path: str):
    """
    Get normalized embedding for a face using ArcFace.
    """
    try:
        if not HAS_DEEPFACE:
            logger.warning("DeepFace not installed, using mock embedding")
            # Return a deterministic random-looking vector for demo
            return (np.random.rand(128) * 2 - 1).tolist()

        # DeepFace.represent returns a list of dictionaries (one for each face)
        embeddings = DeepFace.represent(img_path=image_path, model_name=MODEL_NAME, enforce_detection=True)
        if not embeddings:
            return None
        
        # Get the first face's embedding
        embedding = embeddings[0]["embedding"]
        
        # Normalize the embedding (ArcFace usually outputs normalized, but let's be strict)
        embedding_np = np.array(embedding)
        norm = np.linalg.norm(embedding_np)
        if norm != 0:
            embedding_np = embedding_np / norm
            
        return embedding_np.tolist()
    except Exception as e:
        logger.error(f"DeepFace error: {e}")
        # Fallback for demo if DeepFace or CV2 fails in this environment
        # Return a deterministic random-looking vector if image exists
        return None

def cosine_similarity(v1, v2):
    """
    Manual cosine similarity: (A . B) / (||A|| * ||B||)
    Assuming vectors are already normalized.
    """
    a = np.array(v1)
    b = np.array(v2)
    return np.dot(a, b)

def cosine_distance(v1, v2):
    """
    Cosine distance = 1 - cosine_similarity
    """
    return 1 - cosine_similarity(v1, v2)

def verify_face(stored_embedding, current_image_path):
    """
    Verify if current face matches stored embedding.
    """
    current_embedding = get_embedding(current_image_path)
    if current_embedding is None:
        return {"verified": False, "reason": "No face detected or AI error"}
    
    distance = cosine_distance(stored_embedding, current_embedding)
    
    # Cosine distance < 0.20 means high similarity
    verified = distance < SIMILARITY_THRESHOLD
    
    confidence = max(0, 100 * (1 - distance))
    
    return {
        "verified": bool(verified),
        "distance": float(distance),
        "confidence": float(confidence),
        "threshold": SIMILARITY_THRESHOLD
    }
