# Screen設計_[画面ID]_画面名

> [!TIP]
>
> - 画面ID単位で本設計書を作成します。
>   - **命名規則**
>     - ファイル名：Screen設計_[画面ID]_[画面名]で命名してください。
> 例：Screen設計_N9P0B0X5501W001_集配一覧
>     - タイトル名：ファイル名と同じ。
>     - 関数名：1.1. 関数名のTIPを参照。
>     - 項目名：1.2. 入力パラメータ

- 関連ドキュメント
  - [外部設計書](本画面の外部設計書へのリンク)

> [!TIP]
>
> - 本画面の外部設計書へのリンクを貼ります。
>   - 外部設計書格納リポジトリの`main`ブランチへリンクを貼ります。

## 1. Composable関数設計

> [!TIP]
>
> - Screenは、画面内で最上位のComposable関数として実装されます。
> - Screenは、画面全体のレイアウトを担うComposable関数の役割を持ちます。
> - Screenは、publicスコープの関数として実装します。

### 1.1. 関数名

`[画面ID下9桁]Screen(...)`

> [!TIP]
>
> - 命名規則は、「画面ID下9桁」+「Screen」とします。
> 例：X5501W001Screen

### 1.2. 入力パラメータ

|項目名|型|説明|
|---|---|---|
|featureUiData|{機能ID}FeatureUiData|画面のUI状態を操作する機能内共通のViewModelクラスのUIData※任意|
|screenUiData|{機能ID}{画面ID}ScreenUiData|画面のUI状態を操作する画面固有のViewModelクラスのUIData※必須|
|onClickTab|Unit|出庫前タスクの開始ボタン押下時|
|onClick|Unit|作業タブ押下時|

> [!TIP]
>
> - 本Screenに渡すUIDataとメソッド（アクション）を記載してください。
> - UIDataには、ViewModelのUIStateの中で、UI描画に必要なデータを渡します。
> 描画に関係のないViewModel内の処理用のUIStateについては渡さないような設計にしてください。（ワークデータなど）
> - 関連するViewModelとは、機能ID、画面IDで紐づきます。
> - **項目名**
>   - データ＞アクション、必須＞任意の順となるように項目を上から並べて記載してください。
>   - そのComposable内で一意になるように命名してください。また、項目名から対象が明確にわかるように命名してください。
>   - 「-」の用途：「-」は利用しないでください。
> - **型**
>   - 項目の型を記載します。
> 型引数を指定する際の<>は半角で記載し、`List<XX>`といういった体裁で記載してください。
> ただし、XXに設定するDTOクラスを別だしにする場合は、<>をエスケープし、List&lt;[DTOリンク]()&gt;という形式で記載してください。
>   - 「-」の用途：「-」は利用しないでください。
> - **説明**
>   - **UIState**
> 機能内または、画面内のUIStateのどちらであるかを記載してください。
> 機能内UIStateの利用は任意とします。
>   - **アクション**
>アクションの発火条件を記載してください。
>   - 「-」の用途：「-」は利用しないでください。

### 1.3. 画面構成（画面を構成するComposable関数）

|Composable関数名|種別|内容・役割|備考|
|---|---|---|---|
|NpBaseScreen|DS|Screen基底クラス|-|
|NpTab|DS|タブ|...|
|TaskListSectionCard|-|選択中のカード|-|
|NpHalfModal|DS|モーダル表示|-|
|NpItemLineToggle|DS|ハーフモーダルのトグルボタン|NpHalfModalに渡すComposable|
|NpButtonList|DS|ハーフモーダルのボタンリスト|NpHalfModalに渡すComposable|

> [!TIP]
>
> - **Composable関数の分割指針**
>   - 異なる責務毎にComposable関数を分ける。
>   - 1つのComposable関数は、単一の役割を持ち、できるだけシンプルに保つ。
>   - UIの状態を持つComposable関数（ステートフル）とUIの状態を持たないComposable関数（ステートレス）を分ける。
>   - リスト表示（LazyColumn等）は、表示対象のアイテムのComposable関数を別にする。
> - **Composable関数名**
>   - 描画対象が明確にわかる名前（名詞）とします。
>   - 原則、項目辞書に登録された名前を利用してください。
>     - 項目辞書は、集配PF側で定義されないものは、端末アプリ側で別途管理します。
>   - 画面固有のComposable関数の場合は、同時に作成するComposable関数設計書へのリンクを貼ってください。
> - **種別**
> - 種別欄は、以下の種別を記載します。
>   - FW：Frameworkが提供する共通Composable関数
>   - DS：DesignSystemが提供するComposable関数
>   - 「-」：画面固有のComposable関数
>   - 「-」の用途：画面固有のComposable関数を表現する以外では利用しないでください。
> - **内容・役割欄**
>   - 何を描画するのかを記載します。
>   - 「-」の用途：「-」は利用しないでください。
> - **備考**
>   - 補足事項があれば記載してください。
>   - 「-」の用途：「-」は利用しないでください。
> - レイアウト系のComposable関数(Row、Column等)の記載は任意とします。

### 1.4 Composableに渡す引数

#### 1.4.1 NpBaseScreen

|引数名|設定値|備考|
|---|---|---|
|headerProps|-|ヘッダに渡す情報|
|headerProps.HeaderType|...|ヘッダの左寄せ（LEFT_TITLE）、中央寄せ（CENTER_TITLE）|
|headerProps.title|...|ヘッダタイトル|
|headerProps.dotMenuProps|...|機能ボタンのクリックイベント|
|headerProps.leftButtonProps|-|ファンクションボタン2の設定情報|
|headerProps.leftButtonProps.ButtonType|...|ファンクションボタン2のボタンタイプ|
|headerProps.leftButtonProps.label|...|ファンクションボタン2のボタンテキスト|
|headerProps.leftButtonProps.isEnabled|...|ファンクションボタン2のボタン活性状態|
|headerProps.leftButtonProps.onClick|...|ファンクションボタン2のボタンクリックイベント|
|headerProps.rightButtonProps|-|ファンクションボタン1の設定情報|
|headerProps.rightButtonProps.ButtonType|...|ファンクションボタン1のボタンタイプ|
|headerProps.rightButtonProps.label|...|ファンクションボタン1のボタンテキスト|
|headerProps.rightButtonProps.isEnabled|...|ファンクションボタン1のボタン活性状態|
|headerProps.rightButtonProps.onClick|...|ファンクションボタン1のボタンクリックイベント|
|bottomBarProps|-|フッタの設定情報|
|bottomBarProps.isBackButtonEnable|...|戻るボタンの活性状態|
|bottomBarProps.onClickBackButton|...|戻るボタンクリック時の処理|
|bottomBarProps.isHomeButtonEnable|...|ホームの活性状態|
|bottomBarProps.onClickHomeButton|...|ホームのクリック時の処理|
|bottomBarProps.isMenuButtonEnable|...|メニューボタンの活性状態|
|bottomBarProps.onClickMenuButton|...|メニューボタンのクリック時の処理|
|bottomBarProps.transitionButtonProps|-|他機能遷移ボタン1〜3の定義。※リストであるためそれぞれ定義をする|
|bottomBarProps.transitionButtonProps.label|...|他機能遷移ボタンのラベル|
|bottomBarProps.transitionButtonProps.isEnable|...|他機能遷移ボタンの有効/無効|
|bottomBarProps.transitionButtonProps.onClick|...|他機能遷移ボタンのボタンクリック時の処理|
|bottomBarProps.isEnableSearchButton|...|検索ボタンの活性状態|
|bottomBarProps.onClickSearchButton|...|検索ボタンのクリック時の処理|
|bottomBarProps.isEnableTotalButton|...|小計ボタンの活性状態|
|bottomBarProps.onClickTotalButton|...|小計ボタンのクリック時の処理|

> [!TIP]
>
> - **NpBaseScreenの設計指針**
>   - Screenの基底クラスであるNpBaseScreenに渡すパラメータを定義します。
>   - 各設計者はNpBaseScreenの仕様を十分把握して設計してください。
>   - 上記では全てを網羅して各画面にて共通する引数を記載しています。
> 画面の内容に応じて、必要な引数の追加・任意である引数であれば記載の削除をしてください。
> ※例として、エラーモーダルなどは記載していません。画面で必要となる場合は、設定してください。

#### 1.4.2 NpTab

|引数名|設定値|備考|
|---|---|---|
|options|{"レーザー・手入力", "カメラ"}|-|
|selectedIndex|screenUiState.selectedIndex|-|
|onClick|onClickTab|-|

#### 1.4.3 TaskListSectionCard

|引数名|設定値|備考|
|---|---|---|
|...|...|...|

#### 1.4.4 NpHalfModal

|引数名|設定値|備考|
|---|---|---|
|title|...|---|
|isVisible|screenUiState.isVisible|---|
|canShowCloseButton|true|---|
|onDismiss|onClickClose|---|
|content|NpItemLineToggle, NpButtonList|1.4.4.1〜1.4.4.2|

##### 1.4.4.1 NpItemLineToggle

|引数名|設定値|備考|
|---|---|---|
|label|...|---|
|isSwitched|...|---|
|onClick|...|---|

##### 1.4.4.2 NpButtonList

|引数名|設定値|備考|
|---|---|---|
|buttons|...|---|

> [!TIP]
>
> - **Composableに渡す引数**
>   - **引数名**
> 引数名には、下位のComposableが必要とする引数を並べて記載してください。
>     ただし、カラーやサイズ、アイコンなどのレイアウト系の指定は任意とします
>   - **設定値**
> 設定値には、下位のComposableに渡す設定内容を記載してください。
>     - 固定文字列を渡す場合は、リソース一覧で定義した文字列の物理名を記載してください。
>       リソース一覧で定義されていない論理名を記載するのは禁止です。
>     - UiStateを渡す場合は、入力パラメータで渡したUiStateクラスの
>       どの項目名かわかるように記載してください。
>       項目が階層構造になっている場合は、"."で階層構造を表現してください。
>     - メソッドをイベントに渡す場合は、
>       入力パラメータで渡したメソッド名を記載してください。
>   - **Composableをラムダ関数で渡す場合(後置ラムダ)**
> ラムダ関数を渡す対象となるComposable関数の下に、章段落を設けて記載してください。
> 例）1.4.X.1, 1.4.X.2・・・のような形で記載する。
> ラムダ関数を渡す対象となるComposable関数の設定値には、渡す対象となるComposablem名を設定値に記載し、備考に章番号を記載してください。
>
