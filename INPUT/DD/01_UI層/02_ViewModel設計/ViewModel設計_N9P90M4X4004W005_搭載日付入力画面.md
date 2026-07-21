# ViewModel設計 N9P90M4X4004W005_搭載日付入力画面

## 1. UI State設計

### 1.1. クラス名

`X4004W005UiState`

### 1.2. プロパティ

|プロパティ名|型|説明|初期値|
|---|---|---|---|
|tosaiSbtNm|String|搭載種別名|ブランク（空文字）|
|abnormalSbtNm|String|異常種別名|ブランク（空文字）|
|tosaiDate|String|搭載日付|ブランク（空文字）|
|isVisibleErrorModal|Boolean|モーダル表示フラグ|false|
|isConfirmMsg|Boolean|確認メッセージフラグ（true: 確認モーダル、false: エラーモーダル）|false|
|halfModalTitle|String|モーダルタイトル|ブランク（空文字）|
|halfModalMsg|String|モーダルメッセージ|ブランク（空文字）|

## 2. ViewModel設計

### 2.1. クラス名

`X4004W005ViewModel`

### 2.2. メソッド

|クラスファイル名|メソッド名|入力パラメータ|処理概要|
|---|---|---|---|
|X4004W005ViewModel|initialize|-|[N9P90M4X4004W005_搭載日付入力画面.md#41--画面表示時](../N9P90M4X4004W005_搭載日付入力画面.md#41--画面表示時)を参照|
|X4004W005ViewModel|onClickSearchButton|-|[N9P90M4X4004W005_搭載日付入力画面.md#44-「検索」ボタン押下時](../N9P90M4X4004W005_搭載日付入力画面.md#44-検索ボタン押下時)を参照|
|X4004W005ViewModel|onClickOkModal|-|エラーモーダルの「OK」ボタン押下時の処理|
|X4004W005ViewModel|onClickKakutei|-|[N9P90M4X4004W005_搭載日付入力画面.md#42-キーボード「OK」ボタン押下時](../N9P90M4X4004W005_搭載日付入力画面.md#42-キーボードOKボタン押下時)を参照|
|X4004W005ViewModel|onClickTotalButton|「小計」ボタン押下時|[N9P90M4X4004W005_搭載日付入力画面.md#43-「小計」ボタン押下時](../N9P90M4X4004W005_搭載日付入力画面.md#43-小計ボタン押下時)を参照|

## 3. State更新仕様

### 3.1. メソッド X4004W005ViewModel_initialize

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|tosaiSbtNm|本機能専用領域.搭載種別名|-|-|
|abnormalSbtNm|本機能専用領域.異常種別名|-|-|

### 3.2. メソッド X4004W005ViewModel_onClickSearchButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|

### 3.3. メソッド X4004W005ViewModel_onClickOkModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|tosaiDate|・ワーク.メッセージIDが「MP90AMEM40004」の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|「MP90AMEM40004」: 日付エラー|-|

### 3.4. メソッド X4004W005ViewModel_onClickKakutei

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|isVisibleErrorModal|・ワーク.処理結果がfalse 且つ ワーク.エラー種別リストに日付チェックエラーが含まれる場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;true<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|halfModalTitle|・ワーク.処理結果がfalse 且つ ワーク.エラー種別リストに日付チェックエラーが含まれる場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|halfModalMsg|・ワーク.処理結果がfalse 且つ ワーク.エラー種別リストに日付チェックエラーが含まれる場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ワーク.メッセージID<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|「MP90AMEM40004」: 日付エラー|-|
|isConfirmMsg|・ワーク.処理結果がfalse 且つ ワーク.エラー種別リストに日付チェックエラーが含まれる場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;false<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|tosaiDate|・ワーク.メッセージIDのキー不存在の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|

### 3.5. メソッド X4004W005ViewModel_onClickTotalButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|
