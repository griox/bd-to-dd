# ViewModel設計 N9P90M4X4004W002_搭載種別選択画面

## 1. UI State設計

### 1.1. クラス名

`X4004W002UiState`

### 1.2. プロパティ

|プロパティ名|型|説明|初期値|
|---|---|---|---|
|tosaiSbtList|List&lt;TosaiSbt&gt;|搭載種別リスト|emptyList()|
|selectedTosaiSbtId|String|搭載種別リストで選択した値|ブランク（空文字）|
|selectedTosaiSbtNm|String|搭載種別リストで選択したテキスト|ブランク（空文字）|

## 2. ViewModel設計

### 2.1. クラス名

`X4004W002ViewModel`

### 2.2. メソッド

|クラスファイル名|メソッド名|入力パラメータ|処理概要|
|---|---|---|---|
|X4004W002ViewModel|initialize|-|[N9P90M4X4004W002_搭載種別選択画面.md#41-初期表示時](../N9P90M4X4004W002_搭載種別選択画面.md#41-初期表示時)を参照|
|X4004W002ViewModel|onClickTosaiSbtButton|名称 (meisho: String)|[N9P90M4X4004W002_搭載種別選択画面.md#42-「搭載種別」選択リスト選択時](../N9P90M4X4004W002_搭載種別選択画面.md#42-搭載種別選択リスト選択時)を参照|
|X4004W002ViewModel|onClickSearchButton|-|[N9P90M4X4004W002_搭載種別選択画面.md#43-「検索」ボタン押下時の処理](../N9P90M4X4004W002_搭載種別選択画面.md#42-検索ボタン押下時の処理)を参照|

## 3. State更新仕様

### 3.1. メソッド X4004W002ViewModel_initialize

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|tosaiSbtList|本機能専用領域.搭載種別リスト|-|-|
|selectedTosaiSbtId|ブランク（空文字）|-|-|
|selectedTosaiSbtNm|ブランク（空文字）|-|-|

### 3.2. メソッド X4004W002ViewModel_onClickTosaiSbtButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|selectedTosaiSbtId|tosaiSbtList[index].sbtNaiId|-|-|
|selectedTosaiSbtNm|tosaiSbtList[index].meisho|-|-|

### 3.3. メソッド X4004W002ViewModel_onClickSearchButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|
