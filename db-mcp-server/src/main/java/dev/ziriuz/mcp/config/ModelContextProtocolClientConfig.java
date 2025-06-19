package dev.ziriuz.mcp.config;

import io.modelcontextprotocol.client.McpClient;
import io.modelcontextprotocol.client.McpSyncClient;
import io.modelcontextprotocol.client.transport.ServerParameters;
import io.modelcontextprotocol.client.transport.StdioClientTransport;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.nio.file.Paths;
import java.time.Duration;

@Configuration
public class ModelContextProtocolClientConfig {

    @Value("${app.sqlitedb.location}")
    private String dbLocation;

    @Bean(destroyMethod = "close")
    public McpSyncClient mcpClient() {

        var stdioParams = ServerParameters.builder("uvx")
                .args("mcp-server-sqlite", "--db-path",
                        getDbPath())
                .build();

        var mcpClient = McpClient.sync(new StdioClientTransport(stdioParams))
                .requestTimeout(Duration.ofSeconds(10)).build();

        var init = mcpClient.initialize();

        System.out.println("MCP Initialized: " + init);

        return mcpClient;
    }
    private String getDbPath() {
        return Paths.get(System.getProperty("user.dir"), dbLocation).toString();
    }
}
