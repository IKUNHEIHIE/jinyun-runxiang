<template>
  <div class="users-view">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">👥 用户与乡村班级管理 (A-04)</span>
        </div>
      </template>

      <el-tabs v-model="tab">
        <el-tab-pane label="注册学员与教师" name="users">
          <el-table :data="users" style="width: 100%" stripe>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column label="头像" width="70">
              <template #default="{ row }">
                <el-avatar size="small" :src="row.avatar_url" />
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户名" width="140" />
            <el-table-column prop="nickname" label="昵称" width="140" />
            <el-table-column prop="role_code" label="身份角色" width="120">
              <template #default="{ row }">
                <el-tag :type="row.role_code === 'ADMIN' ? 'danger' : row.role_code === 'TEACHER' ? 'warning' : 'primary'">
                  {{ row.role_code }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="grade" label="学段/身份" width="130" />
            <el-table-column prop="status" label="账号状态" width="100">
              <template #default="{ row }">
                <el-tag type="success" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="乡村美育示范班级" name="classes">
          <el-table :data="classes" style="width: 100%" stripe>
            <el-table-column prop="id" label="班级ID" width="80" />
            <el-table-column prop="name" label="班级名称" min-width="180" />
            <el-table-column prop="teacher" label="授课教师" width="130" />
            <el-table-column prop="school" label="所属乡村学校" min-width="180" />
            <el-table-column prop="count" label="学生数" width="90" />
            <el-table-column prop="completion" label="课程完成率" width="120">
              <template #default="{ row }">
                <el-progress :percentage="row.completion" color="#4D8B63" />
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const tab = ref('users')
const users = ref([
  { id: 1, username: 'admin', nickname: '津韵总管', role_code: 'ADMIN', grade: '平台管理员', status: 'ACTIVE', avatar_url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150' },
  { id: 2, username: 'teacher_wang', nickname: '王秀兰老师', role_code: 'TEACHER', grade: '骨干美育教师', status: 'ACTIVE', avatar_url: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150' },
  { id: 3, username: 'student_ming', nickname: '李小明', role_code: 'STUDENT', grade: '小学三年级', status: 'ACTIVE', avatar_url: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150' },
  { id: 4, username: 'student_hua', nickname: '张小华', role_code: 'STUDENT', grade: '小学四年级', status: 'ACTIVE', avatar_url: 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150' }
])

const classes = ref([
  { id: 1, name: '蓟州非遗美育三年级一班', teacher: '王秀兰', school: '蓟州区下营镇中心小学', count: 42, completion: 84.5 },
  { id: 2, name: '宝坻评剧与年画特色二班', teacher: '张建军', school: '宝坻区大口屯镇初级中学', count: 38, completion: 78.0 }
])
</script>

<style scoped>
.table-card { border-radius: 12px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-title { font-weight: 600; color: #2F2925; }
</style>
