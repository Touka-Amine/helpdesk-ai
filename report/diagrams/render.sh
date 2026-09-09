#!/usr/bin/env bash
# Rend les diagrammes PlantUML du mémoire vers report/img/.
#
#   ./render.sh                 tous les .puml du répertoire, en PNG
#   ./render.sh ch06_classes    un seul diagramme
#   ./render.sh -f pdf          en PDF vectoriel (recommandé pour l'impression)
#
# Le moteur de mise en page est celui embarqué dans le jar : aucune installation
# de Graphviz n'est requise.

set -euo pipefail

FMT=png
if [ "${1:-}" = "-f" ]; then FMT="$2"; shift 2; fi

# Localisation du jar : variable d'environnement, puis emplacements usuels.
JAR="${PLANTUML_JAR:-}"
if [ -z "$JAR" ] || [ ! -f "$JAR" ]; then
  for c in "$LOCALAPPDATA/PlantUML/plantuml.jar" \
           "$HOME/AppData/Local/PlantUML/plantuml.jar" \
           "$HOME/.local/lib/plantuml.jar" \
           "/usr/share/plantuml/plantuml.jar"; do
    [ -f "$c" ] && JAR="$c" && break
  done
fi
if [ -z "$JAR" ] || [ ! -f "$JAR" ]; then
  echo "plantuml.jar introuvable. Installez-le puis exportez PLANTUML_JAR :" >&2
  echo "  curl -L -o \"\$LOCALAPPDATA/PlantUML/plantuml.jar\" \\" >&2
  echo "    https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar" >&2
  exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/../img"
mkdir -p "$OUT"

if [ "$#" -gt 0 ]; then
  FILES=()
  for n in "$@"; do FILES+=("$HERE/${n%.puml}.puml"); done
else
  FILES=("$HERE"/*.puml)
fi

for f in "${FILES[@]}"; do
  b="$(basename "$f")"
  # Le fichier de style est inclus par les autres, il ne se rend pas seul.
  [ "$b" = "_style.puml" ] && continue
  echo "  $b"
  java -jar "$JAR" -charset UTF-8 -failfast2 -nbthread auto \
       -t"$FMT" -o "$OUT" "$f"
done

echo "Sortie : $(cd "$OUT" && pwd)"
