# Architecture — Konnaxion Mega Diagnostic Pack

## Taxonomie

| Niveau | Domaine | Rôle |
|---|---|---|
| N00 | Control & Discovery | session, cible Konnaxion, repo sibling Konnaxion_Worlds, toolchain, surfaces |
| N01 | Repository & Static | forme repo, état Git, ownership Universe/World et guards anti-overlap |
| N02 | Backend / Django / DB | `manage.py check`, migrations, smoke Konnaxion + tests moteur Konnaxion_Worlds |
| N03 | Frontend / Next | TypeScript, ESLint, Jest, build Next, switcher Universe/World |
| N04 | API Contracts | scanners endpoints, OpenAPI, routes/scoping Universe/World |
| N05 | Runtime & Browser | HTTP local + Playwright + probes read-only Universe/World/Release |
| N06 | Jobs / Redis / Celery | tests de tasks + pinning `world_id + release_id` |
| N07 | Security & Auth | Django deploy check + auth + isolation fail-closed |
| N08 | Capsule Local | Manager, healthcheck engine, capsule hash |
| N09 | Deployed Runtime | DNS/HTTPS et deep diagnostic optionnel |
| N10 | Deep Scan | full-scan Konnaxion + isolation/invariants du moteur Konnaxion_Worlds |
| N11 | Correlation & Triage | corrélation uniquement sur la session courante |

## Frontière de repositories

La topologie canonique à diagnostiquer est :

```text
Konnaxion
  ├── frontend Universe/World switcher
  ├── backend host adapters / world_urls
  └── scripts/check_worlds_ownership.py
          │
          └── dépend du package installé
                    │
Konnaxion_Worlds
  ├── backend/konnaxion/worlds
  ├── migrations Universe/World
  ├── control plane / runtime
  ├── docs/Technical-Reference/Worlds
  └── scripts/check_repo_boundaries.py
```

`Konnaxion_Worlds` est l'unique propriétaire du moteur et de la spécification canonique. Le repo Konnaxion ne doit plus contenir `backend/konnaxion/worlds` ni recopier `docs/Technical-Reference/Worlds`. Le frontend produit, le switcher et les adapters de domaines restent dans Konnaxion.

Le lock attendu est `KX-UNIVERSES-1`. La hiérarchie runtime est `Universe → World → WorldRelease`; l'isolation physique reste au niveau World/Release. Les relations/publications inter-World ne donnent jamais un accès SQL implicite entre schemas.

## Routage canonique

```text
UI:  /u/{universe_key}/w/{world_key}/...
API: /api/u/{universe_key}/w/{world_key}/...
```

`/w/{world_key}` et `/api/w/{world_key}` sont seulement des routes de compatibilité U1. Le runtime doit exposer et vérifier le tuple Universe + World + Release, notamment via `X-Konnaxion-Universe`, `X-Konnaxion-World` et `X-Konnaxion-World-Release-Id`.

## Dépendances

Tous les niveaux N01..N11 dépendent logiquement de N00. Les campagnes Konnaxion s'exécutent explicitement en mode séquentiel dans l'ordre déclaré. Une panne d'un domaine ne stoppe pas les domaines suivants sauf dépendance bloquante : cela conserve la collecte croisée, tout en garantissant que N11 est le dernier niveau. N00 crée un `diagnostic_session_id`, enregistre la campagne et ses niveaux attendus; N11 ignore les résultats `latest` hors session et ne réclame que les niveaux attendus par la campagne.

## Sécurité

- aucune opération de restart/deploy/restore ;
- aucun secret dans l'exemple ;
- redaction des tokens/mots de passe dans les sorties de commandes ;
- diagnostic distant désactivé par défaut ;
- deep remote diagnostic uniquement via une commande explicitement configurée ;
- exécution `shell=False` via le core LevelUpDiag ;
- le probe Universe/World est read-only et ne crée/promote aucun objet ;
- les guards anti-overlap des deux repos font partie de N01.

## Pourquoi les outils restent dans leurs repos

Le pack ne recopie pas Jest, Playwright, Django, les tests métier, les tests du moteur ou les healthchecks. Il appelle les surfaces natives depuis **leur owner canonique** et normalise les résultats en Findings LevelUpDiag. Cette règle vaut particulièrement pour Konnaxion_Worlds : ses tests restent dans le repo moteur et ne doivent pas revenir dans Konnaxion.

## Common authentication contract

LevelUpDiag treats Konnaxion authentication as a standalone-first contract:

```text
local django-allauth login
+ optional OpenID Connect federation
+ issuer/sub external identity
+ local Konnaxion authorization
```

N04 statically checks the OIDC/allauth, CSRF, same-origin, legacy-token and Auth0-residue surfaces. N07 runs the canonical `konnaxion/users/tests/test_auth_policy.py` suite in the target backend environment.
