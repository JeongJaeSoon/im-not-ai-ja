# Research and prior art

## Empirical findings used

### yourbright-jp/humanizer-jp

人間記事1,105本と同じテーマで生成した Claude 記事1,105本を比較した公開プロジェクト。初期実装では次を採用した。

- 文長変動係数の低さを、単独ではなく補助的な強い文書レベル特徴として使う。
- 句点・読点、文末、文字種を計測する。
- Markdown 装飾、丁寧体密度、漢字率を単純な AI tell にしない。
- register とジャンルを合わせない比較を禁止する。

Source: https://github.com/yourbright-jp/humanizer-jp

### Zaitsu and Jin (2023)

日本語の学術テキストで品詞 bigram、助詞 bigram、読点位置、機能語率を比較し、GPT生成文と人間文の文体分布差を検討した。対象は2023年時点の限定された学術データであり、現在の全モデル・全ジャンルへ一般化しない。

Source: https://arxiv.org/abs/2304.05534

### Tarumoto and Hatagaki (2024)

翻訳・要約・平易化で ChatGPT の日本語生成を評価し、人手評価では高品質でもタスク固有の細かな要請を満たさない場合があると報告した。本プロジェクトでは「自然さ」だけでなく、用途・意味・制約を別々に監査する根拠として使う。

Source: https://www.jstage.jst.go.jp/article/jnlp/31/2/31_349/_article/-char/en

## Japanese open-source heuristics

- `gonta223/humanizer-ja`: 主語の過剰明示、敬語・語尾の均一性、カタカナ過多。
- `iKora128/stop-ai-slop-jp`: false agency、立場、主体、構造を語彙より先に見る。
- `makotofalcon/humanizer-ja`: 漢語の過剰連続、三層の編集モデル、アンチAI監査。

これらは有用な編集観点だが、実証済み検出特徴として扱わない。taxonomy では `O` ラベルを付け、反復と文脈を必須にする。

## Register and honorifics

文化庁「敬語の指針」は敬語を尊敬語、謙譲語I、謙譲語II、丁寧語、美化語に分け、語形だけでなく誰にどの場面で使うかを重視する。`させていただく` は原則として許可と受益の条件で評価する。

- https://www.bunka.go.jp/seisaku/bunkashingikai/sokai/sokai_6/pdf/keigo_tousin.pdf
- https://www.bunka.go.jp/seisaku/kokugo_nihongo/kokugo_shisaku/keigo/chapter3/detail.html

## Limits

- 生成モデルは更新されるため、固定語彙リストは陳腐化する。
- current metrics は形態素解析器を使わず、文字列・文単位の軽量診断に限定する。
- 自然な文章と人間が書いた文章は同義ではない。
- 著者性、学術的誠実性、検出器回避を保証しない。
