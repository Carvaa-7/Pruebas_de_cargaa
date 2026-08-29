package edu.unisabana.tyvs.registry.config;

import edu.unisabana.tyvs.registry.application.port.out.RegistryRepositoryPort;
import edu.unisabana.tyvs.registry.application.usecase.Registry;
import edu.unisabana.tyvs.registry.infrastructure.persistence.RegistryRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Cableado de la aplicacion (composition root).
 *
 * La URL JDBC se lee de una propiedad, con un valor por defecto, en vez de
 * estar escrita en el codigo. No es cosmetico: permite que cada prueba de
 * integracion use su propia base en memoria y no contamine a las demas, y
 * evita tener que declarar beans alternativos en la prueba.
 *
 * Ese ultimo punto tiene una trampa que costo un build en rojo: si una prueba
 * declara un @TestConfiguration con un @Bean llamado igual que uno de aqui
 * (el nombre del bean es el nombre del METODO), Spring aborta el arranque con
 * BeanDefinitionOverrideException. Parametrizar la URL hace innecesarios esos
 * beans duplicados.
 */
@Configuration
public class RegistryConfig {

    @Bean
    public RegistryRepositoryPort registryRepositoryPort(
            @Value("${registry.jdbc-url:jdbc:h2:mem:regdb;DB_CLOSE_DELAY=-1}") String jdbcUrl)
            throws Exception {
        RegistryRepository repo = new RegistryRepository(jdbcUrl);
        repo.initSchema();
        return repo;
    }

    @Bean
    public Registry registry(RegistryRepositoryPort port) {
        return new Registry(port);
    }
}
