package dev.ziriuz.mcp.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import dev.ziriuz.mcp.services.DatabaseChatService;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.McpSyncServer;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.server.transport.WebFluxSseServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;
import io.modelcontextprotocol.spec.McpServerTransportProvider;
import org.springframework.ai.mcp.McpToolUtils;
import org.springframework.ai.support.ToolCallbacks;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.RouterFunction;

@Configuration
public class ModelContextProtocolServerConfig {

    // STDIO transport
    @Bean
    @ConditionalOnProperty(prefix = "transport", name = "mode", havingValue = "stdio")
    public StdioServerTransportProvider stdioServerTransportProvider() {
        return new StdioServerTransportProvider();
    }

    // SSE transport
    @Bean
    @ConditionalOnProperty(prefix = "transport", name = "mode", havingValue = "sse", matchIfMissing = true)
    public WebFluxSseServerTransportProvider sseServerTransportProvider() {
        return new WebFluxSseServerTransportProvider(new ObjectMapper(), "/mcp/message");
    }

    // Router function for SSE transport used by Spring WebFlux to start an HTTP
    // server.
    @Bean
    @ConditionalOnProperty(prefix = "transport", name = "mode", havingValue = "sse", matchIfMissing = true)
    public RouterFunction<?> mcpRouterFunction(WebFluxSseServerTransportProvider transportProvider) {
        return transportProvider.getRouterFunction();
    }

    @Bean
    public McpSyncServer mcpServer(McpServerTransportProvider transportProvider, DatabaseChatService databaseChatService) { // @formatter:off

        // Configure server capabilities with resource support
        var capabilities = McpSchema.ServerCapabilities.builder()
                .tools(true) // Tool support with list changes notifications
                .logging() // Logging support
                .build();

        // Create the server with both tool and resource capabilities
        return McpServer.sync(transportProvider)
                .serverInfo("MCP Database Retrieval Server", "0.0.1")
                .capabilities(capabilities)
                .tools(McpToolUtils.toSyncToolSpecifications(ToolCallbacks.from(databaseChatService))) // Add @Tools
                .build();
    }
}
