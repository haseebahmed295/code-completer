import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple

def get_function_info(func: Callable) -> str:
    try:
        # Get the function signature
        signature = inspect.signature(func)
        
        # Extract the docstring
        docstring = inspect.getdoc(func) or ""
        
        # Prepare the Markdown header
        markdown = f"# Function: `{func.__name__}`\n\n"
        
        # Add the docstring
        markdown += f"## Docstring\n{docstring}\n\n"
        
        # Prepare the arguments table
        markdown += "## Arguments\n| Parameter | Type | Default | Description |\n|-----------|------|---------|-------------|\n"
        
        # Process each parameter
        for param_name, param in signature.parameters.items():
            type_hint = str(param.annotation) if param.annotation != param.empty else "-"
            default_value = param.default if param.default != param.empty else "-"
            
            # Try to extract description from the docstring
            param_doc = ""
            if docstring:
                lines = docstring.split("\n")
                for line in lines:
                    if line.strip().startswith(f":param {param_name}:"):
                        param_doc = line.strip().split(":")[2].strip()
                        break
            
            markdown += f"| `{param_name}` | {type_hint} | {default_value} | {param_doc} |\n"
        
        # Add return type if available
        return_anno = signature.return_annotation
        if return_anno != inspect.Signature.empty:
            markdown += f"\n## Return Value\nType: `{return_anno}`\n"
        
        return markdown
    
    except Exception as e:
        return f"Error processing function: {str(e)}"

# Example usage
def example_function(a: int, b: str = "hello", *, c: float = None) -> Tuple[int, str]:
    """
    An example function with various parameters.

    :param a: An integer parameter
    :param b: A string parameter with a default value
    :param c: An optional float parameter
    :return: A tuple containing the sum of a and b's length, and b itself
    """
    return a + len(b), b

print(get_function_info(example_function))
