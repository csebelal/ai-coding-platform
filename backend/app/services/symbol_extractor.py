import tree_sitter as ts
import tree_sitter_languages
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class Symbol:
    """Represents a code symbol (function, class, method, etc.)"""
    name: str
    symbol_type: str  # function, class, method, variable, etc.
    file_path: str
    start_line: int
    end_line: int
    content: str
    parent_name: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parameters: Optional[str] = None
    return_type: Optional[str] = None
    language: str = ""
    line_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "symbol_type": self.symbol_type,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "parent_name": self.parent_name,
            "docstring": self.docstring,
            "decorators": self.decorators,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "language": self.language,
            "line_count": self.line_count
        }

class SymbolExtractor:
    """Extract symbols from code using Tree-sitter"""
    
    # Map tree-sitter node types to our symbol types
    PYTHON_SYMBOL_TYPES = {
        "function_definition": "function",
        "class_definition": "class",
        "decorated_definition": "decorated",
    }
    
    JAVASCRIPT_SYMBOL_TYPES = {
        "function_declaration": "function",
        "class_declaration": "class",
        "method_definition": "method",
        "arrow_function": "function",
        "variable_declarator": "variable",
    }
    
    def __init__(self):
        self.languages = {}
    
    def _get_parser(self, language: str) -> Optional[ts.Parser]:
        """Get or create a parser for a language"""
        if language not in self.languages:
            try:
                self.languages[language] = tree_sitter_languages.parser(language)
            except Exception as e:
                logger.warning(f"Could not create parser for {language}: {e}")
                return None
        return self.languages[language]
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, "unknown")
    
    def extract_symbols(self, file_path: str, content: str) -> List[Symbol]:
        """Extract all symbols from a file"""
        language = self._detect_language(file_path)
        if language == "unknown":
            return []
        
        parser = self._get_parser(language)
        if not parser:
            return []
        
        try:
            tree = parser.parse(bytes(content, "utf8"))
            symbols = []
            self._walk_node(tree.root_node, symbols, file_path, language, content)
            return symbols
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return []
    
    def _walk_node(self, node, symbols: List[Symbol], file_path: str, 
                   language: str, content: str, parent_name: str = None):
        """Recursively walk AST and extract symbols"""
        node_type = node.type
        
        # Python symbols
        if language == "python":
            if node_type == "function_definition":
                symbol = self._extract_python_function(node, file_path, content, language, parent_name)
                if symbol:
                    symbols.append(symbol)
            elif node_type == "class_definition":
                class_name = self._get_node_name(node)
                symbol = self._extract_python_class(node, file_path, content, language)
                if symbol:
                    symbols.append(symbol)
                # Walk class body with class name as parent
                for child in node.children:
                    if child.type == "block":
                        self._walk_node(child, symbols, file_path, language, content, class_name)
                return  # Don't walk children again
        
        # JavaScript/TypeScript symbols
        elif language in ("javascript", "typescript"):
            if node_type in ("function_declaration", "arrow_function"):
                symbol = self._extract_js_function(node, file_path, content, language, parent_name)
                if symbol:
                    symbols.append(symbol)
            elif node_type == "class_declaration":
                class_name = self._get_node_name(node)
                symbol = self._extract_js_class(node, file_path, content, language)
                if symbol:
                    symbols.append(symbol)
                for child in node.children:
                    if child.type == "class_body":
                        self._walk_node(child, symbols, file_path, language, content, class_name)
                return
            elif node_type == "method_definition":
                symbol = self._extract_js_method(node, file_path, content, language, parent_name)
                if symbol:
                    symbols.append(symbol)
        
        # Recurse into children
        for child in node.children:
            self._walk_node(child, symbols, file_path, language, content, parent_name)
    
    def _get_node_name(self, node) -> str:
        """Get the name of a node"""
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode()
            elif child.type == "name":
                return child.text.decode()
        return "anonymous"
    
    def _get_node_content(self, node, content: str) -> str:
        """Get the full content of a node"""
        start_byte = node.start_byte
        end_byte = node.end_byte
        return content[start_byte:end_byte]
    
    def _extract_python_function(self, node, file_path: str, content: str, 
                                 language: str, parent_name: str = None) -> Optional[Symbol]:
        """Extract a Python function symbol"""
        name = self._get_node_name(node)
        if name == "anonymous":
            return None
        
        # Get decorators
        decorators = []
        for child in node.children:
            if child.type == "decorated_definition":
                for dec in child.children:
                    if dec.type == "decorator":
                        decorators.append(self._get_node_content(dec, content))
        
        # Get parameters
        params = None
        for child in node.children:
            if child.type == "parameters":
                params = self._get_node_content(child, content)
        
        # Get return type
        return_type = None
        for child in node.children:
            if child.type == "type":
                return_type = self._get_node_content(child, content)
        
        # Get docstring
        docstring = self._extract_docstring(node, content)
        
        return Symbol(
            name=name,
            symbol_type="function",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_content(node, content),
            parent_name=parent_name,
            docstring=docstring,
            decorators=decorators,
            parameters=params,
            return_type=return_type,
            language=language,
            line_count=node.end_point[0] - node.start_point[0] + 1
        )
    
    def _extract_python_class(self, node, file_path: str, content: str, 
                              language: str) -> Optional[Symbol]:
        """Extract a Python class symbol"""
        name = self._get_node_name(node)
        if name == "anonymous":
            return None
        
        # Get base classes
        decorators = []
        for child in node.children:
            if child.type == "argument_list":
                decorators.append(f"extends: {self._get_node_content(child, content)}")
        
        docstring = self._extract_docstring(node, content)
        
        return Symbol(
            name=name,
            symbol_type="class",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_content(node, content),
            docstring=docstring,
            decorators=decorators,
            language=language,
            line_count=node.end_point[0] - node.start_point[0] + 1
        )
    
    def _extract_js_function(self, node, file_path: str, content: str, 
                             language: str, parent_name: str = None) -> Optional[Symbol]:
        """Extract a JavaScript function symbol"""
        name = self._get_node_name(node)
        
        # Get parameters
        params = None
        for child in node.children:
            if child.type == "formal_parameters":
                params = self._get_node_content(child, content)
        
        docstring = self._extract_jsdoc(node, content)
        
        return Symbol(
            name=name,
            symbol_type="function",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_content(node, content),
            parent_name=parent_name,
            docstring=docstring,
            parameters=params,
            language=language,
            line_count=node.end_point[0] - node.start_point[0] + 1
        )
    
    def _extract_js_class(self, node, file_path: str, content: str, 
                          language: str) -> Optional[Symbol]:
        """Extract a JavaScript class symbol"""
        name = self._get_node_name(node)
        
        # Get parent classes
        decorators = []
        for child in node.children:
            if child.type == "class_heritage":
                decorators.append(f"extends: {self._get_node_content(child, content)}")
        
        docstring = self._extract_jsdoc(node, content)
        
        return Symbol(
            name=name,
            symbol_type="class",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_content(node, content),
            docstring=docstring,
            decorators=decorators,
            language=language,
            line_count=node.end_point[0] - node.start_point[0] + 1
        )
    
    def _extract_js_method(self, node, file_path: str, content: str, 
                           language: str, parent_name: str = None) -> Optional[Symbol]:
        """Extract a JavaScript method symbol"""
        name = self._get_node_name(node)
        
        params = None
        for child in node.children:
            if child.type == "formal_parameters":
                params = self._get_node_content(child, content)
        
        return Symbol(
            name=name,
            symbol_type="method",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_content(node, content),
            parent_name=parent_name,
            parameters=params,
            language=language,
            line_count=node.end_point[0] - node.start_point[0] + 1
        )
    
    def _extract_docstring(self, node, content: str) -> Optional[str]:
        """Extract docstring from a Python function or class"""
        for child in node.children:
            if child.type == "block":
                for block_child in child.children:
                    if block_child.type == "expression_statement":
                        for expr in block_child.children:
                            if expr.type == "string":
                                return self._get_node_content(expr, content)
        return None
    
    def _extract_jsdoc(self, node, content: str) -> Optional[str]:
        """Extract JSDoc comment from a JavaScript function or class"""
        # Look for comment before the node
        if node.prev_sibling and node.prev_sibling.type == "comment":
            return self._get_node_content(node.prev_sibling, content)
        return None
