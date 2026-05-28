# Agent Instructions — Natural Language Receipt Generation

Instructions for AI agents (Hermes, Claude, or others) constructing sale JSON
from natural language prompts. The CLI path takes structured JSON directly;
this document covers the NL path where the agent constructs that JSON from
the operator's description.

For the sale JSON schema, field rules, pricing rules, and output structure,
see `decisions/0002-data-model.md`.

## Workflow

1. Load `data/breeders.json` for current breeding stock.
2. Parse the operator's description (natural language or spreadsheet notation).
3. Look up parent names in breeders.json to get breeds and confirm existence.
4. Construct sale JSON per ADR 0002 schema.
5. Show the constructed JSON to the operator for confirmation.
6. On approval, save JSON and call the renderer.

## breeders.json

`data/breeders.json` is the source of truth for current breeding stock. It
changes as stock is added or sold — always load the file, don't rely on a
snapshot.

When the operator says "Xander-Harmony litter," look up Xander and Harmony to
confirm they exist, get their breeds, and use their names in the sire/dam
fields. If a name isn't in breeders.json, ask the operator — don't guess.

The `siblings` field is a general relative tracker, NOT literal littermates.
Asymmetric (A listing B does NOT mean B lists A). Non-exhaustive. Used for
line-breeding tracking. Do NOT flag asymmetries as errors.

## Breed Naming

**ALL rabbits are NZW.** TAMUK and M70 are strains, not breeds.

- "TAMUK NZW" / "M70 NZW" — correct
- "TAMUK" / "M70" alone — WRONG

Applies to the rabbit, its sire, and its dam. The breed field in sale JSON
MUST always include "NZW" after the strain name.

## Spreadsheet Notation (Optional)

The operator's trio optimizer outputs rows in this format:

```
Casey Takacs  706-669-6616  fri lunch  9.   PURE Xander-Harmony-TAM-M-1 => 2 [ Willy-Fiona-TAM-F-9, Willy-Fiona-TAM-F-10 ]
```

**Parsing rules:**
- Whitespace between columns varies (tabs, multiple spaces).
- Row numbers end with `.` — strip them (optimizer artifact).
- `PURE` = all rabbits same strain. `MIXED` = different strains.
- First rabbit listed is always the buck.
- `=> N` means N does follow (buck + N does = trio when N=2).
- Does are always in `[ ... ]` brackets, comma-separated.
- Rabbit naming: `SireName-DamName-BreedCode-GenderCode-KitIndex`
  - SireName/DamName are the rabbit's PARENTS, not the rabbit itself.
  - BreedCode: `TAM` = TAMUK NZW, `M70` = M70 NZW.
  - GenderCode: `M` = buck, `F` = doe.
  - KitIndex: ephemeral optimizer artifact, meaningless — strip it.
- Multiple rows for the same customer = multiple line items on one receipt.
- Pickup "fri lunch" is NOT an ISO date — ask the operator for the actual date.

**This notation is temporary and not required.** The operator may describe
sales in natural language instead. Parse spreadsheet rows when they're pasted;
don't require them.

## Confirmation Step

After constructing the sale JSON, show it to the operator before rendering:

"Here's the sale JSON for Casey Takacs. Two trios, $240 total. Ready to render?"

The operator may say "looks good" or "fix the price on line item 2." Fix and
re-confirm before rendering. Do NOT render without operator confirmation.

## Calling the Renderer

```bash
cd ~/projects/wabbitry-receipt
python -m wabbitry_receipt generate <sale.json> [--output-dir output]
```

Save the constructed sale JSON to a temp file, call the renderer, then deliver
the PDF path to the operator.

## Terms

- **Operator** — the wabbitry owner who runs the tool and manages sales.
- **Sale JSON** — self-contained JSON representing one sale. Schema defined
  in `decisions/0002-data-model.md`.
- **breeders.json** — breeding stock inventory at `data/breeders.json`. Lookup
  reference for parent names and breeds. Not consumed by the renderer.
- **NZW** — New Zealand White. The breed of all rabbits. TAMUK and M70 are
  strains, not breeds.
- **Spreadsheet notation** — tab-delimited rows from the trio optimizer.
  Temporary input format; not required.
