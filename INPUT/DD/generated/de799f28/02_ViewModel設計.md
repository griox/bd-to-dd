## ViewModel/Logic Design: Subtotal Confirmation Screen (N9P90M4X4004W009)

This document details the ViewModel and associated logic for the Subtotal Confirmation Screen, covering state management, API integration, and business rules.

### 1. ViewModel Class: `X4004W009ViewModel`

The `X4004W009ViewModel` class is responsible for managing the UI state, interacting with backend APIs, and implementing the business logic for the Subtotal Confirmation Screen. It exposes observable UI state to the screen and handles user interactions.

### 2. UI State Class: `X4004W009UiState`

The `X4004W009UiState` class represents the observable state of the Subtotal Confirmation Screen. All UI elements on the screen are bound to properties within this state.

#### 2.1. Properties

| Property Name                        | Type      | Description                                                                 | Initial Value   |
| :----------------------------------- | :-------- | :-------------------------------------------------------------------------- | :-------------- |
| `tosaiSbt`                           | `String`  | Display value for Loading Type.                                             | `ブランク（空文字）` |
| `shokeiKensu`                        | `String`  | Formatted subtotal item count (e.g., "10本", "5個").                      | `ブランク（空文字）` |
| `isVisibleErrorModal`                | `Boolean` | Controls the visibility of the half-modal dialog.                           | `false`         |
| `isConfirmMsg`                       | `Boolean` | Flag to differentiate between confirmation and error modals.                | `false`         |
| `halfModalTitle`                     | `String`  | Title to be displayed in the half-modal.                                    | `ブランク（空文字）` |
| `halfModalMsg`                       | `String`  | Message content to be displayed in the half-modal.                          | `ブランク（空文字）` |
| `isVisibleReturnToBoxNoInputButton`  | `Boolean` | Controls visibility of 'ボックスNo.入力へ戻る' button in the half-modal. | `false`         |
| `isVisibleReturnToContainerNoInputButton` | `Boolean` | Controls visibility of 'コンテナNo.入力へ戻る' button in the half-modal. | `false`         |
| `isVisibleReturnToBinNmInputButton`  | `Boolean` | Controls visibility of '便名入力へ戻る' button in the half-modal.       | `false`         |

### 3. State Management

The `X4004W009ViewModel` manages the `X4004W009UiState` through a reactive pattern, typically using `MutableStateFlow` or similar observable state holders. State updates are triggered by user actions or API responses, ensuring the UI reflects the current application state.

*   **Initial Load:** The `initialize` method fetches initial display data and populates `tosaiSbt` and `shokeiKensu`.
*   **Modal Visibility:** `isVisibleErrorModal`, `halfModalTitle`, `halfModalMsg`, and `isConfirmMsg` are updated when the 'Continue' button is pressed and `RegisteredCount` > 0, or when the modal is closed by 'OK'/'Cancel'.
*   **Conditional Buttons:** `isVisibleReturnToBoxNoInputButton`, `isVisibleReturnToContainerNoInputButton`, `isVisibleReturnToBinNmInputButton` are dynamically updated based on `LoadingType` and `AbnormalityType` received from the backend via the `post-continue-operation` API.
*   **Session State (`本機能専用領域`, `ワーク`):** The ViewModel implicitly relies on a backend-managed session state (`本機能専用領域`) for `LoadingType`, `RegisteredCount`, `AbnormalityType`, and `FlightNumber`. Changes to this state (e.g., clearing `FlightNumber` or input data) are triggered via API calls.

### 4. API Integration

The ViewModel integrates with the following backend APIs:

#### 4.1. `initialize()`

*   **API Called:** `get-subtotal-confirmation-data` (GET /api/subtotal-confirmation)
*   **Request:** `sessionId` (query parameter).
*   **Response Handling:**
    *   Upon successful response, map `loadingType.displayValue` to `uiState.tosaiSbt`.
    *   Map `subtotalItemCount.value` and `subtotalItemCount.unit` to format and set `uiState.shokeiKensu` (e.g., `value + unit`).
    *   Store `registeredCount`, `loadingType.code`, and `abnormalityType.code` internally for subsequent logic (e.g., `onClickContinueButton`).
*   **Error Handling:** If API call fails, assume a default error display mechanism (e.g., generic error modal, toast message) as specific error handling for this API is not detailed.

#### 4.2. `onClickContinueButton()`

*   **API Called:** `post-continue-operation` (POST /api/subtotal-confirmation/continue)
*   **Request:** `sessionId` (body).
*   **Response Handling:**
    *   **`action: 'navigate'`:** Navigate to `response.destinationScreenId` (`ボックスNo.入力画面` or `搭載日付入力画面`).
    *   **`action: 'showModal'`:**
        *   Set `uiState.isVisibleErrorModal` to `true`.
        *   Set `uiState.halfModalMsg` to the message associated with `response.modalContent.messageId` (MP90AMQM40034).
        *   Set `uiState.isConfirmMsg` to `true`.
        *   Conditionally set `isVisibleReturnToBoxNoInputButton`, `isVisibleReturnToContainerNoInputButton`, `isVisibleReturnToBinNmInputButton` based on `response.modalContent.loadingType.code` and `response.modalContent.abnormalityType.code` as per business logic (see section 5.2).
*   **Error Handling:** If the API call fails, display a generic error message in a modal or toast.

#### 4.3. `onClickCompleteButton()`

*   **API Called:** `post-complete-function` (POST /api/subtotal-confirmation/complete)
*   **Request:** `sessionId` (body).
*   **Response Handling:**
    *   Upon successful completion, the function terminates. The `feedbackClassification` can be used for logging or further UI feedback if required.
*   **Error Handling:** If API call fails, display a generic error message.

#### 4.4. `onClickTosaiSbtSelectModal()` / `onClickAbnormalSbtSelectModal()`

*   **API Called:** `post-clear-continuation-input` (POST /api/subtotal-confirmation/clear-input)
*   **Request:** `sessionId`, `resumeFlag` (body).
    *   For `onClickTosaiSbtSelectModal`: `resumeFlag` = `'01'` (搭載種別選択再開).
    *   For `onClickAbnormalSbtSelectModal`: `resumeFlag` = `'02'` (異常種別選択再開).
*   **Response Handling:**
    *   After successful API call, navigate to `搭載種別選択画面` (N9P90M4X4004W002) or `異常種別選択画面` (N9P90M4X4004W003).
    *   The `shokeiKensu` might need to be re-evaluated or re-fetched if the clearing of input data impacts the registered count shown on the subtotal screen (as suggested by samples, though typically this navigation leads away from the screen).
*   **Error Handling:** Display messages based on `messageId` and `feedbackClassification` from the API response.

#### 4.5. `onClickReturnToBinNmInputModal()`

*   **API Interaction:** This action primarily involves updating the session state on the backend to clear the flight number before navigation.
*   **API Called:** (Implicitly) An update to the session state (e.g., via a dedicated API or part of the navigation API) to set `本機能専用領域.便名` to blank.
*   **Navigation:** Navigate to `便名入力画面` (N9P90M4X4004W007).

#### 4.6. `onClickOkModal()` / `onClickCancelModal()`

*   **API Interaction:** No direct API calls. These methods are purely for UI state manipulation.
*   **State Update:** Set `uiState.isVisibleErrorModal` to `false` to close the modal. Also reset conditional button visibility flags (`isVisibleReturnToBoxNoInputButton`, etc.) to `false`.

### 5. Business Logic Rules

#### 5.1. Initial Display Logic

*   **Loading Type Display:** `uiState.tosaiSbt` is directly mapped from `LoadingType.displayValue` retrieved from `get-subtotal-confirmation-data`.
*   **Subtotal Item Count Formatting:**
    *   If `LoadingType.code` is `'01'` (トラック), `uiState.shokeiKensu` is formatted as `{RegisteredCount}本` (e.g., using `MP90ARIM40030`).
    *   Otherwise, `uiState.shokeiKensu` is formatted as `{RegisteredCount}個` (e.g., using `MP90ARIM40031`).

#### 5.2. 'Continue' Button (`onClickContinueButton`) Logic

*   **Check Registered Count:** The ViewModel retrieves the `RegisteredCount` from the session state (via `get-subtotal-confirmation-data` or internal state).
*   **Conditional Navigation (if `RegisteredCount` is 0):**
    *   If `LoadingType.code` is `'01'` (トラック), navigate to `ボックスNo.入力画面` (N9P90M4X4004W004).
    *   Otherwise, navigate to `搭載日付入力画面` (N9P90M4X4004W005).
    *   This navigation is handled by the `post-continue-operation` API which returns `action: 'navigate'` and `destinationScreenId`.
*   **Half-Modal Display (if `RegisteredCount` > 0):**
    *   Display the half-modal with message `MP90AMQM40034` ('遷移先を選択して下さい。').
    *   Set `uiState.isConfirmMsg` to `true`.
    *   **Conditional 'Return to Input' Buttons:**
        *   If `LoadingType.code` is `'01'` (トラック): `uiState.isVisibleReturnToBoxNoInputButton` = `true`. Other return buttons (`ContainerNo`, `FlightNo`) are `false`.
        *   Else if `AbnormalityType.code` is `'01'` (誤着): `uiState.isVisibleReturnToContainerNoInputButton` = `true`. Other return buttons are `false`.
        *   Else (default): `uiState.isVisibleReturnToBinNmInputButton` = `true`. Other return buttons are `false`.
    *   The 'キャンセル', '搭載種別選択', '異常種別選択' buttons are always enabled within the modal.

#### 5.3. Half-Modal Navigation Actions Logic

*   **Cancel (`onClickCancelModal`):** Close the half-modal by setting `uiState.isVisibleErrorModal` to `false` and resetting `isVisibleReturnTo...Button` flags to `false`.
*   **Loading Type Selection (`onClickTosaiSbtSelectModal`):**
    *   Call `post-clear-continuation-input` API with `resumeFlag` = `'01'`.
    *   Navigate to `搭載種別選択画面` (N9P90M4X4004W002).
*   **Abnormality Type Selection (`onClickAbnormalSbtSelectModal`):**
    *   Call `post-clear-continuation-input` API with `resumeFlag` = `'02'`.
    *   Navigate to `異常種別選択画面` (N9P90M4X4004W003).
*   **Return to Box No. Input (`onClickReturnToBoxNoInputModal`):** Navigate to `ボックスNo.入力画面` (N9P90M4X4004W004).
*   **Return to Container No. Input (`onClickReturnToContainerNoInputModal`):** Navigate to `コンテナNo.入力画面` (N9P90M4X4004W008).
*   **Return to Flight No. Input (`onClickReturnToBinNmInputModal`):**
    *   Clear `本機能専用領域.便名` (set to blank) via backend interaction.
    *   Navigate to `便名入力画面` (N9P90M4X4004W007).
*   **OK (`onClickOkModal`):** Close the half-modal by setting `uiState.isVisibleErrorModal` to `false`.

#### 5.4. 'Complete' Button (`onClickCompleteButton`) Logic

*   Call `post-complete-function` API.
*   Upon successful API response, terminate the current function/workflow, clearing any temporary session data managed by `本機能専用領域`.