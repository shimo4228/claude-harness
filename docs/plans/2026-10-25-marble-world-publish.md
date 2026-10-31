kind: external
# 2026-10 時点で World Labs Marble の 3D ワールドを生成・加工し、Web と Meta Quest 2 (WebXR) で見られる形で公開する最短の現行手段

as-of: 2026-10-25。著者は個人、Mac、Quest 2 所有。目的は AI コーディング外の AI 活用の手触り。

## Scope searched

角度は 4 つ: marble-product / viewer-webxr / hosting / adversarial。source は docs.worldlabs.ai、worldlabs.ai の ToS、sparkjs.dev、github.com/sparkjsdev/spark、mkkellogg の GaussianSplats3D、PlayCanvas docs、UploadVR、docs.github.com、developers.cloudflare.com、huggingface.co docs、各 forum。tool call は合計 約 49 回。

読み方の注記: marble-product の docs ページは要約 fetcher 経由で、生の全文ではない。以下で「全文」とあるのは各 note の自己申告。

見つからなかった範囲:
- Quest 2 での Marble / splat の実測や公開報告
- 公式 pricing page（404 または到達不能）
- Marble の file-spec ページ（404）
- Marble から Quest 2 へ公開した一人称の報告
- Spark の fork / patch / licence 衝突
- Polycam / Luma、競合の world generator は未調査

## Found

### 1. Marble 本体（角度 marble-product）

**入力**（docs.worldlabs.ai root と FAQ、要約 fetcher）
- text、単一画像、複数画像、360° panorama、video（100MB 未満）、3D layout（Chisel）。
- billing doc によると Free は text / 単一画像 / pano のみ。複数画像・video・3D layout は Standard 以上。

**加工**
- pano edit、click-and-expand、variations、Compose（ワールド結合）、Record（flythrough 動画）。
- billing doc は world expansion を Pro 以上に置く。

**export**（https://docs.worldlabs.ai/marble/export/gaussian-splat.md、要約 fetcher）
- Free は生成できるが export できない。
- Standard は SPZ と PLY の splat、360 panorama、collider mesh。
- Pro は textured GLB mesh と商用権を加える。
- file-specs ページが 404 のため解像度とサイズは不明。
- 第三者情報（未確認）: collider は約 100〜200k tris、高品質 mesh は 4 req/hour。

**共有と VR**（https://docs.worldlabs.ai/marble/support/faq.md、要約 fetcher）
- "Copy link" は web link。"Copy VR link" は VR 互換 link。VR アイコンで headset 内にワールドを開く。
- FAQ は Quest を名指ししない。
- 公開したワールドは community Gallery に載る。
- link がアカウント無しで開けるかは不明。

**価格**（account-billing.md の upgrade 例と第三者。公式 pricing page は到達不能）
- Standard $20、Pro $35、Max 約 $95（Max は第三者）。
- 生成数の上限: Free 最大 4、Standard 12、Pro 25、Max 75。
- credit: world 生成 1,500、入力 80〜100、pano edit 150、expand 2,000。
- subscription credit は繰り越さない。top-up は 1 年で失効。商用権は Pro のみ。

**API**（api/pricing.md、要約 fetcher）
- World API は platform.worldlabs.ai。$1 = 1,250 credit。Marble 側 credit とは別勘定。
- model は marble-1.0-draft / 1.0 / 1.1 / 1.1-plus。
- draft は 150〜250 credit、1.1 は 1,500〜1,600、1.1-plus は 1,500〜3,100。
- GLB export は 3,500 credit（約 $2.80）、PLY export は無料。
- 1.1-plus の観測コストは 2026-06-25 までで平均 $1.714、最大 $2.48。

### 2. 利用規約（角度 adversarial）

https://worldlabs.ai/terms-of-service §3.3。全約 102k 字のうち約 100k 字まで読了。
- Free アカウントの output の権利は World Labs が保持する。利用許諾は個人・非商用のみ。
- 有料ユーザーは output を所有し、公開表示できる。
- アカウントの区分は生成した時点で固定される。
- export は有料プラン必須。
- Free のワールドが公開 listing される点は第三者情報で、ToS との照合は未確認。

### 3. Web / WebXR viewer（角度 viewer-webxr）

**Marble の VR link を使う経路**
- UploadVR（2025-11-22、取得して読了。https://www.uploadvr.com/marble-turns-an-image-into-a-webxr-volumetric-scene-in-minutes/）は、headset browser の WebXR で Marble を Quest 3 と Vision Pro で試した。
- UploadVR の roundup（2026-09-17、取得して読了。https://www.uploadvr.com/the-best-ways-to-view-gaussian-splats-on-quest/）は、Quest 3 の Quest browser で「ほとんどの scene は良好に動いた」と書く。
- 両記事とも Quest 3 のみ。Quest 2 の試験は無い。
- Free tier のワールドは公開 listing され、非公開には有料が要る。

**Spark**（取得して読了。https://github.com/sparkjsdev/spark）
- MIT。対応形式は ply / spz / splat / ksplat / sog。
- 最新は v2.4.0（2026-10-20）で、WebXR 修正を含む。活発。
- 性能ページ（取得して読了、日付なし。https://sparkjs.dev/docs/performance/）: 「Quest 3: 1M splats 以下」、VR では maxStdDev = sqrt(5)。ページは WebXR に言及しない（adversarial note）。
- WebXR 設定の antialias:false / preUpdate:false は snippet のみ。
- SparkXr class が VR 用（hosting note、https://sparkjs.dev/docs/new-features-2.0/ 全文）。
- `.rad` は事前計算した LoD tree を HTTP Range で stream する。host に Range と CORS が要る。SPZ は全 download 後に表示される。
- 10M splat の PLY は約 2.3 GB、SPZ は 200〜250 MB（第三者 https://radiancefields.com/world-labs-releases-spark-v2.0）。

**その他の viewer**
- GaussianSplats3D（取得）: MIT、webXRMode あり。README が「活発な開発は終了」と書き Spark を案内する。
- supersplat-viewer（取得）: MIT、WebGL VR。docs は Quest 2 / 3 で試験済みと謳う（snippet）。形式は ply / sog / compressed.ply / lod-meta。活発。forum（snippet）は Quest 3 の multiview bug で splat が細くなると報告。
- Babylon.js（第三者 snippet）: splat / ply / spz / sog に対応。XR での splat の docs は見当たらない。

**Quest 2 の性能**
- 公式の splat 予算も benchmark も無い。
- Babylon forum（snippet）は Quest 3 で約 100k splat が実用限界の目安、約 400k で 10〜18 fps と報告。
- Marble の export には 500k splat 版があり、第三者 guide は Quest 向けと呼ぶ（公式 docs には無い）。
- Quest 2 の sales / support 終了時期は未確認（snippet）。

### 4. Hosting（角度 hosting）

| 先 | 制限 | 読み方 |
|---|---|---|
| GitHub Pages | site 1 GB 以内、帯域は soft 100 GB/月、per-file 制限の記載なし | 全文 https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits |
| GitHub repo | 100 MiB 超の file は block、50 MiB 超で警告 | 全文 https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github |
| Cloudflare Pages | 1 asset 25 MiB、free で 20,000 files、帯域制限の記載なし | 全文 https://developers.cloudflare.com/pages/platform/limits/ |
| Cloudflare R2 | 無料 10 GB、Class A 100 万 / Class B 1,000 万 ops/月、egress 無料（r2.dev 含む）、bucket CORS 設定が要る、最大 object size は同ページに記載なし | 全文 https://developers.cloudflare.com/r2/pricing/ |
| Hugging Face | public 無料 storage は best-effort、Space repo 1 GB 上限は forum snippet、dataset の resolve/main パターンの CORS は未検証、community 再利用が前提 | 全文 https://huggingface.co/docs/hub/en/storage-limits |
| Vercel / Netlify | 第三者 snippet のみで食い違う。Vercel Hobby は 100 GB/月・非商用 | 未検証 |

- GitHub Pages での LFS 配信は未確認（記憶では不可）。Release asset は総量上限なしだが、release download の CORS は未確認。
- SuperSplat の publish 機能（snippet。https://developer.playcanvas.com/user-manual/supersplat/publishing/）は superspl.at に公開し、viewer は Quest 2 / 3 の VR で試験済みと書く。hosted の size 上限は見つからず。自前 host の単一 HTML export は 32 MB 未満が目安。

### 5. 代替・fallback（角度 adversarial）

- 最も単純な経路は Marble 自身の VR link で、export が要らない（FAQ 全文）。
- 360 panorama export（有料）、Quest 用の native splat アプリ（AirVis、GSVision）、Unity（World Labs の事例は Quest 3）。
- 競合 generator は未調査。

## Contradictions

1. **Spark の最新版**: hosting note は Spark 2.3 を最新と見た（snippet）。viewer note は GitHub を取得し v2.4.0（2026-10-20）を確認した。取得した後者が強いので v2.4.0 を採り、2.3 は古い snippet として併記する。
2. **価格の根拠**: Standard $20 / Pro $35 は billing doc の upgrade 例、Max 約 $95 は第三者で、公式 pricing page は 404 または到達不能。数値は確定でなく、契約前に account 画面で確認が要る。
3. **Free の扱い**: ToS と billing は Free の export 不可・権利は World Labs 保持。一方で Free ワールドが公開 listing される点は第三者情報で、ToS との照合がない。公開時に有料へ上げる必要の有無は、この点が決める。
4. **Quest の対応**: Marble FAQ は Quest を名指しせず、UploadVR は Quest 3 のみ試験。supersplat-viewer の docs だけが Quest 2 を謳う（snippet）。Quest 2 での動作は、どの source でも実測されていない。

## Still unknown

- Quest 2 で Marble VR link や Spark / supersplat-viewer が実用速度で動くか（実測・報告なし）。Quest 2 の実質的な splat 予算も同様。
- 公式の pricing grid と、各プランの現在の価格。
- Marble の export file の解像度とサイズ（file-specs ページ 404）。
- Free で link を共有できるか、link を開くのにアカウントが要るか。
- Marble VR link が Quest 2 の browser で開けるか。
- output の所有権以外の ToS 細目（Free で生成したワールドを後から有料化したとき）。
- GitHub Pages の LFS 配信、release asset と HF の CORS、Pages / Netlify / Vercel の Range 対応。
- Spark の `.rad` を Quest 2 で使う場合の実効。
- 競合 generator、Polycam / Luma は未調査。
