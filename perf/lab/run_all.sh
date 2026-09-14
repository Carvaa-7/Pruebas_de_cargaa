#!/usr/bin/env bash
# Bateria completa usada para las graficas de la presentacion (~45 min).
# El driver retoma lo que ya este en results/: si se interrumpe, basta volver a correrlo.
set -e
cd "$(dirname "$0")"
echo "== modelo cerrado, sin pool";  python driver.py closed nopool 1,10,25,50,100,200,400,800 20s 2
echo "== modelo cerrado, con pool";  python driver.py closed pool   1,10,25,50,100,200,400,800 20s 2
echo "== modelo abierto, sin pool";  python driver.py open   nopool 1000,2000,3000,4000,5000,6000,7000,8000,10000 20s 2
echo "== modelo abierto, con pool";  python driver.py open   pool   2000,4000,6000,8000,10000,12000 20s 2
echo "== percentiles, sin pool";     python driver.py hist   nopool 100
echo "== pico, sin pool";            python driver.py spike  nopool 20 400
python export_data.py
echo "Listo. Regenere la presentacion con: python deck/build.py"
