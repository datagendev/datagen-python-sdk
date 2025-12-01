# DataGen Agent Workflow

This flowchart illustrates the standard lifecycle of an AI agent building and executing applications using the DataGen SDK.

## Core Benefit: Universal MCP Interface

A key advantage of this architecture is that **every tool is an MCP tool**. This means the exact same tool definitions, schemas, and execution paths are used by:
1.  **AI Agents**: Discovering and calling tools dynamically via the Model Context Protocol.
2.  **Human Developers**: Importing and running tools via the Python SDK.
3.  **Low-Code Builders**: Using tools within the DataGen UI.

This unification eliminates "glue code" and ensures that if a tool works for a developer, it works for the agent, and vice versa.

![DataGen Workflow Diagram](datagen_workflow_flowchart.png)

### Mermaid Diagram Source

```mermaid
flowchart TD
    %% Nodes
    Start([Start: User Request])
    
    subgraph Interfaces [Universal Interface]
        direction TB
        Agent[AI Agent via MCP]
        Dev[Developer via SDK]
        UI[Builder via UI]
    end

    subgraph Discovery [1. Tool Discovery]
        Search[searchTools]
        Details[getToolDetails]
    end
    
    subgraph Core [2. Unified Execution Engine]
        Exec[execute_tool]
        MCP_Server[Managed MCP Server]
    end
    
    subgraph AuthLoop [3. Zero-Touch Auth]
        Check{Authenticated?}
        AuthError[401 Request Auth]
        Connect[User Connects Service]
    end
    
    subgraph Output [4. Result]
        Success[Success / Data Returned]
    end

    %% Edge Connections
    Start --> Agent
    
    Agent -- "1. Discover" --> Search
    Search --> Details
    Details -- "2. Call" --> Exec
    
    Dev -- "Import & Call" --> Exec
    UI -- "Click & Run" --> Exec
    
    Exec --> MCP_Server
    MCP_Server --> Check
    
    Check -- "Yes" --> Success
    Check -- "No" --> AuthError
    
    AuthError --> Connect
    Connect --> MCP_Server

    %% Styling
    classDef interface fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef core fill:#e0f2f1,stroke:#00695c,stroke-width:2px;
    classDef error fill:#ffebee,stroke:#c62828,stroke-width:2px;
    classDef success fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    
    class Agent,Dev,UI interface;
    class Search,Details process;
    class Exec,MCP_Server core;
    class Check,AuthError,Connect error;
    class Success success;
```