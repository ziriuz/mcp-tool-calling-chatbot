package dev.ziriuz.mcp.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.client.RestClient;
import org.springframework.web.reactive.config.WebFluxConfigurer;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;
import java.util.concurrent.TimeUnit;


@Configuration
public class ApplicationConfig implements WebFluxConfigurer {

    @Value("${app.httpclient.read-timeout-sec:300}")
    private int readTimeoutSec;
    @Value("${app.httpclient.connect-timeout-sec:300}")
    private int connectTimeoutSec;

    /**
     * OllamaApi is using WebClient.Builder to create WebClient for streaming.
     * This Bean is created to reconfigure connect and read timeouts, to give more time to LLM to generate response
     *
     * @return WebClient Builder with custom configuration
     */
    @Bean
    public WebClient.Builder createWebClientBuilder() {
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

//    @Bean WebClient buildWebClient(WebClient.Builder builder) {
//        return builder.build();
//    }
//
//    @Bean RestClient buildRestClient(RestClient.Builder builder) {
//        return builder.build();
//    }

}
