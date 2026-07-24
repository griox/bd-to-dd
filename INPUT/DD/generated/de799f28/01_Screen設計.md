## 01_UI_Design: 小計確認画面 (N9P90M4X4004W009)

### 1. 画面概要
本画面は、貨物搭載ワークフローにおける中間確認ステップであり、現在の搭載種別と登録された貨物アイテムの小計件数を表示します。ユーザーは「継続」または「完了」を選択できます。「継続」は登録件数に応じて次の入力画面へ遷移するか、あるいは詳細な遷移先選択を促すハーフモーダルを表示します。「完了」は現在の機能を終了し、一時データをクリアします。

### 2. レイアウト
画面は以下の主要なセクションで構成されます。

#### 2.1. ヘッダー
*   **コンポーネント**: `NpBaseScreen` の `headerProps`
*   **タイプ**: `HeaderType.LEFT_TITLE` (左寄せタイトル)
*   **タイトル**: 「小計確認」 (`MP90ARIM40039`)

#### 2.2. メインコンテンツエリア
画面の中央に、現在の搭載種別と小計件数が表示されます。
*   **コンポーネント**: `NpList` (リスト形式で情報を表示)
    *   **境界線**: `NpListBorderType.NONE` (境界線なし)
    *   **表示項目**: 2つの行で構成されます。
        *   **1行目**: 「搭載種別」 (`MP90ARIM40028`) とその値 (`screenUiData.tosaiSbt`) が表示されます。
        *   **2行目**: 「小計件数」 (`MP90ARIM40029`) とその値 (`screenUiData.shokeiKensu`) が表示されます。値は搭載種別に応じて「{0}本」または「{0}個」の形式で表示されます。

#### 2.3. フッター (アクションボタンエリア)
画面下部に、主要なアクションボタンが配置されます。
*   **コンポーネント**: `NpHalfSheet` (半分のシートにボタンを配置)
    *   **区切り線**: `useDivider: true` (上部に区切り線を表示)
    *   **ボタン構成**: 2つのボタンが配置されます。
        *   **完了ボタン**: `NpButtonType.PRIMARY` (主ボタン)
            *   **ラベル**: 「完了」 (`MP90ARIM40033`)
            *   **アクション**: `onClickCompleteButton`
        *   **継続ボタン**: `NpButtonType.SECONDARY` (副ボタン)
            *   **ラベル**: 「継続」 (`MP90ARIM40032`)
            *   **アクション**: `onClickContinueButton`

#### 2.4. グローバルフッター
*   **コンポーネント**: `NpBaseScreen` の `bottomBarProps`
*   **表示**: `useBottomBar: true`
*   **ボタン活性状態**: 「戻る」「ホーム」「メニュー」ボタンはすべて非活性 (`isBackButtonEnable: false`, `isHomeButtonEnable: false`, `isMenuButtonEnable: false`)。

### 3. コンポーザブルコンポーネント

| Composable関数名 | 種別 | 内容・役割 | 備考 |
|---|---|---|---|
| `NpBaseScreen` | DS | 画面基底クラス。ヘッダー、フッター、コンテンツの基本構造を提供。 | ヘッダータイトル、フッターボタンの活性状態を設定。 |
| `NpList` | DS | リスト形式で情報を表示するコンポーネント。 | 搭載種別と小計件数の表示に使用。 |
| `NpHalfSheet` | DS | 画面下部にアクションボタンを配置するためのコンポーネント。 | 「継続」「完了」ボタンの配置に使用。 |
| `NpHalfModal` | DS | 半分の高さで表示されるモーダルダイアログ。 | 「継続」ボタン押下時に条件付きで表示される。 |
| `TmsrvAbnormalHkHalfModal` | DS | 異常系ハーフモーダルのコンテンツコンポーネント。 | `NpHalfModal` の `props.content` として使用。メッセージと複数のアクションボタンを含む。 |

### 4. ユーザーインタラクションとイベント

#### 4.1. 初期表示
1.  画面ロード時、`X4004W009ViewModel.initialize()` メソッドが実行されます。
2.  `get-subtotal-confirmation-data` API を呼び出し、現在の `LoadingType`、`SubtotalItemCount`、`RegisteredCount`、`AbnormalityType` などのデータを取得します。
3.  取得したデータに基づき、`screenUiData.tosaiSbt` と `screenUiData.shokeiKensu` が更新され、画面に表示されます。
4.  `isVisibleErrorModal`、`isConfirmMsg`、`halfModalTitle`、`halfModalMsg`、およびすべての戻るボタンの表示フラグ (`isVisibleReturnToBoxNoInputButton` など) は `false` またはブランクで初期化されます。

#### 4.2. 「継続」ボタン押下時
1.  ユーザーが「継続」ボタン (`MP90ARIM40032`) をクリックします。
2.  `onClickContinueButton` ViewModel メソッドが実行されます。
3.  `post-continue-operation` API を呼び出し、`RegisteredCount` をチェックします。
    *   **`RegisteredCount` が 0 の場合:**
        *   `LoadingType` が「01 : トラック」の場合: `ボックスNo.入力画面` (N9P90M4X4004W004) へ遷移します (戻り遷移)。
        *   それ以外の場合: `搭載日付入力画面` (N9P90M4X4004W005) へ遷移します (戻り遷移)。
    *   **`RegisteredCount` が 0 より大きい場合:**
        *   `NpHalfModal` が表示されます (`screenUiData.isVisibleErrorModal` が `true` に設定されます)。
        *   モーダルメッセージとして「遷移先を選択して下さい。」(`MP90AMQM40034`) が表示されます (`screenUiData.halfModalMsg` に設定)。
        *   モーダル内に以下のボタンが、条件に基づいて活性化/非活性化されて表示されます。
            *   **「ボックスNo.入力へ戻る」** (`MP90ARIM40036`): `LoadingType` が「01 : トラック」の場合に表示 (`isVisibleReturnToBoxNoInputButton: true`)。
            *   **「コンテナNo.入力へ戻る」** (`MP90ARIM40038`): `LoadingType` が「01 : トラック」以外かつ `AbnormalityType` が「01 : 誤着」の場合に表示 (`isVisibleReturnToContainerNoInputButton: true`)。
            *   **「便名入力へ戻る」** (`MP90ARIM40077`): `LoadingType` が「01 : トラック」以外かつ `AbnormalityType` が「01 : 誤着」以外の場合に表示 (`isVisibleReturnToBinNmInputButton: true`)。
            *   **「搭載種別選択」** (`MP90ARIM40005`): 常に表示。
            *   **「異常種別選択」** (`MP90ARIM40088`): 常に表示。
            *   **「キャンセル」** (`MP90ARIM40035`): 常に表示。

#### 4.3. 「完了」ボタン押下時
1.  ユーザーが「完了」ボタン (`MP90ARIM40033`) をクリックします。
2.  `onClickCompleteButton` ViewModel メソッドが実行されます。
3.  `post-complete-function` API を呼び出し、機能終了処理 (`N9P90M4X4004U010_機能終了処理`) を実行して、本機能専用領域のデータをクリアします。
4.  現在の機能が終了し、適切な次の画面へ遷移、またはアプリケーションが終了します。

#### 4.4. ハーフモーダル内のアクション
ハーフモーダルが表示されている場合、以下のインタラクションが可能です。

*   **「キャンセル」ボタン押下時** (`MP90ARIM40035`)
    1.  `onClickCancelModal` ViewModel メソッドが実行されます。
    2.  `isVisibleErrorModal` が `false` に設定され、モーダルが閉じます。関連する戻るボタンの表示フラグも `false` にリセットされます。

*   **「搭載種別選択」ボタン押下時** (`MP90ARIM40005`)
    1.  `onClickTosaiSbtSelectModal` ViewModel メソッドが実行されます。
    2.  `ワーク.再開フラグ` に「01」 (搭載種別選択再開) が設定されます。
    3.  `post-clear-continuation-input` API を呼び出し、`N9P90M4X4004U014_継続時入力情報クリア処理` を実行して、後続の入力情報をクリアします。
    4.  `搭載種別選択画面` (N9P90M4X4004W002) へ遷移します (戻り遷移)。

*   **「異常種別選択」ボタン押下時** (`MP90ARIM40088`)
    1.  `onClickAbnormalSbtSelectModal` ViewModel メソッドが実行されます。
    2.  `ワーク.再開フラグ` に「02」 (異常種別選択再開) が設定されます。
    3.  `post-clear-continuation-input` API を呼び出し、`N9P90M4X4004U014_継続時入力情報クリア処理` を実行して、後続の入力情報をクリアします。
    4.  `異常種別選択画面` (N9P90M4X4004W003) へ遷移します (戻り遷移)。

*   **「ボックスNo.入力へ戻る」ボタン押下時** (`MP90ARIM40036`)
    1.  `onClickReturnToBoxNoInputModal` ViewModel メソッドが実行されます。
    2.  `ボックスNo.入力画面` (N9P90M4X4004W004) へ遷移します (戻り遷移)。

*   **「コンテナNo.入力へ戻る」ボタン押下時** (`MP90ARIM40038`)
    1.  `onClickReturnToContainerNoInputModal` ViewModel メソッドが実行されます。
    2.  `コンテナNo.入力画面` (N9P90M4X4004W008) へ遷移します (戻り遷移)。

*   **「便名入力へ戻る」ボタン押下時** (`MP90ARIM40077`)
    1.  `onClickReturnToBinNmInputModal` ViewModel メソッドが実行されます。
    2.  `本機能専用領域.便名` がブランクに設定されます。
    3.  `便名入力画面` (N9P90M4X4004W007) へ遷移します (戻り遷移)。

### 5. UIの仮定
*   画面遷移は、ネイティブアプリケーションのナビゲーションスタックを使用して管理されます。
*   ハーフモーダルは、画面をオーバーレイし、ユーザーの操作をブロックするモーダルとして機能します。
*   `MP90ARIMxxxx` は表示文字列のリソースキーを指します。
*   `screenUiData` は、画面のUI状態を保持するViewModelのプロパティを指します。これらのプロパティは、APIレスポンスやビジネスロジックの結果に基づいて更新されます。
*   「本機能専用領域」および「ワーク」は、セッションまたはアプリケーション全体で共有される状態管理メカニズムを指します。
