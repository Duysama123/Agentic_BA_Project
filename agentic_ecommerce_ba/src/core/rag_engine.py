def sliding_window_chunking(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """Splits text into sliding window chunks for RAG."""
    if not text:
        return []
    
    # Simple word-based chunking
    words = text.split()
    chunks = []
    
    if len(words) == 0:
        return []
        
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
            
    return chunks
