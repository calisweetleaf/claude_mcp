#!/usr/bin/env python3
"""
Fixed Session Manager Tool - Claude Optimized
Simplified, reliable session management with persistent memory
"""

import json
import logging
import time
import uuid
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import re

class SessionManager:
    """Simplified, reliable session management for Claude MCP"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Setup data directory
        self.data_dir = Path("data")
        self.sessions_dir = self.data_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session state
        self.current_session_id = None
        self.current_session = None
        
        # Session index file
        self.index_file = self.sessions_dir / "session_index.json"
        
        # Auto-memory keywords for insight detection
        self.insight_keywords = [
            "discovered", "learned", "realized", "found", "solution", 
            "breakthrough", "insight", "understand", "figured out"
        ]
        
        self.logger.info("Session Manager initialized successfully")
    
    def _load_index(self) -> Dict[str, Any]:
        """Load session index with error handling"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load session index: {e}")
        
        return {
            "sessions": {},
            "current_session": None,
            "total_sessions": 0,
            "created": time.time()
        }
    
    def _save_index(self, index: Dict[str, Any]) -> None:
        """Save session index with error handling"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save session index: {e}")
    
    def _save_current_session(self) -> None:
        """Save current session to disk"""
        if not self.current_session_id or not self.current_session:
            return
        
        session_file = self.sessions_dir / f"{self.current_session_id}.json"
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save current session: {e}")
    
    def _load_current_session(self) -> None:
        """Load current session from disk"""
        if not self.current_session_id:
            return
        
        session_file = self.sessions_dir / f"{self.current_session_id}.json"
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    self.current_session = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load current session: {e}")
                self.current_session = None
    
    def _detect_insights(self, content: str) -> List[str]:
        """Detect insights in content using keyword matching"""
        insights = []
        content_lower = content.lower()
        
        for keyword in self.insight_keywords:
            if keyword in content_lower:
                # Extract sentence containing the keyword
                sentences = content.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        insights.append(sentence.strip())
                        break
        
        return insights
    
    def _get_system_context(self) -> Dict[str, Any]:
        """Get current system context"""
        return {
            "timestamp": time.time(),
            "working_directory": str(Path.cwd()),
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            "platform": os.name
        }
    
    # ===== MCP TOOL METHODS =====
    
    def bb7_start_session(self, arguments: Dict[str, Any]) -> str:
        """🚀 Start a new development session with intelligent context tracking and auto-memory formation"""
        goal = arguments.get('goal', 'General development work')
        tags = arguments.get('tags', [])
        context = arguments.get('context', '')
        
        try:
            # Generate new session ID
            self.current_session_id = str(uuid.uuid4())
            
            # Create session structure
            self.current_session = {
                "id": self.current_session_id,
                "goal": goal,
                "tags": tags if isinstance(tags, list) else [tags] if tags else [],
                "context": context,
                "created": time.time(),
                "last_updated": time.time(),
                "status": "active",
                
                # Session memory components
                "events": [],
                "insights": [],
                "decisions": [],
                "files_modified": [],
                "commands_run": [],
                
                # System context
                "system_context": self._get_system_context(),
                
                # Metrics
                "metrics": {
                    "duration": 0,
                    "events_count": 0,
                    "insights_count": 0,
                    "files_touched": 0
                }
            }
            
            # Add initial event
            self.current_session["events"].append({
                "timestamp": time.time(),
                "type": "session_start",
                "description": f"Started session: {goal}",
                "context": context
            })
            
            # Save session
            self._save_current_session()
            
            # Update index
            index = self._load_index()
            index["sessions"][self.current_session_id] = {
                "goal": goal,
                "created": time.time(),
                "status": "active",
                "tags": self.current_session["tags"]
            }
            index["current_session"] = self.current_session_id
            index["total_sessions"] = len(index["sessions"])
            self._save_index(index)
            
            self.logger.info(f"Started new session: {self.current_session_id}")
            
            response = f"🚀 **New Session Started**\n\n"
            response += f"**Session ID**: {self.current_session_id}\n"
            response += f"**Goal**: {goal}\n"
            if tags:
                response += f"**Tags**: {', '.join(self.current_session['tags'])}\n"
            if context:
                response += f"**Context**: {context}\n"
            response += f"**Started**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            response += "📝 Session tracking is now active. All insights and decisions will be automatically captured."
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to start session: {e}")
            return f"❌ Failed to start session: {str(e)}"
    
    def bb7_record_insight(self, arguments: Dict[str, Any]) -> str:
        """💡 Record an important insight or learning with automatic context capture"""
        insight = arguments.get('insight', '')
        category = arguments.get('category', 'general')
        importance = arguments.get('importance', 0.5)
        
        if not insight:
            return "❌ Please provide an insight to record"
        
        if not self.current_session_id:
            return "❌ No active session. Start a session first with bb7_start_session"
        
        try:
            if not self.current_session:
                self._load_current_session()
            
            # Create insight record
            insight_record = {
                "id": hashlib.md5(insight.encode()).hexdigest()[:8],
                "insight": insight,
                "category": category,
                "importance": max(0.0, min(1.0, importance)),
                "timestamp": time.time(),
                "context": self._get_system_context()
            }
            
            # Add to session
            self.current_session["insights"].append(insight_record)
            self.current_session["metrics"]["insights_count"] = len(self.current_session["insights"])
            self.current_session["last_updated"] = time.time()
            
            # Add event
            self.current_session["events"].append({
                "timestamp": time.time(),
                "type": "insight_recorded",
                "description": f"Recorded insight: {insight[:50]}...",
                "category": category,
                "importance": importance
            })
            
            self._save_current_session()
            
            return f"💡 **Insight Recorded**\n\n**Content**: {insight}\n**Category**: {category}\n**Importance**: {importance:.1f}/1.0\n**ID**: {insight_record['id']}"
            
        except Exception as e:
            self.logger.error(f"Failed to record insight: {e}")
            return f"❌ Failed to record insight: {str(e)}"
    
    def bb7_record_decision(self, arguments: Dict[str, Any]) -> str:
        """🎯 Record an important decision with reasoning and context"""
        decision = arguments.get('decision', '')
        reasoning = arguments.get('reasoning', '')
        alternatives = arguments.get('alternatives', [])
        
        if not decision:
            return "❌ Please provide a decision to record"
        
        if not self.current_session_id:
            return "❌ No active session. Start a session first with bb7_start_session"
        
        try:
            if not self.current_session:
                self._load_current_session()
            
            # Create decision record
            decision_record = {
                "id": hashlib.md5(decision.encode()).hexdigest()[:8],
                "decision": decision,
                "reasoning": reasoning,
                "alternatives": alternatives if isinstance(alternatives, list) else [alternatives] if alternatives else [],
                "timestamp": time.time(),
                "context": self._get_system_context()
            }
            
            # Add to session
            self.current_session["decisions"].append(decision_record)
            self.current_session["last_updated"] = time.time()
            
            # Add event
            self.current_session["events"].append({
                "timestamp": time.time(),
                "type": "decision_made",
                "description": f"Decision: {decision[:50]}...",
                "reasoning": reasoning
            })
            
            self._save_current_session()
            
            return f"🎯 **Decision Recorded**\n\n**Decision**: {decision}\n**Reasoning**: {reasoning}\n**ID**: {decision_record['id']}"
            
        except Exception as e:
            self.logger.error(f"Failed to record decision: {e}")
            return f"❌ Failed to record decision: {str(e)}"
    
    def bb7_session_summary(self, arguments: Dict[str, Any]) -> str:
        """📊 Generate comprehensive session summary with insights and patterns"""
        session_id = arguments.get('session_id', self.current_session_id)
        
        if not session_id:
            return "❌ No session specified and no active session"
        
        try:
            # Load session if not current
            if session_id != self.current_session_id:
                session_file = self.sessions_dir / f"{session_id}.json"
                if not session_file.exists():
                    return f"❌ Session {session_id} not found"
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    session = json.load(f)
            else:
                if not self.current_session:
                    self._load_current_session()
                session = self.current_session
            
            if not session:
                return f"❌ Failed to load session {session_id}"
            
            # Calculate session metrics
            created = datetime.fromtimestamp(session["created"])
            last_updated = datetime.fromtimestamp(session["last_updated"])
            duration = session["last_updated"] - session["created"]
            
            # Build summary
            summary = []
            summary.append(f"📊 **Session Summary: {session_id[:8]}**\n")
            summary.append(f"**Goal**: {session['goal']}")
            summary.append(f"**Created**: {created.strftime('%Y-%m-%d %H:%M:%S')}")
            summary.append(f"**Duration**: {duration/3600:.1f} hours")
            summary.append(f"**Status**: {session['status']}")
            
            if session.get("tags"):
                summary.append(f"**Tags**: {', '.join(session['tags'])}")
            
            # Events summary
            events = session.get("events", [])
            if events:
                summary.append(f"\n📝 **Events** ({len(events)} total)")
                for event in events[-5:]:  # Last 5 events
                    event_time = datetime.fromtimestamp(event["timestamp"]).strftime("%H:%M")
                    summary.append(f"  • {event_time}: {event['description']}")
            
            # Insights summary
            insights = session.get("insights", [])
            if insights:
                summary.append(f"\n💡 **Insights** ({len(insights)} total)")
                for insight in insights[-3:]:  # Last 3 insights
                    summary.append(f"  • {insight['insight'][:80]}...")
            
            # Decisions summary
            decisions = session.get("decisions", [])
            if decisions:
                summary.append(f"\n🎯 **Decisions** ({len(decisions)} total)")
                for decision in decisions[-3:]:  # Last 3 decisions
                    summary.append(f"  • {decision['decision'][:80]}...")
            
            # Files touched
            files_modified = session.get("files_modified", [])
            if files_modified:
                summary.append(f"\n📁 **Files Modified**: {len(files_modified)}")
            
            return "\n".join(summary)
            
        except Exception as e:
            self.logger.error(f"Failed to generate session summary: {e}")
            return f"❌ Failed to generate session summary: {str(e)}"
    
    def bb7_list_sessions(self, arguments: Dict[str, Any]) -> str:
        """📋 List all sessions with filtering and search capabilities"""
        limit = arguments.get('limit', 10)
        status_filter = arguments.get('status', None)
        tag_filter = arguments.get('tag', None)
        
        try:
            index = self._load_index()
            sessions = index.get("sessions", {})
            
            if not sessions:
                return "📋 No sessions found. Create your first session with bb7_start_session"
            
            # Filter sessions
            filtered_sessions = []
            for session_id, session_info in sessions.items():
                # Status filter
                if status_filter and session_info.get("status") != status_filter:
                    continue
                
                # Tag filter
                if tag_filter and tag_filter not in session_info.get("tags", []):
                    continue
                
                filtered_sessions.append((session_id, session_info))
            
            # Sort by creation time (newest first)
            filtered_sessions.sort(key=lambda x: x[1].get("created", 0), reverse=True)
            
            # Limit results
            filtered_sessions = filtered_sessions[:limit]
            
            # Build response
            response = []
            response.append(f"📋 **Sessions** ({len(filtered_sessions)} shown, {len(sessions)} total)\n")
            
            for session_id, session_info in filtered_sessions:
                created = datetime.fromtimestamp(session_info["created"]).strftime("%Y-%m-%d %H:%M")
                status = session_info.get("status", "unknown")
                goal = session_info.get("goal", "No goal specified")
                tags = session_info.get("tags", [])
                
                response.append(f"**{session_id[:8]}** - {goal}")
                response.append(f"  📅 {created} | 📊 {status}")
                if tags:
                    response.append(f"  🏷️ {', '.join(tags)}")
                response.append("")
            
            current_session = index.get("current_session")
            if current_session:
                response.append(f"🎯 **Current Session**: {current_session[:8]}")
            
            return "\n".join(response)
            
        except Exception as e:
            self.logger.error(f"Failed to list sessions: {e}")
            return f"❌ Failed to list sessions: {str(e)}"
    
    def bb7_end_session(self, arguments: Dict[str, Any]) -> str:
        """🏁 End the current session with final summary and insights consolidation"""
        summary = arguments.get('summary', '')
        
        if not self.current_session_id:
            return "❌ No active session to end"
        
        try:
            if not self.current_session:
                self._load_current_session()
            
            # Update session
            self.current_session["status"] = "completed"
            self.current_session["ended"] = time.time()
            self.current_session["final_summary"] = summary
            self.current_session["last_updated"] = time.time()
            
            # Calculate final metrics
            duration = self.current_session["ended"] - self.current_session["created"]
            self.current_session["metrics"]["duration"] = duration
            
            # Add final event
            self.current_session["events"].append({
                "timestamp": time.time(),
                "type": "session_end",
                "description": f"Session ended: {summary}" if summary else "Session ended",
                "final_metrics": self.current_session["metrics"]
            })
            
            # Save final session
            self._save_current_session()
            
            # Update index
            index = self._load_index()
            if self.current_session_id in index["sessions"]:
                index["sessions"][self.current_session_id]["status"] = "completed"
            index["current_session"] = None
            self._save_index(index)
            
            # Generate final summary
            insights_count = len(self.current_session.get("insights", []))
            decisions_count = len(self.current_session.get("decisions", []))
            events_count = len(self.current_session.get("events", []))
            
            ended_session_id = self.current_session_id
            self.current_session_id = None
            self.current_session = None
            
            response = f"🏁 **Session Completed**\n\n"
            response += f"**Session ID**: {ended_session_id[:8]}\n"
            response += f"**Duration**: {duration/3600:.1f} hours\n"
            response += f"**Insights Captured**: {insights_count}\n"
            response += f"**Decisions Recorded**: {decisions_count}\n"
            response += f"**Total Events**: {events_count}\n"
            if summary:
                response += f"**Final Summary**: {summary}\n"
            response += f"\n✅ Session data saved successfully"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to end session: {e}")
            return f"❌ Failed to end session: {str(e)}"
    
    # ===== MCP TOOL REGISTRATION =====
    
    def get_tools(self) -> Dict[str, Any]:
        """Return all session management tools in MCP format"""
        return {
            'bb7_start_session': {
                'description': '🚀 Start a new development session with intelligent context tracking and auto-memory formation. Perfect for organizing work, tracking insights, and maintaining continuity across development tasks.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'goal': {
                            'type': 'string',
                            'description': 'Main goal or objective for this session'
                        },
                        'tags': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'Tags for categorizing this session'
                        },
                        'context': {
                            'type': 'string',
                            'description': 'Additional context or background information'
                        }
                    },
                    'required': ['goal']
                },
                'function': self.bb7_start_session
            },
            'bb7_record_insight': {
                'description': '💡 Record an important insight or learning with automatic context capture. Perfect for preserving breakthrough moments, lessons learned, and important discoveries.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'insight': {
                            'type': 'string',
                            'description': 'The insight or learning to record'
                        },
                        'category': {
                            'type': 'string',
                            'description': 'Category for this insight',
                            'enum': ['technical', 'architectural', 'business', 'process', 'general'],
                            'default': 'general'
                        },
                        'importance': {
                            'type': 'number',
                            'description': 'Importance level (0.0 to 1.0)',
                            'minimum': 0.0,
                            'maximum': 1.0,
                            'default': 0.5
                        }
                    },
                    'required': ['insight']
                },
                'function': self.bb7_record_insight
            },
            'bb7_record_decision': {
                'description': '🎯 Record an important decision with reasoning and context. Perfect for documenting key choices, architectural decisions, and strategic directions.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'decision': {
                            'type': 'string',
                            'description': 'The decision that was made'
                        },
                        'reasoning': {
                            'type': 'string',
                            'description': 'Reasoning behind the decision'
                        },
                        'alternatives': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'Alternative options that were considered'
                        }
                    },
                    'required': ['decision']
                },
                'function': self.bb7_record_decision
            },
            'bb7_session_summary': {
                'description': '📊 Generate comprehensive session summary with insights and patterns. Perfect for reviewing progress, understanding accomplishments, and planning next steps.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {
                            'type': 'string',
                            'description': 'Session ID to summarize (defaults to current session)'
                        }
                    }
                },
                'function': self.bb7_session_summary
            },
            'bb7_list_sessions': {
                'description': '📋 List all sessions with filtering and search capabilities. Perfect for finding past sessions, reviewing work history, and organizing projects.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'limit': {
                            'type': 'integer',
                            'description': 'Maximum number of sessions to return',
                            'default': 10
                        },
                        'status': {
                            'type': 'string',
                            'description': 'Filter by session status',
                            'enum': ['active', 'completed', 'paused']
                        },
                        'tag': {
                            'type': 'string',
                            'description': 'Filter by specific tag'
                        }
                    }
                },
                'function': self.bb7_list_sessions
            },
            'bb7_end_session': {
                'description': '🏁 End the current session with final summary and insights consolidation. Perfect for wrapping up work, capturing final thoughts, and preparing for next steps.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'summary': {
                            'type': 'string',
                            'description': 'Final summary of accomplishments and outcomes'
                        }
                    }
                },
                'function': self.bb7_end_session
            }
        }


# Create global instance for MCP server
session_manager = SessionManager()

# Export tools for MCP server registration
def get_tools():
    return session_manager.get_tools()