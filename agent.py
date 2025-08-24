from uagents_adapter import MCPServerAdapter
import os
from dotenv import load_dotenv
from server import mcp

load_dotenv()
# Create an MCP adapter with your MCP server
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,                    
    asi1_api_key=os.getenv("AS1_API_KEY"),  
    model="asi1-mini"              
)

# Create a uAgent
agent = Agent()

# Include protocols from the adapter
for protocol in mcp_adapter.protocols:
    agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":

    mcp_adapter.run(agent)