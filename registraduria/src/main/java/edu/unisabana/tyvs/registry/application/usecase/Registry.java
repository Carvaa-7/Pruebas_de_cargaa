package edu.unisabana.tyvs.registry.application.usecase;

import edu.unisabana.tyvs.registry.application.port.out.RegistryRepositoryPort;
import edu.unisabana.tyvs.registry.domain.model.Person;
import edu.unisabana.tyvs.registry.domain.model.RegisterResult;

/**
 * Caso de uso: registrar un votante.
 *
 * Las reglas son las MISMAS que en los talleres de pruebas unitarias y de
 * integracion. Es la misma Registraduria: una regla de negocio no puede
 * cambiar segun el taller desde el que se mire.
 *
 * En este taller la clase no es el objeto de estudio —lo es su comportamiento
 * bajo carga—, pero los scripts de k6 comprueban el resultado de negocio de
 * cada peticion, no solo el codigo HTTP. Por eso las reglas tienen que ser
 * exactas: si aqui devolviera UNDERAGE donde el CSV espera INVALID_AGE, la
 * prueba de carga fallaria y estaria en lo cierto.
 */
public class Registry {

    /** Edad minima para votar. */
    public static final int MIN_AGE = 18;

    /** Edad maxima biologicamente posible; por encima, el dato es imposible. */
    public static final int MAX_AGE = 120;

    private final RegistryRepositoryPort repo;

    public Registry(RegistryRepositoryPort repo) {
        this.repo = repo;
    }

    public RegisterResult registerVoter(Person p) {
        if (p == null)
            return RegisterResult.INVALID;
        if (p.getId() <= 0)
            return RegisterResult.INVALID;
        if (!p.isAlive())
            return RegisterResult.DEAD;
        // El orden importa: una edad imposible se descarta ANTES de preguntar
        // si es menor de edad. Si se invirtiera, -1 caeria en la rama de
        // UNDERAGE e INVALID_AGE quedaria inalcanzable.
        if (p.getAge() < 0 || p.getAge() > MAX_AGE)
            return RegisterResult.INVALID_AGE;
        if (p.getAge() < MIN_AGE)
            return RegisterResult.UNDERAGE;

        try {
            if (repo.existsById(p.getId()))
                return RegisterResult.DUPLICATED;
            repo.save(p.getId(), p.getName(), p.getAge(), p.isAlive());
            return RegisterResult.VALID;
        } catch (Exception e) {
            // El detalle tecnico va en la causa, no en el mensaje que ve el
            // cliente. Bajo carga esto importa mas de lo normal: un mensaje
            // con la excepcion cruda se repite miles de veces en los logs.
            throw new IllegalStateException("No se pudo registrar al votante", e);
        }
    }
}
