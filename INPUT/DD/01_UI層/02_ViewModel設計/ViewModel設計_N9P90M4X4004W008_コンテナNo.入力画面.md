# ViewModel設計 N9P90M4X4004W008_コンテナNo.入力画面

## 1. UI State設計

### 1.1. クラス名

`X4004W008UiState`

### 1.2. プロパティ

|プロパティ名|型|説明|初期値|
|---|---|---|---|
|tosaiSbt|String|搭載種別|ブランク（空文字）|
|kokuKaisha|String|航空会社|ブランク（空文字）|
|binNm|String|便名|ブランク（空文字）|
|tourokuKensu|String|登録件数|ブランク（空文字）|
|tosaiDate|String|搭載日付|ブランク（空文字）|
|abnormalSbtNm|String|異常種別名|ブランク（空文字）|
|containerNo|String|コンテナNo.|ブランク（空文字）|
|isVisibleErrorModal|Boolean|モーダル表示フラグ|false|
|isConfirmMsg|Boolean|確認メッセージフラグ（true: 確認モーダル、false: エラーモーダル）|false|
|halfModalTitle|String|モーダルタイトル|ブランク（空文字）|
|halfModalMsg|String|モーダルメッセージ|ブランク（空文字）|

## 2. ViewModel設計

### 2.1. クラス名

`X4004W008ViewModel`

### 2.2. メソッド

|クラスファイル名|メソッド名|入力パラメータ|処理概要|
|---|---|---|---|
|X4004W008ViewModel|initialize|-|[N9P90M4X4004W008_コンテナNo.入力画面.md#41-初期表示時](../N9P90M4X4004W008_コンテナNo.入力画面.md#41-初期表示時)を参照|
|X4004W008ViewModel|onClickKakutei|-|[N9P90M4X4004W008_コンテナNo.入力画面.md#42-キーボード「OK」ボタン押下時](../N9P90M4X4004W008_コンテナNo.入力画面.md#42-キーボードOKボタン押下時)を参照|
|X4004W008ViewModel|onClickOkModal|-|ハーフモーダルの「OK」ボタン押下時の処理を実行する。|
|X4004W008ViewModel|onClickSearchButton|-|[N9P90M4X4004W008_コンテナNo.入力画面.md#44-「検索」ボタン押下時の処理](../N9P90M4X4004W008_コンテナNo.入力画面.md#44-検索ボタン押下時の処理)を参照|

## 3. State更新仕様

### 3.1. メソッド X4004W008ViewModel_initialize

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|tosaiSbt|本機能専用領域.搭載種別名|-|-|
|kokuKaisha|本機能専用領域.航空会社名|-|-|
|binNm|本機能専用領域.便名|-|-|
|tourokuKensu|本機能専用領域.登録件数|-|-|
|tosaiDate|【MP90ARIM40017】<br/> {0}: 本機能専用領域.搭載日付のMM型<br/> {1}: 本機能専用領域.搭載日付のdd型<br/>|-|-|
|abnormalSbtNm|本機能専用領域.異常種別名|-|-|

### 3.2. メソッド X4004W008ViewModel_onClickKakutei

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|halfModalTitle|・ワーク.処理結果がfalse かつ ワーク.エラー種別リストに登録可能最大件数チェックが含まれ、ワーク.メッセージID のキーが存在する場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|halfModalMsg|・ワーク.処理結果がfalse かつ ワーク.エラー種別リストに登録可能最大件数チェックが含まれ、ワーク.メッセージID のキーが存在する場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ワーク.メッセージID<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|isVisibleErrorModal|・ワーク.処理結果がfalse かつ ワーク.エラー種別リストに登録可能最大件数チェックが含まれ、ワーク.メッセージID のキーが存在する場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;true<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|モーダル表示|
|isConfirmMsg|・ワーク.処理結果がfalse かつ ワーク.エラー種別リストに登録可能最大件数チェックが含まれ、ワーク.メッセージID のキーが存在する場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;false<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|OK ボタンのみの警告表示|
|containerNo|・ワーク.処理結果がfalse かつ ワーク.メッセージID のキー不存在の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|

### 3.3. メソッド X4004W008ViewModel_onClickOkModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|containerNo|・ワーク.メッセージIDが「MP90AMEM40003」の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|「MP90AMEM40003」: 入力可能件数オーバー|-|
|isVisibleErrorModal|false|-|-|

### 3.4. メソッド X4004W008ViewModel_onClickSearchButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|
