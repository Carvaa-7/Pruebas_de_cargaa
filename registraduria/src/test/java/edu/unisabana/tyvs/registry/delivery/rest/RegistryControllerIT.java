package edu.unisabana.tyvs.registry.delivery.rest;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringRunner;

import static org.junit.Assert.assertEquals;

/**
 * Prueba de integracion del endpoint que despues se somete a carga con k6.
 *
 * Sirve de comprobacion previa: si el contrato del endpoint no se cumple con
 * una sola peticion, no tiene sentido lanzarle cien por segundo. Un escenario
 * de carga contra un endpoint roto solo mide lo rapido que devuelve errores.
 *
 * DOS DETALLES QUE COSTARON UN BUILD EN ROJO, y merece la pena conocerlos:
 *
 * 1. Esta clase declaraba un @TestConfiguration con beans propios llamados
 *    `registryRepositoryPort` y `registry`. Como el nombre de un bean es el
 *    nombre del metodo, chocaban con los de RegistryConfig y Spring abortaba
 *    con BeanDefinitionOverrideException. La solucion no es renombrar: es no
 *    duplicar. La URL de la base se inyecta ahora por propiedad.
 *
 * 2. Las comprobaciones usaban la palabra clave `assert` de Java, no
 *    aserciones de JUnit. Maven habilita las aserciones al ejecutar, asi que
 *    funcionaban aqui; pero al lanzar la prueba desde el IDE sin el flag -ea
 *    se desactivan y la prueba pasa SIEMPRE, sin comprobar nada. Un fallo
 *    silencioso que ademas depende de como se ejecute.
 */
@RunWith(SpringRunner.class)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@TestPropertySource(properties = "registry.jdbc-url=jdbc:h2:mem:regdb_ctrl_it;DB_CLOSE_DELAY=-1")
public class RegistryControllerIT {

    @Autowired
    private TestRestTemplate rest;

    private ResponseEntity<String> registrar(String json) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        return rest.postForEntity("/register", new HttpEntity<>(json, headers), String.class);
    }

    @Test
    public void shouldRegisterValidPerson() {
        ResponseEntity<String> resp = registrar(
                "{\"name\":\"Ana\",\"id\":100,\"age\":30,\"gender\":\"FEMALE\",\"alive\":true}");

        assertEquals(HttpStatus.OK, resp.getStatusCode());
        assertEquals("VALID", resp.getBody());
    }

    @Test
    public void shouldRejectUnderage() {
        // El escenario de carga envia una mezcla de casos validos, menores y
        // no vivos. Si el servicio dejara de distinguirlos, k6 seguiria viendo
        // 200 y la prueba de carga saldria verde con el sistema roto: por eso
        // el script comprueba el resultado de negocio y no solo el codigo HTTP.
        ResponseEntity<String> resp = registrar(
                "{\"name\":\"Sara\",\"id\":101,\"age\":17,\"gender\":\"FEMALE\",\"alive\":true}");

        assertEquals(HttpStatus.OK, resp.getStatusCode());
        assertEquals("UNDERAGE", resp.getBody());
    }

    @Test
    public void shouldRejectDeadPerson() {
        ResponseEntity<String> resp = registrar(
                "{\"name\":\"Pedro\",\"id\":102,\"age\":45,\"gender\":\"MALE\",\"alive\":false}");

        assertEquals(HttpStatus.OK, resp.getStatusCode());
        assertEquals("DEAD", resp.getBody());
    }

    @Test
    public void shouldRejectDuplicatedId() {
        // Importa para la prueba de carga: el generador de datos de k6 tiene
        // que producir identificadores unicos entre usuarios virtuales, o la
        // mitad de las peticiones devolveria DUPLICATED y la medicion no
        // reflejaria el camino que se queria medir.
        registrar("{\"name\":\"Luis\",\"id\":103,\"age\":40,\"gender\":\"MALE\",\"alive\":true}");

        ResponseEntity<String> repetida = registrar(
                "{\"name\":\"Otro\",\"id\":103,\"age\":50,\"gender\":\"MALE\",\"alive\":true}");

        assertEquals(HttpStatus.OK, repetida.getStatusCode());
        assertEquals("DUPLICATED", repetida.getBody());
    }
}
