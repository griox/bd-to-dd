# ViewModel設計 N9P90M4X4004W006_航空会社選択画面

## 1. UI State設計

### 1.1. クラス名

`X4004W006UiState`

### 1.2. プロパティ

|プロパティ名|型|説明|初期値|
|---|---|---|---|
|kokuKaishaList|List&lt;String&gt;|航空会社リスト|emptyList()|
|tosaiSbtNm|String|搭載種別名|ブランク（空文字）|
|abnormalSbtNm|String|異常種別名|ブランク（空文字）|
|tosaiDate|String|搭載日付|ブランク（空文字）|

## 2. ViewModel設計

### 2.1. クラス名

`X4004W006ViewModel`

### 2.2. メソッド

|クラスファイル名|メソッド名|入力パラメータ|処理概要|
|---|---|---|---|
|X4004W006ViewModel|initialize|-|[N9P90M4X4004W006_航空会社選択画面.md#41-初期表示時](../N9P90M4X4004W006_航空会社選択画面.md#41-初期表示時時)を参照|
|X4004W006ViewModel|onClickKokuKaishaButton|航空会社名 (kokuKaishaNm: String)|[N9P90M4X4004W006_航空会社選択画面.md#42-「航空会社」選択リスト選択時](../N9P90M4X4004W006_航空会社選択画面.md#42-航空会社選択リスト選択時)を参照|
|X4004W006ViewModel|onClickSearchButton|-|[N9P90M4X4004W006_航空会社選択画面.md#43-「検索」ボタン押下時](../N9P90M4X4004W006_航空会社選択画面.md#43-検索ボタン押下時)を参照|

## 3. State更新仕様

### 3.1. メソッド X4004W006ViewModel_initialize

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|kokuKaishaList|本機能専用領域.航空会社リスト|-|-|
|tosaiSbtNm|本機能専用領域.搭載種別名|-|-|
|abnormalSbtNm|本機能専用領域.異常種別名|-|-|
|tosaiDate|【MP90ARIM40017】<br/> {0}: 本機能専用領域.搭載日付のMM型<br/> {1}: 本機能専用領域.搭載日付のdd型<br/>|-|-|

### 3.2. メソッド X4004W006ViewModel_onClickKokuKaishaButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|

### 3.3. メソッド X4004W006ViewModel_onClickBackButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|
