from app.core.logging import logger


def register_hello_tools(server) -> None:
    """Registers greeting and connection verification tools."""

    @server.tool()
    def hello_world(name: str) -> str:
        """A simple greeting tool to verify the klpod221-mcp connection.

        Args:
            name: The name of the person or client to greet.
        """
        logger.info(f"Executing hello_world tool with name='{name}'")
        return f"Hello {name}, connection to klpod221-mcp Server is successful!"

    logger.debug("Registered 'hello_world' tool.")

