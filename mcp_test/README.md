# Cursor 作为 MCP Host 配置指南

## 什么是 MCP？

Model Context Protocol (MCP) 是一个开放协议，允许 Cursor 连接外部工具和数据源，从而扩展其功能。

## 配置步骤

### 1. 创建 MCP 配置文件

在项目根目录或全局配置目录创建 `mcp.json` 文件。配置文件支持两种位置：

- **项目级别**：`/path/to/your/project/mcp.json`
- **全局级别**：`~/.cursor/mcp.json` 或 `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`

### 2. 配置文件格式

`mcp.json` 文件使用 JSON 格式，包含以下结构：

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

### 3. 通过 Cursor 设置界面配置

1. 打开 Cursor 设置（`Cmd/Ctrl + ,`）
2. 导航至 **功能** > **MCP**
3. 点击 **"+ 添加新的 MCP 服务器"** 按钮
4. 根据传输方式填写服务器信息：
   - **stdio**：标准输入输出传输
   - **SSE**：Server-Sent Events 传输

### 4. 使用命令行工具管理 MCP 服务器

Cursor 提供了 `cursor-agent` 命令行工具来管理 MCP 服务器：

#### 列出所有已配置的服务器
```bash
cursor-agent mcp list
```

#### 查看特定服务器的工具
```bash
cursor-agent mcp list-tools <server-identifier>
```

#### 使用 MCP 工具执行任务
```bash
cursor-agent --prompt "你的任务描述"
```

## 常用 MCP 服务器示例

### 文件系统服务器
允许访问本地文件系统：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    }
  }
}
```

### Brave 搜索服务器
提供网络搜索功能：

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-api-key"
      }
    }
  }
}
```

### GitHub 服务器
集成 GitHub 功能：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token"
      }
    }
  }
}
```

### 自定义服务器
运行你自己的 MCP 服务器：

```json
{
  "mcpServers": {
    "my-custom-server": {
      "command": "node",
      "args": ["/path/to/your/server.js"],
      "env": {
        "CUSTOM_API_KEY": "your-key"
      }
    }
  }
}
```

## 传输方式

### stdio（标准输入输出）
适用于本地运行的服务器，通过标准输入输出进行通信。

### SSE（Server-Sent Events）
适用于远程服务器，通过 HTTP 连接进行通信。

## 注意事项

1. **安全性**：确保不要将敏感信息（如 API 密钥）提交到版本控制系统
2. **环境变量**：使用环境变量存储敏感配置
3. **路径**：使用绝对路径或确保命令在 PATH 中可用
4. **权限**：确保 Cursor 有权限执行配置的命令

## 故障排除

1. **服务器无法启动**：检查命令路径和参数是否正确
2. **工具不可用**：使用 `cursor-agent mcp list-tools` 检查服务器是否正常运行
3. **权限错误**：确保 Cursor 有执行命令的权限

## 更多资源

- [Cursor MCP 官方文档](https://docs.cursor.com/zh/context/mcp)
- [Model Context Protocol 规范](https://modelcontextprotocol.io)

