#!/bin/bash
# draw.sh — code-owned randomness for prompt-perturb.
# LLM に「ランダムに選べ」と頼むと自分の分布から選ぶ（疑似ランダム）。ここでは乱数を
# 「ローカルの札の抽選」には使わず、外部検索の入口を散らす刺激語の無作為抽出にだけ使う。
# 選択肢の供給源は常に外部（web 上のライブラリ・カタログ）であり、閉じたテンプレートを持たない。
set -euo pipefail

# 辞書全体を読み込んでから一様に 5 語引く（先頭から間引くと a/b 始まりに偏る）
WORDS=$(awk -v seed="$RANDOM$RANDOM" '
  length >= 4 && length <= 9 && /^[a-z]+$/ { w[n++] = $0 }
  END {
    srand(seed)
    for (k = 0; k < 5 && n > 0; k++) { i = int(rand() * n); out = out (k ? "," : "") w[i]; w[i] = w[--n] }
    print out
  }' /usr/share/dict/words)

echo "stimulus words: $WORDS"
