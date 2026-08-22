@echo off
REM ===================================================================
REM  Compilation du memoire PFE - HelpDesk AI
REM  Usage : double-clic, ou "compiler.bat" dans cmd depuis report\
REM ===================================================================
setlocal
cd /d "%~dp0"

where pdflatex >nul 2>&1
if errorlevel 1 (
  echo.
  echo [ERREUR] pdflatex est introuvable.
  echo Aucune distribution LaTeX n'est installee ^(MiKTeX ou TeX Live^).
  echo TeXstudio et Texmaker sont des editeurs : ils ne compilent pas seuls.
  echo.
  pause
  exit /b 1
)

echo.
echo === Passe 1/4 : pdflatex ^(structure et references^) ===
pdflatex -interaction=nonstopmode -halt-on-error main.tex
if errorlevel 1 goto erreur

echo.
echo === Passe 2/4 : bibtex ^(bibliographie^) ===
bibtex main

echo.
echo === Passe 3/4 : pdflatex ^(resolution des references^) ===
pdflatex -interaction=nonstopmode -halt-on-error main.tex
if errorlevel 1 goto erreur

echo.
echo === Passe 4/4 : pdflatex ^(table des matieres et minitoc^) ===
pdflatex -interaction=nonstopmode -halt-on-error main.tex
if errorlevel 1 goto erreur

echo.
echo ===================================================
echo  TERMINE : main.pdf genere dans %cd%
echo ===================================================
echo.
pause
exit /b 0

:erreur
echo.
echo ===================================================
echo  ECHEC DE COMPILATION
echo  Ouvrez main.log et cherchez la premiere ligne
echo  commencant par un point d'exclamation.
echo ===================================================
echo.
pause
exit /b 1
