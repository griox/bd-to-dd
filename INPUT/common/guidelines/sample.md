# 1. Screen: PatientCreateScreen
@Composable
fun PatientCreateScreen(
    viewModel: PatientCreateViewModel,
    onNavigateBack: () -> Unit
) {
    val state = viewModel.uiState.collectAsState()
    PatientCreateContent(
        uiState = state.value,
        onNameChanged = viewModel::onNameChanged,
        onBirthdayChanged = viewModel::onBirthdayChanged,
        onCreateClicked = viewModel::onCreateClicked,
        onNavigateBack = onNavigateBack
    )
}

# 2. Composable: PatientCreateContent
@Composable
fun PatientCreateContent(
    uiState: PatientCreateUiState,
    onNameChanged: (String) -> Unit,
    onBirthdayChanged: (String) -> Unit,
    onCreateClicked: () -> Unit,
    onNavigateBack: () -> Unit
) {
    Column {
        Text(text = stringResource(id = R.string.patient_create_title))
        TextField(
            value = uiState.name,
            onValueChange = onNameChanged,
            label = { Text(stringResource(id = R.string.patient_name_label)) }
        )
        TextField(
            value = uiState.birthday,
            onValueChange = onBirthdayChanged,
            label = { Text(stringResource(id = R.string.patient_birthday_label)) }
        )
        Button(onClick = onCreateClicked) {
            Text(stringResource(id = R.string.patient_create_button))
        }
        if (uiState.errorMessage != null) {
            Text(uiState.errorMessage!!, color = Color.Red)
        }
        Button(onClick = onNavigateBack) {
            Text(stringResource(id = R.string.back_button))
        }
    }
}

# 3. ViewModel: PatientCreateViewModel
class PatientCreateViewModel(
    private val patientCreateUseCase: PatientCreateUseCase
) : BaseViewModel() {
    private val _uiState = MutableStateFlow(PatientCreateUiState())
    val uiState: StateFlow<PatientCreateUiState> = _uiState
    fun onNameChanged(name: String) {
        _uiState.value = _uiState.value.copy(name = name)
    }
    fun onBirthdayChanged(birthday: String) {
        _uiState.value = _uiState.value.copy(birthday = birthday)
    }
    fun onCreateClicked() {
        viewModelScope.launch {
            val inEntity = PatientCreateInEntity(
                name = _uiState.value.name,
                birthday = _uiState.value.birthday
            )
            val outEntity = patientCreateUseCase.execute(inEntity)
            if (outEntity.success) {
                _uiState.value = _uiState.value.copy(isCreated = true, errorMessage = null)
            } else {
                _uiState.value = _uiState.value.copy(errorMessage = outEntity.errorMessage)
            }
        }
    }
}
UI State:
data class PatientCreateUiState(
    val name: String = "",
    val birthday: String = "",
    val isCreated: Boolean = false,
    val errorMessage: String? = null
)

# 4. Navigation
// Navigation Graph
NavHost(
    navController = navController,
    startDestination = "patient_create"
) {
    composable("patient_create") { 
        PatientCreateScreen(
            viewModel = hiltViewModel(),
            onNavigateBack = { navController.popBackStack() }
        )
    }
    // ... other screens
}
Navigation Design Table:
| Screen Name | Route Name | Bridge Name | Bridge Summary |
| --- | --- | --- | --- |
| PatientCreateScreen | "patient_create" | PatientCreateBridge | Xử lý tạo mới bệnh nhân |

# 5. Resource (strings.xml)
xmlSao chép mã
<resources>
    <string name="patient_create_title">Tạo thông tin bệnh nhân</string>
    <string name="patient_name_label">Tên bệnh nhân</string>
    <string name="patient_birthday_label">Ngày sinh</string>
    <string name="patient_create_button">Tạo mới</string>
    <string name="back_button">Quay lại</string>
</resources>

# 6. UseCase
Interface:
interface PatientCreateUseCase {
    suspend fun execute(inEntity: PatientCreateInEntity): PatientCreateOutEntity
}
Impl:
class PatientCreateUseCaseImpl(
    private val patientService: PatientService
) : PatientCreateUseCase {
    override suspend fun execute(inEntity: PatientCreateInEntity): PatientCreateOutEntity {
        return patientService.createPatient(inEntity)
    }
}
Input Entity:
data class PatientCreateInEntity(
    val name: String,
    val birthday: String
)
Output Entity:
data class PatientCreateOutEntity(
    val success: Boolean,
    val errorMessage: String? = null
)

# 7. Service
Interface:
interface PatientService {
    suspend fun createPatient(inEntity: PatientCreateInEntity): PatientCreateOutEntity
}
Impl:
class PatientServiceImpl(
    private val repository: PatientRepository
) : PatientService {
    override suspend fun createPatient(inEntity: PatientCreateInEntity): PatientCreateOutEntity {
        return repository.createPatient(inEntity)
    }
}

# 8. Repository Interface
interface PatientRepository {
    suspend fun createPatient(inEntity: PatientCreateInEntity): PatientCreateOutEntity
}

# 9. Repository Implementation (DB)
class PatientRepositoryDbImpl(
    private val patientDao: PatientDao
): PatientRepository {
    override suspend fun createPatient(inEntity: PatientCreateInEntity): PatientCreateOutEntity {
        val dto = PatientDto(
            id = UUID.randomUUID().toString(),
            name = inEntity.name,
            birthday = inEntity.birthday
        )
        val result = patientDao.insert(dto)
        return PatientCreateOutEntity(success = result > 0)
    }
}
// Room DTO
@Entity(tableName = "patient_table")
data class PatientDto(
    @PrimaryKey val id: String,
    val name: String,
    val birthday: String
)
// Room DAO
@Dao
interface PatientDao {
    @Insert
    suspend fun insert(patient: PatientDto): Long
}

# 10. Repository Implementation (DataStore/MemoryStore)
class PatientRepositoryDataStoreImpl(
    private val dataStore: DataStore<PatientProto>
): PatientRepository {
    override suspend fun createPatient(inEntity: PatientCreateInEntity): PatientCreateOutEntity {
        val patientProto = PatientProto.newBuilder()
            .setId(UUID.randomUUID().toString())
            .setName(inEntity.name)
            .setBirthday(inEntity.birthday)
            .build()
        dataStore.updateData { patientProto }
        return PatientCreateOutEntity(success = true)
    }
}
Proto Message:
protoSao chép mã
message PatientProto {
    string id = 1;
    string name = 2;
    string birthday = 3;
}

# 11. Repository Implementation (File)
class PatientRepositoryFileImpl(
    private val fileDir: File
) : PatientRepository {
    override suspend fun createPatient(inEntity: PatientCreateInEntity): PatientCreateOutEntity {
        val fileName = "${fileDir.path}/${UUID.randomUUID()}.json"
        val content = JSONObject().apply {
            put("name", inEntity.name)
            put("birthday", inEntity.birthday)
        }
        fileName.writeText(content.toString())
        return PatientCreateOutEntity(success = true)
    }
}
Folder Structure:
/patient/00001/patient/ (tạo folder với 5 ký tự đầu của RepositoryID)

# 12. Repository Implementation (API)
class PatientRepositoryApiImpl(
    private val api: PatientApi
) : PatientRepository {
    override suspend fun createPatient(inEntity: PatientCreateInEntity): PatientCreateOutEntity {
        val dto = PatientCreateRequest(
            name = inEntity.name,
            birthday = inEntity.birthday
        )
        val response = api.createPatient(dto)
        return PatientCreateOutEntity(
            success = response.success,
            errorMessage = response.errorMessage
        )
    }
}
// DTO cho request/response
data class PatientCreateRequest(
    val name: String,
    val birthday: String
)
data class PatientCreateResponse(
    val success: Boolean,
    val errorMessage: String?
)
// API Spec (OpenAPI/Swagger)
interface PatientApi {
    @POST("/patients")
    suspend fun createPatient(@Body request: PatientCreateRequest): PatientCreateResponse
}
Lưu ý:
Mỗi phần đều có thể mở rộng, validate đầu vào, xử lý lỗi, logging, mapping DTO v.v...
Các phần về mapping, resource, folder/file structure, proto, dao... đều tuân thủ  guideline