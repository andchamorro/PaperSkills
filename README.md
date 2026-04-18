# PaperSkills — Academic Research Agent Skills

A collection of AI agent skills for academic research workflows, designed for OpenCode and compatible with the Vercel Agent Skills standard.

## Skills

| Skill | Description |
|-------|-------------|
| [abstract](./skills/abstract/) | Generate academic abstracts (IMRaD, thematic, extended, word-count variants) |
| [connected-citations](./skills/connected-citations/) | Build and visualize citation networks from seed papers |
| [journal-match](./skills/journal-match/) | Recommend target journals for manuscript submission |
| [literature-review](./skills/literature-review/) | Hybrid literature search + draft Introduction/Related Work sections |
| [paper-orchestra](./skills/paper-orchestra/) | Full 5-agent pipeline: idea → submission-ready manuscript |
| [paper-tracker](./skills/paper-tracker/) | Track newly published papers by author, institution, venue |
| [peer-review](./skills/peer-review/) | Academic peer review with 8-criteria scoring |
| [research-gap](./skills/research-gap/) | Identify research gaps via Semantic Scholar + OpenAlex trend data |
| [topic-framing](./skills/topic-framing/) | Converge fuzzy ideas into researchable paper framings |

## Installation

```bash
# Install via npx skills
npx skills add andchamorro/paperskills

# Or install specific skills
npx skills add andchamorro/paperskills --skill abstract --skill peer-review
```

## Requirements

- OpenCode or Agent supporting Vercel Skills standard
- Semantic Scholar API key (for some skills)
- OpenAlex API (free, no auth)

## License

MIT License — see individual skill documentation for details.

## Contributing

Contributions welcome! Ensure skills follow the Vercel Agent Skills specification:
- `name:` in frontmatter matching directory name
- `description:` with trigger conditions
- Optional `scripts/`, `references/`, `assets/` subdirectories
