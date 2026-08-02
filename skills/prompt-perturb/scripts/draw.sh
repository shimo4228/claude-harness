#!/bin/bash
# draw.sh — code-owned randomness for prompt-perturb.
# LLM に「ランダムに選べ」と頼むと自分の分布から選ぶ（疑似ランダム）。ここでは乱数を
# 「ローカルの札の抽選」には使わず、外部検索の入口を散らす刺激語の無作為抽出にだけ使う。
# 選択肢の供給源は常に外部（web 上のライブラリ・カタログ）であり、閉じたテンプレートを持たない。
set -euo pipefail

WORDS=$(awk 'length >= 4 && length <= 9 && /^[a-z]+$/' /usr/share/dict/words \
  | awk -v seed="$RANDOM$RANDOM" 'BEGIN{srand(seed)} {if (rand() < 0.001) print}' \
  | head -5 | paste -sd, -)

echo "stimulus words: $WORDS"
