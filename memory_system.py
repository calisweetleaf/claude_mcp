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
        
        # Initialize relationship tracking
        self.relationships = self._load_relationships()
        
        self.logger.info("Claude Memory System initialized with persistent storage and semantic indexing")
    
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
                conn.execute('CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_concepts_frequency ON concepts(frequency)')
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _load_relationships(self) -> Dict[str, Any]:
        """Load memory relationship data"""
        relationships_file = self.memory_dir / "relationships.json"
        if relationships_file.exists():
            try:
                with open(relationships_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load relationships: {e}")
        return {
            "cross_project": {},
            "temporal_chains": [],
            "concept_clusters": {},
            "insight_progressions": []
        }
    
    def _save_relationships(self):
        """Save memory relationship data"""
        relationships_file = self.memory_dir / "relationships.json"
        try:
            with open(relationships_file, 'w', encoding='utf-8') as f:
                json.dump(self.relationships, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save relationships: {e}")
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text using Claude-optimized patterns"""
        if not text:
            return []
        concepts = set()
        
        # Extract using each pattern
        for pattern_name, pattern in self.concept_patterns.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches and isinstance(matches[0], tuple):
                    for m in matches:
                        concepts.update([x for x in m if x])
                else:
                    concepts.update(matches)
            except Exception:
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
        
        return list(set(filtered_concepts))[:25]  # Limit to top 25 concepts
    
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
                for concept in concepts[:10]:
                    cursor = conn.execute('SELECT memory_ids FROM concepts WHERE concept = ?', (concept,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        memory_ids = row[0].split(',')
                        for mem_id in memory_ids:
                            if exclude_key and mem_id == exclude_key:
                                continue
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
                return sorted(unique_related, key=lambda x: x['importance'], reverse=True)[:8]
        except Exception as e:
            self.logger.error(f"Error finding related memories: {e}")
            return []
    
    def _update_concept_index(self, concepts: List[str], memory_key: str):
        """Update concept index with new memory"""
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                for concept in concepts:
                    # Check if concept exists
                    cursor = conn.execute('SELECT memory_ids, frequency FROM concepts WHERE concept = ?', (concept,))
                    result = cursor.fetchone()
                    if result:
                        memory_ids = result[0].split(',') if result[0] else []
                        if memory_key not in memory_ids:
                            memory_ids.append(memory_key)
                        conn.execute('UPDATE concepts SET memory_ids = ?, frequency = ? WHERE concept = ?', (','.join(memory_ids), len(memory_ids), concept))
                    else:
                        conn.execute('INSERT INTO concepts (concept, memory_ids, frequency) VALUES (?, ?, ?)', (concept, memory_key, 1))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating concept index: {e}")
    
    def _create_memory_relationships(self, memory_key: str, related_memories: List[Dict[str, Any]]):
        """Create relationships between memories"""
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                for related in related_memories[:5]:  # Limit relationships
                    related_key = related['memory_key']
                    strength = min(related['importance'] * 0.5 + 0.3, 1.0)
                    
                    # Insert relationship (both directions)
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
                content_hash = self._create_content_hash(content)
                timestamp = int(time.time())
                memory_key = f"{category}_{timestamp}_{content_hash[:8]}"
            
            # Validate category
            if category not in self.categories:
                category = 'note'
            
            # Ensure tags is a list
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            elif not isinstance(tags, list):
                tags = []
            
            # Calculate importance if not provided
            if importance is None:
                importance = self._calculate_importance(content, category, tags)
            else:
                importance = max(0.0, min(1.0, float(importance)))
            
            # Extract concepts for semantic indexing
            concepts = self._extract_concepts(content)
            
            # Get current project context
            project_context = str(Path.cwd())
            
            # Find related memories
            related_memories = self._find_related_memories(concepts, memory_key)
            
            # Create content hash for deduplication
            content_hash = self._create_content_hash(content)
            
            # Store in database
            with sqlite3.connect(str(self.memory_db)) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO memories 
                    (memory_key, content, category, importance, tags, context, project_context,
                     semantic_keywords, content_hash, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    memory_key, content, category, importance, 
                    ','.join(tags), context, project_context,
                    ','.join(concepts), content_hash
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
                for rel in related_memories[:3]:
                    response.append(f"  • {rel['memory_key']}: {rel['content_preview']}")
            
            response.append(f"Memory is now persistent across sessions and searchable")
            
            return "\n".join(response)
            
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
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
            with sqlite3.connect(str(self.memory_db)) as conn:
                # Build search query
                sql_parts = []
                params = []
                
                # Base search across content, key, and keywords
                sql_parts.append('''
                    SELECT memory_key, content, category, importance, tags, context, 
                           created_at, access_count, semantic_keywords
                    FROM memories 
                    WHERE (
                        memory_key LIKE ? OR 
                        content LIKE ? OR 
                        semantic_keywords LIKE ? OR
                        tags LIKE ?
                    )
                ''')
                params.extend([f'%{query}%'] * 4)
                
                # Add filters
                if category:
                    sql_parts.append('AND category = ?')
                    params.append(category)
                
                if min_importance > 0:
                    sql_parts.append('AND importance >= ?')
                    params.append(min_importance)
                
                # Order by relevance and importance
                sql_parts.append('ORDER BY importance DESC, access_count DESC, created_at DESC')
                sql_parts.append('LIMIT ?')
                params.append(limit)
                
                final_sql = ' '.join(sql_parts)
                cursor = conn.execute(final_sql, params)
                results = cursor.fetchall()
                
                if not results:
                    return f"No memories found for query: '{query}'\n\nTry different keywords or check available categories with bb7_memory_list_categories"
                
                # Update access counts for found memories
                for result in results:
                    conn.execute('''
                        UPDATE memories 
                        SET access_count = access_count + 1 
                        WHERE memory_key = ?
                    ''', (result[0],))
                conn.commit()
                
                # Build response
                response = []
                response.append(f"Memory Search Results")
                response.append(f"Query: '{query}'")
                response.append(f"Results Found: {len(results)} of {limit} requested\n")
                
                for i, result in enumerate(results, 1):
                    memory_key, content, cat, importance, tags, context, created, access_count, keywords = result
                    
                    response.append(f"{i}. {memory_key}")
                    response.append(f"   Category: {cat} | Importance: {importance:.2f} | Accessed: {access_count} times")
                    
                    # Show content preview
                    preview_length = 200 if include_context else 150
                    content_preview = content[:preview_length] + '...' if len(content) > preview_length else content
                    response.append(f"   Content: {content_preview}")
                    
                    if tags:
                        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                        if tag_list:
                            response.append(f"   Tags: {', '.join(tag_list)}")
                    
                    if include_context and context:
                        context_preview = context[:100] + '...' if len(context) > 100 else context
                        response.append(f"   Context: {context_preview}")
                    
                    response.append("")
                
                return "\n".join(response)
                
        except Exception as e:
            self.logger.error(f"Error searching memories: {e}")
            return f"Failed to search memories: {str(e)}"
    
    def bb7_memory_recall(self, arguments: Dict[str, Any]) -> str:
        """Retrieve a specific memory by key with full context and relationships"""
        memory_key = arguments.get('memory_key', '') or arguments.get('key', '')
        include_related = arguments.get('include_related', True)
        
        if not memory_key:
            return "Please provide a memory key. Example: {'memory_key': 'insight_123456_abc'}"
        
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                # Get the memory
                cursor = conn.execute('''
                    SELECT memory_key, content, category, importance, tags, context, project_context,
                           created_at, updated_at, access_count, semantic_keywords, content_hash
                    FROM memories 
                    WHERE memory_key = ?
                ''', (memory_key,))
                
                result = cursor.fetchone()
                
                if not result:
                    return f"Memory '{memory_key}' not found.\n\nUse bb7_memory_search to find memories by content"
                
                # Update access count
                conn.execute('''
                    UPDATE memories 
                    SET access_count = access_count + 1 
                    WHERE memory_key = ?
                ''', (memory_key,))
                conn.commit()
                
                # Parse result
                (key, content, category, importance, tags, context, project_ctx, 
                 created, updated, access_count, keywords, content_hash) = result
                
                # Build response
                response = []
                response.append(f"Memory Recall: {memory_key}\n")
                
                # Metadata
                response.append(f"Category: {category}")
                response.append(f"Importance: {importance:.2f}/1.0")
                response.append(f"Access Count: {access_count}")
                response.append(f"Created: {created}")
                response.append(f"Updated: {updated}")
                
                if project_ctx:
                    response.append(f"Project: {project_ctx}")
                
                # Tags
                if tags:
                    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    if tag_list:
                        response.append(f"Tags: {', '.join(tag_list)}")
                
                # Content
                response.append(f"\nContent:")
                response.append(content)
                
                # Context
                if context:
                    response.append(f"\nContext:")
                    response.append(context)
                
                # Concepts
                if keywords:
                    concept_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
                    if concept_list:
                        response.append(f"\nKey Concepts: {', '.join(concept_list[:10])}")
                
                # Related memories
                if include_related and keywords:
                    concepts = keywords.split(',')
                    related = self._find_related_memories(concepts, memory_key)
                    
                    if related:
                        response.append(f"\nRelated Memories ({len(related)}):")
                        for rel in related[:5]:
                            response.append(f"  • {rel['memory_key']} ({rel['importance']:.2f})")
                            response.append(f"    {rel['content_preview']}")
                
                return "\n".join(response)
                
        except Exception as e:
            self.logger.error(f"Error recalling memory: {e}")
            return f"Failed to recall memory: {str(e)}"
    
    def bb7_memory_synthesize(self, arguments: Dict[str, Any]) -> str:
        """Synthesize insights across multiple memories to discover patterns and connections"""
        topic = arguments.get('topic', '')
        min_memories = arguments.get('min_memories', 3)
        include_cross_project = arguments.get('include_cross_project', True)
        
        if not topic:
            return "Please provide a topic to synthesize. Example: {'topic': 'performance optimization'}"
        
        try:
            # Get memories using search logic
            with sqlite3.connect(str(self.memory_db)) as conn:
                cursor = conn.execute('''
                    SELECT memory_key, content, category, importance, tags, semantic_keywords, project_context
                    FROM memories 
                    WHERE (
                        memory_key LIKE ? OR 
                        content LIKE ? OR 
                        semantic_keywords LIKE ?
                    ) AND importance >= 0.3
                    ORDER BY importance DESC, created_at DESC
                    LIMIT 20
                ''', (f'%{topic}%', f'%{topic}%', f'%{topic}%'))
                
                memories = cursor.fetchall()
            
            if len(memories) < min_memories:
                return f"Synthesis Incomplete\n\nFound only {len(memories)} memories related to '{topic}', need at least {min_memories}.\n\nTry a broader topic or add more memories with bb7_memory_store"
            
            # Analyze patterns
            categories = Counter()
            concepts = Counter()
            projects = Counter()
            importance_levels = []
            
            for memory in memories:
                categories[memory[2]] += 1
                importance_levels.append(memory[3])
                
                if memory[5]:  # semantic_keywords
                    concepts.update(kw.strip() for kw in memory[5].split(','))
                
                if memory[6]:  # project_context
                    projects[memory[6]] += 1
            
            # Calculate insights
            avg_importance = sum(importance_levels) / len(importance_levels)
            top_categories = categories.most_common(3)
            top_concepts = concepts.most_common(8)
            top_projects = projects.most_common(3)
            
            # Build synthesis response
            response = []
            response.append(f"Memory Synthesis: {topic}\n")
            response.append(f"Analysis: {len(memories)} related memories found")
            response.append(f"Average Importance: {avg_importance:.2f}/1.0")
            response.append(f"Cross-Project Span: {len(projects)} different projects\n")
            
            # Category patterns
            response.append(f"Memory Categories:")
            for category, count in top_categories:
                percentage = (count / len(memories)) * 100
                response.append(f"  • {category}: {count} memories ({percentage:.1f}%)")
            response.append("")
            
            # Concept patterns
            response.append(f"Dominant Concepts:")
            for concept, frequency in top_concepts:
                if concept.strip():
                    response.append(f"  • {concept}: {frequency} occurrences")
            response.append("")
            
            # Pattern synthesis
            response.append(f"Synthesized Patterns:")
            
            # High-importance insights
            high_importance = [m for m in memories if m[3] > 0.7]
            if high_importance:
                response.append(f"  • {len(high_importance)} high-impact insights identified")
            
            # Recommendations
            response.append(f"\nSynthesis Recommendations:")
            
            if avg_importance > 0.7:
                response.append(f"  • This topic shows high strategic importance - consider deeper exploration")
            
            if len(projects) > 2:
                response.append(f"  • Cross-project patterns detected - consider creating unified approach")
            
            return "\n".join(response)
            
        except Exception as e:
            self.logger.error(f"Error synthesizing memories: {e}")
            return f"Failed to synthesize memories: {str(e)}"
    
    def bb7_memory_list_categories(self, arguments: Dict[str, Any]) -> str:
        """List all memory categories with counts and insights"""
        include_stats = arguments.get('include_stats', True)
        
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                # Get category statistics
                cursor = conn.execute('''
                    SELECT category, COUNT(*) as count, AVG(importance) as avg_importance,
                           MAX(updated_at) as last_updated
                    FROM memories 
                    GROUP BY category
                    ORDER BY count DESC
                ''')
                
                results = cursor.fetchall()
                
                # Get total count
                total_cursor = conn.execute('SELECT COUNT(*) FROM memories')
                total_memories = total_cursor.fetchone()[0]
                
                if not results:
                    return "No memories found\n\nCreate your first memory with bb7_memory_store"
                
                response = []
                response.append(f"Memory Categories Overview\n")
                response.append(f"Total Memories: {total_memories}")
                response.append(f"Categories Used: {len(results)}\n")
                
                # Category details
                for category, count, avg_imp, last_updated in results:
                    percentage = (count / total_memories) * 100
                    
                    response.append(f"{category.title()}")
                    response.append(f"  Count: {count} ({percentage:.1f}%)")
                    
                    if include_stats:
                        response.append(f"  Avg Importance: {avg_imp:.2f}/1.0")
                        response.append(f"  Last Updated: {last_updated}")
                    
                    response.append("")
                
                return "\n".join(response)
                
        except Exception as e:
            self.logger.error(f"Error listing categories: {e}")
            return f"Failed to list categories: {str(e)}"
    
    def bb7_memory_insights(self, arguments: Dict[str, Any]) -> str:
        """Generate intelligent insights about your memory system and knowledge patterns"""
        include_relationships = arguments.get('include_relationships', True)
        time_period_days = arguments.get('time_period_days', 30)
        
        try:
            with sqlite3.connect(str(self.memory_db)) as conn:
                # Basic statistics
                cursor = conn.execute('SELECT COUNT(*) FROM memories')
                total_memories = cursor.fetchone()[0]
                
                if total_memories == 0:
                    return "No memories to analyze\n\nStart building your knowledge base with bb7_memory_store"
                
                # Importance distribution
                cursor = conn.execute('''
                    SELECT 
                        SUM(CASE WHEN importance >= 0.8 THEN 1 ELSE 0 END) as high,
                        SUM(CASE WHEN importance >= 0.5 AND importance < 0.8 THEN 1 ELSE 0 END) as medium,
                        SUM(CASE WHEN importance < 0.5 THEN 1 ELSE 0 END) as low
                    FROM memories
                ''')
                high, medium, low = cursor.fetchone()
                
                # Build insights response
                response = []
                response.append(f"Memory System Insights\n")
                response.append(f"Total Memories: {total_memories}")
                response.append(f"Knowledge Quality Distribution:")
                response.append(f"  • High Impact (≥0.8): {high} memories ({high/total_memories*100:.1f}%)")
                response.append(f"  • Medium Impact (0.5-0.8): {medium} memories ({medium/total_memories*100:.1f}%)")
                response.append(f"  • Low Impact (<0.5): {low} memories ({low/total_memories*100:.1f}%)")
                
                # Intelligence insights
                response.append(f"\nIntelligence Insights:")
                
                if high / total_memories > 0.3:
                    response.append(f"  • High-quality knowledge base with {high/total_memories*100:.0f}% high-impact memories")
                
                return "\n".join(response)
                
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return f"Failed to generate insights: {str(e)}"
    
    # ===== MCP TOOL REGISTRATION =====
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all memory tools in MCP format"""
        return {
            'bb7_memory_store': self.bb7_memory_store,
            'bb7_memory_search': self.bb7_memory_search,
            'bb7_memory_recall': self.bb7_memory_recall,
            'bb7_memory_synthesize': self.bb7_memory_synthesize,
            'bb7_memory_list_categories': self.bb7_memory_list_categories,
            'bb7_memory_insights': self.bb7_memory_insights
        }


# Create global instance for MCP server
claude_memory_system = ClaudeMemorySystem()

# Export tools for MCP server registration
def get_tools():
    return claude_memory_system.get_tools()


# For testing and development
if __name__ == "__main__":
    def test_memory_system():
        logging.basicConfig(level=logging.INFO)
        memory = ClaudeMemorySystem()
        
        print("=== Testing Claude Memory System ===\n")
        
        # Test storing insights
        result = memory.bb7_memory_store({
            'content': 'Discovered that using Claude with persistent memory creates true collaborative intelligence.',
            'category': 'insight',
            'tags': ['claude', 'memory', 'collaboration', 'AI'],
            'context': 'Working on MCP server optimization for Claude integration'
        })
        print(f"Store Result:\n{result}\n")
        
        # Test searching
        result = memory.bb7_memory_search({
            'query': 'Claude memory collaboration',
            'limit': 5
        })
        print(f"Search Result:\n{result}\n")
    
    test_memory_system()
