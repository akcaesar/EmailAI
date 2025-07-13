"""
Author: Akshay NS
Contains: Tool registry for managing and registering tools in the application

"""
# backend/api/tools/tool_registry.py
from typing import Dict, Type, Any
from .email_fetcher import EmailFetchTool, EmailFetchConfig, EmailFetchInputs
import inspect

class ToolRegistry:
    _instance = None
    _tools: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._register_default_tools()
        return cls._instance

    @classmethod
    def _register_default_tools(cls):
        """Register all default tools"""
        cls.register_tool(
            name="email_fetcher",
            description="Fetch emails from an IMAP server",
            tool_class=EmailFetchTool,
            config_class=EmailFetchConfig,
            input_class=EmailFetchInputs
        )

    @classmethod
    def register_tool(cls, name: str, description: str, tool_class: Type, 
                    config_class: Type, input_class: Type):
        """Register a new tool"""
        cls._tools[name] = {
            'class': tool_class,
            'config_class': config_class,
            'input_class': input_class,
            'description': description,
            'config_schema': cls._generate_schema(config_class),
            'input_schema': cls._generate_schema(input_class)
        }

    @classmethod
    def _generate_schema(cls, class_obj: Type) -> Dict[str, Any]:
        """Generate JSON schema from dataclass"""
        schema = {
            'type': 'object',
            'properties': {},
            'required': []
        }
        
        for field_name, field_type in class_obj.__annotations__.items():
            field_info = {
                'type': cls._map_type(field_type)
            }
            
            # Check for default value
            if hasattr(class_obj, field_name):
                field_info['default'] = getattr(class_obj, field_name)
            
            schema['properties'][field_name] = field_info
            
            # Check if required (no default value)
            if not hasattr(class_obj, field_name):
                schema['required'].append(field_name)
        
        return schema

    @staticmethod
    def _map_type(python_type) -> str:
        """Map Python types to JSON schema types"""
        type_map = {
            str: 'string',
            int: 'integer',
            float: 'number',
            bool: 'boolean',
            list: 'array',
            dict: 'object'
        }
        
        # Handle Optional types
        if hasattr(python_type, '__origin__') and python_type.__origin__ is Union:
            if type(None) in python_type.__args__:
                actual_type = next(t for t in python_type.__args__ if t is not type(None))
                return type_map.get(actual_type, 'string')
        
        return type_map.get(python_type, 'string')

    def get_tool(self, name: str):
        """Get tool class by name"""
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all available tools"""
        return {
            name: {
                'description': info['description'],
                'config_schema': info['config_schema'],
                'input_schema': info['input_schema']
            }
            for name, info in self._tools.items()
        }