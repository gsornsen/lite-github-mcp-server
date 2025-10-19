from fastmcp.server.server import FastMCP

from lite_github_mcp import __version__ as pkg_version
from lite_github_mcp.tools.router import register_tools

app = FastMCP(name="lite-github-mcp", version=pkg_version)
register_tools(app)


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
