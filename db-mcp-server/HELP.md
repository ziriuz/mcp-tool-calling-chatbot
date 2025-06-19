# Getting Started


## Troubleshooting

Here is some problems which were faced during implementation and solutions

1. WebFlux doesn't support `@RequestParam` when data is sent in POST request form html form.  
   Solution is to use ServerWebExchange as parameter in controller method  
```java
    @PostMapping(
            path = "/chat",
            consumes = {MediaType.APPLICATION_FORM_URLENCODED_VALUE}
    )
    public Mono<String> queryLLMReactive(ServerWebExchange serverWebExchange, Model model) {
        return serverWebExchange.getFormData().log()
                .map(request -> request.getFirst("question"))
                .doOnNext(question -> {
                    System.out.printf("Q: %s%n", question);
                    model.addAttribute("question", question);
                })
                .flatMap(chatService::getResponseAsMono)
                .doOnNext(response -> {
                    System.out.printf("A: %s%n", response);
                    model.addAttribute("answer", response);
                })
                .map(response ->  "chat");
    }
```
2. When response from `Ollama` is delayed, request fails with error `io.netty.handler.timeout.ReadTimeoutException: null`  
   To fix this problem create custom `RestClient.Builder` and `WebClient.Builder` Beans with bigger timeouts 
```java
    /**
     * OllamaApi is using WebClient.Builder to create WebClient for streaming.
     * This Bean is created to reconfigure connect and read timeouts, to give more time to LLM to generate response
     *
     * @return WebClient Builder with custom configuration
     */
    @Bean
    public WebClient.Builder createWebClient() {
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 1000 * connectTimeoutSec)
                .doOnConnected(conn -> conn.addHandlerLast(new ReadTimeoutHandler(readTimeoutSec, TimeUnit.SECONDS)));

        return WebClient.builder()
                .clientConnector(new ReactorClientHttpConnector(httpClient));
    }

    /**
     * OllamaApi is using RestClient.Builder to create RestClient.
     * This Bean is created to reconfigure connect and read timeouts, to give more time to LLM to generate response
     *
     * @return RestClient Builder with custom configuration
     */
    @Bean
    public RestClient.Builder getRestClientBuilder(){
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(connectTimeoutSec));
        factory.setReadTimeout(Duration.ofSeconds(readTimeoutSec));
        return RestClient.builder().requestFactory(factory);
    }
```




### Reference Documentation
For further reference, please consider the following sections:

* [Official Gradle documentation](https://docs.gradle.org)
* [Spring Boot Gradle Plugin Reference Guide](https://docs.spring.io/spring-boot/3.4.2/gradle-plugin)
* [Create an OCI image](https://docs.spring.io/spring-boot/3.4.2/gradle-plugin/packaging-oci-image.html)
* [Ollama](https://docs.spring.io/spring-ai/reference/api/chat/ollama-chat.html)

### Additional Links
These additional references should also help you:

* [Gradle Build Scans – insights for your project's build](https://scans.gradle.com#gradle)

