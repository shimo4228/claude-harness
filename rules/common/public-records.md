<!-- origin: shimo4228 -->
<!-- rationale: 2026-10-12 著者決定。公開 repo の記録（rfcs/、行為ログ、plan、report）が増え、各 repo で「何を名指し何を伏せるか」がばらついた。公開の場の行為は既に公開済みの事実で、伏せていたのは周辺の文脈と、vendor 中立の書き方の慣習だった。authorship-strategy ADR-0025 / ADR-0026、gpt-6-astra のレビュー -->
<!-- review-when: 公開記録が原因の機微の事故が起きた時、platform が著者のアカウントについての判断で公開記録を引いた時、verify-public-detail の検査が形だけ通すようになった時 -->
# Public Records

公開 repo に残す記録（`rfcs/`、行為ログ、plan、調査 report）の境界:

- 公開の場で行った行為（PR、投稿、コメント、プロフィール編集、deposit）は、場所と URL を名指して書く
- 非公開の経路（フォーム、申請、メール）で行った行為は、行為があったことだけを書く。場所も URL も書かない
- rfc には機微でない理由を書いてよい。行為ログには理由を書かない
- 相手の反応・連絡先・個人的な事情・非公開 repo の名前とパスは、公開記録に書かず `.notes/` に置き、リンクする。リンク先のファイル名にも書かない。著者の戦略や project の名前は書いてよい
- 公開の前に `~/.claude/scripts/verify-public-detail.sh` を回し、著者が diff を読む
