<template>
  <div class="users-view">
    <el-card shadow="never" class="main-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="header-title">👥 用户与班级治理中心 (A-04)</span>
            <span class="header-subtitle">管理全平台管理员、乡村美育教师与研学学员账号，支持角色授权、密码重置与学情档案联动</span>
          </div>
          <el-button type="primary" class="primary-btn" @click="handleOpenCreateDialog">
            <el-icon><Plus /></el-icon> 新增用户账号
          </el-button>
        </div>
      </template>

      <el-tabs v-model="tab">
        <!-- Tab 1: 用户全生命周期管理 -->
        <el-tab-pane label="全量注册用户治理" name="users">
          <!-- 检索过滤工具栏 -->
          <div class="filter-toolbar">
            <el-row :gutter="16">
              <el-col :xs="24" :sm="8" :md="6">
                <el-input
                  v-model="filters.keyword"
                  placeholder="搜索用户名 / 昵称 / 手机号"
                  clearable
                  @clear="fetchUsers"
                  @keyup.enter="fetchUsers"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </el-col>
              <el-col :xs="12" :sm="6" :md="4">
                <el-select v-model="filters.role_code" placeholder="身份角色" clearable @change="fetchUsers" style="width: 100%;">
                  <el-option label="全部角色" value="" />
                  <el-option label="管理员 (ADMIN)" value="ADMIN" />
                  <el-option label="乡村教师 (TEACHER)" value="TEACHER" />
                  <el-option label="乡村学员 (STUDENT)" value="STUDENT" />
                </el-select>
              </el-col>
              <el-col :xs="12" :sm="6" :md="4">
                <el-select v-model="filters.status" placeholder="账号状态" clearable @change="fetchUsers" style="width: 100%;">
                  <el-option label="全部状态" value="" />
                  <el-option label="正常启用" value="ACTIVE" />
                  <el-option label="已停用" value="DISABLED" />
                </el-select>
              </el-col>
              <el-col :xs="24" :sm="8" :md="6">
                <el-button type="primary" @click="fetchUsers" plain>
                  <el-icon><Search /></el-icon> 查询
                </el-button>
                <el-button @click="handleResetFilters">
                  <el-icon><Refresh /></el-icon> 重置
                </el-button>
              </el-col>
            </el-row>
          </div>

          <!-- 用户数据表格 -->
          <el-table :data="users" v-loading="loading" style="width: 100%" stripe border class="user-table">
            <el-table-column prop="id" label="ID" width="70" align="center" />
            <el-table-column label="用户资料" min-width="180">
              <template #default="{ row }">
                <div class="user-cell">
                  <el-avatar size="default" :src="row.avatar_url" class="user-avatar" />
                  <div class="user-meta">
                    <div class="user-name">
                      <strong>{{ row.nickname || row.username }}</strong>
                      <span class="user-account">(@{{ row.username }})</span>
                    </div>
                    <div class="user-contact">{{ row.phone || '未绑定手机' }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="role_code" label="身份角色" width="130" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.role_code === 'ADMIN' ? 'danger' : row.role_code === 'TEACHER' ? 'warning' : 'primary'"
                  effect="light"
                  round
                >
                  {{ row.role_code === 'ADMIN' ? '平台管理员' : row.role_code === 'TEACHER' ? '乡村教师' : '研学学员' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="学段与所属学校" min-width="200">
              <template #default="{ row }">
                <div class="school-info">
                  <div class="school-name">{{ row.school_name || '未录入所属学校' }}</div>
                  <div class="grade-tag">{{ row.grade || '未分配学段' }}</div>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="美育成长与能量" width="150" align="center">
              <template #default="{ row }">
                <div class="growth-box">
                  <div class="energy-text">⚡ {{ row.energy_value }} 能量</div>
                  <el-tag size="small" type="info">{{ row.level_code }}</el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="账号状态" width="100" align="center">
              <template #default="{ row }">
                <el-switch
                  :model-value="row.status === 'ACTIVE'"
                  active-color="#4D8B63"
                  inactive-color="#DCDFE6"
                  @change="(val: any) => handleToggleStatus(row, val)"
                />
              </template>
            </el-table-column>

            <el-table-column prop="created_at" label="注册时间" width="150" align="center" />

            <el-table-column label="操作" width="200" fixed="right" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleOpenEditDialog(row)">
                  编辑
                </el-button>
                <el-button type="warning" link size="small" @click="handleOpenResetPwdDialog(row)">
                  重置密码
                </el-button>
                <el-button
                  type="danger"
                  link
                  size="small"
                  :disabled="row.role_code === 'ADMIN'"
                  @click="handleDeleteUser(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页控件 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :page-sizes="[10, 20, 50]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="fetchUsers"
              @current-change="fetchUsers"
            />
          </div>
        </el-tab-pane>

        <!-- Tab 2: 示范班级 -->
        <el-tab-pane label="乡村美育班级（真实数据）" name="classes">
          <div class="class-header">
            <span class="class-summary">
              共 {{ classes.length }} 个在班班级 · {{ classStudentTotal }} 在班学生人次；学完率按已开始课程的已发布章节实时统计
            </span>
            <el-button size="small" plain :loading="classesLoading" @click="fetchClasses">刷新</el-button>
          </div>
          <el-table :data="classes" v-loading="classesLoading" style="width: 100%" stripe border>
            <el-table-column prop="id" label="班级ID" width="90" align="center" />
            <el-table-column prop="name" label="班级名称" min-width="220" />
            <el-table-column label="带班教师" width="140" align="center">
              <template #default="{ row }">{{ row.teacher_name || '未登记' }}</template>
            </el-table-column>
            <el-table-column label="所属乡村学校" min-width="200">
              <template #default="{ row }">{{ row.school || '未登记' }}</template>
            </el-table-column>
            <el-table-column prop="student_count" label="在班学生数" width="110" align="center" />
            <el-table-column label="课程学完率" width="180">
              <template #default="{ row }">
                <el-progress v-if="typeof row.completion === 'number'" :percentage="row.completion" color="#4D8B63" />
                <span v-else class="muted-text">暂无学习记录</span>
              </template>
            </el-table-column>
            <el-table-column label="学段/年级" width="140" align="center">
              <template #default="{ row }">
                <el-tag type="success">{{ row.grade || '未设置' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 弹窗：创建新用户 -->
    <el-dialog v-model="createDialogVisible" title="新增平台用户账号" width="540px" destroy-on-close>
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="110px">
        <el-form-item label="登录账号" prop="username">
          <el-input v-model="createForm.username" placeholder="英文、数字或下划线" />
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input v-model="createForm.password" type="password" show-password placeholder="默认 123456" />
        </el-form-item>
        <el-form-item label="姓名/昵称" prop="nickname">
          <el-input v-model="createForm.nickname" placeholder="例如：王秀兰老师 或 张小明" />
        </el-form-item>
        <el-form-item label="身份角色" prop="role_code">
          <el-select v-model="createForm.role_code" placeholder="请选择角色" style="width: 100%;">
            <el-option label="研学学员 (STUDENT)" value="STUDENT" />
            <el-option label="乡村教师 (TEACHER)" value="TEACHER" />
            <el-option label="平台管理员 (ADMIN)" value="ADMIN" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号码" prop="phone">
          <el-input v-model="createForm.phone" placeholder="选填，用于接收研学通知短信" />
        </el-form-item>
        <el-form-item label="学段/年级" prop="grade">
          <el-input v-model="createForm.grade" placeholder="如：小学四年级、骨干美育教师" />
        </el-form-item>
        <el-form-item label="所属乡村学校" prop="school_name">
          <el-input v-model="createForm.school_name" placeholder="如：蓟州区下营镇中心小学" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createSubmitting" @click="handleConfirmCreate">确认创建</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗：编辑用户信息 -->
    <el-dialog v-model="editDialogVisible" title="编辑用户资料与学校关联" width="540px" destroy-on-close>
      <el-form :model="editForm" label-width="110px">
        <el-form-item label="登录账号">
          <el-input :model-value="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="姓名/昵称">
          <el-input v-model="editForm.nickname" placeholder="请输入姓名/昵称" />
        </el-form-item>
        <el-form-item label="身份角色">
          <el-select v-model="editForm.role_code" style="width: 100%;">
            <el-option label="研学学员 (STUDENT)" value="STUDENT" />
            <el-option label="乡村教师 (TEACHER)" value="TEACHER" />
            <el-option label="平台管理员 (ADMIN)" value="ADMIN" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号码">
          <el-input v-model="editForm.phone" placeholder="请输入手机号码" />
        </el-form-item>
        <el-form-item label="学段/年级">
          <el-input v-model="editForm.grade" placeholder="如：小学四年级" />
        </el-form-item>
        <el-form-item label="所属乡村学校">
          <el-input v-model="editForm.school_name" placeholder="如：蓟州区下营镇中心小学" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="handleConfirmEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onMounted } from 'vue'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const tab = ref('users')
const loading = ref(false)
const users = ref<any[]>([])

const filters = reactive({
  keyword: '',
  role_code: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 示范班级
const classes = ref<any[]>([])
const classesLoading = ref(false)
const classStudentTotal = computed(() =>
  classes.value.reduce((sum, item) => sum + (item.student_count || 0), 0)
)

const fetchClasses = async () => {
  classesLoading.value = true
  try {
    const res: any = await request.get('/teacher/classes')
    classes.value = Array.isArray(res) ? res : []
  } catch (err: any) {
    ElMessage.error('获取班级列表失败: ' + (err.message || '网络异常'))
  } finally {
    classesLoading.value = false
  }
}

// 加载用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const res: any = await request.get('/admin/users', {
      params: {
        page: pagination.page,
        pageSize: pagination.pageSize,
        keyword: filters.keyword || undefined,
        role_code: filters.role_code || undefined,
        status: filters.status || undefined
      }
    })
    if (res) {
      users.value = res.list || []
      pagination.total = res.total || 0
    }
  } catch (err: any) {
    ElMessage.error('获取用户列表失败: ' + (err.message || '网络异常'))
  } finally {
    loading.value = false
  }
}

const handleResetFilters = () => {
  filters.keyword = ''
  filters.role_code = ''
  filters.status = ''
  pagination.page = 1
  fetchUsers()
}

// 切换账号启停状态
const handleToggleStatus = async (row: any, activeVal: boolean) => {
  const newStatus = activeVal ? 'ACTIVE' : 'DISABLED'
  const actionText = activeVal ? '启用' : '停用'
  try {
    await request.put(`/admin/users/${row.id}/status`, { status: newStatus })
    row.status = newStatus
    ElMessage.success(`用户【${row.username}】已成功${actionText}`)
  } catch (err: any) {
    ElMessage.error(`操作失败: ${err.message || '无法修改状态'}`)
  }
}

// 重置密码
const handleOpenResetPwdDialog = (row: any) => {
  ElMessageBox.prompt(
    `请输入用户【${row.username}】的新密码：`,
    '重置密码',
    {
      confirmButtonText: '确定重置',
      cancelButtonText: '取消',
      inputValue: '123456',
      inputPattern: /^.{6,}$/,
      inputErrorMessage: '密码长度至少6位'
    }
  ).then(async ({ value }) => {
    try {
      await request.post(`/admin/users/${row.id}/reset-password`, { new_password: value })
      ElMessage.success(`用户【${row.username}】密码已重置为：${value}`)
    } catch (err: any) {
      ElMessage.error('重置密码失败: ' + (err.message || '系统错误'))
    }
  }).catch(() => {})
}

// 删除用户
const handleDeleteUser = (row: any) => {
  ElMessageBox.confirm(
    `确定要注销并删除用户【${row.username}】及其关联的学情档案吗？此操作不可恢复！`,
    '注销确认',
    {
      confirmButtonText: '确认注销',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await request.delete(`/admin/users/${row.id}`)
      ElMessage.success('用户注销成功')
      fetchUsers()
    } catch (err: any) {
      ElMessage.error('删除用户失败: ' + (err.message || '系统错误'))
    }
  }).catch(() => {})
}

// 创建新用户弹窗
const createDialogVisible = ref(false)
const createSubmitting = ref(false)
const createFormRef = ref()
const createForm = reactive({
  username: '',
  password: 'admin123',
  nickname: '',
  phone: '',
  role_code: 'STUDENT',
  grade: '小学三年级',
  school_name: '蓟州区下营镇中心小学'
})

const createRules = {
  username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入初始密码', trigger: 'blur' }],
  nickname: [{ required: true, message: '请输入姓名或昵称', trigger: 'blur' }]
}

const handleOpenCreateDialog = () => {
  createForm.username = ''
  createForm.password = '123456'
  createForm.nickname = ''
  createForm.phone = ''
  createForm.role_code = 'STUDENT'
  createForm.grade = '小学三年级'
  createForm.school_name = '蓟州区下营镇中心小学'
  createDialogVisible.value = true
}

const handleConfirmCreate = async () => {
  if (!createForm.username || !createForm.nickname) {
    ElMessage.warning('请填写必填项')
    return
  }
  createSubmitting.value = true
  try {
    await request.post('/admin/users', createForm)
    ElMessage.success('新用户账号创建成功')
    createDialogVisible.value = false
    fetchUsers()
  } catch (err: any) {
    ElMessage.error('创建用户失败: ' + (err.message || '系统错误'))
  } finally {
    createSubmitting.value = false
  }
}

// 编辑用户弹窗
const editDialogVisible = ref(false)
const editSubmitting = ref(false)
const editForm = reactive({
  id: 0,
  username: '',
  nickname: '',
  phone: '',
  role_code: '',
  grade: '',
  school_name: ''
})

const handleOpenEditDialog = (row: any) => {
  editForm.id = row.id
  editForm.username = row.username
  editForm.nickname = row.nickname
  editForm.phone = row.phone
  editForm.role_code = row.role_code
  editForm.grade = row.grade
  editForm.school_name = row.school_name
  editDialogVisible.value = true
}

const handleConfirmEdit = async () => {
  editSubmitting.value = true
  try {
    await request.put(`/admin/users/${editForm.id}`, {
      nickname: editForm.nickname,
      phone: editForm.phone,
      role_code: editForm.role_code,
      grade: editForm.grade,
      school_name: editForm.school_name
    })
    ElMessage.success('用户资料更新成功')
    editDialogVisible.value = false
    fetchUsers()
  } catch (err: any) {
    ElMessage.error('更新失败: ' + (err.message || '系统错误'))
  } finally {
    editSubmitting.value = false
  }
}

onMounted(() => {
  fetchUsers()
  fetchClasses()
})
</script>

<style scoped>
.users-view {
  padding: 8px 4px 40px;
}

.main-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #2F2925;
}

.header-subtitle {
  font-size: 13px;
  color: #8C827A;
}

.primary-btn {
  background-color: #8B4A2F;
  border-color: #8B4A2F;
}
.primary-btn:hover {
  background-color: #A35939;
  border-color: #A35939;
}

.filter-toolbar {
  margin-bottom: 18px;
  padding: 16px;
  background-color: #FBF9F5;
  border-radius: 8px;
  border: 1px solid #EAE3D9;
}

.user-table {
  border-radius: 8px;
  overflow: hidden;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  border: 1px solid #EAE3D9;
  flex-shrink: 0;
}

.user-meta {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  color: #2F2925;
}

.user-account {
  font-size: 12px;
  color: #8C827A;
  margin-left: 4px;
}

.user-contact {
  font-size: 12px;
  color: #8C827A;
  margin-top: 2px;
}

.school-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.school-name {
  font-size: 13px;
  color: #2F2925;
  font-weight: 500;
}

.grade-tag {
  font-size: 12px;
  color: #8C827A;
}

.growth-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.energy-text {
  font-size: 13px;
  font-weight: bold;
  color: #D6A85C;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.class-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.class-summary {
  font-size: 14px;
  color: #5C554E;
}

.muted-text {
  font-size: 12px;
  color: #8C827A;
}
</style>
