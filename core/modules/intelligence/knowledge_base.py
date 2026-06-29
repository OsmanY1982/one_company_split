# -*- coding: utf-8 -*-
"""
知识库管理 - 文档导入、向量检索、智能问答
"""

import os
import json
import hashlib
import pickle
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class Document:
    """文档对象"""
    id: str
    title: str
    content: str
    source: str
    doc_type: str  # txt, pdf, md, json, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[str] = field(default_factory=list)
    embeddings: List[List[float]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "source": self.source,
            "doc_type": self.doc_type,
            "metadata": self.metadata,
            "chunk_count": len(self.chunks),
            "created_at": self.created_at.isoformat(),
        }


class SimpleVectorStore:
    """简单向量存储（使用TF-IDF替代真实向量）"""
    
    def __init__(self, dimension: int = 100):
        self.dimension = dimension
        self.documents: Dict[str, Document] = {}
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        # 简单的中文和英文分词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+', text.lower())
        return words
    
    def _compute_tfidf(self, text: str) -> Dict[str, float]:
        """计算TF-IDF向量"""
        words = self._tokenize(text)
        if not words:
            return {}
        
        # 词频
        tf = {}
        for word in words:
            tf[word] = tf.get(word, 0) + 1
        
        # 归一化
        total = len(words)
        for word in tf:
            tf[word] = tf[word] / total
        
        # TF-IDF
        tfidf = {}
        for word, freq in tf.items():
            if word in self.idf:
                tfidf[word] = freq * self.idf[word]
        
        return tfidf
    
    def _text_to_vector(self, text: str) -> List[float]:
        """将文本转换为向量"""
        tfidf = self._compute_tfidf(text)
        
        # 构建向量
        vector = [0.0] * len(self.vocabulary)
        for word, score in tfidf.items():
            if word in self.vocabulary:
                idx = self.vocabulary[word]
                vector[idx] = score
        
        return vector
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        if not v1 or not v2:
            return 0.0
        
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def add_document(self, doc: Document) -> bool:
        """添加文档"""
        try:
            # 分块
            chunks = self._chunk_text(doc.content)
            doc.chunks = chunks
            
            # 更新词汇表
            all_text = doc.content
            words = self._tokenize(all_text)
            
            for word in set(words):
                if word not in self.vocabulary:
                    self.vocabulary[word] = len(self.vocabulary)
            
            # 更新IDF
            doc_count = len(self.documents) + 1
            for word in set(words):
                doc_freq = sum(1 for d in self.documents.values() if word in d.content)
                self.idf[word] = doc_count / (doc_freq + 1)
            
            # 计算块向量
            doc.embeddings = [self._text_to_vector(chunk) for chunk in chunks]
            
            self.documents[doc.id] = doc
            return True
            
        except Exception as e:
            print(f"添加文档失败: {e}")
            return False
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """文本分块"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # 尝试在句子边界截断
            if end < len(text):
                # 查找最近的句号、问号或换行
                for sep in ['。', '？', '！', '.', '?', '!', '\n']:
                    pos = chunk.rfind(sep)
                    if pos > chunk_size * 0.5:
                        chunk = chunk[:pos + 1]
                        end = start + pos + 1
                        break
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float, str]]:
        """搜索相关文档"""
        query_vector = self._text_to_vector(query)
        
        results = []
        for doc in self.documents.values():
            # 计算与每个块的相似度
            best_score = 0
            best_chunk = ""
            
            for i, chunk_vector in enumerate(doc.embeddings):
                score = self._cosine_similarity(query_vector, chunk_vector)
                if score > best_score:
                    best_score = score
                    best_chunk = doc.chunks[i] if i < len(doc.chunks) else ""
            
            if best_score > 0:
                results.append((doc, best_score, best_chunk))
        
        # 排序并返回前k个
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False
    
    def list_documents(self) -> List[Document]:
        """列出所有文档"""
        return list(self.documents.values())
    
    def save(self, path: str) -> bool:
        """保存向量存储"""
        try:
            data = {
                "vocabulary": self.vocabulary,
                "idf": self.idf,
                "documents": {k: v.to_dict() for k, v in self.documents.items()},
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    def load(self, path: str) -> bool:
        """加载向量存储"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.vocabulary = data.get("vocabulary", {})
            self.idf = data.get("idf", {})
            # 注意：这里只加载了元数据，完整内容需要重新导入
            return True
        except Exception as e:
            print(f"加载失败: {e}")
            return False


class KnowledgeBase:
    """知识库管理器"""
    
    def __init__(self, storage_path: str = "./knowledge_base"):
        self.storage_path = storage_path
        self.vector_store = SimpleVectorStore()
        self._ensure_storage()
        
    def _ensure_storage(self):
        """确保存储目录存在"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
    
    def _generate_id(self, content: str) -> str:
        """生成文档ID"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def import_document(self, file_path: str, title: str = "", metadata: Dict = None) -> Dict[str, Any]:
        """导入文档"""
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": "文件不存在"}
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 获取文件类型
            _, ext = os.path.splitext(file_path)
            doc_type = ext.lower().strip('.')
            
            # 生成文档ID
            doc_id = self._generate_id(content)
            
            # 创建文档对象
            doc = Document(
                id=doc_id,
                title=title or os.path.basename(file_path),
                content=content,
                source=file_path,
                doc_type=doc_type,
                metadata=metadata or {},
            )
            
            # 添加到向量存储
            if self.vector_store.add_document(doc):
                # 保存到文件
                doc_path = os.path.join(self.storage_path, f"{doc_id}.json")
                with open(doc_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "id": doc.id,
                        "title": doc.title,
                        "content": doc.content,
                        "source": doc.source,
                        "doc_type": doc.doc_type,
                        "metadata": doc.metadata,
                        "created_at": doc.created_at.isoformat(),
                    }, f, ensure_ascii=False, indent=2)
                
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "title": doc.title,
                    "chunks": len(doc.chunks),
                }
            else:
                return {"success": False, "error": "添加到向量存储失败"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def import_text(self, text: str, title: str, metadata: Dict = None) -> Dict[str, Any]:
        """导入文本"""
        doc_id = self._generate_id(text)
        
        doc = Document(
            id=doc_id,
            title=title,
            content=text,
            source="manual",
            doc_type="txt",
            metadata=metadata or {},
        )
        
        if self.vector_store.add_document(doc):
            return {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "chunks": len(doc.chunks),
            }
        else:
            return {"success": False, "error": "添加失败"}
    
    def query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """查询知识库"""
        try:
            results = self.vector_store.search(question, top_k)
            
            if not results:
                return {
                    "success": True,
                    "answer": "未找到相关知识",
                    "sources": [],
                }
            
            # 构建答案
            sources = []
            context_parts = []
            
            for doc, score, chunk in results:
                sources.append({
                    "title": doc.title,
                    "score": round(score, 4),
                    "chunk": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                })
                context_parts.append(f"[{doc.title}]\n{chunk}")
            
            # 简单的答案生成（实际应用中可以使用LLM）
            context = "\n\n".join(context_parts)
            answer = self._generate_answer(question, context)
            
            return {
                "success": True,
                "answer": answer,
                "sources": sources,
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_answer(self, question: str, context: str) -> str:
        """生成答案（简化版）"""
        # 这里可以集成LLM来生成更好的答案
        # 现在使用简单的模板
        return f"基于知识库内容，以下是相关信息：\n\n{context[:500]}..."
    
    def list_documents(self) -> List[Dict]:
        """列出所有文档"""
        docs = self.vector_store.list_documents()
        return [doc.to_dict() for doc in docs]
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        # 删除向量存储中的文档
        self.vector_store.delete_document(doc_id)
        
        # 删除文件
        doc_path = os.path.join(self.storage_path, f"{doc_id}.json")
        if os.path.exists(doc_path):
            os.remove(doc_path)
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        docs = self.vector_store.list_documents()
        total_chunks = sum(len(d.chunks) for d in docs)
        
        return {
            "document_count": len(docs),
            "total_chunks": total_chunks,
            "vocabulary_size": len(self.vector_store.vocabulary),
            "storage_path": self.storage_path,
        }


# 全局知识库实例
knowledge_base = KnowledgeBase()


if __name__ == "__main__":
    # 测试知识库
    kb = KnowledgeBase("./test_kb")
    
    # 导入测试文档
    result = kb.import_text(
        text="Iqra是一个智能助手系统，支持多种AI能力。",
        title="Iqra介绍",
    )
    print(f"导入结果: {result}")
    
    # 查询
    result = kb.query("什么是Iqra？")
    print(f"查询结果: {result}")
