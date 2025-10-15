from fastmcp import FastMCP
from lite_github_mcp.tools.router import register_tools


app = FastMCP(server_name="lite-github-mcp", server_version="0.1.0")


def main() -> None:
    register_tools(app)
    app.run()


if __name__ == "__main__":
    main()
