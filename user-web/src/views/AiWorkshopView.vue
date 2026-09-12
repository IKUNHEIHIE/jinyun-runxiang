<template>
  <div class="ai-page">
    <div class="page-header">
      <div class="tag-gold mb-2">❖ 垂类大模型多模态生成 · 具身智能设计中枢</div>
      <h1 class="page-title font-serif">AI 工坊 · 天津非遗数字创客空间</h1>
      <p class="page-sub">
        让乡村孩子用一句话生成津派皮影造型、商周青铜纹饰与古法大漆配色，感受科技赋能传统手艺的奇妙碰撞
      </p>
    </div>

    <!-- 工具选择器 -->
    <div class="tools-selector">
      <div 
        v-for="tool in tools" 
        :key="tool.key"
        :class="['tool-tab paper-card', { active: currentTool === tool.key }]"
        @click="selectTool(tool.key)"
      >
        <span class="tool-tab-icon">{{ tool.icon }}</span>
        <div class="tool-tab-text">
          <h4 class="font-serif">{{ tool.name }}</h4>
          <p>{{ tool.desc }}</p>
        </div>
      </div>
    </div>

    <!-- 创作流程引导步骤条 (Element Plus 工业级组件) -->
    <div class="steps-box paper-card" style="margin-bottom: 24px; padding: 18px 24px;">
      <el-steps :active="activeStep" finish-status="success" align-center>
        <el-step title="1. 选择非遗工艺" description="皮影 / 青铜 / 曲牌 / 漆艺" />
        <el-step title="2. 灵感与提示词" description="自然语言描述角色或器物" />
        <el-step title="3. AI 多模态推理" description="抽取津派特征并生成矢量线稿" />
        <el-step title="4. 纸样下料与3D检视" description="下载激光纸样与3D骨骼模型" />
      </el-steps>
    </div>

    <!-- 线下手工实物 AI 审美测评入口 -->
    <div class="quick-eval-bar paper-card">
      <div class="quick-eval-left">
        <span class="quick-eval-icon">📷</span>
        <div>
          <strong class="eval-banner-title">乡村美育小工匠 · 线下手工作品 AI 审美门诊</strong>
          <p class="eval-banner-sub">完成非遗剪纸、皮影拼装或年画填色？拍照上传即可获得天津美院专家组与 AI 导师的量化评分与名师寄语！</p>
        </div>
      </div>
      <el-button type="warning" round class="btn-eval" :loading="evaluating" @click="triggerUploadEval">
        📸 上传手作照片诊断 (+30 能量)
      </el-button>
      <input type="file" ref="fileInput" style="display: none" accept="image/*" @change="onPhotoSelected" />
    </div>

    <!-- 创作工坊主工作台 -->
    <div class="workshop-layout">
      <!-- 左侧：提示词与生成参数 -->
      <div class="paper-card panel-left">
        <h3 class="font-serif panel-title">
          <span>🎨 灵感输入与风格设定</span>
          <span class="tool-badge">{{ currentToolName }}</span>
        </h3>

        <div class="form-group">
          <label class="form-label">创意提示词（津门非遗特色）：</label>
          <el-input 
            v-model="promptText" 
            type="textarea" 
            :rows="4" 
            placeholder="描述您想生成的津派非遗角色、神兽纹样或器物..."
            resize="none"
          />
        </div>

        <div class="preset-prompts">
          <span class="preset-label">津门灵感预设：</span>
          <div class="preset-tags">
            <span 
              v-for="(p, idx) in presetPrompts" 
              :key="idx" 
              class="preset-chip"
              @click="promptText = p"
            >
              {{ p }}
            </span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">非遗渲染色调与工艺：</label>
          <el-radio-group v-model="selectedStyle">
            <el-radio-button label="TIANJIN_HERITAGE">津沽传统本色</el-radio-button>
            <el-radio-button label="MINERAL_LACQUER">古法矿物大漆</el-radio-button>
            <el-radio-button label="BRONZE_PATINA">金石拓片古铜</el-radio-button>
          </el-radio-group>
        </div>

        <div class="action-row">
          <el-button 
            type="primary" 
            size="large" 
            class="btn-primary w-full"
            :loading="generating"
            @click="submitAiTask"
          >
            <span v-if="!generating">✦ 启动 AI 多模态生成 (+20 能量)</span>
            <span v-else>正在进行非遗多模态推理...</span>
          </el-button>
        </div>

        <!-- 进度条 -->
        <div v-if="generating" class="progress-box">
          <div class="progress-status">
            <span>{{ progressText }}</span>
            <span>{{ progressVal }}%</span>
          </div>
          <el-progress :percentage="progressVal" color="#8B4A2F" :stroke-width="8" :show-text="false" />
        </div>
      </div>

      <!-- 右侧：生成成果展示视窗 -->
      <div class="paper-card panel-right">
        <h3 class="font-serif panel-title">
          <span>❖ 非遗创作数字资产与 3D 成果</span>
          <span v-if="taskResult" class="status-chip success">生成成功</span>
        </h3>

        <div v-if="!taskResult && !generating" class="empty-state">
          <div class="empty-icon">🏮</div>
          <p>在左侧输入您的非遗灵感，AI 将为您生成专属艺术成果与 3D 打印模型！</p>
        </div>

        <div v-else-if="generating" class="generating-state">
          <el-icon class="is-loading gen-spinner"><Loading /></el-icon>
          <p class="gen-title font-serif">匠心演算中，正在抽取天津非遗艺术特征...</p>
          <p class="gen-sub">线稿拓印 ➔ 传统套色渲染 ➔ 3D骨骼拓扑结构搭建</p>
        </div>

        <div v-else-if="taskResult" class="result-showcase">
          <!-- 彩色贴图 -->
          <div class="result-card">
            <img :src="taskResult.colored_image_url || taskResult.rendered_image_url || taskResult.completed_sketch_url" class="result-img" />
            <div class="result-desc">
              <span class="tag-heritage">非遗艺术语言解析</span>
              <p>{{ taskResult.description }}</p>
            </div>
          </div>

          <!-- 3D 模型与激光图纸 -->
          <div class="asset-actions">
            <div class="asset-btn-box">
              <span class="asset-name">GLTF 3D 可动模型</span>
              <a :href="taskResult.mesh_3d_url || '#'" target="_blank" class="download-btn">
                查看 3D 预览 ↗
              </a>
            </div>
            <div class="asset-btn-box">
              <span class="asset-name">A4 纸样/激光雕镂模板</span>
              <button class="download-btn" @click="downloadTemplate">
                下载打印纸样 ↓
              </button>
            </div>
          </div>

          <!-- 底部操作按钮 -->
          <div class="showcase-footer">
            <el-button type="primary" class="btn-primary" :loading="evaluating" @click="runEvaluation(null)">
              ✦ 发起 AI 名师审美诊断 (+30 能量)
            </el-button>
            <el-button type="success" @click="shareToCommunity">
              发布到美育社区广场
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 名师审美诊断评价卡片弹窗 -->
    <el-dialog
      v-model="evalModalVisible"
      title="天津非遗名师 · AI 多模态审美诊断成长档案"
      width="680px"
      custom-class="eval-dialog"
      destroy-on-close
    >
      <div v-if="evalResult" class="eval-card-body">
        <div class="eval-header-banner">
          <div class="eval-badge-seal">非遗<br>认证</div>
          <div style="flex: 1;">
            <div class="eval-cert-id">档案编号：{{ evalResult.evaluation_id }}</div>
            <h3 class="font-serif eval-work-title">{{ evalResult.title }} · 审美评定报告</h3>
            <div class="eval-stars">
              <span v-for="s in evalResult.stars" :key="s" class="star-icon">★</span>
              <span class="eval-score-num">{{ evalResult.total_score }}</span>
              <span class="eval-score-unit">分</span>
              <span class="eval-energy-tag">⚡ 美育能量 +{{ evalResult.energy_reward }}</span>
            </div>
          </div>
        </div>

        <!-- 诊断三维指标 -->
        <div class="eval-dimensions">
          <div class="dim-item">
            <div class="dim-head">
              <span class="dim-name">❖ {{ evalResult.dimensions.composition.name }}</span>
              <span class="dim-score">{{ evalResult.dimensions.composition.score }}分</span>
            </div>
            <el-progress :percentage="evalResult.dimensions.composition.score" color="#8B4A2F" :stroke-width="6" :show-text="false" />
            <p class="dim-tip">{{ evalResult.dimensions.composition.feedback }}</p>
          </div>

          <div class="dim-item">
            <div class="dim-head">
              <span class="dim-name">❖ {{ evalResult.dimensions.color.name }}</span>
              <span class="dim-score">{{ evalResult.dimensions.color.score }}分</span>
            </div>
            <el-progress :percentage="evalResult.dimensions.color.score" color="#C4863A" :stroke-width="6" :show-text="false" />
            <p class="dim-tip">{{ evalResult.dimensions.color.feedback }}</p>
          </div>

          <div class="dim-item">
            <div class="dim-head">
              <span class="dim-name">❖ {{ evalResult.dimensions.technique.name }}</span>
              <span class="dim-score">{{ evalResult.dimensions.technique.score }}分</span>
            </div>
            <el-progress :percentage="evalResult.dimensions.technique.score" color="#4D8B63" :stroke-width="6" :show-text="false" />
            <p class="dim-tip">{{ evalResult.dimensions.technique.feedback }}</p>
          </div>
        </div>

        <!-- 名师寄语 -->
        <div class="eval-mentor-box">
          <div class="mentor-title">
            <span class="mentor-icon">✒️</span>
            <span>津派非遗名师评语与进阶指引：</span>
          </div>
          <p class="mentor-quote">{{ evalResult.mentor_comment }}</p>
          <div class="mentor-sign">
            <span>{{ evalResult.certified_by }}</span>
            <span class="eval-date">{{ evalResult.created_at }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="evalModalVisible = false">关闭档案</el-button>
        <el-button type="primary" class="btn-primary" @click="saveEvalReport">
          保存诊断档案卡
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../api/request'

const tools = [
  { key: 'SHADOW_PUPPET', icon: '🎭', name: '津派皮影生成', desc: '三签关节、镂空刀法、3D骨骼' },
  { key: 'BRONZE', icon: '🏺', name: '青铜神兽饕餮', desc: '天博礼器、金石拓片、铜绿质感' },
  { key: 'BALLAD', icon: '🥁', name: '骆派曲牌哼唱', desc: '五声音阶、时调鼓韵、三弦配曲' },
  { key: 'LACQUER', icon: '✨', name: '古法大漆螺钿', desc: '天然矿物色系、流线修复、螺钿生辉' }
]

const currentTool = ref('SHADOW_PUPPET')
const promptText = ref('身披红绫战甲，手执银枪的津沽小英雄穆桂英')
const selectedStyle = ref('TIANJIN_HERITAGE')

const generating = ref(false)
const progressVal = ref(0)
const progressText = ref('')
const taskResult = ref<any>(null)

const currentToolName = computed(() => {
  const t = tools.find(x => x.key === currentTool.value)
  return t ? t.name : '非遗工坊'
})

const activeStep = computed(() => {
  if (taskResult.value) return 4
  if (generating.value) return 2
  if (promptText.value && promptText.value.trim().length > 0) return 1
  return 0
})

const presetPrompts = computed(() => {
  if (currentTool.value === 'SHADOW_PUPPET') {
    return [
      '身穿绣金文生巾的津门赶考书生',
      '齐天大圣大闹天宫皮影，带三签活动翎毛',
      '手执杨柳青红锦鲤的吉庆福娃'
    ]
  } else if (currentTool.value === 'BRONZE') {
    return [
      '商周饕餮双龙神兽纹饰，金石拓片风',
      '夔龙纹青铜编钟浮雕，带斑驳氧化铜绿',
      '天津运河出土青铜礼器饕餮纹杯'
    ]
  } else if (currentTool.value === 'BALLAD') {
    return [
      '津门九河下梢海河晚渡风情鼓词',
      '时调大鼓快板，三弦伴奏欢快节奏',
      '杨柳青古镇运河码头春日书场'
    ]
  } else {
    return [
      '天然大漆黑漆螺钿花鸟圆盘',
      '泥金配岱红古法漆艺茶盏',
      '天津市花月季天然矿物色螺钿托盘'
    ]
  }
})

const selectTool = (key: string) => {
  currentTool.value = key
  if (presetPrompts.value.length > 0) {
    promptText.value = presetPrompts.value[0]
  }
  taskResult.value = null
}

const submitAiTask = async () => {
  if (!promptText.value.trim()) {
    ElMessage.warning('请输入创意提示词')
    return
  }

  generating.value = true
  progressVal.value = 15
  progressText.value = '正在连接天津非遗垂直多模态推理节点...'
  taskResult.value = null

  try {
    const res: any = await request.post('/ai/tasks', {
      tool_type: currentTool.value,
      input_payload: {
        prompt: promptText.value,
        style: selectedStyle.value
      }
    })

    const taskId = res.task_id

    // 模拟状态机进度轮询
    setTimeout(() => {
      progressVal.value = 45
      progressText.value = '正在提取非遗传统刀法线稿与轮廓拓扑...'
    }, 600)

    setTimeout(() => {
      progressVal.value = 80
      progressText.value = '正在依据古法标准套印天然矿物色泽...'
    }, 1200)

    setTimeout(async () => {
      progressVal.value = 100
      progressText.value = '多模态艺术资产已构建完成！'
      
      const pollRes: any = await request.get(`/ai/tasks/${taskId}`)
      taskResult.value = pollRes.result
      generating.value = false
      ElMessage.success('非遗 AI 作品生成成功！美育能量 +20')
    }, 1800)

  } catch (e) {
    generating.value = false
    ElMessage.error('生成任务失败，请重试')
  }
}

const downloadTemplate = () => {
  ElMessage.success('正在为您打包下载津派非遗 A4 激光切割与手工打印纸样！')
}

const shareToCommunity = async () => {
  try {
    await request.post('/community/posts', {
      title: `我的AI非遗工坊作品：${promptText.value.slice(0, 18)}`,
      content: `在《津韵润乡》AI工坊创作完成了【${currentToolName.value}】作品，感受到了家乡非遗的美！`,
      category: currentTool.value,
      cover_url: taskResult.value.colored_image_url || taskResult.value.rendered_image_url || 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600'
    })
    ElMessage.success('已一键发布到美育社区广场！欢迎同学们交流点评')
  } catch (e) {
    ElMessage.error('发布失败')
  }
}

const evalModalVisible = ref(false)
const evaluating = ref(false)
const evalResult = ref<any>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const triggerUploadEval = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const onPhotoSelected = async (e: Event) => {
  const target = e.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  const file = target.files[0]

  evaluating.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const uploadRes: any = await request.post('/ai/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const uploadedUrl = uploadRes.file_url
    await runEvaluation(uploadedUrl, file.name.replace(/\.[^/.]+$/, ''))
  } catch (err) {
    ElMessage.error('照片上传或测评失败')
    evaluating.value = false
  } finally {
    target.value = ''
  }
}

const runEvaluation = async (customImg?: string | null, customTitle?: string) => {
  evaluating.value = true
  try {
    const targetImg = customImg || taskResult.value?.colored_image_url || taskResult.value?.rendered_image_url || '/static/images/shadow_puppet_sheng.svg'
    const targetTitle = customTitle || taskResult.value?.description?.slice(0, 16) || '津派非遗手作创客作品'
    const res: any = await request.post('/ai/evaluate', {
      image_url: targetImg,
      heritage_type: currentTool.value,
      title: targetTitle
    })
    evalResult.value = res
    evalModalVisible.value = true
    ElMessage.success('非遗 AI 名师审美诊断完成！美育能量 +30 点已汇入！')
  } catch (e) {
    ElMessage.error('审美诊断失败，请重试')
  } finally {
    evaluating.value = false
  }
}

const saveEvalReport = () => {
  ElMessage.success('审美诊断成长档案已保存至个人中心！')
  evalModalVisible.value = false
}
</script>

<style scoped>
.ai-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px;
}

.page-header {
  margin-bottom: 28px;
}

.page-title {
  font-size: 32px;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.page-sub {
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* 工具选项卡 */
.tools-selector {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.tool-tab {
  padding: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 14px;
  border-radius: 12px;
}

.tool-tab:hover {
  border-color: var(--color-gold);
}

.tool-tab.active {
  border-color: var(--color-primary);
  background: #FFF8F3;
  box-shadow: 0 4px 16px rgba(139, 74, 47, 0.12);
}

.tool-tab-icon {
  font-size: 28px;
}

.tool-tab-text h4 {
  font-size: 16px;
  color: var(--color-text-main);
  margin-bottom: 4px;
}

.tool-tab-text p {
  font-size: 11px;
  color: var(--color-text-secondary);
}

/* 工作台布局 */
.workshop-layout {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 32px;
}

.panel-left, .panel-right {
  padding: 28px;
  display: flex;
  flex-direction: column;
}

.panel-title {
  font-size: 18px;
  color: var(--color-text-main);
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.tool-badge {
  font-size: 12px;
  font-family: var(--font-sans);
  background: rgba(139, 74, 47, 0.1);
  color: var(--color-primary);
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 700;
}

.status-chip.success {
  font-size: 12px;
  background: #EBF8F2;
  color: #059669;
  border: 1px solid rgba(5, 150, 105, 0.3);
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 600;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-regular);
  margin-bottom: 8px;
}

.preset-prompts {
  margin-bottom: 20px;
}

.preset-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  display: block;
  margin-bottom: 6px;
}

.preset-tags {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preset-chip {
  font-size: 12px;
  color: var(--color-text-regular);
  background: var(--color-paper);
  border: 1px solid var(--color-border);
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.preset-chip:hover {
  background: #FFF8EA;
  color: var(--color-primary);
  border-color: var(--color-gold);
}

.w-full {
  width: 100%;
}

.progress-box {
  margin-top: 20px;
  padding: 16px;
  background: var(--color-paper);
  border-radius: 8px;
}

.progress-status {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 600;
  margin-bottom: 8px;
}

/* Panel Right States */
.empty-state, .generating-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 360px;
  padding: 32px;
}

.empty-icon {
  font-size: 56px;
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 14px;
  color: var(--color-text-secondary);
  max-width: 320px;
}

.gen-spinner {
  font-size: 48px;
  color: var(--color-primary);
  margin-bottom: 16px;
}

.gen-title {
  font-size: 18px;
  color: var(--color-text-main);
  margin-bottom: 6px;
}

.gen-sub {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.result-showcase {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.result-card {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.result-img {
  width: 100%;
  height: 280px;
  object-fit: cover;
}

.result-desc {
  padding: 14px;
  background: var(--color-paper);
}

.result-desc p {
  font-size: 13px;
  color: var(--color-text-regular);
  line-height: 1.6;
  margin-top: 6px;
}

.asset-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.asset-btn-box {
  padding: 12px 14px;
  background: var(--color-paper);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.asset-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-main);
}

.download-btn {
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 700;
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
}

.download-btn:hover {
  text-decoration: underline;
}

.showcase-footer {
  margin-top: 8px;
  text-align: right;
}

/* 线下手工实物快速评测 Banner */
.quick-eval-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #FFFDF8 0%, #FFF5EB 100%);
  border: 1px solid rgba(196, 134, 58, 0.3);
  border-radius: 12px;
}

.quick-eval-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.quick-eval-icon {
  font-size: 28px;
}

.eval-banner-title {
  font-size: 15px;
  color: var(--color-primary);
  display: block;
}

.eval-banner-sub {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.btn-eval {
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(217, 119, 6, 0.2);
}

/* 审美诊断卡片 */
.eval-card-body {
  background: #FFFDF8;
  border: 1px solid #EEDDC9;
  border-radius: 12px;
  padding: 24px;
}

.eval-header-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 18px;
  border-bottom: 1px dashed var(--color-border);
  margin-bottom: 20px;
}

.eval-badge-seal {
  width: 52px;
  height: 52px;
  border-radius: 8px;
  background: #B64A44;
  color: #fff;
  font-family: var(--font-serif);
  font-size: 14px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  line-height: 1.2;
  box-shadow: 0 3px 8px rgba(182, 74, 68, 0.3);
}

.eval-cert-id {
  font-size: 12px;
  color: #92400E;
  font-family: monospace;
}

.eval-work-title {
  font-size: 18px;
  color: var(--color-primary);
  margin: 4px 0;
}

.eval-stars {
  display: flex;
  align-items: center;
  gap: 4px;
}

.star-icon {
  color: #D97706;
  font-size: 16px;
}

.eval-score-num {
  font-size: 20px;
  font-weight: 900;
  color: #B45309;
  margin-left: 8px;
}

.eval-score-unit {
  font-size: 12px;
  color: #B45309;
  margin-right: 12px;
}

.eval-energy-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: #FEF3C7;
  color: #92400E;
  border-radius: 12px;
  font-weight: 700;
}

.eval-dimensions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.dim-item {
  background: #FAF6EF;
  padding: 12px 16px;
  border-radius: 8px;
}

.dim-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 6px;
}

.dim-score {
  color: var(--color-primary);
}

.dim-tip {
  font-size: 12px;
  color: var(--color-text-regular);
  margin-top: 6px;
  line-height: 1.5;
}

.eval-mentor-box {
  background: #FFF9EE;
  border-left: 4px solid var(--color-gold);
  padding: 14px 18px;
  border-radius: 0 8px 8px 0;
}

.mentor-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #92400E;
  margin-bottom: 6px;
}

.mentor-quote {
  font-size: 13px;
  color: #78350F;
  line-height: 1.6;
  font-style: italic;
}

.mentor-sign {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 11px;
  color: #A16207;
  font-weight: 600;
}
</style>
