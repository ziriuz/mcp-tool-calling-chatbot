package dev.ziriuz.mcp.tools;

import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

@Component
public class ConversationalResponse {

    @Tool(description = "Respond in a conversational manner. Be kind and helpful.")
    public String echo(
            @ToolParam(description = "A conversational response to the user's query")
            String assistantResponse
    )
    {
        return assistantResponse;
    }

}
