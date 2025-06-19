package dev.ziriuz.mcp.tools;

import dev.ziriuz.mcp.services.DatabaseChatService;

//@Service
public class DatabaseRetrievalTools {

  //  @Autowired
    private DatabaseChatService databaseChatService;

    //@Tool(description = "Call this whenever you need information about: products, customers and orders")
    public String customerAssistanceTool(String query) {
        return databaseChatService.getResponse(query);
    }

}
