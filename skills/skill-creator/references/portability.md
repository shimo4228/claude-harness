<!-- origin: shimo4228 -->
# Skill Portability

スキルは複数の文脈で再利用されることを前提とする。作成・編集時に以下を守る。
（2026-07-25 に `rules/common/skills.md` から移設 — skill を書くときしか使わないため
常駐 rule から降格した。ADR-0018）

- **本文は汎用的に書く**: パターン・決定・ワークフローを、誰でも自分の状況に当てはめられる
  形で記述する
- **個人プロジェクト URL を本文に埋め込まない**: 自分の canonical implementation、個人 repo、
  特定プロジェクト内のパスへの link は、skill を一人のユーザの filesystem / 一つの
  プロジェクトのライフサイクルに縛るため、本文に入れない
- **具体例・origin story の置き場所**:
  - 抽象的 worked example（仮想シナリオ） → skill 本文内 OK
  - 個人プロジェクト参照・origin story・canonical implementation → `inspiration.md`、
    ADR Notes、memory、または同一 repo 内の "Related Projects" ファイルへ
  - ユーザ固有の設定 → skill parameter / 環境変数。本文にハードコードしない
- **自プロジェクト内リンクは許容**: skill が置かれている同一 repo 内の README / docs /
  config template への相対リンクは、skill を動作させるのに必要な文脈なので本文に入れてよい

## Portability test

他人が install して、著者の個人文脈を一切知らずに使えるか？
「この skill を理解するには `claude-skill-foo` を読む必要がある」状態なら原則違反。

Origin Tracking（`rules/common/skills.md`）は *誰が作ったか* を記録するが、
Portability は *誰が使えるか* を決める。

## 長い skill は分割する

progressive disclosure は skill 内部にも適用する。1 ファイルが長くなったら
`references/` に切り出し、SKILL.md からポインタで参照させる。SKILL.md 本文に全部を
前置きしない（Claude 5 世代のコンテキストエンジニアリング原則）。

## Repo packaging

GitHub 公開手順（命名規約 `claude-skill-` prefix の要否、subagent 同梱、install.sh、
SkillsMP caveat）は skill: `harness-sync` の **Skill repo packaging** 節が正本。
