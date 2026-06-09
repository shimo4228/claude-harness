---
name: hf-sync
description: Hugging Face Datasets mirror sync for graph.jsonld-bearing research repos. `<Owner/dataset>` を引数に取り、cwd の graph.jsonld を flatten して graph.jsonl と一緒に HF dataset へ upload する。`release-doi` の tag push 後、または ad-hoc resync で起動する。Local の `hf login` token を使うので GitHub Actions / CI auth は不要。
user-invocable: true
origin: shimo4228
---

# hf-sync — Local HF Dataset Mirror Sync

`graph.jsonld` を持つ research repo の HF dataset mirror を、手元から 1 コマンドで同期する skill。`jsonld-knowledge-graph` で encode した graph を HF Datasets 上の mirror に反映する operational layer。

## When to use

- `release-doi` の Phase 5 末尾、`gh release create` 後の HF mirror 反映
- Graph に手を加えた直後の ad-hoc resync（release を切らずに HF だけ更新したい）
- HF token を rotate した後の動作確認

## When NOT to use

- `graph.jsonld` を持たない repo（HF mirror が存在しない）
- HF dataset 自体がまだ作成されていない project（先に `hf repo create <Owner/dataset> --repo-type dataset` で repo を作る）
- HF clone dir (`$HF_CLONE_BASE/<dataset>/`) が存在しない（先に `mkdir -p ~/MyAI_Lab/hf-datasets/<dataset>` で staging dir を作る。HF 側の README.md と過去 snapshot がここに置かれる)
- `hf login` していない / token が write scope を持たない（先に `hf auth login` で token を入れ直す）

## Execution

```
bash ~/.claude/skills/hf-sync/sync.sh $ARGUMENTS
```

`$ARGUMENTS` は HF dataset の repo ID（例: `Shimo4228/agent-knowledge-cycle`）。

cwd 制約: `graph.jsonld` が存在する project root で実行する。

## What it does

1. cwd の `graph.jsonld` の structural sanity check（`@graph` が array で non-empty）
2. Source の `graph.jsonld` を HF clone dir (`$HF_CLONE_BASE/<dataset>/`, default `~/MyAI_Lab/hf-datasets/<dataset>/`) にコピー
3. HF clone 側で `jq -c '.["@graph"][]' graph.jsonld > graph.jsonl` を生成（HF Dataset Viewer 用 1 node 1 行 flatten）
4. `hf upload <Owner/dataset> <hf-clone>/graph.jsonld graph.jsonld --repo-type dataset`
5. `hf upload <Owner/dataset> <hf-clone>/graph.jsonl graph.jsonl --repo-type dataset`
6. Success log + HF URL を表示

**Source repo は汚さない**: `graph.jsonl` は HF clone 側でだけ生成・存在し、source の git tree には残らない。

Auth は `~/.cache/huggingface/token`（`hf login` で保存されたもの）を `hf` CLI が自動で読む。

## Repo mapping

各 project の GitHub repo と HF dataset の対応は project ごとに違う。Skill 本体には embed しない（portability 保持）。Mapping は project の `CLAUDE.md` または同等の場所に記録しておき、起動時にコピペで引数に渡す。

shimo4228 系の現行 mapping は `~/MyAI_Lab/shimo4228/CLAUDE.md` の "HF Datasets mirror" section を参照。

## Related skills

- [`jsonld-knowledge-graph`](../jsonld-knowledge-graph/SKILL.md) — `graph.jsonld` の **設計** layer。本 skill はその **operational mirror** に対応
- [`release-doi`](../release-doi/SKILL.md) — Zenodo DOI release flow。Phase 5 末尾で本 skill を呼ぶ

## Failure modes

- **`graph.jsonld` not found in cwd** → project root に移動してから起動
- **HF clone dir not found** → `mkdir -p $HF_CLONE_BASE/<dataset>/` で staging dir を作成 (もし HF 側に既存ファイルがあれば手動で取得して置く、または `hf download <Owner/dataset> --local-dir <hf-clone>` で初期 sync)
- **`@graph` not array / empty** → `graph.jsonld` の構造を見直す（`jsonld-knowledge-graph` skill 参照）
- **`hf upload` 401 / 403** → `hf auth whoami` で token 確認。write scope を持っていなければ HF settings で新規発行 → `hf auth login`
- **HF dataset repo が存在しない (404)** → 先に `hf repo create <Owner/dataset> --repo-type dataset` で repo を作る
