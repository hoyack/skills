# SearXNG Categories and Engines Reference

## Categories

| Category | Description | Example Query |
|----------|-------------|---------------|
| `general` | Web search (default) | `docker tutorial` |
| `images` | Image search | `cat photos` |
| `videos` | Video search | `kubernetes demo` |
| `news` | News articles | `AI regulation` |
| `music` | Music/audio | `jazz piano` |
| `files` | Files/torrents | `ubuntu iso` |
| `it` | IT/programming | `python asyncio` |
| `science` | Scientific papers | `transformer architecture` |
| `social media` | Social platforms | `#rustlang` |
| `map` | Map/location | `coffee shop downtown` |
| `q&a` | Q&A sites | `how to use docker volumes` |
| `repos` | Code repositories | `MCP server` |
| `packages` | Software packages | `express.js` |
| `wikimedia` | Wikimedia content | `history of computing` |

### Using Categories

```bash
# Single category
curl -s 'http://localhost:8090/search?q=kubernetes&format=json&categories=news'

# Multiple categories
curl -s 'http://localhost:8090/search?q=python&format=json&categories=it,repos,packages'
```

## Key Engines by Category

### General / Web
| Engine | Shortcut | Notes |
|--------|----------|-------|
| google | g | Primary web search |
| bing | b | Microsoft search |
| duckduckgo | ddg | Privacy-focused |
| brave | br | Brave Search |
| startpage | sp | Google proxy |
| wikipedia | wp | Encyclopedia |
| wikidata | wd | Structured data |

### IT / Development
| Engine | Shortcut | Notes |
|--------|----------|-------|
| github | gh | Code repos + issues |
| docker hub | dh | Container images |
| pypi | pypi | Python packages |
| mdn | mdn | Mozilla developer docs |
| stackoverflow | so | Q&A (via StackExchange) |
| askubuntu | au | Ubuntu Q&A |
| arch linux wiki | aw | Arch docs |

### Science
| Engine | Shortcut | Notes |
|--------|----------|-------|
| arxiv | ar | Preprints |
| google scholar | gs | Academic papers |
| pubmed | pm | Biomedical literature |
| semantic scholar | ss | AI-powered paper search |

### News
| Engine | Shortcut | Notes |
|--------|----------|-------|
| google news | gn | Google News |
| bing news | bn | Bing News |
| reuters | — | Reuters wire |
| yahoo news | yn | Yahoo News |
| wikinews | wn | Wikimedia news |

### Images
| Engine | Shortcut | Notes |
|--------|----------|-------|
| google images | gi | Google Images |
| bing images | bi | Bing Images |
| flickr | fl | Photo sharing |
| pexels | px | Stock photos |
| unsplash | un | Free photos |
| deviantart | da | Art community |

### Videos
| Engine | Shortcut | Notes |
|--------|----------|-------|
| youtube | yt | YouTube |
| google videos | gv | Google Videos |
| dailymotion | dm | Dailymotion |
| vimeo | vm | Vimeo |

### Social
| Engine | Notes |
|--------|-------|
| lemmy communities | Fediverse communities |
| lemmy posts | Fediverse posts |
| mastodon users | Fediverse users |
| mastodon hashtags | Fediverse hashtags |

### Using Specific Engines

```bash
# Search only GitHub and StackOverflow
curl -s 'http://localhost:8090/search?q=MCP+server+typescript&format=json&engines=github,stackoverflow'

# Search only scientific engines
curl -s 'http://localhost:8090/search?q=large+language+models&format=json&engines=arxiv,google+scholar,semantic+scholar'

# Search only news engines
curl -s 'http://localhost:8090/search?q=open+source+AI&format=json&engines=google+news,reuters,yahoo+news'
```

Note: engine names must match exactly as listed in `/config`. Use `+` for spaces in URL encoding.

## Discovering Available Engines

```bash
# Get full config with all engines
curl -s http://localhost:8090/config | python3 -c "
import sys, json
cfg = json.load(sys.stdin)
engines = cfg.get('engines', [])
for e in sorted(engines, key=lambda x: x.get('name','')):
    cats = ', '.join(e.get('categories', []))
    print(f\"  {e['name']:30s} [{cats}]\")
"
```
