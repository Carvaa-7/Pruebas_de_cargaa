package edu.unisabana.tyvs.registry.domain.model;

/**
 * Resultado posible de un intento de registro de votante.
 *
 * Mismo conjunto de constantes que en los talleres de pruebas unitarias y de
 * integracion: es la misma Registraduria.
 */
public enum RegisterResult {
    /** Persona viva, mayor de edad, id valido y no registrada previamente. */
    VALID,
    /** Persona nula o con id invalido (id <= 0). */
    INVALID,
    /** Edad dentro del rango 0..17. */
    UNDERAGE,
    /** La persona no esta viva. */
    DEAD,
    /** El id ya fue registrado antes. */
    DUPLICATED,
    /** Edad fuera del rango biologicamente posible (< 0 o > 120). */
    INVALID_AGE
}
