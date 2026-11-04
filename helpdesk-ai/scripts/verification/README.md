# Vérification des chiffres du mémoire

Six contrôleurs qui confrontent ce que le mémoire affirme à ce que le dépôt mesure.
Ils ne contiennent aucune valeur recopiée : tout est recalculé depuis `data/` et `metrics/`.

```bash
python scripts/verification/tracabilite_chiffres.py
python scripts/verification/coherence_memoire.py
python scripts/verification/coherence_memoire_2.py
python scripts/verification/coherence_affirmations.py
python scripts/verification/relecture_typographique.py
python scripts/verification/orthographe_memoire.py
```

| Script | Ce qu'il vérifie |
|---|---|
| `tracabilite_chiffres.py` | Chaque valeur `0,XXXX` publiée existe dans un artefact de mesure. Signale les orphelines et les valeurs présentes dans plusieurs artefacts, donc ambiguës. |
| `coherence_memoire.py` | Vérité terrain (le texte contre les données), cohérence interne (une quantité, une valeur), formulations périmées par les corrections T1 à T8. |
| `coherence_memoire_2.py` | Répartitions qui doivent sommer, les deux découpages jamais confondus, coûts et latence contre les artefacts, images incluses qui doivent exister. |
| `coherence_affirmations.py` | Les PHRASES, non les nombres : une affirmation du mémoire contre l'état du dépôt. Chaque contrôle a une vérité lue dans le dépôt, des formulations interdites si cette vérité tient, et une formulation attendue — pour que supprimer la phrase fautive sans la remplacer ne suffise pas. |
| `relecture_typographique.py` | Les formes fautives : mots doublés par-dessus un retour à la ligne, guillemets ou parenthèses déséquilibrés, ponctuation doublée, unité collée au nombre. Pas l'orthographe. |
| `orthographe_memoire.py` | L'orthographe, sur le dictionnaire français que MiKTeX embarque : 432 403 formes après développement des affixes. Le vocabulaire du projet vit dans `lexique_memoire.txt`, suivi en version. |

## Deux écarts attendus, et pourquoi

`coherence_memoire.py` signale **58 contre « cinquante-huit »**. Le mémoire écrit le nombre en
chiffres dans les énoncés techniques et en lettres dans les phrases de synthèse. La valeur est la
même ; la convention est suivie partout.

`coherence_memoire_2.py` signale **111,5 millions de paramètres** comme non cité. Le mémoire écrit
111 519 760 au chapitre 4 : même nombre, précision différente.

## Les huit valeurs orphelines, toutes justifiées

Cinq sont des differences entre deux lignes d'un meme tableau : `+0,1932`, `+0,2074`, `+0,2516`,
`+0,2658` et `+0,0334`. Une est une valeur a atteindre et non une mesure (`0,5719`). Les deux
dernieres, `0,3746` et `0,4789`, viennent d'une cellule du carnet `05_camembert_finetuning` ou
elles sont inscrites en dur : elles ont ete mesurees mais ne sont pas recalculables. L'annexe F du
memoire le dit explicitement.

## Pourquoi un quatrième

Les trois premiers comparent des NOMBRES. Ils ne voient pas une phrase. Le mémoire a donc pu
écrire six fois « ni anonymisation ni pseudonymisation » pendant que le dépôt portait un module de
pseudonymisation, un script de purge et un audit rendant `conforme: true`, sans qu'aucun contrôle
ne bronche. De même pour « cent quatre-vingt-un tests » quand la suite en comptait 260, et pour
« les trois exigences non traitées sont EF-11, EF-12 et EF-13 » quand les trois avaient été
reprises. `coherence_affirmations.py` ferme cet angle mort.

Son décompte de la suite vient de `metrics/suite_tests.json`, que `scripts/releve_suite_tests.py`
produit par une commande plutôt qu'à la main. À relancer après avoir ajouté des tests.

## Ce que les deux derniers ajoutent, et ce qu'ils ne font pas

`relecture_typographique.py` cherche des FORMES, pas du sens : un mot doublé par-dessus un retour
à la ligne, un guillemet ouvrant sans fermant. Ce sont les fautes qui survivent le mieux à la
relecture humaine, parce que l'œil les lit comme correctes.

`orthographe_memoire.py` fait ce que ferait hunspell, qui n'est pas installé : il développe les
affixes du dictionnaire français de MiKTeX, puis confronte le texte au vocabulaire obtenu. Il ne
juge NI la grammaire NI l'accord — un « ces » pour « ses » passe sans bruit. La relecture humaine
reste nécessaire ; il lui retire seulement le travail mécanique.

Au 10 octobre 2026, il ne signale **aucune forme inconnue dans le corps du mémoire**. Les 142
restantes sont les développements anglais de la liste d'abréviations, le résumé anglais, la
webographie et le préambule LaTeX.

## Quand les rejouer

Après toute modification d'un chiffre du mémoire, d'un paramètre de `params.yaml`, ou après avoir
régénéré un artefact de `metrics/`. Les trois scripts tournent en quelques secondes et écrivent
leur rapport détaillé en JSON à côté d'eux.
