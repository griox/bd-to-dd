# ViewModel設計 N9P90M4X4004W009_小計確認画面

## 1. UI State設計

### 1.1. クラス名

`X4004W009UiState`

### 1.2. プロパティ

|プロパティ名|型|説明|初期値|
|---|---|---|---|
|tosaiSbt|String|搭載種別|ブランク（空文字）|
|shokeiKensu|String|小計件数|ブランク（空文字）|
|isVisibleErrorModal|Boolean|モーダル表示フラグ|false|
|isConfirmMsg|Boolean|確認メッセージフラグ（true: 確認モーダル、false: エラーモーダル）|false|
|halfModalTitle|String|モーダルタイトル|ブランク（空文字）|
|halfModalMsg|String|モーダルメッセージ|ブランク（空文字）|
|isVisibleReturnToBoxNoInputButton|Boolean|「ボックスNo.入力へ戻る」ボタンの状態|false|
|isVisibleReturnToContainerNoInputButton|Boolean|「コンテナNo.入力へ戻る」ボタンの状態|false|
|isVisibleReturnToBinNmInputButton|Boolean|「便名入力へ戻る」ボタンの状態|false|

## 2. ViewModel設計

### 2.1. クラス名

`X4004W009ViewModel`

### 2.2. メソッド

|クラスファイル名|メソッド名|入力パラメータ|処理概要|
|---|---|---|---|
|X4004W009ViewModel|initialize|-|[N9P90M4X4004W009_小計確認画面.md#41-初期表示時](../N9P90M4X4004W009_小計確認画面.md#41-初期表示時)を参照|
|X4004W009ViewModel|onClickContinueButton|「継続」ボタン押下時|[N9P90M4X4004W009_小計確認画面.md#42-「継続」ボタン押下処理](../N9P90M4X4004W009_小計確認画面.md#42-継続ボタン押下処理)を参照|
|X4004W009ViewModel|onClickCompleteButton|「完了」ボタン押下時|[N9P90M4X4004W009_小計確認画面.md#43-「完了」ボタン押下処理](../N9P90M4X4004W009_小計確認画面.md#43-完了ボタン押下処理)を参照|
|X4004W009ViewModel|onClickOkModal|-|ハーフモーダルの「OK」ボタン押下時の処理を実行する。|
|X4004W009ViewModel|onClickTosaiSbtSelectModal|「搭載種別選択」ボタン押下時|[N9P90M4X4004W009_小計確認画面.md#42-「継続」ボタン押下処理](../N9P90M4X4004W009_小計確認画面.md#42-継続ボタン押下処理)を参照|
|X4004W009ViewModel|onClickAbnormalSbtSelectModal|「異常種別選択」ボタン押下時|[N9P90M4X4004W009_小計確認画面.md#42-「継続」ボタン押下処理](../N9P90M4X4004W009_小計確認画面.md#42-継続ボタン押下処理)を参照|
|X4004W009ViewModel|onClickReturnToBoxNoInputModal|「ボックスNo.入力へ戻る」ボタン押下時|[N9P90M4X4004W009_小計確認画面.md#42-「継続」ボタン押下処理](../N9P90M4X4004W009_小計確認画面.md#42-継続ボタン押下処理)を参照|
|X4004W009ViewModel|onClickReturnToContainerNoInputModal|「コンテナNo.入力へ戻る」ボタン押下時|[N9P90M4X4004W009_小計確認画面.md#42-「継続」ボタン押下処理](../N9P90M4X4004W009_小計確認画面.md#42-継続ボタン押下処理)を参照|
|X4004W009ViewModel|onClickReturnToBinNmInputModal|「便名入力へ戻る」ボタン押下時|[N9P90M4X4004W009_小計確認画面.md#42-「継続」ボタン押下処理](../N9P90M4X4004W009_小計確認画面.md#42-継続ボタン押下処理)を参照|
|X4004W009ViewModel|onClickCancelModal|-|ハーフモーダルの「キャンセル」ボタン押下時の処理を実行する。|

## 3. State更新仕様

### 3.1. メソッド X4004W009ViewModel_initialize

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|tosaiSbt|本機能専用領域.搭載種別|-|-|
|shokeiKensu|・本機能専用領域.搭載種別が「01 :トラック」の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;【MP90ARIM40030】: 本機能専用領域.登録件数<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;【MP90ARIM40031】: 本機能専用領域.登録件数|-|-|
|isVisibleErrorModal|false|-|-|
|isConfirmMsg|false|-|-|
|halfModalTitle|ブランク（空文字）|-|-|
|halfModalMsg|ブランク（空文字）|-|-|
|isVisibleReturnToBoxNoInputButton|false|-|-|
|isVisibleReturnToContainerNoInputButton|false|-|-|
|isVisibleReturnToBinNmInputButton|false|-|-|

### 3.2. メソッド X4004W009ViewModel_onClickContinueButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|isVisibleErrorModal|・本機能専用領域.登録件数が「0」以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;true<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|halfModalTitle|・本機能専用領域.登録件数が「0」以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;ブランク（空文字）<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|halfModalMsg|・本機能専用領域.登録件数が「0」以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;【MP90AMQM40034】<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|isConfirmMsg|・本機能専用領域.登録件数が「0」以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;true<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|
|isVisibleReturnToBoxNoInputButton|・本機能専用領域.登録件数が「0」以外 かつ 本機能専用領域.搭載種別が「01」の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;true<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;false|-|-|
|isVisibleReturnToContainerNoInputButton|・本機能専用領域.登録件数が「0」以外 かつ 本機能専用領域.搭載種別が「01」以外 かつ 本機能専用領域.異常種別が「01」の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;true<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;false|-|-|
|isVisibleReturnToBinNmInputButton|・本機能専用領域.登録件数が「0」以外 かつ 本機能専用領域.搭載種別が「01」以外 かつ 本機能専用領域.異常種別が「01」以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;true<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;false|-|-|

### 3.3. メソッド X4004W009ViewModel_onClickOkModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|isVisibleErrorModal|false|-|-|

### 3.4. メソッド X4004W009ViewModel_onClickCompleteButton

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|

### 3.5. メソッド X4004W009ViewModel_onClickTosaiSbtSelectModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|shokeiKensu|・ワーク.処理結果がtrue の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;・本機能専用領域.搭載種別が「01 :トラック」の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;【MP90ARIM40030】: 本機能専用領域.登録件数<br/>&nbsp;&nbsp;&nbsp;&nbsp;・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;【MP90ARIM40031】: 本機能専用領域.登録件数<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|

### 3.6. メソッド X4004W009ViewModel_onClickAbnormalSbtSelectModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|shokeiKensu|・ワーク.処理結果がtrue の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;・本機能専用領域.搭載種別が「01 :トラック」の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;【MP90ARIM40030】: 本機能専用領域.登録件数<br/>&nbsp;&nbsp;&nbsp;&nbsp;・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;【MP90ARIM40031】: 本機能専用領域.登録件数<br/>・上記以外の場合<br/>&nbsp;&nbsp;&nbsp;&nbsp;変更なし|-|-|

### 3.7. メソッド X4004W009ViewModel_onClickReturnToBoxNoInputModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|

### 3.8. メソッド X4004W009ViewModel_onClickReturnToContainerNoInputModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|

### 3.9. メソッド X4004W009ViewModel_onClickReturnToBinNmInputModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|-|-|-|-|

### 3.10. メソッド X4004W009ViewModel_onClickCancelModal

|UIStateプロパティ|設定値|変換仕様|備考|
|---|---|---|---|
|isVisibleErrorModal|false|-|-|
|isVisibleReturnToBoxNoInputButton|false|-|-|
|isVisibleReturnToContainerNoInputButton|false|-|-|
|isVisibleReturnToBinNmInputButton|false|-|-|
