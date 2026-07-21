# ViewModel設計 N9P90M4X4004W004_ボックスNo.入力画面

## 1. UI State設計

### 1.1. クラス名

`X4004W004UiState`

### 1.2. プロパティ

|プロパティ名|型|説明|初期値|
|---|---|---|---|
|tosaiSbtNm|String|搭載種別名|ブランク（空文字）|
|tourokuKensu|String|登録件数|ブランク（空文字）|
|abnormalSbtNm|String|異常種別名|ブランク（空文字）|
|boxNo|String|ボックスNo.|ブランク（空文字）|
|isVisibleErrorModal|Boolean|モーダル表示フラグ|false|
|isConfirmMsg|Boolean|確認メッセージフラグ（true: 確認モーダル、false: エラーモーダル）|false|
|halfModalTitle|String|モーダルタイトル|ブランク（空文字）|
|halfModalMsg|String|モーダルメッセージ|ブランク（空文字）|

## 2. ViewModel設計

### 2.1. クラス名

`X4004W004ViewModel`

### 2.2. メソッド

|クラスファイル名|メソッド名|入力パラメータ|処理概要|
|---|---|---|---|
|X4004W004ViewModel|initialize|-|[N9P90M4X4004W004_ボックスNo.入力画面.md#41-初期表示時](../N9P90M4X4004W004_ボックスNo.入力画面.md#41-初期表示時)を参照|
|X4004W004ViewModel|onClickKakutei|-|[N9P90M4X4004W004_ボックスNo.入力画面.md#42-キーボードの「OK」ボタン押下時](../N9P90M4X4004W004_ボックスNo.入力画面.md#42-キーボードのOKボタン押下時)を参照|
|X4004W004ViewModel|onClickTotalButton|「小計」ボタン押下時|[N9P90M4X4004W004_ボックスNo.入力画面.md#43-「小計」ボタン押下時](../N9P90M4X4004W004_ボックスNo.入力画面.md#43-小計ボタン押下時)を参照|
|X4004W004ViewModel|onClickOkModal|-|エラーモーダルの「OK」ボタン押下時の処理|
|X4004W004ViewModel|onClickSearchButton|-|[N9P90M4X4004W004_ボックスNo.md#45-「検索」ボタン押下時の処理](../N9P90M4X4004W004_ボックスNo.md#45-検索ボタン押下時の処理)を参照|

## 3. State更新仕様

### 3.1. メソッド X4004W004ViewModel_initialize

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|tosaiSbtNm|本機能専用領域.搭載種別名|-|-|
|tourokuKensu|【MP90ARIM40007】: 本機能専用領域.登録件数|-|-|
|abnormalSbtNm|本機能専用領域.異常種別名|-|-|

### 3.2. メソッド X4004W004ViewModel_onClickKakutei

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|isVisibleErrorModal|・ワーク.処理結果がfalseかつワーク.エラー種別リストに「異常エラー」または「最大件数チェックエラー」が含まれる場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;true<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|halfModalTitle|・ワーク.処理結果がfalseかつワーク.エラー種別リストに「異常エラー」または「最大件数チェックエラー」が含まれる場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|halfModalMsg|・ワーク.処理結果がfalseかつワーク.エラー種別リストに「異常エラー」または「最大件数チェックエラー」が含まれる場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ワーク.メッセージID<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|isConfirmMsg|・ワーク.処理結果がfalseかつワーク.エラー種別リストに「異常エラー」または「最大件数チェックエラー」が含まれる場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;true<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|boxNo|・ワーク.処理結果がfalseかつワーク.メッセージIDのキー不存在の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|

### 3.3. メソッド X4004W004ViewModel_onClickTotalButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|

### 3.4. メソッド X4004W004ViewModel_onClickOkModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|isVisibleErrorModal|false|-|-|
|boxNo|・ワーク.メッセージIDが「MP90AMEM40002」または「MP90AMEM40003」の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|「MP90AMEM40002」: 7チェックエラー<br/>「MP90AMEM40003」: 入力可能件数オーバー|-|

### 3.5. メソッド X4004W004ViewModel_onClickSearchButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|
