# **Claude and the Model Context Protocol: The Definitive Developer's Guide (June 2025 Edition)**

## **Part 1: Foundations of the Model Context Protocol**

### **Chapter 1: Introduction to the Model Context Protocol (MCP)**

#### **1.1 What is MCP?**

The Model Context Protocol (MCP) is a standardized set of rules for communication that enables AI models like Claude to interact with external tools, data sources, and systems in a consistent and interoperable way. It is crucial to understand that MCP is a protocol, not a framework. Unlike opinionated frameworks such as LangChain, MCP defines a universal language that any compatible application can speak, regardless of the programming language or environment in which it is built.  
The core value of MCP lies in its ability to create a standardized ecosystem. Before MCP, integrating an AI with a new tool, such as a code editor's file system or a third-party API, required bespoke, one-off solutions. With MCP, any "Host" application (like Claude Desktop) that understands the protocol can connect to any "Server" that also speaks the protocol, with minimal friction. This standardization is the key to unlocking a vast, collaborative ecosystem of tools and capabilities for AI agents.  
A common point of confusion is the distinction between the protocol and its implementation. "MCP" refers to the specification—the rules of communication. An "MCP Server" is a concrete program that implements these rules to provide a specific capability, such as searching the web or editing files. This guide will cover both the protocol's fundamentals and the practical use of various MCP servers.  
An interesting development in the MCP ecosystem has been its adoption for a purpose beyond its original design. While many servers provide Claude with new *tools* (e.g., filesystem access), a significant number of community-built servers act as *proxies* or *gateways*. These servers receive a request from a Claude client, translate it from Anthropic's API format to another format (like OpenAI's), and route it to a different model provider, such as Google Gemini, OpenAI's GPT models, or aggregation services like OpenRouter. This has effectively turned MCP into a de facto standard for building universal LLM middleware, allowing developers to switch backend models for reasons of cost, capability, or content policy without changing their client-side setup. This guide will clearly distinguish between "Tool Servers" that add capabilities and "Proxy Servers" that route requests.

#### **1.2 Why Use MCP? The Shift to Agentic AI**

The Model Context Protocol is the foundational technology that elevates Claude from a purely conversational AI into a powerful *agentic* assistant. An agent is an AI that can not only process information but also take actions and perform tasks in a digital environment. By connecting to MCP servers, Claude gains the ability to interact with the world beyond the chat interface.  
This enables a wide range of powerful workflows that were previously impossible. For example, with the appropriate MCP servers, Claude can:

* **Perform File System Operations:** Read, write, edit, and manage files and directories on your local machine.  
* **Execute Shell Commands:** Run terminal commands, compile code, and manage system processes.  
* **Conduct Web Searches:** Access up-to-date information from the internet to answer questions or perform research.  
* **Integrate with Version Control:** Stage files, create commits, and manage pull requests in Git repositories.  
* **Interact with Third-Party APIs:** Connect to services like GitHub, Slack, Notion, or any other platform with an API, allowing Claude to manage issues, send messages, or update database records.

The difference between a standard Claude instance and one augmented with MCP servers is transformative. The former is a knowledgeable conversationalist; the latter is an active participant in your development workflow, capable of executing complex, multi-step tasks on your behalf.

### **Chapter 2: The MCP Architecture: A Technical Deep-Dive**

#### **2.1 The Three Core Components**

The MCP architecture is composed of three distinct components that work in concert.

* **Host:** The Host is the end-user application that the user interacts with directly. It is responsible for managing connections to one or more MCP servers. Examples of Hosts include the official Claude Desktop and Claude Code applications, as well as third-party tools like the Cursor IDE and VS Code extensions.  
* **Client:** The Client is a component that lives within the Host. Each Client maintains a dedicated, one-to-one connection with a single MCP Server. Its primary responsibilities are to handle the connection lifecycle, negotiate capabilities with the server, and route messages between the Host and the Server.  
* **Server:** A Server is a standalone process that exposes tools (functions the AI can call) and resources (data the AI can access) to a connected Client. Servers are the workhorses of the MCP ecosystem, providing the actual capabilities, whether it's accessing a database, interacting with a local file, or calling a web API.

#### **2.2 Communication Protocols and Transport Mechanisms**

Communication between Clients and Servers is governed by a strict set of rules to ensure interoperability.

* **JSON-RPC 2.0:** All communication within MCP is structured using the JSON-RPC 2.0 specification. This defines three primary message types: a Request (a Client asks a Server to perform an action), a Response (a Server replies to a Request with a result or an error), and a Notification (a one-way message that does not require a response).  
* **Transport Layers:** MCP defines two primary transport mechanisms for these JSON-RPC messages:  
  * **Stdio (Standard Input/Output):** This is the most common transport for local servers. The Host application launches the server as a new process and communicates with it by writing to its standard input (stdin) and reading from its standard output (stdout). This is the mechanism used for most local filesystem and terminal servers.  
  * **HTTP with Server-Sent Events (SSE):** This transport is used for remote, internet-hosted servers. It allows for a persistent, real-time, and unidirectional flow of data from the server to the client over a standard HTTP connection. This is the mechanism used by services like the Remote GitHub MCP Server.

#### **2.3 The Lifecycle of an MCP Connection**

A typical MCP session follows a well-defined lifecycle :

1. **Startup:** The Host application starts a local server process (via Stdio) or prepares to connect to a remote server URL (via HTTP/SSE).  
2. **Connection and Negotiation:** The Client establishes a connection with the Server. They exchange initialization messages to negotiate the protocol version and the capabilities (i.e., the available tools and resources) the Server offers.  
3. **Operation:** The user interacts with the Host (e.g., by typing a prompt in Claude Desktop). The Host sends a request to the AI model. If the model decides to use a tool provided by an MCP server, the Host forwards a tool-use request through the Client to the appropriate Server. The Server executes the tool and sends the result back in a Response message.  
4. **Error Handling:** If any part of the process fails, standardized error messages are sent to ensure the system can handle failures gracefully.  
5. **Shutdown:** When the Host application is closed, it sends shutdown notifications to its Clients, which in turn terminate their connections with the Servers.

## **Part 2: Configuration and Management**

### **Chapter 3: Getting Started: Your First MCP Server**

This chapter provides a practical, step-by-step guide to connecting your first MCP server to the Claude Desktop application.

#### **3.1 Prerequisites**

Before you begin, ensure you have the following installed and configured:

* **Claude Desktop:** Download and install the official desktop application for your operating system (macOS, Windows, or Linux) from the Anthropic website. MCP integration is exclusive to the desktop application and is not available on the web version.  
* **Runtimes:** Many MCP servers are scripts that require a specific runtime. Always check the server's documentation. The two most common are:  
  * **Node.js:** Required for servers launched with npx. You can verify your installation by running node \--version in your terminal.  
  * **Docker:** Required for containerized servers. Verify with docker \--version and ensure the Docker Desktop application is running.  
* **Configuration Directory:** You will need to locate the Claude Desktop configuration directory. The path varies by operating system :  
  * **macOS:** \~/Library/Application Support/Claude/  
  * **Windows:** %APPDATA%\\Claude\\ (e.g., C:\\Users\\YourUser\\AppData\\Roaming\\Claude\\)  
  * **Linux:** \~/.config/Claude/

#### **3.2 Method 1: Manual Configuration via claude\_desktop\_config.json**

This method involves directly editing the JSON configuration file and is an excellent way to understand how MCP servers are registered. We will use the official Filesystem server as an example.

1. **Create the Configuration File:** Open the Claude Desktop app. Navigate to **Settings** \\rightarrow **Developer** and click **Edit config**. This action will create an empty claude\_desktop\_config.json file in the correct directory and open it in your default text editor.  
2. **Add the Server Configuration:** Copy and paste the following JSON block into the file. This configuration tells Claude Desktop how to launch the Filesystem server using npx.  
   `{`  
     `"mcpServers": {`  
       `"filesystem": {`  
         `"command": "npx",`  
         `"args":`  
       `}`  
     `}`  
   `}`  
   **Important:** Replace YOUR\_USERNAME with your actual user folder name. The \--allow flags grant the server permission to access specific directories. You can add more paths as needed.  
3. **Restart Claude Desktop:** This is a critical step. Simply closing the application window is not enough, as the app often continues running in the background. You must fully quit the application from the system tray (Windows) or the menu bar (macOS) and then relaunch it for the new configuration to be loaded.  
4. **Verify the Connection:** After restarting, open Claude Desktop. You should now see a new tool icon (resembling a wrench or sliders) in the bottom-right corner of the chat input box. Clicking this icon will reveal the list of available tools from the Filesystem server, such as listDirectory and writeFile. To test it, try a prompt like: "List all the files on my Desktop." Claude will ask for permission the first time it tries to use the tool. After you grant permission, it should return a list of your desktop files.

#### **3.3 Method 2: Using a GUI with the Docker Desktop Extension**

For users who prefer a graphical interface over manual JSON editing, the Docker MCP Toolkit provides a streamlined, "no-code" alternative.

1. **Install the Extension:** Launch Docker Desktop. Navigate to the **Extensions** marketplace from the left-hand menu. Search for and install the **Docker MCP Toolkit** (it may have been previously named "Labs: AI Tools for Devs").  
2. **Connect to Claude Desktop:** Open the installed extension. In its settings screen, navigate to the **MCP Clients** tab. Find "Claude Desktop" in the list and click the **Connect** button. This action will automatically find and write the necessary configuration to your claude\_desktop\_config.json file, setting up a bridge between Docker and Claude.  
3. **Add Tools and Verify:** Within the Docker MCP Toolkit interface, you can now add pre-packaged tools, such as the "Chrome web scraper." After adding a tool, restart Claude Desktop (a full quit and relaunch). You can then verify the connection and use the new tool by selecting it from the tool menu in the Claude chat interface.

### **Chapter 4: Mastering MCP Server Configuration**

#### **4.1 The claude\_desktop\_config.json Schema in Detail**

The claude\_desktop\_config.json file is the central hub for managing local MCP servers in the desktop app. Understanding its schema is key to configuring a wide range of community servers. Each server is an entry within the mcpServers object.  
A server entry consists of the following keys:

* command (string): The executable program that starts the server. This can be a system command like npx or docker, a runtime like python, or an absolute path to a compiled binary.  
* args (array of strings): A list of command-line arguments to pass to the command. This is where you specify server-specific flags, paths, or options.  
* env (object): A key-value map of environment variables to be set for the server process. This is the recommended and most secure method for providing sensitive information like API keys, preventing them from being exposed in process lists or logs.

For example, the configuration for the claude-search-mcp server might look like this, demonstrating the use of the env object for an API key :  
`"claude-search": {`  
  `"command": "mcp-server-claude-search",`  
  `"env": {`  
    `"ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY_HERE"`  
  `}`  
`}`

The configuration for the zen-mcp-server, which uses Docker, shows a more complex command and args structure :  
`"zen": {`  
  `"command": "docker",`  
  `"args": [`  
    `"exec",`  
    `"-i",`  
    `"zen-mcp-server",`  
    `"python",`  
    `"server.py"`  
  `]`  
`}`

#### **4.2 The claude mcp Command-Line Interface (CLI)**

For power users and those working primarily in the terminal, the claude mcp command suite, part of the claude-code package, provides a robust alternative to manually editing JSON files. It allows for programmatic and scriptable management of MCP server configurations.  
**Core Commands:**

* claude mcp add \<name\> \<command\> \[args...\]: Adds a new server. This is the primary command for registration. It supports flags for setting environment variables (-e KEY=value) and specifying the transport type (--transport sse for remote servers).  
* claude mcp list: Lists all currently configured MCP servers, showing their names and configuration scopes.  
* claude mcp get \<name\>: Displays the detailed JSON configuration for a specific server.  
* claude mcp remove \<name\>: Deletes a server's configuration.  
* claude mcp add-from-claude-desktop: A convenient utility for macOS and WSL users that reads the claude\_desktop\_config.json file and imports its server configurations into the claude-code management system.

#### **4.3 Understanding Configuration Scopes**

A crucial concept when using the claude mcp CLI is that of "scopes," which determine where a server's configuration is stored and how it is shared. This system allows for fine-grained control over which tools are available in different contexts.

* user (formerly global): Configurations are stored in a central file in the user's home directory. These servers are available to that user across all projects and directories. This is ideal for universal tools like filesystem access or web search.  
* project: Configurations are stored in a .mcp.json file located at the root of the current project directory. This file is intended to be committed to version control (e.g., Git), ensuring that all team members working on the project have access to the same set of project-specific tools, such as a database connector or an internal API gateway.  
* local (default): Configurations are stored in a project-specific location (e.g., within the .git directory) that is *not* intended for version control. This is for servers that are specific to a project but contain personal information (like local paths or private keys) that should not be shared with the team.

The existence of multiple configuration sources (claude\_desktop\_config.json for the desktop app, and user/project/local scopes for the claude-code CLI) can create ambiguity. When multiple sources define servers, the client application (Claude Desktop or Claude Code) must resolve them into a final, active list. The precise order of precedence is that more specific scopes override more general ones. For example, a server defined at the project scope would typically be loaded for that project, potentially alongside servers from the user scope. If a server with the same name is defined in multiple scopes, the most specific scope's definition (project \> user) will likely take precedence. This is a common source of confusion, and checking the output of claude mcp list within a project is the definitive way to see the final resolved set of active servers.

#### **4.4 Connecting to Remote Servers**

While many MCP servers run locally, the protocol also fully supports remote servers hosted on the internet, which communicate via HTTP and Server-Sent Events (SSE). The premier example is the official Remote GitHub MCP Server.  
Connecting to a remote server involves adding it to your configuration, typically specifying its URL. Authentication is a key consideration for remote services.

* **OAuth 2.0:** This is the recommended and most secure method. When you first use a tool from the server, Claude will initiate an OAuth 2.0 flow, redirecting you to the service (e.g., GitHub) to log in and grant specific, scoped permissions. This ensures that Claude never handles your password and can only perform the actions you explicitly authorize.  
* **Personal Access Tokens (PATs):** Some servers may also support authentication via a PAT. This is simpler to set up (often passed via an environment variable) but is generally less secure as the token may have overly broad permissions.

When adding a custom integration via the Claude settings UI, you will be prompted for the remote MCP server URL. Always review the permissions requested during the OAuth flow carefully and only connect to servers from trusted developers and organizations.

## **Part 3: The Ecosystem and Advanced Applications**

### **Chapter 5: Exploring the MCP Ecosystem: A Curated Guide**

The true power of MCP is realized through the diverse and growing ecosystem of community-built servers. This chapter serves as a curated catalog of some of the most popular and powerful servers available, helping you discover and implement new capabilities.  
The following table provides a quick-reference guide. For each server, follow the installation instructions in its GitHub repository, then add the example configuration to your claude\_desktop\_config.json or use the claude mcp CLI.

| Server Name | Primary Function | GitHub Repository | Key Features | Example claude\_desktop\_config.json Entry |
| :---- | :---- | :---- | :---- | :---- |
| **DesktopCommanderMCP** | Terminal & Filesystem Control | wonderwhy-er/DesktopCommanderMCP | Execute shell commands, manage processes, advanced file search (ripgrep), diff-based editing, detailed logging. | {"desktop-commander": {"command": "npx", "args": \["-y", "@wonderwhy-er/desktop-commander"\]}} |
| **claude-code-mcp** | Agentic CLI Execution | steipete/claude-code-mcp | Exposes the claude CLI itself as a tool, with a \--dangerously-skip-permissions flag for enabling complex, unattended agentic workflows. | {"claude-code": {"command": "path/to/claude-code-mcp-binary"}} (Requires local build) |
| **claude-search-mcp** | Web Search | Doriandarko/claude-search-mcp | Provides a web search tool using the Claude API. Supports domain filtering and configurable result limits. | {"claude-search": {"command": "mcp-server-claude-search", "env": {"ANTHROPIC\_API\_KEY": "sk-..."}}} |
| **zen-mcp-server** | AI Model Orchestration | BeehiveInnovations/zen-mcp-server | Gives Claude access to other models (Gemini, OpenAI) as tools, allowing it to delegate sub-tasks to the most suitable AI. | {"zen": {"command": "docker", "args": \["exec", "-i", "zen-mcp-server", "python", "server.py"\]}} |
| **mcp-server-reddit** | Reddit Integration | (Community Project) | Fetches and summarizes hot, new, or top posts and comments from specified subreddits. | (Varies by implementation, typically requires npx or python command) |
| **CWM-API-Gateway-MCP** | Enterprise API Gateway | jasondsmith72/CWM-API-Gateway-MCP | Acts as a gateway to the ConnectWise Manage API, simplifying complex API interactions into natural language prompts. | {"cwm-gateway": {"command": "npm", "args": \["start"\], "env": {"CONNECTWISE\_...": "..."}}} |

### **Chapter 6: Graphical Interfaces and Local Web Content**

This chapter addresses methods for interacting with MCP servers through graphical user interfaces (GUIs) and the specific challenge of serving local HTML content to Claude.

#### **6.1 Managing Servers with GUIs**

While manual JSON editing and CLI commands offer maximum control, GUI-based tools can significantly simplify the setup and management of MCP servers. The **Docker MCP Toolkit**, discussed in Chapter 3, is a prime example. It provides a point-and-click interface within Docker Desktop to connect to clients like Claude and add pre-configured tools, abstracting away the underlying JSON configuration.  
Other applications in the AI ecosystem also leverage MCP. The **Cursor IDE**, a fork of VS Code designed for AI-assisted development, has its own MCP integration, allowing it to connect to the same servers as Claude Desktop. Furthermore, community projects like tauri-claude have emerged, offering alternative desktop clients for Claude, sometimes with their own unique features and interfaces.

#### **6.2 Serving Local Web Content to Claude**

A common desire is to have Claude analyze or render local web content, such as an HTML report or a data visualization generated by a script. However, this presents a technical challenge: for security reasons, the Content Security Policy (CSP) of the Claude Desktop application prevents its rendered "artifact" views from loading resources directly from the local filesystem (i.e., via file:// URLs).  
The claude-local-files project provides an ingenious solution to this problem. It works by temporarily tricking your local machine and Claude into thinking your local files are being served from a trusted, secure, remote domain.  
The process works as follows:

1. **Host File Modification:** The script temporarily adds an entry to your system's hosts file (/etc/hosts on macOS/Linux) that points the domain cdn.jsdelivr.net to your local machine's loopback address (127.0.0.1).  
2. **Local HTTPS Server:** It uses mkcert to generate a valid local SSL certificate for cdn.jsdelivr.net and starts a local web server (Caddy) that serves files from a specific local directory (e.g., ./files).  
3. **Proxying:** The local server is configured to serve any requests for https://cdn.jsdelivr.net/pyodide/claude-local-files/\* from the local ./files directory, while proxying all other requests to the real cdn.jsdelivr.net. This ensures that normal functionality is not broken.  
4. **Cleanup:** When you stop the script, it automatically removes the entry from your hosts file, restoring normal network configuration.

To use this method:

1. Clone the claude-local-files repository and run its setup script.  
2. Place your HTML, JavaScript, CSS, or JSON files into the designated files/ directory.  
3. Prompt Claude to fetch and render the content using the special URL, for example: "Please fetch and display the webpage from https://cdn.jsdelivr.net/pyodide/claude-local-files/my\_report.html."

This provides a powerful and direct solution to the "local HTML setup" requirement, enabling rich, interactive local content within the Claude environment.

#### **6.3 GUI Agents: The Next Frontier**

While not strictly an MCP-based technology, the concept of GUI agents represents the ultimate evolution of local AI control. Projects like computer\_use\_ootb leverage the "Computer Use" feature of the Claude 3.5 API, which allows the model to see the user's screen, understand GUI elements, and control the mouse and keyboard. This moves beyond tool-based interaction to direct manipulation of the desktop environment, offering a glimpse into the future of agentic AI where models can operate any application, just as a human would.

## **Part 4: Security, Compliance, and Operations**

### **Chapter 7: Security and Trust in the MCP Ecosystem**

As you extend Claude's capabilities with MCP servers, security becomes a paramount concern. Granting an AI access to your local files, terminal, and third-party services introduces potential risks that must be managed responsibly.

#### **7.1 API Key Security: The First Line of Defense**

Many MCP servers require API keys to interact with external services. Protecting these keys is your first and most critical security responsibility.

* **Use Secure Storage:** Never hardcode API keys directly into your code or configuration files. The recommended practice is to use environment variables, which can be set via the env block in your claude\_desktop\_config.json or a secure key management system (KMS).  
* **Rotate Keys Regularly:** Periodically (e.g., every 90 days) create new API keys and deactivate the old ones. This limits the window of exposure if a key is ever compromised.  
* **Use Scoped Keys:** Create separate API keys for different applications and environments (development, testing, production). If a key is leaked, you can disable it without disrupting other services.  
* **Scan for Secrets:** Integrate automated secret scanning tools like Gitleaks into your development workflow and CI/CD pipeline to prevent keys from being accidentally committed to public repositories. GitHub actively scans for and Anthropic automatically revokes exposed API keys found in public repositories.

#### **7.2 Understanding the Claude Code Permission Model**

The Claude Code client includes a built-in permission system designed to give you granular control over the actions the AI can take. It requires explicit user approval for any potentially sensitive operation.

| Tool Type | Example | Approval Required | "Yes, don't ask again" Behavior |
| :---- | :---- | :---- | :---- |
| Read-only | read, ls, grep | No | N/A |
| Bash Commands | bash (shell execution) | Yes | Permanently allows that specific command in that project directory. |
| File Modification | edit, write | Yes | Allows modifications for the current session only. |
| Web Access | webFetch, webSearch | Yes | Varies by tool and session. |

This system acts as a crucial safety layer, ensuring that Claude cannot execute arbitrary commands or modify files without your consent.

#### **7.3 Mitigating Risks: Prompt Injection and Malicious Servers**

Two primary threats in an open ecosystem like MCP are prompt injection and malicious servers.

* **Prompt Injection:** An attacker attempts to manipulate Claude by embedding malicious instructions within seemingly benign content (e.g., in a file or webpage that Claude is asked to analyze). Claude Code has several built-in safeguards, including context-aware analysis to detect harmful instructions, input sanitization, and a blocklist for inherently risky commands like curl and wget.  
* **Malicious Servers:** A community-built MCP server could be designed to perform unintended or harmful actions. It is vital to evaluate the trustworthiness of any server you install.

The MCP ecosystem exists on a trust spectrum. On one end, official servers from Anthropic and trusted partners like GitHub are highly vetted. On the other end, unaudited, experimental servers from unknown developers carry higher risk. In the middle are well-maintained, popular community projects. A key point of divergence is the approach to security. While Anthropic enforces a strict permission model , some community servers explicitly offer ways to bypass it, such as the \--dangerously-skip-permissions flag in one claude-code-mcp implementation. This flag is designed for trusted, automated workflows but highlights the need for user discretion.  
Before installing a community MCP server, ask these questions:

* Is the repository actively maintained?  
* Does the README contain clear security warnings?  
* Does the server offer to bypass standard security features? If so, why?  
* Does the server log sensitive data? Where?  
* Is the developer reputable within the community?

#### **7.4 The Sandbox: Using Development Containers for Isolation**

For maximum security, especially when running unattended agentic workflows, the recommended approach is to use a development container. Anthropic provides a reference implementation for a devcontainer that creates a fully isolated environment for Claude Code.  
This setup uses a Docker container with a restrictive firewall (init-firewall.sh) that blocks all outbound network traffic by default, only allowing connections to a whitelist of essential domains (e.g., GitHub, npm registry, Anthropic API). Within this secure sandbox, it is safe to run Claude with permissions bypassed (claude \--dangerously-skip-permissions), as the agent's actions are confined to the container and its allowed network endpoints.

### **Chapter 8: Operational Best Practices**

#### **8.1 Monitoring and Managing Costs**

Using Claude Code and API-driven MCP servers incurs costs based on token usage. It is essential to monitor and manage this spending.

* **Track Session Costs:** Within an interactive claude session, use the /cost command to see a real-time summary of the tokens used and the associated cost in USD for the current session.  
* **Review Historical Usage:** For a complete overview of your spending, visit the Anthropic Console, which provides detailed historical usage data.  
* **Reduce Token Usage:** Employ strategies to minimize unnecessary token consumption:  
  * Use /compact to condense the conversation history when it becomes long.  
  * Use /clear to start a new task with a fresh context.  
  * Write specific, focused queries to avoid triggering broad, expensive file scans.  
  * Break down large, complex tasks into smaller, more manageable sub-tasks.

#### **8.2 Handling API Rate Limits**

Applications making frequent API calls will eventually encounter rate limits. Understanding and handling these limits is crucial for building robust applications. Anthropic's API rate limits are measured in three ways: Requests Per Minute (RPM), Input Tokens Per Minute (ITPM), and Output Tokens Per Minute (OTPM). Exceeding any of these will result in an HTTP 429 Too Many Requests error. The API response will include a retry-after header indicating how many seconds to wait before retrying.  
The best practice for handling 429 errors is to implement an **exponential backoff with jitter** strategy. This means your code should wait for a progressively longer duration between retries, with a small random delay (jitter) added to prevent multiple clients from retrying in synchronized waves.  
The following table summarizes the standard rate limits for popular models as of June 2025\. For higher limits, contact Anthropic sales about custom or Priority Tier plans.

| Model | Maximum RPM | Maximum ITPM | Maximum OTPM |
| :---- | :---- | :---- | :---- |
| Claude Opus 4 | 50 | 20,000 | 8,000 |
| Claude Sonnet 4 | 50 | 20,000 | 8,000 |
| Claude Sonnet 3.5 (2024-06-20) | 50 | 40,000 | 8,000 |
| Claude Haiku 3.5 | 50 | 50,000 | 10,000 |
| Claude Opus 3 | 50 | 20,000 | 4,000 |
| Claude Sonnet 3 | 50 | 40,000 | 8,000 |
| Claude Haiku 3 | 50 | 50,000 | 10,000 |

#### **8.3 Troubleshooting Common Issues**

When an MCP server fails to connect or a tool doesn't work as expected, follow this systematic debugging process.

1. **Check the UI:** In Claude Desktop, is the tool icon present? Is the server shown as "running" in the Developer settings?.  
2. **Verify Configuration:** Double-check your claude\_desktop\_config.json for syntax errors (e.g., missing commas), incorrect file paths, or missing environment variables.  
3. **Perform a Full Restart:** Ensure you have fully quit and restarted the Claude Desktop application.  
4. **Check the Logs:** This is the most important step for diagnosing issues. MCP-related logs are written to specific files :  
   * **macOS:** \~/Library/Logs/Claude/  
   * **Windows:** %APPDATA%\\Claude\\logs\\  
   * Look for mcp.log for general connection issues and mcp-server-SERVERNAME.log for errors specific to a named server.

The following table maps common symptoms to their likely causes and recommended actions, consolidating knowledge from official documentation and community-reported issues.

| Symptom / Error Message | Potential Causes | Recommended Actions |
| :---- | :---- | :---- |
| Server not listed or not "running" in UI. | 1\. Claude was not fully restarted. \<br\> 2\. Syntax error in claude\_desktop\_config.json. \<br\> 3\. Incorrect path to command or runtime. | 1\. Quit Claude from system tray/menu bar and relaunch. \<br\> 2\. Use a JSON validator to check your config file. \<br\> 3\. Verify paths are absolute and correct for your OS. |
| "Server disconnected" error. | 1\. Bug in a specific version of the MCP server. \<br\> 2\. A long-running command finished or crashed. | 1\. Check the server's GitHub issues for known problems with your version. \<br\> 2\. Check the mcp-server-SERVERNAME.log file for error output from the server process. |
| Unexpected token 'T', "Terminate "... is not valid JSON | A process is printing non-JSON text to stdout, which the client cannot parse. Often occurs with long-running commands. | Check the server's GitHub issues; this is likely a bug in how the server handles command output. |
| Claude Desktop crashes during a long response. | A specific MCP server may have a memory leak or instability when handling large amounts of data. | Identify which server is active. Try disabling it to confirm it's the cause. Report the issue on the server's GitHub repository. |
| A specific tool (e.g., search\_code) fails every time. | 1\. Missing dependency for that tool (e.g., ripgrep not installed). \<br\> 2\. Bug within the tool's implementation. | 1\. Check the server's documentation for prerequisites. \<br\> 2\. Report the issue on the server's GitHub repository. |

### **Chapter 9: Anthropic's Terms and Data Policies**

Using Claude, its API, and the MCP ecosystem is governed by a set of legal and data policies. It is important to be aware of these terms.

* **Commercial Terms of Service:** All use of the Anthropic API, including through Claude Code and MCP servers, is subject to the Commercial Terms of Service, regardless of whether you are an individual hobbyist or a large enterprise. Key provisions include customer ownership of any outputs generated and a copyright indemnity from Anthropic, which protects customers from infringement claims related to their authorized use of the services.  
* **Usage Policy:** Formerly the Acceptable Use Policy (AUP), this document outlines prohibited and restricted use cases. It includes clear rules against using the models for political campaigning and misinformation. It also defines requirements for "high-risk" use cases, such as applications in healthcare or legal advice, which require additional safety measures and disclosures.  
* **Data Privacy and Retention:** When you use Claude Code, Anthropic collects usage data and feedback to debug and improve the product. For customers with specific compliance needs (e.g., healthcare), Anthropic offers Zero Data Retention (ZDR) and will sign a Business Associate Agreement (BAA), ensuring that API traffic is not used for model training.

## **Part 5: Appendices**

### **Appendix A: Building Your Own MCP Server**

This section provides "Hello, World" examples for creating a minimal MCP server in both Python and TypeScript.  
**Python Example (using fast-mcp-server)** This example uses a community library to quickly create a server.  
`# server.py`  
`from fast_mcp_server import FastMCP, tool`

`# Initialize the server. The variable name 'mcp' is standard. [span_148](start_span)[span_148](end_span)`  
`mcp = FastMCP("HelloWorldServer")`

`@tool()`  
`def greet(name: str) -> str:`  
    `"""Returns a simple greeting."""`  
    `return f"Hello, {name}!"`

`# To run this server, you would typically use a command like:`  
`# python -m fast_mcp_server.cli server.py`

**TypeScript Example (using @modelcontext/mcp-sdk)** This example uses the official MCP SDK.  
`// server.ts`  
`import { McpServer, McpServerStdio } from "@modelcontext/mcp-sdk";`  
`import { z } from "zod";`

`async function main() {`  
  `const server = new McpServer();`

  `// Define a tool with Zod for argument validation [span_149](start_span)[span_149](end_span)`  
  `server.tool(`  
    `"greet",`  
    `"Returns a simple greeting.",`  
    `{`  
      `name: z.string().describe("The name of the person to greet."),`  
    `},`  
    `async ({ name }) => {`  
      ``const message = `Hello, ${name}!`;``  
      `return {`  
        `content: [{ type: "text", text: message }],`  
      `};`  
    `}`  
  `);`

  `// Start the server over stdio`  
  `const transport = new McpServerStdio(server);`  
  `await transport.listen();`  
`}`

`main();`

### **Appendix B: The MCP Proxy Server Architecture**

As noted in Chapter 1, a significant use case for MCP is as a protocol for building API proxy servers. This architecture allows a standard MCP client (like Claude Desktop) to communicate with various backend LLM providers.  
**Architectural Flow:**

1. **Client Request:** The user issues a prompt in an MCP Host (e.g., Claude Desktop).  
2. **MCP Proxy Server:** The request is sent to a locally running MCP Proxy Server (e.g., claude-code-proxy).  
3. **API Translation:** The proxy server receives the request in Anthropic's API format. It then translates this request into a different format, such as the OpenAI API standard.  
4. **Forward to External Provider:** The translated request is sent to the configured external provider, which could be the OpenAI API, Google's Vertex AI, or an aggregator like OpenRouter.  
5. **Response and Reverse Translation:** The external provider processes the request and sends a response back to the proxy. The proxy server translates this response back into the Anthropic API format.  
6. **Return to Client:** The final, translated response is sent back to the MCP client, which displays it to the user.

**Primary Motivations:**

* **Model Choice:** Access models from other providers (e.g., Gemini, GPT-4) that may have different strengths.  
* **Cost Optimization:** Route requests to cheaper models (like Haiku or Gemini Flash) for less complex tasks.  
* **Content Filter Differences:** Use models or providers that may have less restrictive content filters for certain creative or role-playing applications.

An example configuration for claude-code-proxy might involve setting environment variables in a .env file to specify the preferred provider and model mappings :  
`#.env file for a proxy server`  
`OPENAI_API_KEY="sk-..."`  
`GEMINI_API_KEY="AIza..."`  
`PREFERRED_PROVIDER="google"`  
`BIG_MODEL="gemini-2.5-pro-preview-03-25"`  
`SMALL_MODEL="gemini-2.0-flash"`

### **Appendix C: Reference Tables**

This section provides a consolidated collection of the key reference tables from this guide for quick access.  
**Table 1: Popular Community MCP Servers** | Server Name | Primary Function | GitHub Repository | Key Features | | :--- | :--- | :--- | :--- | | **DesktopCommanderMCP** | Terminal & Filesystem Control | wonderwhy-er/DesktopCommanderMCP | Execute shell commands, manage processes, advanced file search (ripgrep), diff-based editing, detailed logging. | | **claude-code-mcp** | Agentic CLI Execution | steipete/claude-code-mcp | Exposes the claude CLI itself as a tool, with a \--dangerously-skip-permissions flag for enabling complex, unattended agentic workflows. | | **claude-search-mcp** | Web Search | Doriandarko/claude-search-mcp | Provides a web search tool using the Claude API. Supports domain filtering and configurable result limits. | | **zen-mcp-server** | AI Model Orchestration | BeehiveInnovations/zen-mcp-server | Gives Claude access to other models (Gemini, OpenAI) as tools, allowing it to delegate sub-tasks to the most suitable AI. | | **mcp-server-reddit** | Reddit Integration | (Community Project) | Fetches and summarizes hot, new, or top posts and comments from specified subreddits. | | **CWM-API-Gateway-MCP** | Enterprise API Gateway | jasondsmith72/CWM-API-Gateway-MCP | Acts as a gateway to the ConnectWise Manage API, simplifying complex API interactions into natural language prompts. |  
**Table 2: Anthropic API Rate Limits (Standard Tier)** | Model | Maximum RPM | Maximum ITPM | Maximum OTPM | | :--- | :--- | :--- | :--- | | Claude Opus 4 | 50 | 20,000 | 8,000 | | Claude Sonnet 4 | 50 | 20,000 | 8,000 | | Claude Sonnet 3.5 (2024-06-20) | 50 | 40,000 | 8,000 | | Claude Haiku 3.5 | 50 | 50,000 | 10,000 | | Claude Opus 3 | 50 | 20,000 | 4,000 | | Claude Sonnet 3 | 50 | 40,000 | 8,000 | | Claude Haiku 3 | 50 | 50,000 | 10,000 |  
**Table 3: Comprehensive Troubleshooting Guide** | Symptom / Error Message | Potential Causes | Recommended Actions | | :--- | :--- | :--- | | Server not listed or not "running" in UI. | 1\. Claude was not fully restarted. \<br\> 2\. Syntax error in claude\_desktop\_config.json. \<br\> 3\. Incorrect path to command or runtime. | 1\. Quit Claude from system tray/menu bar and relaunch. \<br\> 2\. Use a JSON validator to check your config file. \<br\> 3\. Verify paths are absolute and correct for your OS. | | "Server disconnected" error. | 1\. Bug in a specific version of the MCP server. \<br\> 2\. A long-running command finished or crashed. | 1\. Check the server's GitHub issues for known problems with your version. \<br\> 2\. Check the mcp-server-SERVERNAME.log file for error output from the server process. | | Unexpected token 'T', "Terminate "... is not valid JSON | A process is printing non-JSON text to stdout, which the client cannot parse. Often occurs with long-running commands. | Check the server's GitHub issues; this is likely a bug in how the server handles command output. | | Claude Desktop crashes during a long response. | A specific MCP server may have a memory leak or instability when handling large amounts of data. | Identify which server is active. Try disabling it to confirm it's the cause. Report the issue on the server's GitHub repository. | | A specific tool (e.g., search\_code) fails every time. | 1\. Missing dependency for that tool (e.g., ripgrep not installed). \<br\> 2\. Bug within the tool's implementation. | 1\. Check the server's documentation for prerequisites. \<br\> 2\. Report the issue on the server's GitHub repository. |

#### **Works cited**

1\. auchenberg/claude-code-mcp \- GitHub, https://github.com/auchenberg/claude-code-mcp 2\. What is MCP: Clearing the Air : r/ClaudeAI \- Reddit, https://www.reddit.com/r/ClaudeAI/comments/1j92kbd/what\_is\_mcp\_clearing\_the\_air/ 3\. ujisati/claude-code-provider-proxy \- GitHub, https://github.com/ujisati/claude-code-provider-proxy 4\. 1rgs/claude-code-proxy: Run Claude Code on OpenAI models \- GitHub, https://github.com/1rgs/claude-code-proxy 5\. maxnowack/anthropic-proxy: Proxy server that converts Anthropic API requests to OpenAI format and sends it to OpenRouter. It's used to use Claude Code with OpenRouter instead of the Anthropic API \- GitHub, https://github.com/maxnowack/anthropic-proxy 6\. README.md \- 1rgs/claude-code-proxy \- GitHub, https://github.com/1rgs/claude-code-proxy/blob/main/README.md 7\. Here's how to use proxies, Deepseek, Claude, and Openrouter : r/JanitorAI\_Official \- Reddit, https://www.reddit.com/r/JanitorAI\_Official/comments/1ikn1d7/heres\_how\_to\_use\_proxies\_deepseek\_claude\_and/ 8\. anthropics/claude-code: Claude Code is an agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster by executing routine tasks, explaining complex code, and handling git workflows \- all through natural language commands. \- GitHub, https://github.com/anthropics/claude-code 9\. What's the difference between Claude Code and MCP? : r/ClaudeAI \- Reddit, https://www.reddit.com/r/ClaudeAI/comments/1johk1b/whats\_the\_difference\_between\_claude\_code\_and\_mcp/ 10\. www.reddit.com, https://www.reddit.com/r/ClaudeAI/comments/1h55zxd/can\_someone\_explain\_mcp\_to\_me\_how\_are\_you\_using/\#:\~:text=MCP%20essentially%20allows%20you%20to,you%20couldn't%20do%20before. 11\. steipete/claude-code-mcp: Claude Code as one-shot MCP server to have an agent in your agent. \- GitHub, https://github.com/steipete/claude-code-mcp 12\. wonderwhy-er/DesktopCommanderMCP: This is MCP ... \- GitHub, https://github.com/wonderwhy-er/DesktopCommanderMCP 13\. A MCP server that provides web search capabilities using the Claude API. \- GitHub, https://github.com/doriandarko/claude-search-mcp 14\. Remote GitHub MCP Server is now in public preview \- GitHub Changelog, https://github.blog/changelog/2025-06-12-remote-github-mcp-server-is-now-available-in-public-preview/ 15\. ConnectWise Manage API Gateway MCP Server for Claude \- GitHub, https://github.com/jasondsmith72/CWM-API-Gateway-MCP 16\. Must-Have MCP Servers for Coding and Beyond : r/ClaudeAI \- Reddit, https://www.reddit.com/r/ClaudeAI/comments/1k0f3vs/musthave\_mcp\_servers\_for\_coding\_and\_beyond/ 17\. Claude Code overview \- Anthropic API, https://docs.anthropic.com/s/claude-code-security 18\. eyaltoledano/claude-task-master: An AI-powered task-management system you can drop into Cursor, Lovable, Windsurf, Roo, and others. \- GitHub, https://github.com/eyaltoledano/claude-task-master 19\. The Easiest Way to Set Up MCP with Claude Desktop and Docker Desktop, https://dev.to/suzuki0430/the-easiest-way-to-set-up-mcp-with-claude-desktop-and-docker-desktop-5o 20\. Model Context Protocol (MCP) \- Anthropic API, https://docs.anthropic.com/en/docs/claude-code/mcp 21\. Connect Claude to MCP Servers for Better AI Capabilities \- MESA, https://www.getmesa.com/blog/how-to-connect-mcp-server-claude/ 22\. How to use an MCP Server in Claude Desktop, https://blog.egmond.dev/mcp-server-claude 23\. For Claude Desktop Users \- Model Context Protocol, https://modelcontextprotocol.io/quickstart/user 24\. Claude Desktop Commander MCP \- Glama, https://glama.ai/mcp/servers/@wonderwhy-er/DesktopCommanderMCP 25\. My Claude Workflow Guide: Advanced Setup with MCP External ..., https://www.reddit.com/r/ClaudeAI/comments/1ji8ruv/my\_claude\_workflow\_guide\_advanced\_setup\_with\_mcp/ 26\. Getting Started with Model Context Protocol Part 1: Add a Simple MCP Server to Claude Desktop \- Daniel Liden, https://www.danliden.com/posts/20250412-mcp-quickstart.html 27\. BeehiveInnovations/zen-mcp-server: The power of Claude Code \+ \[Gemini Pro / Flash / O3 / O3-Mini / OpenRouter / Ollama / Custom Model / All Of The Above\] working as one. \- GitHub, https://github.com/BeehiveInnovations/zen-mcp-server 28\. About Custom Integrations Using Remote MCP | Anthropic Help Center, https://support.anthropic.com/en/articles/11175166-about-custom-integrations-using-remote-mcp 29\. litongjava/tauri-claude: Claude Desktop \- GitHub, https://github.com/litongjava/tauri-claude 30\. Every front-end GUI client for ChatGPT, Claude, and other LLMs \- GitHub, https://github.com/billmei/every-chatgpt-gui 31\. runekaagaard/claude-local-files \- GitHub, https://github.com/runekaagaard/claude-local-files 32\. showlab/computer\_use\_ootb: Out-of-the-box (OOTB) GUI Agent for Windows and macOS \- GitHub, https://github.com/showlab/computer\_use\_ootb 33\. API Key Best Practices: Keeping Your Keys Safe and Secure | Anthropic Help Center, https://support.anthropic.com/en/articles/9767949-api-key-best-practices-keeping-your-keys-safe-and-secure 34\. Manage permissions and security \- Anthropic API, https://docs.anthropic.com/en/docs/claude-code/security 35\. Mitigate jailbreaks and prompt injections \- Anthropic API, https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks 36\. Rate limits \- Anthropic API, https://docs.anthropic.com/en/api/rate-limits 37\. Our approach to API rate limits | Anthropic Help Center, https://support.anthropic.com/en/articles/8243635-our-approach-to-api-rate-limits 38\. Understanding rate limits anthropic api for scalable tech tools \- BytePlus, https://www.byteplus.com/en/topic/448917 39\. Hitting Claude API Rate Limits? Here's What You Need to Do \- Apidog, https://apidog.com/blog/claude-api-rate-limits/ 40\. Issues · wonderwhy-er/DesktopCommanderMCP · GitHub, https://github.com/wonderwhy-er/DesktopCommanderMCP/issues 41\. Legal and compliance \- Anthropic API, https://docs.anthropic.com/en/docs/claude-code/legal-and-compliance 42\. Can I use the Anthropic API for individual use?, https://support.anthropic.com/en/articles/8987200-can-i-use-the-anthropic-api-for-individual-use 43\. Expanded legal protections and improvements to our API \- Anthropic, https://www.anthropic.com/news/expanded-legal-protections-api-improvements 44\. Updating our Usage Policy \- Anthropic, https://www.anthropic.com/news/updating-our-usage-policy 45\. Claude Proxy for low spender : r/JanitorAI\_Official \- Reddit, https://www.reddit.com/r/JanitorAI\_Official/comments/1befrfp/claude\_proxy\_for\_low\_spender/ 46\. How does Claude work?? I need some help : r/JanitorAI\_Official \- Reddit, https://www.reddit.com/r/JanitorAI\_Official/comments/1huvvcp/how\_does\_claude\_work\_i\_need\_some\_help/