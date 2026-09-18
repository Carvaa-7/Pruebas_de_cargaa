package edu.unisabana.tyvs.registry.infrastructure.persistence;

import edu.unisabana.tyvs.registry.application.port.out.RegistryRepositoryPort;
import javax.sql.DataSource;
import java.sql.*;
import java.util.Optional;

public class RegistryRepository implements RegistryRepositoryPort {
    private final DataSource dataSource;

    /**
     * Constructor principal: recibe un DataSource (puede ser HikariCP en prod
     * o un DataSource simple en pruebas unitarias/integración).
     */
    public RegistryRepository(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /**
     * Constructor de compatibilidad para pruebas existentes que pasan una URL.
     * Crea un DataSource mínimo sin pool — solo para tests con H2 en memoria.
     */
    public RegistryRepository(String jdbcUrl) {
        this(jdbcUrl, "", "");
    }

    public RegistryRepository(String jdbcUrl, String username, String password) {
        // DataSource mínimo para tests: crea una conexión nueva cada vez (sin pool).
        // En producción se usa el constructor DataSource con HikariCP.
        this.dataSource = new javax.sql.DataSource() {
            public Connection getConnection() throws SQLException {
                return DriverManager.getConnection(jdbcUrl, username, password);
            }
            public Connection getConnection(String u, String p) throws SQLException {
                return DriverManager.getConnection(jdbcUrl, u, p);
            }
            public <T> T unwrap(Class<T> iface) { throw new UnsupportedOperationException(); }
            public boolean isWrapperFor(Class<?> iface) { return false; }
            public java.io.PrintWriter getLogWriter() { return null; }
            public void setLogWriter(java.io.PrintWriter pw) {}
            public void setLoginTimeout(int s) {}
            public int getLoginTimeout() { return 0; }
            public java.util.logging.Logger getParentLogger() { return null; }
        };
    }

    private Connection getConnection() throws SQLException {
        // Ahora pide la conexión al pool en lugar de crearla desde cero
        return dataSource.getConnection();
    }

    @Override
    public void initSchema() throws Exception {
        final String ddl = "CREATE TABLE IF NOT EXISTS registry(" +
                " id INT PRIMARY KEY," +
                " name VARCHAR(100) NOT NULL," +
                " age INT NOT NULL," +
                " is_alive BOOLEAN NOT NULL" +
                ");";
        try (Connection con = getConnection(); Statement st = con.createStatement()) {
            st.execute(ddl);
        }
    }

    @Override
    public boolean existsById(int id) throws Exception {
        final String sql = "SELECT 1 FROM registry WHERE id = ?";
        try (Connection con = getConnection(); PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setInt(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next();
            }
        }
    }

    @Override
    public void save(int id, String name, int age, boolean isAlive) throws Exception {
        final String sql = "INSERT INTO registry(id, name, age, is_alive) VALUES(?, ?, ?, ?)";
        try (Connection con = getConnection(); PreparedStatement ps = con.prepareStatement(sql)) {
            boolean prev = con.getAutoCommit();
            con.setAutoCommit(false);
            try {
                ps.setInt(1, id);
                ps.setString(2, name);
                ps.setInt(3, age);
                ps.setBoolean(4, isAlive);
                ps.executeUpdate();
                con.commit();
            } catch (SQLException e) {
                con.rollback();
                throw e;
            } finally {
                con.setAutoCommit(prev);
            }
        }
    }

    @Override
    public Optional<RegistryRecord> findById(int id) throws Exception {
        final String sql = "SELECT id, name, age, is_alive FROM registry WHERE id = ?";
        try (Connection con = getConnection(); PreparedStatement ps = con.prepareStatement(sql)) {
            ps.setInt(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next())
                    return Optional.empty();
                return Optional.of(new RegistryRecord(
                        rs.getInt("id"),
                        rs.getString("name"),
                        rs.getInt("age"),
                        rs.getBoolean("is_alive")));
            }
        }
    }

    @Override
    public void deleteAll() throws Exception {
        try (Connection con = getConnection(); Statement st = con.createStatement()) {
            st.executeUpdate("DELETE FROM registry");
        }
    }
}
