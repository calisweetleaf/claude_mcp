#!/usr/bin/env python3
"""
Claude-Optimized Memory System - Fixed Implementation
=====================================

This is the "heart" of our MCP server - providing persistent memory, cross-session 
intelligence, and semantic understanding that enables true collaboration with Claude.
"""

import sys
import os
import logging
import sqlite3
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class ClaudeMemorySystem:
    """
    Complete memory system optimized for Claude's reasoning capabilities
    Combines memory storage, interconnection, and intelligent retrieval
    """
    
    def __init__(self, data_dir: str = "data"):
        self.logger = logging.getLogger(__name__)
        
        # Setup data directory
        self.data_dir = Path(data_dir)
        self.memory_dir = self.data_dir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Database file
        self.memory_db = self.memory_dir / "claude_memories.db"
        
        # Initialize database
        self._init_database()
        
        # Memory categories with Claude-optimized importance weights
        self.categories = {
            'insight': 0.95,      # High value for Claude's reasoning
            'decision': 0.90,     # Critical for tracking choices
            'pattern': 0.85,      # Claude excels at pattern recognition
            'solution': 0.80,     # Problem solutions are valuable
            'architecture': 0.75,  # System design insights
            'learning': 0.70,     # New knowledge acquired
            'context': 0.60,      # Situational information
            'fact': 0.50,         # Basic factual information
            'note': 0.40,         # General notes
            'temp': 0.20          # Temporary information
        }
        
        # Concept extraction patterns optimized for development
        self.concept_patterns = {
            'technical_terms': r'\b[a-zA-Z]+[A-Z][a-zA-Z]*\b|\b[a-z]+_[a-z_]+\b|\b[A-Z_]{2,}\b',
            'file_paths': r'\b[\w/\\.-]+\.(?:py|js|ts|json|md|txt|yml|yaml|toml|cfg|html|css)\b',
            'function_names': r'\b[a-z_][a-z0-9_]*(?=\s*\()',
            'quoted_terms': r'["\']([^"\']{3,30})["\']',
            'urls': r'https?://[^\s]+',
            'code_blocks': r'`([^`]+)`',
            'variables': r'\$[a-zA-Z_][a-zA-Z0-9_]*|\b[a-z_][a-z0-9_]*\s*[=:]',
        }
        
        
        self.logger.info(f"Claude Memory System initialized. DB: {self.memory_db}")
    
    def _init_database(self):
        """Initialize SQLite database with optimized schema"""
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS memories (
                        memory_key TEXT PRIMARY KEY,
                        content TEXT,
                        category TEXT,
                        importance REAL,
                        tags TEXT,
                        context TEXT,
                        project_context TEXT,
                        semantic_keywords TEXT,
                        content_hash TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        access_count INTEGER DEFAULT 0
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS concepts (
                        concept TEXT PRIMARY KEY,
                        memory_ids TEXT,
                        frequency INTEGER DEFAULT 1
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS memory_relationships (
                        memory_a TEXT,
                        memory_b TEXT,
                        relationship_type TEXT,
                        strength REAL,
                        PRIMARY KEY (memory_a, memory_b, relationship_type)
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE,
                        session_title TEXT,
                        session_metadata TEXT
                    )
                ''')

                # Indexes for memories table
                conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_content_hash ON memories(content_hash)')

                # Indexes for concepts table
                conn.execute('CREATE INDEX IF NOT EXISTS idx_concepts_frequency ON concepts(frequency)')

                # Indexes for memory_relationships table
                conn.execute('CREATE INDEX IF NOT EXISTS idx_relationships_strength ON memory_relationships(strength)')

                # Indexes for sessions table
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity)')

                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text using Claude-optimized patterns"""
        if not text or not isinstance(text, str) or not text.strip():
            return []

        concepts = set()
        
        # Extract using each pattern
        for pattern_name, pattern in self.concept_patterns.items():
            try:
                # Ensure pattern is a string before compiling
                if not isinstance(pattern, str):
                    self.logger.warning(f"Pattern {pattern_name} is not a string, skipping.")
                    continue

                compiled_pattern = re.compile(pattern, re.IGNORECASE)
                matches = compiled_pattern.findall(text)

                if matches:
                    if isinstance(matches[0], tuple): # Handle patterns that return tuples (e.g. from capturing groups)
                        for match_tuple in matches:
                            concepts.update(m_item for m_item in match_tuple if m_item and isinstance(m_item, str) and m_item.strip())
                    else: # Handle patterns that return a list of strings
                        concepts.update(m for m in matches if isinstance(m, str) and m.strip())
            except re.error as e:
                self.logger.warning(f"Regex error for pattern {pattern_name}: {e}. Skipping pattern.")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error processing pattern {pattern_name}: {e}. Skipping pattern.")
                continue
        
        # Extract meaningful phrases (2-3 words)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        if len(words) > 1:
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                if len(phrase) > 6 and not any(common in phrase.lower() for common in ['the ', 'and ', 'but ', 'for ', 'with ']):
                    concepts.add(phrase)
        
        # Filter out noise
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'is', 'are', 'was', 'were'}
        filtered_concepts = []
        for concept in concepts:
            concept = concept.strip()
            if (len(concept) >= 3 and 
                concept.lower() not in common_words and 
                not concept.isdigit() and
                len(set(concept)) > 1):
                filtered_concepts.append(concept)
        
        if not concepts: # if after all pattern matching, concepts is still empty
            return []

        return list(set(filtered_concepts))[:25]  # Limit to top 25 concepts
    
    def _calculate_relevance(self, query_concepts: List[str], memory_concepts: List[str]) -> float:
        """Calculate relevance score between query concepts and memory concepts (Jaccard Index)."""
        if not query_concepts or not memory_concepts:
            return 0.0

        set_query = set(query_concepts)
        set_memory = set(memory_concepts)

        if not set_memory: # Handles case where memory_concepts might be empty list after set conversion
            return 0.0

        intersection = set_query.intersection(set_memory)
        union = set_query.union(set_memory)

        if not union: # Avoid division by zero if both lists were empty (though caught by earlier checks)
            return 0.0

        return float(len(intersection)) / float(len(union))

    def _calculate_importance(self, content: str, category: str, tags: Optional[List[str]] = None) -> float:
        """Calculate importance score using Claude-optimized factors"""
        importance = self.categories.get(category, 0.5)
        
        # Content length factor
        length_bonus = min(len(content) / 500, 0.15)
        importance += length_bonus
        
        # Technical content indicators
        tech_indicators = [
            'error', 'bug', 'fix', 'solution', 'optimize', 'performance',
            'architecture', 'design', 'pattern', 'algorithm', 'implementation',
            'debug', 'issue', 'problem', 'resolve', 'discovered', 'learned'
        ]
        tech_score = sum(0.05 for indicator in tech_indicators if indicator in content.lower())
        importance += min(tech_score, 0.25)
        
        # Decision/insight indicators
        insight_indicators = [
            'decided', 'realized', 'understood', 'insight', 'breakthrough',
            'important', 'critical', 'key', 'significant', 'major'
        ]
        insight_score = sum(0.08 for indicator in insight_indicators if indicator in content.lower())
        importance += min(insight_score, 0.20)
        
        # Tag-based importance boost
        if tags:
            important_tags = ['critical', 'important', 'breakthrough', 'architecture', 'security']
            tag_boost = sum(0.1 for tag in tags if tag.lower() in important_tags)
            importance += min(tag_boost, 0.15)
        
        return min(importance, 1.0)
    
    def _create_content_hash(self, content: str) -> str:
        """Create hash for content deduplication"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def _find_related_memories(self, concepts: List[str], exclude_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find memories related to given concepts"""
        if not concepts:
            return []
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                related = []
                for concept in concepts[:10]: # Limit number of concepts to check for performance
                    cursor = conn.execute('SELECT memory_ids FROM concepts WHERE concept = ?', (concept,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        memory_ids = row[0].split(',')
                        for mem_id in memory_ids:
                            if exclude_key and mem_id == exclude_key:
                                continue
                            # Ensure we don't add too many, and avoid re-fetching if already added
                            if len(related) < 15 and not any(r['memory_key'] == mem_id for r in related):
                                mem_cursor = conn.execute('SELECT memory_key, content, importance FROM memories WHERE memory_key = ?', (mem_id,))
                                mem_row = mem_cursor.fetchone()
                                if mem_row:
                                    related.append({
                                        'memory_key': mem_row[0],
                                        'content_preview': mem_row[1][:60] + ('...' if len(mem_row[1]) > 60 else ''),
                                        'importance': mem_row[2]
                                    })
                # Remove duplicates and sort by importance
                seen_keys = set()
                unique_related = []
                for item in related:
                    if item['memory_key'] not in seen_keys:
                        unique_related.append(item)
                        seen_keys.add(item['memory_key'])
                return sorted(unique_related, key=lambda x: x['importance'], reverse=True)[:8] # Return top 8
        except Exception as e:
            self.logger.error(f"Error finding related memories: {e}")
            return []
    
    def _update_concept_index(self, concepts: List[str], memory_key: str):
        """Update concept index with new memory"""
        if not concepts:
            return
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                for concept in concepts:
                    # Check if concept exists
                    cursor = conn.execute('SELECT memory_ids, frequency FROM concepts WHERE concept = ?', (concept,))
                    result = cursor.fetchone()
                    if result:
                        memory_ids_str, frequency = result
                        memory_ids = memory_ids_str.split(',') if memory_ids_str else []
                        if memory_key not in memory_ids:
                            memory_ids.append(memory_key)
                            conn.execute('UPDATE concepts SET memory_ids = ?, frequency = ? WHERE concept = ?',
                                         (','.join(memory_ids), len(memory_ids), concept))
                        else: # If memory_key already in list, no change to memory_ids, but ensure frequency is updated if somehow it's off
                            conn.execute('UPDATE concepts SET frequency = ? WHERE concept = ?', (len(memory_ids), concept))

                    else:
                        conn.execute('INSERT INTO concepts (concept, memory_ids, frequency) VALUES (?, ?, ?)', (concept, memory_key, 1))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating concept index: {e}")
    
    def _create_memory_relationships(self, memory_key: str, related_memories: List[Dict[str, Any]]):
        """Create relationships between memories based on shared concepts or other criteria"""
        if not related_memories:
            return
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                for related in related_memories[:5]:  # Limit number of relationships created per store
                    related_key = related['memory_key']
                    if memory_key == related_key: # Don't create relationship with self
                        continue

                    # Example: Simple semantic relationship based on being found through common concepts
                    # Strength could be based on importance of related memory or number of shared concepts
                    strength = min(related.get('importance', 0.1) * 0.5 + 0.3, 1.0)
                    
                    # Insert relationship (both directions for easier querying)
                    conn.execute('''
                        INSERT OR REPLACE INTO memory_relationships 
                        (memory_a, memory_b, relationship_type, strength)
                        VALUES (?, ?, 'semantic', ?)
                    ''', (memory_key, related_key, strength))
                    
                    conn.execute('''
                        INSERT OR REPLACE INTO memory_relationships 
                        (memory_a, memory_b, relationship_type, strength)
                        VALUES (?, ?, 'semantic', ?)
                    ''', (related_key, memory_key, strength))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error creating memory relationships: {e}")
    
    # ===== MCP TOOL METHODS =====
    
    def bb7_memory_store(self, arguments: Dict[str, Any]) -> str:
        """Store information in persistent memory with intelligent categorization and semantic indexing"""
        content = arguments.get('content', '')
        category = arguments.get('category', 'note')
        tags = arguments.get('tags', [])
        context = arguments.get('context', '')
        memory_key = arguments.get('memory_key', '')
        importance = arguments.get('importance', None)
        
        if not content:
            return "Please provide content to store. Example: {'content': 'Discovered async improves performance'}"
        
        try:
            # Generate memory key if not provided
            if not memory_key:
                content_hash_short = self._create_content_hash(content)[:8] # Shorten for key
                timestamp = int(time.time())
                memory_key = f"{category}_{timestamp}_{content_hash_short}"
            
            # Validate category
            if category not in self.categories:
                self.logger.warning(f"Category '{category}' not in defined list. Defaulting to 'note'.")
                category = 'note'
            
            # Ensure tags is a list
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            elif not isinstance(tags, list):
                self.logger.warning(f"Tags field was not a list or string. Defaulting to empty list. Received: {tags}")
                tags = []
            
            # Calculate importance if not provided
            if importance is None:
                importance = self._calculate_importance(content, category, tags)
            else:
                try:
                    importance = max(0.0, min(1.0, float(importance)))
                except ValueError:
                    self.logger.warning(f"Invalid importance value. Using default calculation. Received: {importance}")
                    importance = self._calculate_importance(content, category, tags)

            # Extract concepts for semantic indexing
            concepts = self._extract_concepts(content)
            
            # Get current project context
            try:
                project_context = str(Path.cwd())
            except Exception: # Path.cwd() can fail in some restricted environments
                project_context = "unknown_project"

            # Find related memories BEFORE storing the current one
            related_memories = self._find_related_memories(concepts, exclude_key=memory_key)
            
            # Create content hash for deduplication (full hash for storage)
            content_hash_full = self._create_content_hash(content)
            
            # Store in database
            with sqlite3.connect(str(self.memory_db)) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO memories 
                    (memory_key, content, category, importance, tags, context, project_context,
                     semantic_keywords, content_hash, updated_at, access_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
                ''', (
                    memory_key, content, category, importance, 
                    ','.join(tags), context, project_context,
                    ','.join(concepts), content_hash_full
                ))
                conn.commit()
            
            # Update concept index
            self._update_concept_index(concepts, memory_key)
            
            # Create memory relationships
            if related_memories:
                self._create_memory_relationships(memory_key, related_memories)
            
            # Build response
            response = []
            response.append(f"Memory Stored Successfully")
            response.append(f"Memory Key: {memory_key}")
            response.append(f"Category: {category}")
            response.append(f"Importance: {importance:.2f}/1.0")
            response.append(f"Concepts Extracted: {len(concepts)}")
            
            if tags:
                response.append(f"Tags: {', '.join(tags)}")
            
            if concepts:
                response.append(f"Key Concepts: {', '.join(concepts[:5])}{'...' if len(concepts) > 5 else ''}")
            
            if related_memories:
                response.append(f"Related Memories Found: {len(related_memories)}")
                response.append("Top Related:")
                for rel in related_memories[:3]: # Show top 3 related
                    response.append(f"  • {rel['memory_key']}: {rel['content_preview']}")
            
            response.append(f"Memory is now persistent across sessions and searchable")
            
            return "\n".join(response)
            
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}", exc_info=True)
            return f"Failed to store memory: {str(e)}"
    
    def bb7_memory_search(self, arguments: Dict[str, Any]) -> str:
        """Search through all memories using intelligent semantic matching and concept relationships"""
        query = arguments.get('query', '')
        limit = arguments.get('limit', 10)
        category = arguments.get('category', '')
        min_importance = arguments.get('min_importance', 0.0)
        include_context = arguments.get('include_context', True)

        if not query:
            return "Please provide a search query. Example: {'query': 'python async patterns'}"

        try:
            query_concepts = self._extract_concepts(query)

            with sqlite3.connect(str(self.memory_db)) as conn:
                conn.row_factory = sqlite3.Row # Access columns by name
                
                # Initial Candidate Selection
                candidate_sql = 'SELECT * FROM memories'
                filters = []
                params = []

                if category:
                    filters.append("category = ?")
                    params.append(category)
                
                if min_importance > 0:
                    filters.append("importance >= ?")
                    params.append(min_importance)
                
                if filters:
                    candidate_sql += " WHERE " + " AND ".join(filters)
                
                # Order by general importance first to get a good pool of candidates
                candidate_sql += ' ORDER BY importance DESC LIMIT 200'
                
                cursor = conn.execute(candidate_sql, params)
                candidate_memories_raw = cursor.fetchall()

                if not candidate_memories_raw:
                    return f"No memories found matching initial criteria (category/importance) for query: '{query}'"

                scored_memories = []
                for mem_row in candidate_memories_raw:
                    memory_concept_list = [kw.strip() for kw in mem_row['semantic_keywords'].split(',') if kw.strip()] if mem_row['semantic_keywords'] else []

                    relevance_score = 0.0
                    if query_concepts:
                       relevance_score = self._calculate_relevance(query_concepts, memory_concept_list)

                    # Fallback for queries with no extractable concepts or if no semantic match initially
                    # Also, if query concepts exist but relevance is 0, still try keyword match for a base score.
                    if relevance_score == 0.0:
                        if query.lower() in mem_row['content'].lower() or \
                           (mem_row['tags'] and query.lower() in mem_row['tags'].lower()) or \
                           (mem_row['semantic_keywords'] and query.lower() in mem_row['semantic_keywords'].lower()): # check raw keywords string too
                            relevance_score = 0.05 # Lower base score for simple keyword match than concept match

                    if relevance_score > 0.0: # Only include if some relevance is found
                        scored_memories.append(dict(mem_row, relevance_score=relevance_score))

                # Sort by relevance_score, then importance
                sorted_memories = sorted(scored_memories, key=lambda x: (x['relevance_score'], x['importance']), reverse=True)
                
                final_results = sorted_memories[:limit]

                if not final_results:
                    return f"No sufficiently relevant memories found for query: '{query}'\n\nTry different keywords or check available categories with bb7_memory_list_categories"

                # Update access counts for found memories
                for res_mem in final_results:
                    conn.execute('''
                        UPDATE memories 
                        SET access_count = access_count + 1 
                        WHERE memory_key = ?
                    ''', (res_mem['memory_key'],))
                conn.commit()

                # Build response
                response = []
                response.append(f"Memory Search Results")
                response.append(f"Query: '{query}' (Concepts: {', '.join(query_concepts) if query_concepts else 'N/A'})")
                response.append(f"Results Found: {len(final_results)} of {limit} requested (from {len(scored_memories)} scored, {len(candidate_memories_raw)} candidates)\n")

                for i, res_mem in enumerate(final_results, 1):
                    response.append(f"{i}. {res_mem['memory_key']}")
                    response.append(f"   Relevance: {res_mem['relevance_score']:.2f} | Category: {res_mem['category']} | Importance: {res_mem['importance']:.2f} | Accessed: {res_mem['access_count']} times")
                    
                    preview_length = 200 if include_context else 150
                    content = res_mem['content']
                    content_preview = content[:preview_length] + '...' if len(content) > preview_length else content
                    response.append(f"   Content: {content_preview}")
                    
                    if res_mem['tags']:
                        tag_list = [tag.strip() for tag in res_mem['tags'].split(',') if tag.strip()]
                        if tag_list:
                            response.append(f"   Tags: {', '.join(tag_list)}")
                    
                    if include_context and res_mem['context']:
                        context_preview = res_mem['context'][:100] + '...' if len(res_mem['context']) > 100 else res_mem['context']
                        response.append(f"   Context: {context_preview}")
                    
                    response.append("")
                
                return "\n".join(response)
                
        except Exception as e:
            self.logger.error(f"Error searching memories: {e}", exc_info=True)
            return f"Failed to search memories: {str(e)}"
    
    def bb7_memory_recall(self, arguments: Dict[str, Any]) -> str:
        """Retrieve a specific memory by key with full context and relationships"""
        memory_key = arguments.get('memory_key', '') or arguments.get('key', '')
        include_related = arguments.get('include_related', True)
        
        if not memory_key:
            return "Please provide a memory key. Example: {'memory_key': 'insight_123456_abc'}"
        
        # Note: Full concept-based retrieval yielding multiple results is better handled by bb7_memory_search.
        # This method focuses on robust recall by a unique ID.

        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                conn.row_factory = sqlite3.Row # Access columns by name
                # Get the memory
                cursor = conn.execute('SELECT * FROM memories WHERE memory_key = ?', (memory_key,))
                result_row = cursor.fetchone()
                
                if not result_row:
                    return f"Memory '{memory_key}' not found.\n\nUse bb7_memory_search to find memories by content or bb7_memory_list_categories."
                
                # Increment access count first
                new_access_count = result_row["access_count"] + 1
                conn.execute('UPDATE memories SET access_count = ? WHERE memory_key = ?', (new_access_count, memory_key))
                conn.commit()
                
                # Use the updated access count in the response
                result = dict(result_row) # Convert row to dict
                result["access_count"] = new_access_count # Update with new count for current response

                # Build response
                response = []
                response.append(f"Memory Recall: {result['memory_key']}\n")
                
                response.append(f"Category: {result['category']}")
                response.append(f"Importance: {result['importance']:.2f}/1.0")
                response.append(f"Access Count: {result['access_count']}")
                response.append(f"Created: {result['created_at']}")
                response.append(f"Updated: {result['updated_at']}")
                
                if result['project_context']:
                    response.append(f"Project: {result['project_context']}")
                
                if result['tags']:
                    tag_list = [tag.strip() for tag in result['tags'].split(',') if tag.strip()]
                    if tag_list:
                        response.append(f"Tags: {', '.join(tag_list)}")
                
                response.append(f"\nContent:")
                response.append(result['content'])
                
                if result['context']:
                    response.append(f"\nContext:")
                    response.append(result['context'])
                
                keywords = result['semantic_keywords']
                if keywords:
                    concept_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
                    if concept_list:
                        response.append(f"\nKey Concepts: {', '.join(concept_list[:10])}")
                
                if include_related and keywords:
                    concepts_for_related = keywords.split(',')
                    related_memories = self._find_related_memories(concepts_for_related, result['memory_key'])
                    
                    if related_memories:
                        response.append(f"\nRelated Memories ({len(related_memories)}):")
                        for rel in related_memories[:5]: # Show top 5 related
                            response.append(f"  • {rel['memory_key']} ({rel['importance']:.2f})")
                            response.append(f"    {rel['content_preview']}")
                
                return "\n".join(response)
                
        except Exception as e:
            self.logger.error(f"Error recalling memory: {e}", exc_info=True)
            return f"Failed to recall memory: {str(e)}"
    
    def bb7_memory_synthesize(self, arguments: Dict[str, Any]) -> str:
        """Synthesize insights across multiple memories to discover patterns and connections"""
        topic = arguments.get('topic', '')
        min_memories = arguments.get('min_memories', 3)
        # include_cross_project is not directly used as a filter, but influences recommendations
        include_cross_project = arguments.get('include_cross_project', True)
        
        if not topic:
            return "Please provide a topic to synthesize. Example: {'topic': 'performance optimization'}"
        
        try:
            # Get memories using search logic (simplified for synthesis context)
            # This could use the bb7_memory_search logic if more complex filtering is needed
            topic_concepts = self._extract_concepts(topic)

            with sqlite3.connect(str(self.memory_db)) as conn:
                conn.row_factory = sqlite3.Row
                # Broad search, then filter/score. This ensures we don't miss things due to strict initial query.
                # Order by importance to get more relevant items if many match.
                base_query = "SELECT * FROM memories WHERE importance >= 0.3 ORDER BY importance DESC LIMIT 100"
                cursor = conn.execute(base_query)
                all_potential_memories = cursor.fetchall()

                # Filter and score these memories based on the topic
                related_memories_data = []
                for mem_row in all_potential_memories:
                    mem_concepts = [kw.strip() for kw in mem_row['semantic_keywords'].split(',') if kw.strip()] if mem_row['semantic_keywords'] else []
                    relevance = 0.0
                    if topic_concepts:
                        relevance = self._calculate_relevance(topic_concepts, mem_concepts)
                    # Fallback: check if topic string itself is in content or concepts
                    if relevance == 0.0 and (topic.lower() in mem_row['content'].lower() or topic.lower() in mem_row['semantic_keywords'].lower()):
                         relevance = 0.1 # Small relevance for direct keyword match

                    if relevance > 0: # Only include if some relevance to topic
                        related_memories_data.append(dict(mem_row, relevance=relevance))
            
            # Sort by relevance for the synthesis
            related_memories_data = sorted(related_memories_data, key=lambda x: x['relevance'], reverse=True)[:20] # Use top 20 for synthesis

            if len(related_memories_data) < min_memories:
                return f"Synthesis Incomplete\n\nFound only {len(related_memories_data)} memories related to '{topic}', need at least {min_memories}.\n\nTry a broader topic or add more memories with bb7_memory_store"
            
            # Analyze patterns
            categories = Counter()
            all_concepts_from_memories = []
            projects = Counter()
            importance_levels = []
            
            for memory_item in related_memories_data:
                categories[memory_item['category']] += 1
                importance_levels.append(memory_item['importance'])
                
                if memory_item['semantic_keywords']:
                    current_mem_concepts = [kw.strip() for kw in memory_item['semantic_keywords'].split(',') if kw.strip()]
                    all_concepts_from_memories.extend(current_mem_concepts)
                
                if memory_item['project_context']:
                    projects[memory_item['project_context']] += 1
            
            concepts_counter = Counter(all_concepts_from_memories)

            avg_importance = sum(importance_levels) / len(importance_levels) if importance_levels else 0
            top_categories = categories.most_common(3)
            top_concepts = concepts_counter.most_common(8)
            # top_projects = projects.most_common(3) # Not used in current response string

            # Co-occurrence analysis for actual concepts in the filtered memories
            co_occurrences = defaultdict(Counter)
            for memory_item in related_memories_data:
                if memory_item['semantic_keywords']:
                    mem_concepts_list = sorted(list(set(kw.strip() for kw in memory_item['semantic_keywords'].split(',') if kw.strip())))
                    for i in range(len(mem_concepts_list)):
                        for j in range(i + 1, len(mem_concepts_list)):
                            pair = tuple(sorted((mem_concepts_list[i], mem_concepts_list[j])))
                            # Count how many memories this pair appears in
                            co_occurrences[pair][memory_item['memory_key']] = 1
            
            co_occurrence_counts = Counter({pair: len(mems.keys()) for pair, mems in co_occurrences.items() if len(mems.keys()) > 1}) # Only pairs in >1 memory
            top_co_occurrences = co_occurrence_counts.most_common(5)

            response = []
            response.append(f"Memory Synthesis: {topic}\n")
            response.append(f"Analysis: {len(related_memories_data)} related memories used for synthesis.")
            response.append(f"Average Importance of related memories: {avg_importance:.2f}/1.0")
            response.append(f"Cross-Project Span (among related): {len(projects)} different projects\n")
            
            response.append(f"Key Memory Categories:")
            for category_name, count in top_categories:
                percentage = (count / len(related_memories_data)) * 100 if len(related_memories_data) > 0 else 0
                response.append(f"  • {category_name}: {count} memories ({percentage:.1f}%)")
            response.append("")
            
            response.append(f"Dominant Concepts in these memories:")
            for concept, frequency in top_concepts:
                if concept.strip(): # Ensure concept is not empty string
                    response.append(f"  • {concept}: {frequency} occurrences")
            response.append("")

            response.append(f"Key Concept Co-occurrences (Pairs appearing in >1 memory, Top {len(top_co_occurrences)}):")
            if top_co_occurrences:
                for (concept1, concept2), count in top_co_occurrences:
                    response.append(f"  • '{concept1}' & '{concept2}': Found together in {count} memories")
            else:
                response.append("  • No significant concept co-occurrences found (pairs in >1 memory).")
            response.append("")
            
            response.append(f"Synthesized Patterns:")
            high_importance_mem_count = sum(1 for m in related_memories_data if m['importance'] > 0.7)
            if high_importance_mem_count > 0:
                response.append(f"  • {high_importance_mem_count} high-impact insights identified related to '{topic}'.")
            else:
                response.append(f"  • No specific high-impact insights (>0.7 importance) found directly related to '{topic}'.")
            
            response.append(f"\nSynthesis Recommendations:")
            if avg_importance > 0.7:
                response.append(f"  • The topic '{topic}' shows high strategic importance based on memory content.")
            if len(projects) > 1 and include_cross_project: # Changed from >2 to >1 for more utility
                response.append(f"  • Patterns for '{topic}' span multiple projects. Consider knowledge sharing or unified approaches.")
            if not top_co_occurrences and len(related_memories_data) > 5 :
                 response.append(f"  • Concepts related to '{topic}' are diverse but not strongly interlinked. Explore potential connections.")
            
            return "\n".join(response)
            
        except Exception as e:
            self.logger.error(f"Error synthesizing memories: {e}", exc_info=True)
            return f"Failed to synthesize memories: {str(e)}"
    
    def bb7_memory_list_categories(self, arguments: Dict[str, Any]) -> str:
        """List all memory categories with counts and insights"""
        include_stats = arguments.get('include_stats', True)
        
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT category, COUNT(*) as count, AVG(importance) as avg_importance,
                           MAX(updated_at) as last_updated
                    FROM memories 
                    GROUP BY category
                    ORDER BY count DESC
                ''')
                
                results = cursor.fetchall()
                
                total_cursor = conn.execute('SELECT COUNT(*) FROM memories')
                total_memories = total_cursor.fetchone()[0]
                
                if not results:
                    return "No memories found\n\nCreate your first memory with bb7_memory_store"
                
                response = []
                response.append(f"Memory Categories Overview\n")
                response.append(f"Total Memories: {total_memories}")
                response.append(f"Categories Used: {len(results)}\n")
                
                for row in results:
                    percentage = (row['count'] / total_memories) * 100 if total_memories > 0 else 0
                    response.append(f"{row['category'].title()}")
                    response.append(f"  Count: {row['count']} ({percentage:.1f}%)")
                    
                    if include_stats:
                        response.append(f"  Avg Importance: {row['avg_importance']:.2f}/1.0" if row['avg_importance'] is not None else "  Avg Importance: N/A")
                        response.append(f"  Last Updated: {row['last_updated']}")
                    response.append("")
                
                return "\n".join(response)
                
        except Exception as e:
            self.logger.error(f"Error listing categories: {e}", exc_info=True)
            return f"Failed to list categories: {str(e)}"
    
    def bb7_memory_insights(self, arguments: Dict[str, Any]) -> str:
        """Generate intelligent insights about your memory system and knowledge patterns"""
        # include_relationships and time_period_days are not currently used but kept for future API compatibility
        # include_relationships = arguments.get('include_relationships', True)
        # time_period_days = arguments.get('time_period_days', 30)
        
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                conn.row_factory = sqlite3.Row

                total_memories_row = conn.execute('SELECT COUNT(*) as count FROM memories').fetchone()
                total_memories = total_memories_row['count'] if total_memories_row else 0
                
                if total_memories == 0:
                    return "No memories to analyze\n\nStart building your knowledge base with bb7_memory_store"
                
                imp_dist_row = conn.execute('''
                    SELECT 
                        SUM(CASE WHEN importance >= 0.8 THEN 1 ELSE 0 END) as high_imp,
                        SUM(CASE WHEN importance >= 0.5 AND importance < 0.8 THEN 1 ELSE 0 END) as medium_imp,
                        SUM(CASE WHEN importance < 0.5 THEN 1 ELSE 0 END) as low_imp
                    FROM memories
                ''').fetchone()
                high_imp, medium_imp, low_imp = (imp_dist_row['high_imp'] or 0), \
                                                (imp_dist_row['medium_imp'] or 0), \
                                                (imp_dist_row['low_imp'] or 0)

                frequent_memories_rows = conn.execute('''
                    SELECT memory_key, access_count, content
                    FROM memories
                    WHERE access_count > 0
                    ORDER BY access_count DESC
                    LIMIT 5
                ''').fetchall()

                high_imp_keywords_rows = conn.execute('''
                    SELECT semantic_keywords
                    FROM memories
                    WHERE importance >= 0.8 AND semantic_keywords IS NOT NULL AND semantic_keywords != ''
                ''').fetchall()
                
                prolific_concepts_counter = Counter()
                for row in high_imp_keywords_rows:
                    prolific_concepts_counter.update(kw.strip() for kw in row['semantic_keywords'].split(',') if kw.strip())
                top_prolific_concepts = prolific_concepts_counter.most_common(5)

                response = []
                response.append(f"Memory System Insights\n")
                response.append(f"Total Memories: {total_memories}")
                
                if total_memories > 0:
                    response.append(f"Knowledge Quality Distribution:")
                    response.append(f"  • High Impact (≥0.8): {high_imp} memories ({high_imp/total_memories*100:.1f}%)")
                    response.append(f"  • Medium Impact (0.5-0.8): {medium_imp} memories ({medium_imp/total_memories*100:.1f}%)")
                    response.append(f"  • Low Impact (<0.5): {low_imp} memories ({low_imp/total_memories*100:.1f}%)")
                else:
                    response.append("Knowledge Quality Distribution: No memories to analyze.")

                response.append(f"\nIntelligence Insights:")
                if total_memories > 0 and high_imp > 0 and high_imp / total_memories > 0.3 : # Check high_imp > 0
                    response.append(f"  • Strong foundation: {high_imp/total_memories*100:.0f}% of memories are high-impact.")
                elif total_memories > 0:
                     response.append(f"  • Consider strategies to increase high-impact memory creation (currently {high_imp/total_memories*100:.0f}%).")
                else: # Should be caught by total_memories == 0 earlier
                    response.append(f"  • No memories to assess impact distribution.")


                if frequent_memories_rows:
                    response.append(f"\nMost Frequently Accessed Memories (Top {len(frequent_memories_rows)}):")
                    for mem_row in frequent_memories_rows:
                        response.append(f"  • '{mem_row['memory_key']}' (Accessed {mem_row['access_count']} times): {mem_row['content'][:50]}...")
                else:
                    response.append(f"\nMost Frequently Accessed Memories: None with access_count > 0.")
                
                if top_prolific_concepts:
                    response.append(f"\nMost Prolific Concepts in High-Importance Memories (Top {len(top_prolific_concepts)}):")
                    for concept, count in top_prolific_concepts:
                        response.append(f"  • '{concept}': Appears in {count} high-impact memories")
                else:
                    response.append(f"\nMost Prolific Concepts in High-Importance Memories: None found or no high-importance memories with concepts.")
                
                return "\n".join(response)
                
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}", exc_info=True)
            return f"Failed to generate insights: {str(e)}"
    
    # ===== MCP TOOL REGISTRATION =====
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all memory tools in MCP format"""
        return {
            'bb7_memory_store': {
                'function': self.bb7_memory_store,
                'description': "Stores information in persistent memory with intelligent categorization and semantic indexing. Arguments: content (str), category (str, optional), tags (list, optional), context (str, optional), memory_key (str, optional), importance (float, optional)."
            },
            'bb7_memory_search': {
                'function': self.bb7_memory_search,
                'description': "Searches through all memories using semantic matching and concept relationships. Arguments: query (str), limit (int, optional), category (str, optional), min_importance (float, optional), include_context (bool, optional)."
            },
            'bb7_memory_recall': {
                'function': self.bb7_memory_recall,
                'description': "Retrieves a specific memory by its key, providing full content and context. Arguments: memory_key (str), include_related (bool, optional)."
            },
            'bb7_memory_synthesize': {
                'function': self.bb7_memory_synthesize,
                'description': "Synthesizes insights across multiple memories to discover patterns and connections related to a topic. Arguments: topic (str), min_memories (int, optional), include_cross_project (bool, optional)."
            },
            'bb7_memory_list_categories': {
                'function': self.bb7_memory_list_categories,
                'description': "Lists all memory categories with counts and statistics. Arguments: include_stats (bool, optional)."
            },
            'bb7_memory_insights': {
                'function': self.bb7_memory_insights,
                'description': "Generates intelligent insights about the memory system, knowledge patterns, and overall content. Arguments: include_relationships (bool, optional), time_period_days (int, optional)."
            }
        }


# Create global instance for MCP server
claude_memory_system = ClaudeMemorySystem()

# Export tools for MCP server registration
def get_tools(): # This function is the entry point for the MCP server
    return claude_memory_system.get_tools()


# For testing and development
if __name__ == "__main__":
    def test_memory_system():
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)

        test_data_dir = "test_mcp_data"
        
        # Instantiate memory system for testing
        memory = ClaudeMemorySystem(data_dir=test_data_dir)
        logger.info(f"Using test data directory: {Path(test_data_dir).resolve()}")

        # Clean up database before test
        db_path = memory.memory_db
        if os.path.exists(db_path):
            logger.info(f"Deleting existing test database: {db_path}")
            os.remove(db_path)

        # Re-initialize to ensure tables are created after deletion
        memory._init_database() # Call init_database again if it was tied to constructor of old instance
        logger.info("Test database cleared and initialized.")

        print("\n=== Testing Claude Memory System ===\n")

        # Test bb7_memory_store
        print("\n--- Testing bb7_memory_store ---")
        store_results = []
        
        mem1_content = "Python is a versatile language. Async programming in Python can lead to significant performance improvements, especially for I/O bound tasks using asyncio."
        res1 = memory.bb7_memory_store({
            'content': mem1_content,
            'category': 'insight',
            'tags': ['python', 'performance', 'asyncio'],
            'context': 'Discussing Python optimization techniques'
        })
        print(f"Store Result 1:\n{res1}\n")
        store_results.append(json.loads(json.dumps(dict(memory_key=res1.split("Memory Key: ")[1].split("\n")[0])))) # Simplified capture

        mem2_content = "Decided to use FastAPI for the new microservice due to its performance and Python type hints support. Alternatives considered: Flask, Django."
        res2 = memory.bb7_memory_store({
            'content': mem2_content,
            'category': 'decision',
            'tags': ['fastapi', 'microservice', 'architecture', 'python'],
            'importance': 0.95
        })
        print(f"Store Result 2:\n{res2}\n")
        store_results.append(json.loads(json.dumps(dict(memory_key=res2.split("Memory Key: ")[1].split("\n")[0]))))

        mem3_content = "SQLite is a C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine. Good for embedded systems and local storage."
        res3 = memory.bb7_memory_store({
            'content': mem3_content,
            'category': 'fact',
            'tags': ['sqlite', 'database', 'sql', 'embedded'],
            'context': 'Researching lightweight database options'
        })
        print(f"Store Result 3:\n{res3}\n")
        store_results.append(json.loads(json.dumps(dict(memory_key=res3.split("Memory Key: ")[1].split("\n")[0]))))

        mem4_content = "A quick note about effective database indexing: always analyze query patterns. Covering indexes can be very useful for read-heavy workloads involving `SELECT` statements on specific columns."
        res4 = memory.bb7_memory_store({
            'content': mem4_content,
            'category': 'note',
            'tags': ['database', 'indexing', 'performance', 'sql'],
            'memory_key': 'custom_db_indexing_note'
        })
        print(f"Store Result 4:\n{res4}\n")
        store_results.append({'memory_key': 'custom_db_indexing_note'})

        memory_key_for_recall_test = store_results[0]['memory_key'] # Key from first memory

        # Test bb7_memory_search
        print("\n--- Testing bb7_memory_search ---")
        search_res1 = memory.bb7_memory_search({'query': 'Python performance improvements'})
        print(f"Search 'Python performance improvements':\n{search_res1}\n")

        search_res2 = memory.bb7_memory_search({'query': 'database indexing strategies', 'limit': 2})
        print(f"Search 'database indexing strategies' (limit 2):\n{search_res2}\n")

        search_res3 = memory.bb7_memory_search({'query': 'FastAPI decision', 'category': 'decision'})
        print(f"Search 'FastAPI decision' (category 'decision'):\n{search_res3}\n")

        search_res4 = memory.bb7_memory_search({'query': 'non_existent_concept_test_string'})
        print(f"Search 'non_existent_concept_test_string':\n{search_res4}\n")

        # Test bb7_memory_recall
        print("\n--- Testing bb7_memory_recall ---")
        recall_res1 = memory.bb7_memory_recall({'memory_key': memory_key_for_recall_test})
        print(f"Recall '{memory_key_for_recall_test}':\n{recall_res1}\n")

        recall_res_non_existent = memory.bb7_memory_recall({'memory_key': 'non_existent_key_123'})
        print(f"Recall 'non_existent_key_123':\n{recall_res_non_existent}\n")

        # Test bb7_memory_list_categories
        print("\n--- Testing bb7_memory_list_categories ---")
        list_cat_res = memory.bb7_memory_list_categories({})
        print(f"List Categories:\n{list_cat_res}\n")

        # Simulate Persistence and Test Access Counts
        print("\n--- Testing Persistence and Access Counts ---")
        print(f"Accessing '{memory_key_for_recall_test}' multiple times...")
        memory.bb7_memory_recall({'memory_key': memory_key_for_recall_test}) # Access 1 (already done above, total 2 after this)
        memory.bb7_memory_recall({'memory_key': memory_key_for_recall_test}) # Access 2 (total 3)

        logger.info("Re-instantiating memory system to test persistence...")
        memory_reloaded = ClaudeMemorySystem(data_dir=test_data_dir)

        recalled_after_reload_res = memory_reloaded.bb7_memory_recall({'memory_key': memory_key_for_recall_test})
        # Expected sequence for memory_key_for_recall_test (e.g., insight_xxxxxxxx_xxxxxxx):
        # 1. Store: 0 in DB
        # 2. Search 'Python performance improvements': Finds it if it matches, access_count becomes 1 in DB. (Search result shows 0 at time of query)
        # 3. First dedicated recall (recall_res1): Fetches 1, new_access_count=2. Shows 2.
        # 4. Second dedicated recall: Fetches 2, new_access_count=3. Shows 3.
        # 5. Third dedicated recall: Fetches 3, new_access_count=4. Shows 4.
        # 6. Reload.
        # 7. Recall after reload: Fetches 4, new_access_count=5. Shows 5.
        print(f"Recall '{memory_key_for_recall_test}' after reload (should be 5th access overall):\n{recalled_after_reload_res}\n")
        if "Access Count: 5" in recalled_after_reload_res:
             print("PASS: Access count persisted and incremented correctly (5).\n")
        else:
             print(f"FAIL: Access count issue. Expected 5. Got: {recalled_after_reload_res[recalled_after_reload_res.find('Access Count:'):].splitlines()[0]}\n")

        search_after_reload = memory_reloaded.bb7_memory_search({'query': 'SQLite fact'})
        print(f"Search 'SQLite fact' after reload:\n{search_after_reload}\n")
        # Check for the actual key of the SQLite fact memory, or part of its content
        # Note: Key includes timestamp, so check for a stable part or content.
        if "fact_" in search_after_reload and "SQLite is a C-language library" in search_after_reload :
            print("PASS: Data persisted and searchable after reload.\n")
        else:
            print("FAIL: Data not found or not searchable after reload.\n")

        # Test bb7_memory_synthesize
        print("\n--- Testing bb7_memory_synthesize ---")
        synthesize_res_python = memory.bb7_memory_synthesize({'topic': 'Python language'})
        print(f"Synthesize 'Python language':\n{synthesize_res_python}\n")

        synthesize_res_db = memory.bb7_memory_synthesize({'topic': 'database technologies', 'min_memories': 2})
        print(f"Synthesize 'database technologies' (min 2):\n{synthesize_res_db}\n")

        # Test bb7_memory_insights
        print("\n--- Testing bb7_memory_insights ---")
        insights_res = memory.bb7_memory_insights({})
        print(f"Insights:\n{insights_res}\n")

        logger.info(f"Test run finished. Check {Path(test_data_dir).resolve()} for database.")

    test_memory_system()
