import os
import time
import uuid
import json
import pickle
import re
from typing import List, Optional, Dict, Tuple
from pathlib import Path
from dotenv import load_dotenv

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from models import RAGChunk, GuidelineMetadata, ClinicalQuery, RAGResult, RAGResponse, Indication, DosingTable

class MarkdownPageSplitter:
    """Markdown-aware page splitter with overlap for medical guidelines"""
    
    def __init__(self, overlap_sentences: int = 3):
        self.overlap_sentences = overlap_sentences
        self.page_delimiter = "---"
    
    def split_into_pages(self, content: str) -> List[Dict]:
        """Split markdown content into pages with overlap integrated into each page"""
        # Split by page delimiters
        pages = content.split(self.page_delimiter)
        
        page_chunks = []
        for i, page_content in enumerate(pages):
            page_content = page_content.strip()
            if not page_content:
                continue
            
            # Create page chunk with integrated overlap
            enhanced_content = self._create_page_with_overlap(pages, i)
            
            # Extract page metadata
            page_metadata = self._extract_page_metadata(page_content, i + 1)
            
            # Create page chunk with overlap
            page_chunk = {
                'content': enhanced_content,
                'original_content': page_content,  # Keep original for metadata
                'page_number': i + 1,
                'chunk_type': 'page_with_overlap',
                'metadata': page_metadata
            }
            page_chunks.append(page_chunk)
        
        return page_chunks
    
    def _create_page_with_overlap(self, pages: List[str], current_index: int) -> str:
        """Create a page chunk with overlap from previous and next pages, preserving tables"""
        current_page = pages[current_index].strip()
        
        # Get overlap from previous page (last N sentences, but extend for tables)
        prev_overlap = ""
        if current_index > 0 and self.overlap_sentences > 0:
            prev_page = pages[current_index - 1].strip()
            prev_overlap = self._get_last_content_with_tables(prev_page, self.overlap_sentences, 'end')
            if prev_overlap:
                prev_overlap = f"[...Kontext von vorheriger Seite...]\n{prev_overlap}\n\n"
        
        # Get overlap from next page (first N sentences, but extend for tables)
        next_overlap = ""
        if current_index < len(pages) - 1 and self.overlap_sentences > 0:
            next_page = pages[current_index + 1].strip()
            next_overlap = self._get_first_content_with_tables(next_page, self.overlap_sentences, 'start')
            if next_overlap:
                next_overlap = f"\n\n[...Kontext von nächster Seite...]\n{next_overlap}"
        
        # Combine: previous overlap + current page + next overlap
        enhanced_content = prev_overlap + current_page + next_overlap
        return enhanced_content
    
    def _get_last_content_with_tables(self, text: str, n_sentences: int, position: str) -> str:
        """Get last N sentences, but extend to include complete tables"""
        # Check if there are tables in the content
        if self._contains_table(text):
            # If there's a table near the end, include the whole table
            table_extended_content = self._extend_for_table(text, n_sentences, 'end')
            if table_extended_content:
                return table_extended_content
        
        # Fallback to normal sentence extraction
        return self._get_last_sentences(text, n_sentences)
    
    def _get_first_content_with_tables(self, text: str, n_sentences: int, position: str) -> str:
        """Get first N sentences, but extend to include complete tables"""
        # Check if there are tables in the content
        if self._contains_table(text):
            # If there's a table near the beginning, include the whole table
            table_extended_content = self._extend_for_table(text, n_sentences, 'start')
            if table_extended_content:
                return table_extended_content
        
        # Fallback to normal sentence extraction
        return self._get_first_sentences(text, n_sentences)
    
    def _contains_table(self, text: str) -> bool:
        """Check if text contains table markers"""
        table_indicators = [
            'Tabelle', 'Tab.', '|', '---', 
            'Dosierung', 'mg/kg', 'Antibiotikum',
            '<table>', '</table>'
        ]
        text_lower = text.lower()
        return any(indicator.lower() in text_lower for indicator in table_indicators)
    
    def _extend_for_table(self, text: str, n_sentences: int, direction: str) -> str:
        """Extend content to include complete tables"""
        lines = text.split('\n')
        
        if direction == 'end':
            # Start from the end and work backwards
            sentences = self._get_last_sentences(text, n_sentences)
            sentence_lines = sentences.split('\n')
            
            # Check if we're in the middle of a table
            start_idx = max(0, len(lines) - len(sentence_lines) * 2)  # Rough estimate
            
            # Look for table boundaries
            for i in range(start_idx, len(lines)):
                line = lines[i].strip()
                if any(table_marker in line.lower() for table_marker in ['tabelle', 'tab.', '|']):
                    # Found table, extend to include it fully
                    table_end = self._find_table_end(lines, i)
                    if table_end > i:
                        return '\n'.join(lines[i:table_end + 1])
        
        elif direction == 'start':
            # Start from the beginning
            sentences = self._get_first_sentences(text, n_sentences)
            sentence_lines = sentences.split('\n')
            
            # Check if we're in the middle of a table
            end_idx = min(len(lines), len(sentence_lines) * 2)  # Rough estimate
            
            # Look for table boundaries
            for i in range(0, end_idx):
                line = lines[i].strip()
                if any(table_marker in line.lower() for table_marker in ['tabelle', 'tab.', '|']):
                    # Found table, extend to include it fully
                    table_end = self._find_table_end(lines, i)
                    if table_end > i:
                        return '\n'.join(lines[i:table_end + 1])
        
        return None
    
    def _find_table_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a table starting from start_idx"""
        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()
            # Table likely ends at empty line or next heading
            if not line or line.startswith('#'):
                return i - 1
            # Or if we hit another table
            if line.lower().startswith('tabelle') or line.lower().startswith('tab.'):
                return i - 1
        
        return len(lines) - 1
    
    def _extract_page_metadata(self, content: str, page_num: int) -> Dict:
        """Extract structured metadata from markdown content"""
        metadata = {
            'page_number': page_num,
            'headers': [],
            'tables': [],
            'content_types': []
        }
        
        # Extract headers
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        metadata['headers'] = headers[:5]  # Limit to first 5 headers
        
        # Extract table information
        table_matches = re.findall(r'# (Tab\.\d+.*?)$', content, re.MULTILINE)
        metadata['tables'] = table_matches
        
        # Extract figure information
        figure_matches = re.findall(r'# (Abb\.\d+.*?)$', content, re.MULTILINE)
        metadata['figures'] = figure_matches
        
        # Determine content types
        if '<table>' in content:
            metadata['content_types'].append('table')
        if re.search(r'^\d+\)', content, re.MULTILINE):
            metadata['content_types'].append('list')
        if any(keyword in content.lower() for keyword in ['dosierung', 'therapie', 'behandlung']):
            metadata['content_types'].append('therapy')
        if any(keyword in content.lower() for keyword in ['antibiotik', 'penicillin', 'cephalosporin']):
            metadata['content_types'].append('medication')
        
        return metadata
    
    def _create_overlap_chunk(self, prev_content: str, current_content: str, 
                            page_num: int, direction: str) -> Optional[Dict]:
        """Create overlap chunk between pages"""
        try:
            if direction == 'previous':
                # Last N sentences from previous + first N sentences from current
                prev_sentences = self._get_last_sentences(prev_content, self.overlap_sentences)
                curr_sentences = self._get_first_sentences(current_content, self.overlap_sentences)
                overlap_content = prev_sentences + "\n\n" + curr_sentences
                chunk_type = f'overlap_prev_{page_num-1}_{page_num}'
            else:  # next
                # Last N sentences from current + first N sentences from next
                curr_sentences = self._get_last_sentences(current_content, self.overlap_sentences)
                next_sentences = self._get_first_sentences(prev_content, self.overlap_sentences)  # prev_content is actually next in this context
                overlap_content = curr_sentences + "\n\n" + next_sentences
                chunk_type = f'overlap_next_{page_num}_{page_num+1}'
            
            if len(overlap_content.strip()) < 50:  # Skip very short overlaps
                return None
                
            return {
                'content': overlap_content,
                'page_number': page_num,
                'chunk_type': chunk_type,
                'metadata': {'overlap': True, 'direction': direction}
            }
        except:
            return None
    
    def _get_last_sentences(self, text: str, n: int) -> str:
        """Get last N sentences from text"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return '. '.join(sentences[-n:]) + '.' if sentences else ''
    
    def _get_first_sentences(self, text: str, n: int) -> str:
        """Get first N sentences from text"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return '. '.join(sentences[:n]) + '.' if sentences else ''

class AdvancedRAGService:
    def __init__(self, data_dir: str = "data"):
        # Load environment variables
        load_dotenv()
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.embeddings_dir = self.data_dir / "embeddings"
        self.embeddings_dir.mkdir(exist_ok=True)
        
        self.guidelines_dir = self.data_dir / "guidelines"
        self.guidelines_dir.mkdir(exist_ok=True)
        
        # Detect and configure device
        self.device = self._detect_device()
        print(f"Using device: {self.device}")
        
        # Get embedding model from environment or use default
        self.embedding_model_name = os.getenv('EMBEDDING_MODEL')
        print(f"Using embedding model: {self.embedding_model_name}")
        
        # Load embedding model with device configuration
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer(self.embedding_model_name, device=self.device)
        print(f"Embedding model loaded successfully on {self.device}")
        
        # Markdown page splitter
        self.page_splitter = MarkdownPageSplitter(overlap_sentences=3)
        
        # FAISS index
        self.index = None
        self.chunks_metadata = []
        self.guidelines_metadata = {}
        
        # Dosing tables system
        self.dosing_tables = []  # List of DosingTable objects
        self.dosing_index = None  # Separate FAISS index for dosing table names
        self.dosing_embeddings_path = self.embeddings_dir / "dosing_index.bin"
        self.dosing_metadata_path = self.embeddings_dir / "dosing_tables.json"
        
        # Load existing index if available
        self._load_index()
        
        # Load dosing tables from bundled file
        self._load_dosing_tables()
    
    def _detect_device(self) -> str:
        """Detect the best available device for inference"""
        try:
            import torch
            
            # Check for NVIDIA GPU with CUDA
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown GPU"
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3 if gpu_count > 0 else 0
                print(f"CUDA available: {gpu_count} GPU(s) detected")
                print(f"Primary GPU: {gpu_name} ({gpu_memory:.1f} GB)")
                return "cuda"
            
            # Check for Apple Silicon MPS
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                print("Apple MPS (Metal Performance Shaders) available")
                return "mps"
            
            print("PyTorch available but no GPU acceleration detected, using CPU")
            return "cpu"
            
        except ImportError:
            print("PyTorch not available, using CPU with sentence-transformers default")
            print("To enable GPU acceleration, run: pip install torch torchvision torchaudio")
            return "cpu"
        except Exception as e:
            print(f"Device detection failed: {e}, falling back to CPU")
            return "cpu"
    
    def get_device_info(self) -> Dict:
        """Get detailed information about the current device"""
        info = {
            "device": self.device,
            "device_name": "CPU",
            "memory_gb": 0,
            "torch_available": False,
            "cuda_available": False,
            "mps_available": False
        }
        
        try:
            import torch
            info["torch_available"] = True
            info["cuda_available"] = torch.cuda.is_available()
            
            if hasattr(torch.backends, 'mps'):
                info["mps_available"] = torch.backends.mps.is_available()
            
            if self.device == "cuda" and torch.cuda.is_available():
                info["device_name"] = torch.cuda.get_device_name(0)
                info["memory_gb"] = torch.cuda.get_device_properties(0).total_memory / 1024**3
            elif self.device == "mps":
                info["device_name"] = "Apple Silicon GPU"
            else:
                import psutil
                info["device_name"] = f"CPU ({psutil.cpu_count()} cores)"
                info["memory_gb"] = psutil.virtual_memory().total / 1024**3
                
        except ImportError as e:
            info["error"] = f"Missing dependency: {e}"
        except Exception as e:
            info["error"] = f"Device info error: {e}"
        
        return info
    
    def upload_guideline(self, content: str, filename: str, guideline_id: str, indications: List[Indication]) -> Dict:
        """Upload and process a new markdown guideline"""
        try:
            # Determine file extension
            file_extension = '.md' if content.startswith('#') or '---' in content else '.txt'
            
            # Save original file
            file_path = self.guidelines_dir / f"{guideline_id}{file_extension}"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Create metadata
            metadata = GuidelineMetadata(
                guideline_id=guideline_id,
                title=filename,
                indications=indications
            )
            self.guidelines_metadata[guideline_id] = metadata
            
            # Process and chunk the content
            if file_extension == '.md':
                chunks = self._chunk_markdown_document(content, guideline_id)
            else:
                chunks = self._chunk_text_document(content, guideline_id)
            
            # Generate embeddings and add to index
            self._add_chunks_to_index(chunks)
            
            # Save updated index and metadata
            self._save_index()
            self._save_metadata()
            
            return {
                "status": "success",
                "guideline_id": guideline_id,
                "chunks_created": len(chunks),
                "file_type": file_extension,
                "message": f"Successfully processed {len(chunks)} chunks from {file_extension} file"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing guideline: {str(e)}"
            }
    
    def _chunk_markdown_document(self, content: str, guideline_id: str) -> List[RAGChunk]:
        """Split markdown document into page-based chunks with overlap"""
        chunks = []
        
        # Split into pages with overlap
        page_chunks = self.page_splitter.split_into_pages(content)
        
        for i, page_data in enumerate(page_chunks):
            chunk_id = f"{guideline_id}:page_{page_data['page_number']:03d}_{page_data['chunk_type']}"
            
            # Extract additional metadata
            headers = page_data['metadata'].get('headers', [])
            tables = page_data['metadata'].get('tables', [])
            
            # Determine section path from headers
            section_path = headers[0] if headers else None
            if section_path:
                # Clean up section path
                section_path = re.sub(r'^#+\s*', '', section_path)
                section_path = section_path[:100]  # Limit length
            
            chunk = RAGChunk(
                chunk_id=chunk_id,
                guideline_id=guideline_id,
                section_path=section_path,
                page=page_data['page_number'],
                kind="section",  # Could be enhanced to detect tables
                table_id=tables[0] if tables else None,
                snippet=page_data['content'],
                metadata={
                    "chunk_index": i,
                    "chunk_type": page_data['chunk_type'],
                    "length": len(page_data['content']),
                    "headers": headers,
                    "tables": tables,
                    "content_types": page_data['metadata'].get('content_types', []),
                    "is_overlap": page_data['metadata'].get('overlap', False)
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_text_document(self, content: str, guideline_id: str) -> List[RAGChunk]:
        """Enhanced: Split plain text document into page-based chunks with overlap"""
        chunks = []
        
        # Check if content has page separators (---) for page-based splitting
        if '---' in content:
            # Use page-based splitting with overlap (similar to markdown)
            pages = content.split('---')
            
            for i, page_content in enumerate(pages):
                page_content = page_content.strip()
                if not page_content:
                    continue
                
                # Create page chunk with integrated overlap
                enhanced_content = self._create_text_page_with_overlap(pages, i)
                
                chunk_id = f"{guideline_id}:text_page_{i + 1:03d}_with_overlap"
                
                # Extract basic metadata from text
                page_metadata = self._extract_text_metadata(page_content, i + 1)
                
                chunk = RAGChunk(
                    chunk_id=chunk_id,
                    guideline_id=guideline_id,
                    section_path=page_metadata.get('first_heading'),
                    page=i + 1,
                    snippet=enhanced_content,
                    metadata={
                        "chunk_index": i,
                        "chunk_type": "text_page_with_overlap",
                        "length": len(enhanced_content),
                        "original_length": len(page_content),
                        "has_tables": page_metadata.get('has_tables', False),
                        "headings": page_metadata.get('headings', [])
                    }
                )
                chunks.append(chunk)
        
        else:
            # Fallback: Traditional sentence-based splitting with overlap
            chunks = self._chunk_text_traditional_with_overlap(content, guideline_id)
        
        return chunks
    
    def _create_text_page_with_overlap(self, pages: List[str], current_index: int) -> str:
        """Create a text page chunk with overlap from previous and next pages"""
        current_page = pages[current_index].strip()
        overlap_sentences = 3  # Same as markdown splitter
        
        # Get overlap from previous page (last N sentences)
        prev_overlap = ""
        if current_index > 0 and overlap_sentences > 0:
            prev_page = pages[current_index - 1].strip()
            prev_overlap = self._get_last_sentences(prev_page, overlap_sentences)
            if prev_overlap:
                prev_overlap = f"[...Kontext von vorheriger Seite...]\n{prev_overlap}\n\n"
        
        # Get overlap from next page (first N sentences)
        next_overlap = ""
        if current_index < len(pages) - 1 and overlap_sentences > 0:
            next_page = pages[current_index + 1].strip()
            next_overlap = self._get_first_sentences(next_page, overlap_sentences)
            if next_overlap:
                next_overlap = f"\n\n[...Kontext von nächster Seite...]\n{next_overlap}"
        
        # Combine: previous overlap + current page + next overlap
        enhanced_content = prev_overlap + current_page + next_overlap
        return enhanced_content
    
    def _extract_text_metadata(self, content: str, page_num: int) -> Dict:
        """Extract basic metadata from plain text content"""
        metadata = {
            'page_number': page_num,
            'headings': [],
            'has_tables': False,
            'first_heading': None
        }
        
        lines = content.split('\n')
        
        # Look for headings (lines that are shorter and followed by content)
        headings = []
        for i, line in enumerate(lines):
            line = line.strip()
            if (len(line) > 0 and len(line) < 100 and 
                not line.endswith('.') and not line.endswith(',') and
                i < len(lines) - 1 and len(lines[i + 1].strip()) > 0):
                # Likely a heading
                headings.append(line)
        
        metadata['headings'] = headings[:5]  # Limit to first 5
        metadata['first_heading'] = headings[0] if headings else None
        
        # Simple table detection
        content_lower = content.lower()
        table_indicators = [
            'tabelle', 'tab.', 'begriff', 'definition',
            'erreger', 'dosierung', 'antibiotikum'
        ]
        metadata['has_tables'] = any(indicator in content_lower for indicator in table_indicators)
        
        return metadata
    
    def _chunk_text_traditional_with_overlap(self, content: str, guideline_id: str) -> List[RAGChunk]:
        """Fallback: Traditional sentence-based splitting enhanced with overlap"""
        chunks = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunk_size = 16000
        overlap_sentences = 4  # Overlap for traditional chunking
        current_chunk_sentences = []
        chunk_index = 0
        
        for i, sentence in enumerate(sentences):
            current_chunk_sentences.append(sentence)
            current_text = '. '.join(current_chunk_sentences) + '.'
            
            # Check if we should create a chunk
            if (len(current_text) > chunk_size or i == len(sentences) - 1):
                if current_chunk_sentences:
                    chunk_id = f"{guideline_id}:text_chunk_{chunk_index:04d}_overlap"
                    
                    # Add overlap from previous chunk if available
                    enhanced_content = current_text
                    if chunk_index > 0 and overlap_sentences > 0:
                        # Get overlap from previous sentences
                        start_idx = max(0, i - len(current_chunk_sentences) - overlap_sentences)
                        prev_sentences = sentences[start_idx:i - len(current_chunk_sentences)]
                        if prev_sentences:
                            prev_overlap = '. '.join(prev_sentences) + '.'
                            enhanced_content = f"[...Kontext...]\n{prev_overlap}\n\n{current_text}"
                    
                    chunk = RAGChunk(
                        chunk_id=chunk_id,
                        guideline_id=guideline_id,
                        section_path=None,
                        page=None,
                        snippet=enhanced_content,
                        metadata={
                            "chunk_index": chunk_index,
                            "chunk_type": "text_traditional_overlap",
                            "length": len(enhanced_content),
                            "sentence_count": len(current_chunk_sentences),
                            "has_overlap": chunk_index > 0
                        }
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    
                    # Keep overlap for next chunk
                    if overlap_sentences > 0:
                        current_chunk_sentences = current_chunk_sentences[-overlap_sentences:]
                    else:
                        current_chunk_sentences = []
        
        return chunks
    
    def _add_chunks_to_index(self, chunks: List[RAGChunk]):
        """Add chunks to FAISS index"""
        if not chunks:
            return
        
        # Generate embeddings
        texts = [chunk.snippet for chunk in chunks]
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        
        # Initialize or expand FAISS index
        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
            self.chunks_metadata = []
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        # Add metadata
        self.chunks_metadata.extend(chunks)
        
        print(f"Added {len(chunks)} chunks to index. Total chunks: {len(self.chunks_metadata)}")
    
    def search(self, query: ClinicalQuery, top_k: int = 5) -> RAGResponse:
        """Search for relevant chunks based on clinical query - returns top_k chunks from EACH matching guideline"""
        start_time = time.time()
        
        # Build search query
        search_text = self._build_search_query(query)
        
        # Get negative terms for filtering
        negative_terms = self._build_negative_query(query)
        
        # Get query embedding
        query_embedding = self.embedding_model.encode([search_text], convert_to_numpy=True)
        
        # Get chunks grouped by guideline for the specified indication
        guideline_chunks = self._get_chunks_by_guideline_and_indication(query.indication)
        
        # Fallback strategy: if no chunks found for specific indication, search all chunks with warning
        use_fallback = False
        if not guideline_chunks:
            print(f"⚠️  No chunks found for indication {query.indication.value}, using fallback search across all chunks")
            use_fallback = True
            # Get all chunks grouped by guideline (without indication filter)
            guideline_chunks = {}
            for i, chunk in enumerate(self.chunks_metadata):
                if chunk.guideline_id not in guideline_chunks:
                    guideline_chunks[chunk.guideline_id] = []
                guideline_chunks[chunk.guideline_id].append(i)
        
        if not guideline_chunks:
            return RAGResponse(
                query=search_text,
                results=[],
                total_chunks_searched=0,
                execution_time_ms=(time.time() - start_time) * 1000,
                metadata={"warning": f"No guidelines available for indication {query.indication.value}"} if use_fallback else None
            )
        
        # Search for top_k chunks from EACH guideline
        all_results = []
        total_chunks_searched = 0
        
        for guideline_id, chunk_indices in guideline_chunks.items():
            # Search in FAISS index with more candidates for post-filtering per guideline
            search_k = min(top_k * 3, len(chunk_indices))  # Get more candidates per guideline
            
            # Get all scores for this guideline's chunks
            guideline_results = []
            
            if search_k > 0:
                scores, indices = self.index.search(query_embedding.astype('float32'), self.index.ntotal)
                
                # Filter to only this guideline's chunks and apply negative scoring
                for score, idx in zip(scores[0], indices[0]):
                    if idx in chunk_indices:
                        chunk = self.chunks_metadata[idx]
                        
                        # Apply negative scoring for opposite indication terms
                        adjusted_score = self._apply_negative_scoring(chunk.snippet, negative_terms, float(score))
                        
                        result = RAGResult(
                            chunk_id=chunk.chunk_id,
                            guideline_id=chunk.guideline_id,
                            section_path=chunk.section_path,
                            page=chunk.page,
                            snippet=chunk.snippet,
                            score=adjusted_score,
                            metadata=chunk.metadata
                        )
                        
                        guideline_results.append(result)
                
                # Sort this guideline's results by score and take top_k
                guideline_results.sort(key=lambda x: x.score, reverse=True)
                all_results.extend(guideline_results[:top_k])
                
                total_chunks_searched += len(chunk_indices)
                
                print(f"📋 {guideline_id}: {len(guideline_results[:top_k])} von {len(chunk_indices)} Chunks")
        
        # Final sort by score across all guidelines (optional - maintains per-guideline diversity)
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        # Search for top 3 dosing tables in parallel
        dosing_tables = self._search_dosing_tables(query)
        
        execution_time = (time.time() - start_time) * 1000
        
        print(f"🔍 Gesamt: {len(all_results)} Chunks aus {len(guideline_chunks)} Leitlinien + {len(dosing_tables)} Dosing Tables")
        
        # Prepare metadata with warnings if needed
        response_metadata = {}
        if use_fallback:
            response_metadata["warning"] = f"No specific guidelines found for {query.indication.value}. Showing general results."
            response_metadata["fallback_search"] = True
        
        return RAGResponse(
            query=search_text,
            results=all_results,
            dosing_tables=dosing_tables,
            total_chunks_searched=total_chunks_searched,
            execution_time_ms=execution_time,
            metadata=response_metadata if response_metadata else None
        )
    
    def _apply_negative_scoring(self, text: str, negative_terms: List[str], original_score: float) -> float:
        """Apply negative scoring for chunks containing opposite indication terms"""
        if not negative_terms:
            return original_score
        
        text_lower = text.lower()
        negative_count = 0
        
        for term in negative_terms:
            if term.lower() in text_lower:
                negative_count += 1
        
        # Reduce score based on negative term frequency
        # More negative terms = bigger penalty
        if negative_count > 0:
            penalty_factor = 0.8 ** negative_count  # Exponential penalty
            adjusted_score = original_score * penalty_factor
            print(f"⚠️ Negative terms found ({negative_count}): {original_score:.3f} → {adjusted_score:.3f}")
            return adjusted_score
        
        return original_score
    
    def _build_search_query(self, query: ClinicalQuery) -> str:
        """Build structured German search query from clinical parameters using MUST/SHOULD/BOOST/NEGATIVE pattern"""
        
        # MUST: Core context/filter - the main indication and severity
        must_parts = self._build_must_query(query)
        
        # SHOULD: Clinical specificities and risk factors
        should_parts = self._build_should_query(query)
        
        # BOOST: Therapy/dosage/table anchors
        boost_parts = self._build_boost_query()
        
        # NEGATIVE: Terms to avoid (opposite indication)
        negative_parts = self._build_negative_query(query)
        
        # Combine all parts with appropriate weighting
        # For embeddings, we concatenate with implicit importance through order and repetition
        query_parts = []
        
        # Add MUST parts (highest priority) - only once to avoid duplication
        if must_parts:
            query_parts.extend(must_parts)
        
        # Add SHOULD parts
        if should_parts:
            query_parts.extend(should_parts)
        
        # Add BOOST parts
        query_parts.extend(boost_parts)
        
        # Add free text if provided
        if query.free_text:
            query_parts.append(query.free_text)
        
        # Create negative context to reduce opposite indication matches
        # We'll handle this in the embedding similarity calculation instead
        final_query = " ".join(query_parts)
        
        # Debug logging for query structure
        print(f"🔍 Query Debug:")
        print(f"  MUST: {must_parts}")
        print(f"  SHOULD: {should_parts}")
        print(f"  BOOST: {boost_parts}...")  # Show first 10 boost terms
        print(f"  NEGATIVE: {negative_parts}")
        print(f"  FINAL: {final_query}...")  # Show first 200 chars
        
        return final_query
        print(f"  FINAL: {final_query[:200]}...")  # Show first 200 chars
        
        return final_query
    
    def _build_must_query(self, query: ClinicalQuery) -> List[str]:
        """Build MUST query parts - core context that MUST be present"""
        must_parts = []
        
        # Indication with synonyms
        indication_synonyms = {
            Indication.CAP: [
                "CAP", 
                "ambulant erworbene Pneumonie", 
                "community-acquired pneumonia",
                "Pneumonie ambulant"
            ],
            Indication.HAP: [
                "HAP", 
                "nosokomial erworbene Pneumonie", 
                "hospital-acquired pneumonia",
                "Pneumonie nosokomial"
            ],
            Indication.AECOPD: [
                "AECOPD",
                "Akute Exazerbation der COPD",
                "COPD Exazerbation",
                "chronisch obstruktive Lungenerkrankung",
                "COPD"
            ]
        }
        
        synonyms = indication_synonyms.get(query.indication, [str(query.indication)])
        must_parts.extend(synonyms)
        
        # Severity with synonyms
        severity_synonyms = {
            "LEICHT": ["leicht", "mild", "niedriggradig"],
            "MITTELSCHWER": ["mittelschwer", "moderat", "moderate", "mäßig"],
            "SCHWER": ["schwer", "severe", "hochgradig", "schwerwiegend"],
            "SEPTISCH": ["septisch", "Schock"]
        }
        
        severity_terms = severity_synonyms.get(query.severity, [query.severity])
        must_parts.extend(severity_terms)
        
        return must_parts
    
    def _build_should_query(self, query: ClinicalQuery) -> List[str]:
        """Build SHOULD query parts - clinical specificities and risk factors"""
        should_parts = []
        
        # Risk factors with comprehensive synonyms
        risk_factor_synonyms = {
            "ANTIBIOTISCHE_VORBEHANDLUNG": [
                "antibiotischer Vorbehandlung",
                "Antibiotika-Vortherapie", 
                "vorherige Antibiotika",
               
            ],
            "MRGN_VERDACHT": [
                "MRGN",
                "multiresistente Erreger",
                "MRE", 
                "ESBL",
                "Extended-Spectrum Beta-Lactamase",
                "multiresistente Bakterien"
               
            ],
            "MRSA_VERDACHT": [
                "MRSA",
                "methicillin-resistenter Staphylococcus aureus",
                "MRSA-Kolonisation",
                "methicillin-resistente Erreger",
                "Staphylococcus aureus resistent"
               
            ],
            "BEATMUNG": [
                "Beatmung",
                "mechanische Ventilation",
                "VAP",
                "ventilator-assoziierte Pneumonie",
                "invasive Beatmung"
               
            ],
            "KATHETER": [
                "Katheter",
                "ZVK",
                "zentraler Venenkatheter",
                "zentralvenös",
                "Gefäßzugang"
               
            ]
        }
        
        for risk in query.risk_factors:
            synonyms = risk_factor_synonyms.get(risk, [risk])
            should_parts.extend(synonyms)
        
        # Infection site with synonyms
        if query.infection_site:
            site_synonyms = {
                "LUNGE": [
                    "pulmonal", "respiratorisch", "Lunge", "Atemwege", 
                    "bronchial", "alveolär"
                ],
                "BLUT": [
                    "Bakteriämie", "Sepsis", "Blutstrominfektion", "BSI",
                    "systemisch", "hämatogen"
                ],
                "HARNTRAKT": [
                    "Harnwegsinfektion", "UTI", "Urogenital", "Zystitis",
                    "Pyelonephritis", "Harnwege"
                ]
            }
            synonyms = site_synonyms.get(query.infection_site, [query.infection_site])
            should_parts.extend(synonyms)
        
        # Suspected pathogens
        if query.suspected_pathogens:
            should_parts.extend(query.suspected_pathogens)
        
        return should_parts
    
    def _build_boost_query(self) -> List[str]:
        """Build BOOST query parts - therapy/dosage/table anchors"""
        boost_parts = [
            # Therapy anchors with synonyms
            "kalkulierte Initialtherapie",
            "empirisch",
            "initial",
            "Empfehlung",
            "Behandlung",
            "antibiotischen",
            "antimikrobiellen",
            "Therapie",
            "Therapieempfehlung",
            
            # Targeted therapy synonyms
            "Fokussierung",
            "Deeskalation",
       
            
            # Dosage anchors with variations
            "Dosierung",
            "Dosis", 
            "Tagesdosis",
            "Dosierungsempfehlung",
            "Dosierungsschema",
            
            # Table and reference anchors
            "Tabelle",
            "Tab.",
            "Übersicht",
            "Zusammenfassung",
            
            # Duration and monitoring
            "Therapiedauer",
            "Behandlungsdauer",
            "Monitoring",
            "Dauer der Behandlung"
        ]
        
        return boost_parts
    
    def _build_negative_query(self, query: ClinicalQuery) -> List[str]:
        """Build NEGATIVE query parts - terms to avoid (opposite indication synonyms)"""
        
        # Define all indication synonyms in a centralized way for easy extension
        indication_synonyms = {
            Indication.CAP: [
                "CAP", 
                "ambulant erworbene Pneumonie", 
                "community-acquired pneumonia",
                "Pneumonie ambulant",
                "ambulante Pneumonie"
            ],
            Indication.HAP: [
                "HAP", 
                "nosokomial erworbene Pneumonie", 
                "hospital-acquired pneumonia",
                "nosokomiale Pneumonie",
                "Krankenhaus-Pneumonie"
            ],
            Indication.AECOPD: [
                "AECOPD",
                "Akute Exazerbation der COPD",
                "COPD Exazerbation",
                "chronisch obstruktive Lungenerkrankung",
                "COPD"
            ]
        }
        
        negative_terms = []
        
        # For CAP: add HAP and AECOPD terms as negative
        if query.indication == Indication.CAP:
            negative_terms.extend(indication_synonyms[Indication.HAP])
            negative_terms.extend(indication_synonyms[Indication.AECOPD])
            
        # For HAP: add CAP and AECOPD terms as negative  
        elif query.indication == Indication.HAP:
            negative_terms.extend(indication_synonyms[Indication.CAP])
            negative_terms.extend(indication_synonyms[Indication.AECOPD])
            
        # For AECOPD: add CAP and HAP terms as negative
        elif query.indication == Indication.AECOPD:
            negative_terms.extend(indication_synonyms[Indication.CAP])
            negative_terms.extend(indication_synonyms[Indication.HAP])
        
        return negative_terms

    def _get_chunks_by_guideline_and_indication(self, indication: Indication) -> Dict[str, List[int]]:
        """Group chunk indices by guideline for the specified indication"""
        guideline_chunks = {}
        
        for i, chunk in enumerate(self.chunks_metadata):
            guideline = self.guidelines_metadata.get(chunk.guideline_id)
            if guideline and indication in guideline.indications:
                if chunk.guideline_id not in guideline_chunks:
                    guideline_chunks[chunk.guideline_id] = []
                guideline_chunks[chunk.guideline_id].append(i)
        
        return guideline_chunks
    
    def _filter_chunks_by_indication(self, indication: Indication) -> List[int]:
        """Filter chunk indices by indication"""
        valid_indices = []
        
        for i, chunk in enumerate(self.chunks_metadata):
            guideline = self.guidelines_metadata.get(chunk.guideline_id)
            if guideline and indication in guideline.indications:
                valid_indices.append(i)
        
        return valid_indices
    
    def _search_dosing_tables(self, query: ClinicalQuery, top_k: int = 5) -> List:
        """Search for relevant dosing tables based on clinical query"""
        if not self.dosing_tables or not self.dosing_index:
            return []
        
        try:
            # Build search query for dosing tables (focus on clinical context)
            search_text = self._build_dosing_search_query(query)
            
            # Get query embedding
            query_embedding = self.embedding_model.encode([search_text], convert_to_numpy=True)
            
            # Search in dosing index
            scores, indices = self.dosing_index.search(query_embedding.astype('float32'), min(top_k * 2, len(self.dosing_tables)))
            
            # Filter and score results based on clinical context matching
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.dosing_tables):
                    table = self.dosing_tables[idx]
                    
                    # Calculate clinical context match score
                    context_score = self._calculate_clinical_context_match(query, table.clinical_context)
                    
                    # Combine semantic similarity with clinical context matching
                    # For medical dosing tables, clinical context is MUCH MORE important than semantic similarity
                    combined_score = float(score) * 0.3 + context_score * 0.7
                    
                    # Additional penalties and boosts for specific scenarios
                    print(f"🔍 DEBUG - Before penalty check:")
                    print(f"   table.clinical_context: {table.clinical_context}")
                    print(f"   has indication: {table.clinical_context.get('indication')}")
                    print(f"   has table_name: {table.clinical_context.get('table_name')}")
                    
                    # Always process indication penalties, even if table_name is missing
                    query_indication = str(query.indication.value if hasattr(query.indication, 'value') else query.indication)
                    table_indication = table.clinical_context.get('indication')
                    table_name = table.clinical_context.get('table_name', 'NO_TABLE_NAME').lower()
                    
                    # Map query indication to expected values
                    query_indication_mapped = None
                    if 'nosokomial' in query_indication.lower() or 'hap' in query_indication.lower():
                        query_indication_mapped = 'HAP'
                    elif 'ambulant' in query_indication.lower() or 'cap' in query_indication.lower():
                        query_indication_mapped = 'CAP'
                    elif ('aecopd' in query_indication.lower() or 'copd' in query_indication.lower() or 
                          'akute_exazerbation' in query_indication.lower()):
                        query_indication_mapped = 'AECOPD'
                    
                    print(f"🎯 PENALTY CHECK - Query: {query_indication} → Mapped: {query_indication_mapped}, Table: {table_indication}")
                    
                    # Define available indications (should match frontend options)
                    available_indications = ['CAP', 'HAP', 'AECOPD']  # Added AECOPD
                    
                    # Penalty system
                    if table_indication is None:
                        print(f"🚫 NO INDICATION in table - Heavy penalty by 0.05x")
                        combined_score *= 0.05  # Heavy penalty for tables without indication
                    elif query_indication_mapped == table_indication:
                        print(f"✅ PERFECT MATCH - Boosting score by 1.3x")
                        combined_score *= 1.3
                    elif table_indication in available_indications:
                        print(f"❌ WRONG INDICATION - Penalizing score by 0.1x")
                        combined_score *= 0.1  # Heavy penalty for wrong indication
                    else:
                        print(f"🚫 UNSUPPORTED INDICATION - Penalizing score by 0.05x")
                        combined_score *= 0.05  # Even heavier penalty for unsupported indications
                    
                    # Handle "ohne/mit" risk factor scenarios
                    if query.risk_factors and table_name != 'no_table_name':
                        has_ohne = any(word in table_name for word in ['ohne', 'kein', 'keine', 'nicht'])
                        has_mit = any(word in table_name for word in ['mit', 'für', 'bei', 'risikofaktoren'])
                        print(f"🎲 RISK FACTORS - has_ohne: {has_ohne}, has_mit: {has_mit}")
                        
                        if has_ohne:
                            print(f"⬇️ OHNE penalty - score *= 0.2")
                            combined_score *= 0.2  # Heavy penalty for "ohne" when risk factors present
                        elif has_mit:
                            print(f"⬆️ MIT boost - score *= 1.4")
                            combined_score *= 1.4  # Boost for "mit" when risk factors present
                    
                    print(f"📊 FINAL SCORE: {combined_score}")
                    print("=" * 50)
                    
                    # Create result with combined score
                    result_table = DosingTable(
                        table_id=table.table_id,
                        table_name=table.table_name,
                        table_html=table.table_html,
                        score=combined_score,
                        clinical_context=table.clinical_context
                    )
                    results.append(result_table)
            
            # Sort by combined score and return top_k
            results.sort(key=lambda x: x.score, reverse=True)
            final_results = results[:top_k]
            
            if final_results:
                print(f"💊 Found {len(final_results)} dosing tables:")
                for table in final_results:
                    print(f"  - {table.table_name[:60]}... (score: {table.score:.3f})")
            
            return final_results
            
        except Exception as e:
            print(f"Error searching dosing tables: {e}")
            return []
    
    def _build_dosing_search_query(self, query: ClinicalQuery) -> str:
        """Build search query specifically for dosing tables"""
        query_parts = []
        
        # Add indication
        if query.indication:
            query_parts.append(str(query.indication.value if hasattr(query.indication, 'value') else query.indication))
        
        # Add severity
        if query.severity:
            query_parts.append(query.severity)
        
        # Add infection site
        if query.infection_site:
            query_parts.append(query.infection_site)
        
        # Add therapy-specific terms
        therapy_terms = [
            "Therapieempfehlung", "Initialtherapie", "Dosierung", 
            "Antibiotika", "Therapie", "Behandlung"
        ]
        query_parts.extend(therapy_terms)
        
        # Add free text if provided
        if query.free_text:
            query_parts.append(query.free_text)
        
        return " ".join(query_parts)
    
    def _calculate_clinical_context_match(self, query: ClinicalQuery, table_context: Dict) -> float:
        """Calculate how well the table's clinical context matches the query with improved weighting"""
        if not table_context:
            return 0.0
        
        score = 0.0
        max_score = 0.0
        
        # INDICATION - HIGHEST PRIORITY (60% weight - increased!)
        max_score += 0.6
        if table_context.get('indication'):
            query_indication = str(query.indication.value if hasattr(query.indication, 'value') else query.indication)
            table_indication = table_context['indication'].lower()
            query_indication_lower = query_indication.lower()
            
            # Perfect match for specific indication types
            if table_indication == query_indication_lower:
                score += 0.6  # Perfect match
            elif query_indication_lower in table_indication or table_indication in query_indication_lower:
                score += 0.45  # Strong partial match
           
        
        # RISK FACTORS - HIGH PRIORITY (25% weight) with intelligent "ohne/mit" handling
        max_score += 0.25
        if table_context.get('table_name') or table_context.get('keywords'):
            table_name = table_context.get('table_name', '').lower()
            table_keywords = [kw.lower() for kw in table_context.get('keywords', [])]
            
            if query.risk_factors:
                # Check if table explicitly mentions "ohne Risikofaktoren" or similar
                has_ohne_keywords = any(word in table_name for word in ['ohne', 'kein', 'keine', 'nicht'])
                has_mit_keywords = any(word in table_name for word in ['mit', 'für', 'bei'])
                
                risk_factor_matches = 0
                total_risk_factors = len(query.risk_factors)
                
                # Check each risk factor against table content
                for risk_factor in query.risk_factors:
                    risk_lower = risk_factor.lower()
                    
                    # Check in table name and keywords
                    found_in_name = any(term in table_name for term in risk_lower.split())
                    found_in_keywords = any(any(term in keyword for term in risk_lower.split()) for keyword in table_keywords)
                    
                    if found_in_name or found_in_keywords:
                        risk_factor_matches += 1
                
                # Calculate base risk score
                if total_risk_factors > 0:
                    risk_score = (risk_factor_matches / total_risk_factors) * 0.25
                    
                    # Apply intelligent modifiers
                    if has_ohne_keywords and risk_factor_matches > 0:
                        # Table says "ohne" but we have risk factors -> heavy penalty
                        risk_score *= 0.05
                    elif has_mit_keywords and risk_factor_matches > 0:
                        # Table says "mit" and we have matching risk factors -> boost
                        risk_score *= 1.8
                    elif not has_ohne_keywords and not has_mit_keywords and risk_factor_matches > 0:
                        # Neutral table with risk factor matches -> moderate boost
                        risk_score *= 1.3
                    
                    score += min(risk_score, 0.25)  # Cap at max possible score
            else:
                # No risk factors in query
                if any(word in table_name for word in ['ohne', 'kein', 'keine']):
                    score += 0.15  # Credit for "ohne" tables when no risk factors specified
        
        # SEVERITY - MEDIUM PRIORITY (10% weight - reduced)
        max_score += 0.10
        if table_context.get('severity') and query.severity:
            table_severity = table_context['severity'].lower()
            query_severity = query.severity.lower()
            
            if table_severity == query_severity:
                score += 0.10
            elif any(term in table_severity for term in query_severity.split()) or any(term in query_severity for term in table_severity.split()):
                score += 0.05
        
        # INFECTION SITE - LOW PRIORITY (5% weight)
        max_score += 0.05
        if table_context.get('infection_site') and query.infection_site:
            table_site = table_context['infection_site'].lower()
            query_site = query.infection_site.lower()
            
            if table_site == query_site:
                score += 0.05
            elif any(term in table_site for term in query_site.split()) or any(term in query_site for term in table_site.split()):
                score += 0.025
        
        # Normalize score
        return score / max_score if max_score > 0 else 0.0
    
    def _save_index(self):
        """Save FAISS index to disk"""
        if self.index is not None:
            index_path = self.embeddings_dir / "faiss_index.bin"
            faiss.write_index(self.index, str(index_path))
    
    def _save_metadata(self):
        """Save metadata to disk"""
        # Save chunks metadata
        chunks_path = self.embeddings_dir / "chunks_metadata.pkl"
        with open(chunks_path, 'wb') as f:
            pickle.dump(self.chunks_metadata, f)
        
        # Save guidelines metadata
        guidelines_path = self.embeddings_dir / "guidelines_metadata.json"
        with open(guidelines_path, 'w', encoding='utf-8') as f:
            # Convert to dict for JSON serialization
            guidelines_dict = {}
            for guid_id, metadata in self.guidelines_metadata.items():
                guidelines_dict[guid_id] = metadata.model_dump()
            json.dump(guidelines_dict, f, ensure_ascii=False, indent=2)
    
    def _load_index(self):
        """Load existing FAISS index and metadata"""
        try:
            # Load FAISS index
            index_path = self.embeddings_dir / "faiss_index.bin"
            if index_path.exists():
                self.index = faiss.read_index(str(index_path))
                print(f"Loaded FAISS index with {self.index.ntotal} vectors")
            
            # Load chunks metadata
            chunks_path = self.embeddings_dir / "chunks_metadata.pkl"
            if chunks_path.exists():
                with open(chunks_path, 'rb') as f:
                    self.chunks_metadata = pickle.load(f)
                print(f"Loaded {len(self.chunks_metadata)} chunk metadata entries")
            
            # Load guidelines metadata
            guidelines_path = self.embeddings_dir / "guidelines_metadata.json"
            if guidelines_path.exists():
                with open(guidelines_path, 'r', encoding='utf-8') as f:
                    guidelines_dict = json.load(f)
                    self.guidelines_metadata = {}
                    for guid_id, data in guidelines_dict.items():
                        self.guidelines_metadata[guid_id] = GuidelineMetadata(**data)
                print(f"Loaded {len(self.guidelines_metadata)} guideline metadata entries")
                
        except Exception as e:
            print(f"Error loading existing index: {e}")
            # Reset to empty state
            self.index = None
            self.chunks_metadata = []
            self.guidelines_metadata = {}
        
        # Also try to load dosing tables index
        self._load_dosing_index()
    
    def delete_guideline(self, guideline_id: str) -> Dict:
        """Delete a specific guideline and its associated data"""
        try:
            if guideline_id not in self.guidelines_metadata:
                return {
                    "success": False,
                    "message": f"Guideline '{guideline_id}' not found"
                }
            
            # Remove chunks associated with this guideline
            original_chunk_count = len(self.chunks_metadata)
            self.chunks_metadata = [
                chunk for chunk in self.chunks_metadata 
                if chunk.guideline_id != guideline_id
            ]
            removed_chunks = original_chunk_count - len(self.chunks_metadata)
            
            # Remove guideline metadata
            del self.guidelines_metadata[guideline_id]
            
            # Remove guideline file
            for ext in ['.md', '.txt']:
                file_path = self.guidelines_dir / f"{guideline_id}{ext}"
                if file_path.exists():
                    file_path.unlink()
                    break
            
            # Rebuild the index with remaining chunks
            self._rebuild_index()
            
            return {
                "success": True,
                "message": f"Successfully deleted guideline '{guideline_id}'",
                "removed_chunks": removed_chunks
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error deleting guideline: {str(e)}"
            }
    
    def delete_all_data(self) -> Dict:
        """Delete all guidelines and embeddings"""
        try:
            # Clear all in-memory data
            self.chunks_metadata = []
            self.guidelines_metadata = {}
            self.index = None
            
            # Remove all files
            import shutil
            
            # Remove all guideline files
            if self.guidelines_dir.exists():
                shutil.rmtree(self.guidelines_dir)
                self.guidelines_dir.mkdir(exist_ok=True)
            
            # Remove all embedding files
            if self.embeddings_dir.exists():
                shutil.rmtree(self.embeddings_dir)
                self.embeddings_dir.mkdir(exist_ok=True)
            
            return {
                "success": True,
                "message": "Successfully deleted all guidelines and embeddings"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error deleting all data: {str(e)}"
            }
    
    def _rebuild_index(self):
        """Rebuild FAISS index with current chunks"""
        try:
            if not self.chunks_metadata:
                self.index = None
                self._save_index()
                self._save_metadata()
                return
            
            # Generate embeddings for all remaining chunks
            chunk_texts = [chunk.snippet for chunk in self.chunks_metadata]
            embeddings = self.embedding_model.encode(chunk_texts, convert_to_numpy=True)
            
            # Create new index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(embeddings.astype('float32'))
            
            # Save updated index and metadata
            self._save_index()
            self._save_metadata()
            
            print(f"Index rebuilt with {len(self.chunks_metadata)} chunks")
            
        except Exception as e:
            print(f"Error rebuilding index: {e}")
            self.index = None
    
    def _load_dosing_tables(self):
        """Load dosing tables from bundled markdown file"""
        dosing_file_path = self.data_dir / "dose_info" / "dosis_tabellen.md"
        
        # Check if the dosing tables file exists
        if not dosing_file_path.exists():
            print(f"⚠️ Dosing tables file not found: {dosing_file_path}")
            return
        
        try:
            # Read the dosing tables file
            with open(dosing_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse tables from the markdown content
            tables = self._parse_dosing_tables(content)
            
            if tables:
                # Process and embed the table names
                self._process_dosing_tables(tables)
                print(f"✅ Loaded {len(tables)} dosing tables")
            else:
                print("⚠️ No dosing tables found in file")
                
        except Exception as e:
            print(f"❌ Error loading dosing tables: {e}")
    
    def _parse_dosing_tables(self, content: str) -> List[Dict]:
        """Parse dosing tables from markdown content"""
        tables = []
        
        # Split content by table headers - improved pattern
        # Look for lines starting with # followed by "Tabelle" and capture everything until next # or end
        pattern = r'^# (Tabelle[^\n]+)\n'
        table_headers = re.finditer(pattern, content, re.MULTILINE)
        
        header_positions = []
        for match in table_headers:
            header_positions.append({
                'start': match.start(),
                'end': match.end(),
                'name': match.group(1).strip()
            })
        
        # Extract content for each table
        for i, header in enumerate(header_positions):
            table_name = header['name']
            
            # Get content from end of header to start of next header (or end of file)
            content_start = header['end']
            content_end = header_positions[i + 1]['start'] if i + 1 < len(header_positions) else len(content)
            
            table_content = content[content_start:content_end].strip()
            
            # Extract HTML table from this section
            table_match = re.search(r'<table[^>]*>.*?</table>', table_content, re.DOTALL)
            if table_match:
                table_html = table_match.group(0)
                
                # Clean up HTML for LLM consumption
                llm_optimized_html = self._optimize_table_for_llm(table_html)
                
                # Extract clinical context from table name
                clinical_context = self._extract_clinical_context_from_name(table_name)
                
                table_data = {
                    'table_id': f"dosing_table_{len(tables) + 1:02d}",
                    'table_name': table_name,
                    'table_html': llm_optimized_html,
                    'clinical_context': clinical_context
                }
                tables.append(table_data)
        
        return tables
    
    def _optimize_table_for_llm(self, html_table: str) -> str:
        """Optimize HTML table for LLM consumption with better formatting"""
        # Clean up HTML for better LLM readability
        cleaned = html_table
        
        # Convert to more readable format while preserving structure
        cleaned = re.sub(r'<tbody>', '', cleaned)
        cleaned = re.sub(r'</tbody>', '', cleaned)
        cleaned = re.sub(r'<tr>', '\n| ', cleaned)
        cleaned = re.sub(r'</tr>', ' |', cleaned)
        cleaned = re.sub(r'<td[^>]*>', '', cleaned)
        cleaned = re.sub(r'</td>', ' | ', cleaned)
        cleaned = re.sub(r'<th[^>]*>', '**', cleaned)
        cleaned = re.sub(r'</th>', '** | ', cleaned)
        
        # Clean up multiple spaces and pipes
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\|\s*\|', '|', cleaned)
        cleaned = cleaned.strip()
        
        # Add table markers for LLM
        formatted_table = f"""
DOSING TABLE (LLM Format):
{cleaned}
END OF DOSING TABLE
"""
        return formatted_table.strip()
    
    def _extract_clinical_context_from_name(self, table_name: str) -> Dict:
        """Extract clinical context (indication, severity, infection_site) from table name"""
        context = {
            'indication': None,
            'severity': None,
            'infection_site': None,
            'keywords': [],
            'table_name': table_name  # Add the original table name for better matching
        }
        
        name_lower = table_name.lower()
        
        # Define all possible indications in one place for flexible system
        # This list should match the available indications in the frontend
        indication_patterns = {
            'CAP': ['cap', 'ambulant', 'community-acquired'],
            'HAP': ['hap', 'nosokomial', 'hospital-acquired'],
            'AECOPD': ['aecopd', 'copd'],
            # Future indications can be easily added here
        }
        
        # Extract indication using flexible pattern matching
        for indication_key, patterns in indication_patterns.items():
            if any(term in name_lower for term in patterns):
                context['indication'] = indication_key
                break  # Take first match
        
        # Extract severity
        if any(term in name_lower for term in ['leicht', 'mild']):
            context['severity'] = 'LEICHT'
        elif any(term in name_lower for term in ['mittelschwer', 'moderat']):
            context['severity'] = 'MITTELSCHWER'
        elif any(term in name_lower for term in ['schwer', 'severe']):
            context['severity'] = 'SCHWER'
        elif any(term in name_lower for term in ['septisch', 'septic', 'schock']):
            context['severity'] = 'SEPTISCH'
        
        # Extract infection site
        if any(term in name_lower for term in ['pneumonie', 'lunge', 'respiratorisch']):
            context['infection_site'] = 'LUNGE'
        elif any(term in name_lower for term in ['harnweg', 'uti', 'urogenital']):
            context['infection_site'] = 'HARNTRAKT'
        elif any(term in name_lower for term in ['bakteriämie', 'sepsis', 'blut']):
            context['infection_site'] = 'BLUT'
        
        # Extract additional keywords for matching
        keywords = []
        keyword_patterns = [
            'initialtherapie', 'antibiotika', 'therapie', 'behandlung',
            'hospitalisiert', 'intensiv', 'beatmung', 'risiko'
        ]
        
        for keyword in keyword_patterns:
            if keyword in name_lower:
                keywords.append(keyword)
        
        context['keywords'] = keywords
        
        return context
    
    def _process_dosing_tables(self, tables_data: List[Dict]):
        """Process and embed dosing table names for semantic search"""
        if not tables_data:
            return
        
        # Create DosingTable objects
        self.dosing_tables = []
        table_names = []
        
        for table_data in tables_data:
            dosing_table = DosingTable(
                table_id=table_data['table_id'],
                table_name=table_data['table_name'],
                table_html=table_data['table_html'],
                score=0.0,  # Will be set during search
                clinical_context=table_data['clinical_context']
            )
            self.dosing_tables.append(dosing_table)
            table_names.append(table_data['table_name'])
        
        # Generate embeddings for table names
        if table_names:
            embeddings = self.embedding_model.encode(table_names, convert_to_numpy=True)
            
            # Create separate FAISS index for dosing tables
            dimension = embeddings.shape[1]
            self.dosing_index = faiss.IndexFlatIP(dimension)
            self.dosing_index.add(embeddings.astype('float32'))
            
            # Save dosing index and metadata
            self._save_dosing_index()
            
            print(f"✅ Created embeddings for {len(table_names)} dosing table names")
    
    def _save_dosing_index(self):
        """Save dosing tables FAISS index and metadata"""
        try:
            if self.dosing_index is not None:
                faiss.write_index(self.dosing_index, str(self.dosing_embeddings_path))
            
            # Save dosing table metadata
            dosing_data = []
            for table in self.dosing_tables:
                dosing_data.append(table.model_dump())
            
            with open(self.dosing_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(dosing_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error saving dosing index: {e}")
    
    def _load_dosing_index(self):
        """Load existing dosing tables index and metadata"""
        try:
            # Load dosing index
            if self.dosing_embeddings_path.exists():
                self.dosing_index = faiss.read_index(str(self.dosing_embeddings_path))
                print(f"Loaded dosing index with {self.dosing_index.ntotal} table embeddings")
            
            # Load dosing metadata
            if self.dosing_metadata_path.exists():
                with open(self.dosing_metadata_path, 'r', encoding='utf-8') as f:
                    dosing_data = json.load(f)
                    self.dosing_tables = [DosingTable(**data) for data in dosing_data]
                print(f"Loaded {len(self.dosing_tables)} dosing table metadata entries")
                
        except Exception as e:
            print(f"Error loading dosing index: {e}")
            self.dosing_index = None
            self.dosing_tables = []

    def get_stats(self) -> Dict:
        """Get current statistics"""
        chunk_types = {}
        page_counts = {}
        
        for chunk in self.chunks_metadata:
            chunk_type = chunk.metadata.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            if chunk.page:
                guideline_id = chunk.guideline_id
                page_counts[guideline_id] = max(page_counts.get(guideline_id, 0), chunk.page)
        
        return {
            "total_guidelines": len(self.guidelines_metadata),
            "total_chunks": len(self.chunks_metadata),
            "index_size": self.index.ntotal if self.index else 0,
            "chunk_types": chunk_types,
            "page_counts": page_counts,
            "guidelines": [
                {
                    "id": guid_id,
                    "title": metadata.title,
                    "indications": [ind.value for ind in metadata.indications],
                    "pages": page_counts.get(guid_id, 0)
                }
                for guid_id, metadata in self.guidelines_metadata.items()
            ]
        }

# Alias for backward compatibility
RAGService = AdvancedRAGService