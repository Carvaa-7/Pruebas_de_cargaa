"""Construye la variante "con pool" de la registraduria en perf/lab/pool/.

Copia registraduria/ tal cual y cambia solo dos cosas:
  1. pom.xml: agrega HikariCP.
  2. RegistryRepository.getConnection(): toma la conexion de un pool de 20
     en lugar de abrir una nueva con DriverManager en cada operacion.

Todo lo demas queda identico, para que la comparacion antes/despues mida solo
el efecto del pool. perf/lab/pool/ no se versiona.

    python prepare_pool.py            # copia, modifica y ejecuta mvn package
"""
import os, shutil, subprocess

LAB = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(LAB, '..', '..', 'registraduria'))
DST = os.path.join(LAB, 'pool')


def replace_once(path, old, new):
    text = open(path, encoding='utf8').read()
    if text.count(old) != 1:
        raise SystemExit(f'No se encontro exactamente una vez el fragmento esperado en {path}:\n{old}')
    open(path, 'w', encoding='utf8').write(text.replace(old, new))


if os.path.exists(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('target'))

# Las mediciones de data/ se hicieron con HikariCP 5.1.0 (Boot 2.7 gestionaria la 4.0.3).
replace_once(os.path.join(DST, 'pom.xml'),
             '<artifactId>spring-boot-starter-actuator</artifactId>\n    </dependency>',
             '<artifactId>spring-boot-starter-actuator</artifactId>\n    </dependency>\n\n'
             '    <dependency>\n      <groupId>com.zaxxer</groupId>\n      <artifactId>HikariCP</artifactId>\n'
             '      <version>5.1.0</version>\n    </dependency>')

repo = os.path.join(DST, 'src', 'main', 'java', 'edu', 'unisabana', 'tyvs', 'registry', 'infrastructure',
                    'persistence', 'RegistryRepository.java')
replace_once(repo,
             '        this.password = password;\n    }',
             '        this.password = password;\n'
             '        com.zaxxer.hikari.HikariConfig cfg = new com.zaxxer.hikari.HikariConfig();\n'
             '        cfg.setJdbcUrl(jdbcUrl);\n'
             '        cfg.setUsername(username);\n'
             '        cfg.setPassword(password);\n'
             '        cfg.setMaximumPoolSize(20);\n'
             '        this.ds = new com.zaxxer.hikari.HikariDataSource(cfg);\n'
             '    }\n\n'
             '    private final com.zaxxer.hikari.HikariDataSource ds;')
replace_once(repo,
             'return DriverManager.getConnection(jdbcUrl, username, password);',
             'return ds.getConnection();')

mvn = 'mvn.cmd' if os.name == 'nt' else 'mvn'
subprocess.run([mvn, '-q', '-B', '-DskipTests', 'package'], cwd=DST, check=True)
print('Variante con pool lista en', os.path.join(DST, 'target'))
