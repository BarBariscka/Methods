from smolagents import tool

@tool
def test_tool(input_text: str) -> str:
    """Test tool.

    Args:
        input_text: input text
    """
    return "ok"

print("name:", test_tool.name)
print("OK")
