"""
Distributed Tracing Utilities
Simple distributed tracing implementation for request tracking
"""
import uuid
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from flask import g, request

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """Tracing span for distributed tracing"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    tags: Dict[str, Any]
    logs: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            'span_id': self.span_id,
            'trace_id': self.trace_id,
            'parent_span_id': self.parent_span_id,
            'operation_name': self.operation_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'tags': self.tags,
            'logs': self.logs,
        }


class TraceContext:
    """Trace context manager for distributed tracing"""
    
    def __init__(self, trace_id: Optional[str] = None, parent_span_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.parent_span_id = parent_span_id
        self.spans: List[Span] = []
        self.current_span: Optional[Span] = None
    
    def start_span(self, operation_name: str, tags: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new span"""
        span_id = str(uuid.uuid4())
        parent_id = self.current_span.span_id if self.current_span else self.parent_span_id
        
        span = Span(
            span_id=span_id,
            trace_id=self.trace_id,
            parent_span_id=parent_id,
            operation_name=operation_name,
            start_time=datetime.now(timezone.utc),
            end_time=None,
            duration_ms=None,
            tags=tags or {},
            logs=[]
        )
        
        self.spans.append(span)
        self.current_span = span
        
        return span
    
    def end_span(self, span: Optional[Span] = None, tags: Optional[Dict[str, Any]] = None):
        """End a span"""
        if span is None:
            span = self.current_span
        
        if span:
            span.end_time = datetime.now(timezone.utc)
            span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
            
            if tags:
                span.tags.update(tags)
            
            # Update parent span
            if span.parent_span_id:
                parent = self.get_span(span.parent_span_id)
                if parent:
                    self.current_span = parent
            else:
                self.current_span = None
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """Get span by ID"""
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None
    
    def add_log(self, span: Span, message: str, level: str = 'info', **kwargs):
        """Add log to span"""
        span.logs.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'message': message,
            **kwargs
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace context to dictionary"""
        return {
            'trace_id': self.trace_id,
            'spans': [span.to_dict() for span in self.spans],
            'span_count': len(self.spans),
            'total_duration_ms': sum(
                s.duration_ms or 0 for s in self.spans if s.duration_ms
            )
        }


class TraceManager:
    """Manager for distributed tracing"""
    
    @staticmethod
    def get_trace_context() -> Optional[TraceContext]:
        """Get current trace context from Flask g"""
        return getattr(g, 'trace_context', None)
    
    @staticmethod
    def set_trace_context(trace_context: TraceContext):
        """Set trace context in Flask g"""
        g.trace_context = trace_context
    
    @staticmethod
    def create_trace_context(trace_id: Optional[str] = None) -> TraceContext:
        """Create new trace context"""
        # Try to get trace ID from request headers
        if trace_id is None:
            try:
                trace_id = request.headers.get('X-Trace-ID')
            except RuntimeError:
                pass
        
        context = TraceContext(trace_id=trace_id)
        TraceManager.set_trace_context(context)
        return context
    
    @staticmethod
    def start_span(operation_name: str, tags: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new span in current trace context"""
        context = TraceManager.get_trace_context()
        if context is None:
            context = TraceManager.create_trace_context()
        
        return context.start_span(operation_name, tags)
    
    @staticmethod
    def end_span(span: Optional[Span] = None, tags: Optional[Dict[str, Any]] = None):
        """End a span"""
        context = TraceManager.get_trace_context()
        if context:
            context.end_span(span, tags)
    
    @staticmethod
    def trace_function(operation_name: Optional[str] = None):
        """Decorator to trace function execution"""
        def decorator(func):
            from functools import wraps
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                span = TraceManager.start_span(op_name, tags={'function': func.__name__})
                
                try:
                    result = func(*args, **kwargs)
                    TraceManager.end_span(span, tags={'status': 'success'})
                    return result
                except Exception as e:
                    TraceManager.end_span(span, tags={'status': 'error', 'error': str(e)})
                    raise
            
            return wrapper
        return decorator


# Convenience functions
def get_trace_id() -> Optional[str]:
    """Get current trace ID"""
    context = TraceManager.get_trace_context()
    return context.trace_id if context else None


def start_span(operation_name: str, tags: Optional[Dict[str, Any]] = None) -> Span:
    """Start a new span"""
    return TraceManager.start_span(operation_name, tags)


def end_span(span: Optional[Span] = None, tags: Optional[Dict[str, Any]] = None):
    """End a span"""
    TraceManager.end_span(span, tags)

