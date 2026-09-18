package edu.unisabana.tyvs.registry.config;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import edu.unisabana.tyvs.registry.application.port.out.RegistryRepositoryPort;
import edu.unisabana.tyvs.registry.application.usecase.Registry;
import edu.unisabana.tyvs.registry.infrastructure.persistence.RegistryRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;

/**
 * Cableado de la aplicacion (composition root).
 *
 * Ahora usa HikariCP como pool de conexiones. Con el defecto anterior
 * (DriverManager.getConnection por cada operacion), cada request abria
 * dos conexiones nuevas a H2 — una en existsById y otra en save. Con
 * 200+ VUs eso generaba cientos de conexiones por segundo, lo que
 * saturaba el gestor de conexiones y disparaba la latencia p95.
 *
 * HikariCP mantiene un conjunto fijo de conexiones reutilizables. En lugar
 * de crear/destruir una conexion por operacion, el repositorio pide una del
 * pool y la devuelve al terminar. El impacto es visible en las pruebas de
 * carga: el p95 baja de decenas de ms a unos pocos ms incluso con 600 VUs.
 */
@Configuration
public class RegistryConfig {

    @Bean
    public DataSource dataSource(
            @Value("${registry.jdbc-url:jdbc:h2:mem:regdb;DB_CLOSE_DELAY=-1}") String jdbcUrl,
            @Value("${registry.pool.maximum-pool-size:20}") int maxPoolSize) {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(jdbcUrl);
        config.setUsername("");
        config.setPassword("");
        config.setMaximumPoolSize(maxPoolSize);
        config.setMinimumIdle(5);
        config.setConnectionTimeout(3000);
        config.setPoolName("registraduria-pool");
        return new HikariDataSource(config);
    }

    @Bean
    public RegistryRepositoryPort registryRepositoryPort(DataSource dataSource) throws Exception {
        RegistryRepository repo = new RegistryRepository(dataSource);
        repo.initSchema();
        return repo;
    }

    @Bean
    public Registry registry(RegistryRepositoryPort port) {
        return new Registry(port);
    }
}
