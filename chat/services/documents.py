import json
import os
import pickle
from pathlib import Path
from typing import List

import faiss
import numpy as np
import openai

from chat.models import Chat
from chat.services.settings import EMBEDDING_MODEL
from crm.services import bitrix
from crm.services.request_data_handler import RequestDataHandler
from users.models import Company
import logging

logger = logging.getLogger(__name__)


def retrieve(index, docs, query: str) -> List[dict]:
    k = 3 if len(query.split()) < 7 else 5
    q_resp = openai.embeddings.create(model=EMBEDDING_MODEL, input=[query])
    q_emb = np.array(q_resp.data[0].embedding, dtype=np.float32).reshape(1, -1)

    _, indices = index.search(q_emb, k * 2)
    matched_docs = [docs[i] for i in indices[0] if 0 <= i < len(docs)]

    return matched_docs[:k]


def load_rag_chunks(company: Company) -> List[dict]:
    docs = []
    files = [obj.file.path for obj in company.rag_files.all()]

    for file_path in files:
        if not Path(file_path).exists():
            logger.error("Файл не найден: %s", file_path)
            continue

        with open(file_path, encoding="utf-8") as f:
            for lineno, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    docs.append(obj)
                except json.JSONDecodeError as e:
                    logger.warning("Пропущена строка %s:%d — %s", file_path, lineno, e)
    return docs


def load_index(company: Company):
    return None, None
    faiss_obj = company.faiss_files.all().first()
    doc_obj = company.doc_files.all().first()
    index = faiss.read_index(faiss_obj.file.path)
    with open(doc_obj.file.path, "rb") as f:
        all_docs = pickle.load(f)
    return index, all_docs
