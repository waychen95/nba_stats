import json
import os
import pickle
import numpy as np
import faiss
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DOCS_JSONL = "docs.jsonl"
OUT_INDEX = "nbadle.index"
OUT_DOCS = "docs.pkl"
OUT_METAS = "metas.pkl"

EMBED_MODEL = "text-embedding-3-small"
BATCH_SIZE = 256


def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    texts = []
    metas = []

    with open(DOCS_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            texts.append(obj["text"])
            meta = obj.get("meta", {})
            meta["id"] = obj.get("id", "")
            metas.append(meta)

    if not texts:
        raise RuntimeError("No documents found in docs.jsonl")

    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        vectors.extend([e.embedding for e in resp.data])

    vecs = np.array(vectors, dtype="float32")

    # Cosine similarity setup: normalize, then IndexFlatIP
    faiss.normalize_L2(vecs)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)

    faiss.write_index(index, OUT_INDEX)

    with open(OUT_DOCS, "wb") as f:
        pickle.dump(texts, f)

    with open(OUT_METAS, "wb") as f:
        pickle.dump(metas, f)

    print(f"Embedded {len(texts)} docs.")
    print(f"Saved index: {OUT_INDEX}")
    print(f"Saved docs:  {OUT_DOCS}")
    print(f"Saved metas: {OUT_METAS}")


if __name__ == "__main__":
    main()
