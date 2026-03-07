# Another Me Skills Registry

Shared skills for Another Me AI agents.

## Structure

```
skill-name/
  skill.json    # Metadata (name, version, description)
  SKILL.md      # Instructions for the agent
  scripts/      # Optional helper scripts
  assets/       # Optional reference files
```

## index.json

Auto-generated aggregation of all `skill.json` files. Used by the admin dashboard for listing.

Regenerate: `./scripts/build-index.sh`
