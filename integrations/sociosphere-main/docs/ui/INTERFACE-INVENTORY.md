# UI Interface Inventory (authoritative)

## Core (end-user)
- Home / Omnibox: `/`
- Search Results (blended/local/global): `/search?q=`
- Entity Profile: `/entity/:type/:id`
- Graph Explorer: `/graph/:id`
- Curated KB Home: `/kb`
- Settings (privacy/policy): `/settings`

## Admin / Builder
- Connectors: `/connectors`
- Curation Dashboard: `/curation`
- Trust Registry: `/admin/trust`

## Shared primitives (must exist everywhere)
- TrustBadge (trusted/mixed/untrusted)
- ProvenancePanel (sources, quotes, snapshots)
- RankingExplanation ("why this result")
