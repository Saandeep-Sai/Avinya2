import os
import re
from typing import List, Dict

SUPPORTED_EXTENSIONS = ['.py', '.c', '.cpp', '.java']

def collect_code_files(folder: str) -> List[str]:
    files = []
    for root, _, filenames in os.walk(folder):
        for fname in filenames:
            if any(fname.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                files.append(os.path.join(root, fname))
    return files

def normalize_names(code: str, ext: str) -> str:
    # Replace variable and function names with generic tokens
    if ext == '.py':
        # Replace Python def function names
        code = re.sub(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'def func', code)
        # Replace variable assignments
        code = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=','var =', code)
    elif ext in ['.c', '.cpp', '.java']:
        # Replace C/Java function names
        code = re.sub(r'(int|void|float|double|char|public|private|static)\s+([a-zA-Z_][a-zA-Z0-9_]*)', r'\1 func', code)
        # Replace variable assignments
        code = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=','var =', code)
    return code

def remove_comments_and_empty_lines(code: str, ext: str) -> str:
    # Remove comments for Python, C/C++, Java
    if ext == '.py':
        code = re.sub(r'#.*', '', code)
    else:
        code = re.sub(r'//.*', '', code)  # Single-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)  # Multi-line comments
    # Remove empty lines
    code = '\n'.join([line for line in code.splitlines() if line.strip()])
    return code

def preprocess_file(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1]
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()
    code = remove_comments_and_empty_lines(code, ext)
    code = normalize_names(code, ext)
    return code


# --- CodeBERT Embedding ---
from transformers import AutoTokenizer, AutoModel
import torch
from tqdm import tqdm

def get_codebert_model():
    tokenizer = AutoTokenizer.from_pretrained('microsoft/codebert-base')
    model = AutoModel.from_pretrained('microsoft/codebert-base')
    return tokenizer, model

def get_embedding_batch(texts: list, tokenizer, model) -> torch.Tensor:
    # Batch embedding for speed
    inputs = tokenizer(texts, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        emb = outputs.last_hidden_state.mean(dim=1)
    return emb

import multiprocessing as mp

def preprocess_file_mp(file):
    return preprocess_file(file)

if __name__ == '__main__':
    folder = 'submissions'  # Change as needed
    files = collect_code_files(folder)
    print(f'Found {len(files)} code files.')
    tokenizer, model = get_codebert_model()
    # Multiprocessing for preprocessing
    with mp.Pool(processes=mp.cpu_count()) as pool:
        processed_texts = pool.map(preprocess_file_mp, files)
    print('Generating embeddings in batch...')
    batch_embs = get_embedding_batch(processed_texts, tokenizer, model)
    embeddings: Dict[str, torch.Tensor] = {f: batch_embs[i] for i, f in enumerate(files)}
    print(f'Generated embeddings for {len(embeddings)} files.')

    # --- Similarity Computation ---
    from sklearn.metrics.pairwise import cosine_similarity
    import pandas as pd

    threshold = 0.95  # Stricter threshold
    results = []
    file_list = list(embeddings.keys())
    emb_matrix = torch.stack([embeddings[f] for f in file_list]).numpy()
    sim_matrix = cosine_similarity(emb_matrix)

    for i in range(len(file_list)):
        for j in range(i+1, len(file_list)):
            score = sim_matrix[i][j]
            if score > threshold:
                results.append({
                    'File 1': os.path.basename(file_list[i]),
                    'File 2': os.path.basename(file_list[j]),
                    'Similarity': round(score, 4)
                })

    # --- Output Report ---
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values(by='Similarity', ascending=False)
        print('\nFlagged Similar Files:')
        print(df.to_string(index=False))
        df.to_csv('similarity_report.csv', index=False)
        print('\nReport saved to similarity_report.csv')
    else:
        print('No similar file pairs found above threshold.')