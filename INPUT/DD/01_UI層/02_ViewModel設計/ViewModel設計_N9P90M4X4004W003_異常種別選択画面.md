# ViewModel設計 N9P90M4X4004W003_異常種別選択画面

## 1. UI State設計

### 1.1. クラス名

`X4004W003UiState`

### 1.2. プロパティ

|プロパティ名|型|説明|初期値|
|---|---|---|---|
|abnormalSbtList|List&lt;AbnormalSbt&gt;|異常種別リスト|emptyList()|
|tosaiSbtNm|String|搭載種別名|ブランク（空文字）|
|selectedAbnormalSbtId|String|異常種別リストで選択した値|ブランク（空文字）|
|selectedAbnormalSbtNm|String|異常種別リストで選択したテキスト|ブランク（空文字）|

## 2. ViewModel設計

### 2.1. クラス名

`X4004W003ViewModel`

### 2.2. メソッド

|クラスファイル名|メソッド名|入力パラメータ|処理概要|
|---|---|---|---|
|X4004W003ViewModel|initialize|-|[N9P90M4X4004W003_異常種別選択画面.md#41-初期表示時](../N9P90M4X4004W003_異常種別選択画面.md#41-初期表示時)を参照|
|X4004W003ViewModel|onClickAbnormalSbtButton|名称 (meisho: String)|[N9P90M4X4004W003_異常種別選択画面.md#42-「異常種別」選択リスト選択時](../N9P90M4X4004W003_異常種別選択画面.md#42-異常種別選択リスト選択時)を参照|
|X4004W003ViewModel|onClickSearchButton|-|[N9P90M4X4004W003_異常種別選択画面.md#43-「検索」ボタン押下時の処理](../N9P90M4X4004W003_異常種別選択画面.md#43-検索ボタン押下時の処理)を参照|

## 3. State更新仕様

### 3.1. メソッド X4004W003ViewModel_initialize

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|abnormalSbtList|本機能専用領域.異常種別リスト|-|-|
|tosaiSbtNm|本機能専用領域.搭載種別名|-|-|

### 3.2. メソッド X4004W003ViewModel_onClickAbnormalSbtButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|selectedAbnormalSbtId|abnormalSbtList[index].sbtNaiId|-|-|
|selectedAbnormalSbtNm|abnormalSbtList[index].meisho|-|-|

### 3.3. メソッド X4004W003ViewModel_onClickSearchButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|
