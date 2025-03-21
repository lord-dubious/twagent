from crewai.tools import BaseTool, tool
import subprocess
from typing import Type
from pydantic import BaseModel, Field


class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."


@tool("Run Python Script")
def run_python_script(script_path: str) -> str:
    """
    Runs a Python script from the specified path and returns its output.
    
    Args:
    script_path (str): The path to the Python script to be executed.
    
    Returns:
    str: The output of the script execution.
    """
    try:
        result = subprocess.run(['python', script_path], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing script: {e.stderr}"
    