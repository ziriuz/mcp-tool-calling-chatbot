package dev.ziriuz.mcp;

import dev.ziriuz.mcp.services.DatabaseChatService;
import io.modelcontextprotocol.client.McpSyncClient;
import io.modelcontextprotocol.spec.McpSchema;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;
import java.util.Map;

@SpringBootTest
class SpringAiDemoApplicationTests {

	@Autowired
	private List<McpSyncClient> mcpClients;

	@Autowired
	private DatabaseChatService databaseChatService;

	@Test
	void contextLoads() {
	}

	@Test
	void mcpClients_test() {
		mcpClients.forEach(
				client -> System.out.println("Available tools: " + client.listTools())
		);

		System.out.println("=====================================================================");
		McpSchema.CallToolRequest request = new McpSchema.CallToolRequest("list_tables", Map.of());
		var result = mcpClients.getFirst().callTool(request);
		System.out.println("list_tables call tool result: " + result);

		System.out.println("=====================================================================");
		var describeTableResult = mcpClients.getFirst().callTool(
				new McpSchema.CallToolRequest("describe_table", Map.of("table_name","products"))
		);
		System.out.println("describe_table(products) call tool result: " + describeTableResult);
	}

	@Test
	void databaseChatService_test() {
		var response = databaseChatService.getResponse("5 most expensive products");
		System.out.println(response);
	}

}
