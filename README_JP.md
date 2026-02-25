日本語/[English](README.md)

# Snippet Palette

Glyphs 3 のサイドバーにボタンを配置し、短い Python スクリプトをワンクリックで実行できるパレットプラグイン。

![Screenshot](screenshot.png)

## 機能

- サイドパレットに **4つのボタン**（2行×2列）を表示
- 各ボタンに**タイトル**と**スクリプト**を設定・保存できる
- ボタンをクリックするだけでスクリプトを実行
- ボタンにマウスホバーでタイトルをツールチップ表示
- 設定はすべての Glyphs ファイルで共通（`Glyphs.defaults` に保存）

## インストール

### 方法 1 — ダブルクリック（推奨）

Finder で `SnippetPalette.glyphsPalette` をダブルクリック（または右クリック → 「このアプリケーションで開く」→ Glyphs 3）すると、インストール確認ダイアログが表示されます。「Install」をクリックすると自動的にプラグインディレクトリにコピーされます。

### 方法 2 — 手動コピー

`SnippetPalette.glyphsPalette` フォルダをプラグインディレクトリにコピー：

```bash
cp -R SnippetPalette.glyphsPalette ~/Library/Application\ Support/Glyphs\ 3/Plugins/
```

---

インストール後、Glyphs 3 を再起動し、`Window → Palette`（`⌘⇧P`）でサイドパネルを開く → **Snippet Palette** が表示されます。

> **Note:** `vanilla` ライブラリが必要です。Glyphs 3 の `Window → Plugin Manager → Modules` から Python をインストール済みであれば利用可能です。

## 使い方

### スクリプトの設定

ボタンを **Option+クリック** または **右クリック** すると設定ダイアログが開きます。

| 項目 | 説明 |
|---|---|
| **Title** | ボタンのツールチップに表示される名前 |
| **Script** | 実行する Python スクリプト |

入力後 **Save** をクリックして保存。ボタンの表示は常に番号（1〜4）のままです。

### スクリプトの実行

設定済みのボタンをクリックするだけ。未設定のボタンをクリックした場合は自動的に設定ダイアログが開きます。

### スクリプト例

選択中のグリフの左右サイドベアリングを 60 に設定：

```python
for thisLayer in Glyphs.font.selectedLayers:
    thisLayer.LSB = 60
    thisLayer.RSB = 60
```

### 外部スクリプトファイルの実行

ボタンの Script 欄に以下のように書くと、外部の `.py` ファイルを実行できます：

```python
exec(open("/path/to/your_script.py").read())
```

### スクリプト内で使える変数

スクリプトはマクロウインドウと同等の環境で実行されます。`GlyphsApp` の公開クラス（`GSGuide`, `GSGlyph`, `GSNode`, `GSPath` など）はすべてインポートなしで利用可能です。

| 変数 | 内容 |
|---|---|
| `Glyphs` | Glyphs アプリケーションオブジェクト |
| `Font` | 現在開いているフォント（`Glyphs.font`） |
| `selectedLayers` | 選択中のレイヤー（`Glyphs.font.selectedLayers`）※フォントが開いている場合のみ |

## 設定データについて

スクリプトの設定は `Glyphs.defaults`（macOS のユーザー設定領域）に保存されます。そのため：

- **プラグインを再インストールしても設定は保持されます**
- どの Glyphs ファイルを開いても同じ設定が使えます

### 設定のリセット

すべてのボタンの登録をクリアするには、マクロウインドウで以下を実行：

```python
del Glyphs.defaults["com.toktaro.SnippetPalette.snippets"]
```

## エラー時

スクリプト実行中にエラーが発生した場合、マクロウインドウが自動的に開き詳細が表示されます。

## ライセンス

このプロジェクトは [MIT License](LICENSE) のもとで公開されています。
