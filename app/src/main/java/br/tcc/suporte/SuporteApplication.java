package br.tcc.suporte;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class SuporteApplication {
    public static void main(String[] args) {
        SpringApplication.run(SuporteApplication.class, args);
    }
}
