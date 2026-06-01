"""
Pipeline RAG mínimo usando ChromaDB + sentence-transformers.

Requisitos (instalar com pip):
  pip install chromadb sentence-transformers langchain

Stack exigida:
  - Python
  - ChromaDB (local) para vector store
  - sentence-transformers (`all-MiniLM-L6-v2`) para embeddings
  - LangChain opcional (não usado aqui; orquestração manual)
  - Geração externa via Claude (manual copy-paste do prompt)

Funcionalidades:
  1) Ingestão: lê os arquivos em `anexo-a-documentos-individuais/`, faz chunking,
	 gera embeddings e armazena no ChromaDB local.
	 Estratégia de chunking: fragmentação por caractere com janela deslizante
	 (chunk_size=1000 chars, overlap=200). Justificativa: modelo `all-MiniLM-L6-v2`
	 trabalha bem com frases/trechos curtos; chunk por caractere é simples,
	 determinístico e evita depender de bibliotecas de tokenização.

  2) Busca: dado uma pergunta, gera embedding da pergunta e faz query no ChromaDB
	 retornando os N chunks mais similares com as distâncias.

  3) Montagem de prompt: recebe os chunks recuperados e monta um prompt completo
	 (system prompt + contexto + pergunta) pronto para colar no chat do Claude.

Observação: o script não usa nenhuma API de Claude. Ele constrói um prompt
que você pode colar manualmente no chat do Claude para a geração.
"""

import os
import glob
import uuid
from typing import List, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer

import chromadb

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
	"""Divide o texto em chunks usando janela deslizante de caracteres.

	Args:
		text: Texto completo a ser chunked.
		chunk_size: Tamanho alvo do chunk em caracteres.
		chunk_overlap: Sobreposição entre chunks em caracteres.

	Returns:
		Lista de strings (chunks).
	"""
	if chunk_size <= 0:
		raise ValueError("chunk_size must be > 0")
	if chunk_overlap >= chunk_size:
		raise ValueError("chunk_overlap must be smaller than chunk_size")

	chunks = []
	start = 0
	text_len = len(text)
	step = chunk_size - chunk_overlap
	while start < text_len:
		end = min(start + chunk_size, text_len)
		chunk = text[start:end].strip()
		if chunk:
			chunks.append(chunk)
		start += step
	return chunks


def ingest_documents(
	data_dir: str = "anexo-a-documentos-individuais",
	persist_directory: str = "./chroma_db",
	collection_name: str = "rag_docs",
	model_name: str = "all-MiniLM-L6-v2",
	chunk_size: int = 1000,
	chunk_overlap: int = 200,
):
	"""Ingesta: lê arquivos, chunk, embeddings e salva no ChromaDB.

	Retorna a coleção Chroma criada/usada.
	"""
	# Carrega o modelo de embeddings
	model = SentenceTransformer(model_name)

	# Cria cliente ChromaDB local
	client = chromadb.PersistentClient(path=persist_directory)

	# Cria ou obtém collection
	try:
		collection = client.get_collection(name=collection_name)
	except Exception:
		collection = client.create_collection(name=collection_name)

	ids = []
	documents = []
	metadatas = []

	files = sorted(glob.glob(os.path.join(data_dir, "*")))
	for file_path in files:
		if os.path.isdir(file_path):
			continue
		with open(file_path, "r", encoding="utf-8") as f:
			text = f.read()
		base = os.path.basename(file_path)
		# opcional: pré-processamento simples
		text = text.replace("\r\n", "\n")
		chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
		for i, c in enumerate(chunks):
			doc_id = f"{base}::{i}::{uuid.uuid4().hex[:8]}"
			ids.append(doc_id)
			documents.append(c)
			metadatas.append({"source": base, "chunk_index": i})

	if not documents:
		print("Nenhum documento encontrado para ingestão em:", data_dir)
		return collection

	# Gera embeddings em batch
	embeddings = model.encode(documents, show_progress_bar=True, convert_to_numpy=True)

	# Converte embeddings para listas simples (serializável)
	emb_list = [e.tolist() for e in embeddings]

	# Adiciona à coleção
	collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=emb_list)

	# Persistência (algumas versões do Chroma exigem persist explicitamente)
	try:
		client.persist()
	except Exception:
		pass

	print(f"Ingestão concluída — {len(documents)} chunks indexados na collection '{collection_name}'.")
	return collection


def retrieve(
	question: str,
	persist_directory: str = "./chroma_db",
	collection_name: str = "rag_docs",
	model_name: str = "all-MiniLM-L6-v2",
	n_results: int = 3,
) -> List[Dict[str, Any]]:
	"""Busca os N chunks mais similares a `question` e retorna lista com documento,
	metadata e distância.
	"""
	model = SentenceTransformer(model_name)
	client = chromadb.PersistentClient(path=persist_directory)
	collection = client.get_collection(name=collection_name)

	q_emb = model.encode([question], convert_to_numpy=True)[0].tolist()

	results = collection.query(query_embeddings=[q_emb], n_results=n_results, include=["documents", "metadatas", "distances"])

	out = []
	# results format: keys -> documents, metadatas, distances each is a list-of-lists per query
	docs = results.get("documents", [[]])[0]
	metas = results.get("metadatas", [[]])[0]
	dists = results.get("distances", [[]])[0]

	for doc, meta, dist in zip(docs, metas, dists):
		out.append({"document": doc, "metadata": meta, "distance": dist})
	return out


def build_prompt(retrieved_chunks: List[Dict[str, Any]], question: str, system_prompt: str = None) -> str:
	"""Monta prompt pronto para colar no chat do Claude.

	O prompt inclui um `system prompt` (padrão em Português), os trechos recuperados
	com suas fontes, e a pergunta do usuário.
	"""
	if system_prompt is None:
		system_prompt = (
			"Você é um assistente útil que responde em Português. "
			"Use apenas as informações fornecidas no contexto abaixo para responder; "
			"se a resposta não estiver contida no contexto, diga que não sabe. "
			"Cite as fontes entre colchetes após cada fato (por exemplo: [PROC-042-frete-especial-v1.md])."
		)

	context_parts = []
	for i, item in enumerate(retrieved_chunks, start=1):
		src = item.get("metadata", {}).get("source", "unknown")
		header = f"--- Fonte: {src} (chunk {item.get('metadata', {}).get('chunk_index', '?')}) ---"
		context_parts.append(f"{header}\n{item.get('document')}\n")

	context = "\n".join(context_parts)

	prompt = f"SYSTEM:\n{system_prompt}\n\nCONTEXT:\n{context}\n\nPERGUNTA:\n{question}\n\nINSTRUÇÕES: Responda em Português, sendo conciso. Ao citar informações, referencie as fontes entre colchetes.\n"

	return prompt


if __name__ == "__main__":
    # Exemplo de uso
    data_dir = "anexo-a-documentos-individuais"
    persist_dir = "./chroma_db"

    # 1) Ingestão (rode uma vez, depois comente esta linha adicionando um # no início para evitar reindexar)
    ingest_documents(data_dir=data_dir, persist_directory=persist_dir)

    # 2) Lista de perguntas
    perguntas = [
        "Qual o prazo de devolução?",
        "Qual o SLA do cliente Gold?",
        "Frete para 600kg para Manaus?",
        "Posso devolver carga perigosa?",
        "Qual o multiplicador para o Sudeste?"
    ]

    # 3) Loop de Busca e Montagem de Prompt
    for pergunta in perguntas:
        print(f"\n==========================================")
        print(f"Testando a pergunta: {pergunta}")
        
        # Faz o retrieve para a pergunta atual do loop
        resultados = retrieve(pergunta, persist_directory=persist_dir, n_results=3)
        
        # Mostra os chunks recuperados para você avaliar
        print("\nRecuperados:")
        for r in resultados:
            print(f"- Fonte: {r['metadata'].get('source')} | distância: {r['distance']:.4f}")
        
        # Monta o prompt para o Claude
        prompt = build_prompt(resultados, pergunta)
        print("\n--- Prompt pronto para colar no Claude ---\n")
        print(prompt)