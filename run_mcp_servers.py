import threading
from mcp.server.fastmcp import FastMCP
from openai_mcp.mcp_server.building_mcp import build_mcp
from openai_mcp.mcp_server.moving_mcp import actor_mcp


def run_server(mcp_server: FastMCP):
    print("[INFO] 启动 MCP Server...")
    mcp_server.run(transport="sse")  # 阻塞式
    print("[INFO] MCP Server 已退出")


def run_server_in_thread(mcp_server: FastMCP):
    server_thread = threading.Thread(target=run_server, args=(mcp_server,), daemon=True)
    server_thread.start()
    return server_thread


if __name__ == "__main__":
    mcp_servers = [actor_mcp, build_mcp]
    if mcp_servers[:-1]:
        server_thread = run_server_in_thread(mcp_servers[0])
    server_thread = run_server(mcp_servers[-1])