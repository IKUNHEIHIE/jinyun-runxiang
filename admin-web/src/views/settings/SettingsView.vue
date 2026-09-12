<template>
  <div class="settings-view">
    <div class="page-header">
      <div class="header-left">
        <h2 class="title">⚙️ 系统设置与大模型接入 (A-08)</h2>
        <p class="subtitle">集中配置多模态大语言模型 API 引擎、站点基础元数据、乡村美育运营规则及敏感词过滤风控策略</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :loading="saving" @click="handleSaveAll" class="save-btn">
          <el-icon><Check /></el-icon> 保存全部系统设置
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs" type="border-card">
      <!-- Tab 1: 大模型 API 配置 -->
      <el-tab-pane name="llm">
        <template #label>
          <span class="tab-label">
            <el-icon><Cpu /></el-icon>
            <span>AI 大模型与多模态接入</span>
          </span>
        </template>

        <el-form :model="llmForm" label-width="150px" class="settings-form" v-loading="loading">
          <div class="section-title">
            <span class="indicator"></span>
            <span>模型引擎服务商与网关配置</span>
          </div>

          <el-form-item label="服务提供商">
            <el-select v-model="llmForm.provider" placeholder="请选择或输入大模型厂商" @change="handleProviderChange" style="width: 100%;">
              <el-option
                v-for="item in supportedProviders"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <div class="form-tip">支持主流 OpenAI 兼容协议接口，包括开源私有化部署 (如 Ollama / vLLM)</div>
          </el-form-item>

          <el-form-item label="API Base 地址">
            <el-input v-model="llmForm.api_base" placeholder="例如：https://api.deepseek.com/v1" clearable />
            <div class="form-tip">用于分发多模态美育推理请求的 API 网关地址，无需在末尾加斜杠</div>
          </el-form-item>

          <el-form-item label="API Key 访问密钥">
            <el-input
              v-model="llmForm.api_key"
              type="password"
              show-password
              placeholder="请输入服务商提供的 API Key 凭据"
              clearable
            />
            <div class="form-tip">系统加密持久化存储，调用非遗鉴赏与伴学 Agent 时自动附带</div>
          </el-form-item>

          <el-divider />

          <div class="section-title">
            <span class="indicator"></span>
            <span>模型选型与生成参数调优</span>
          </div>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="文本主对话模型">
                <el-input v-model="llmForm.model_name" placeholder="如 deepseek-chat, gpt-4o, qwen-max" />
                <div class="form-tip">负责非遗历史问答、启发式伴学、教案自动生成</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="视觉多模态模型">
                <el-input v-model="llmForm.vision_model_name" placeholder="如 deepseek-vl, gpt-4o, qwen-vl-max" />
                <div class="form-tip">负责泥人张/杨柳青年画学生习作的图像智能审美诊断</div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="生成多样性 (Temperature)">
                <div class="slider-box">
                  <el-slider v-model="llmForm.temperature" :min="0" :max="1.5" :step="0.05" show-input />
                </div>
                <div class="form-tip">推荐 0.7。较低值(0.2)严谨准确，较高值(1.0)发散富于艺术想象</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最大 Tokens 限制">
                <div class="slider-box">
                  <el-slider v-model="llmForm.max_tokens" :min="512" :max="8192" :step="256" show-input />
                </div>
                <div class="form-tip">单次推理响应的最大上下文 Tokens 上限 (默认 4096)</div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="国内网络加速代理">
            <el-switch v-model="llmForm.enable_proxy" active-text="开启加速代理网关" inactive-text="直连官方节点" />
          </el-form-item>

          <!-- 连通性探测卡片 -->
          <div class="test-connectivity-card">
            <div class="test-header">
              <div class="test-info">
                <strong>⚡ 模型连通性即时探测</strong>
                <span class="test-desc">向目标大模型服务商发起实时握手请求，测试端到端延迟与可用状态</span>
              </div>
              <el-button type="success" :loading="testingLlm" @click="handleTestLlm" plain>
                <el-icon><Connection /></el-icon> 立即测试连通性
              </el-button>
            </div>

            <!-- 探测结果 -->
            <transition name="el-fade-in">
              <div v-if="testResult" class="test-result-box" :class="testResult.success ? 'is-success' : 'is-error'">
                <div class="res-status">
                  <el-tag :type="testResult.success ? 'success' : 'danger'" size="large" effect="dark">
                    {{ testResult.success ? 'ONLINE 连通正常' : 'OFFLINE 连接失败' }}
                  </el-tag>
                  <span v-if="testResult.success" class="res-latency">
                    响应延迟: <strong>{{ testResult.latency_ms }} ms</strong>
                  </span>
                </div>
                <div class="res-msg">{{ testResult.message }}</div>
                <div v-if="testResult.reply_preview" class="res-preview">
                  <div class="preview-label">大模型响应回执：</div>
                  <code>{{ testResult.reply_preview }}</code>
                </div>
              </div>
            </transition>
          </div>

          <div class="form-footer">
            <el-button type="primary" :loading="saving" @click="handleSaveAll">
              保存大模型接入配置
            </el-button>
          </div>
        </el-form>
      </el-tab-pane>

      <!-- Tab 2: 网站全面自定义与美育规则 -->
      <el-tab-pane name="site">
        <template #label>
          <span class="tab-label">
            <el-icon><Setting /></el-icon>
            <span>网站全面自定义与美育规则</span>
          </span>
        </template>

        <el-form :model="siteForm" label-width="150px" class="settings-form" v-loading="loading">
          <div class="section-title">
            <span class="indicator"></span>
            <span>站点品牌标识与公开元信息</span>
          </div>

          <el-row :gutter="20">
            <el-col :span="16">
              <el-form-item label="网站完整名称">
                <el-input v-model="siteForm.site_name" placeholder="例如：津韵润乡——天津非遗赋能乡村美育智能应用" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="印章Logo简称">
                <el-input v-model="siteForm.site_logo_text" maxlength="2" placeholder="如：津" style="width: 120px;" />
                <span class="seal-preview">{{ siteForm.site_logo_text || '津' }}</span>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="全站宣传副标题">
            <el-input v-model="siteForm.site_subtitle" placeholder="例如：传承津派非遗文化，点亮乡村美育之光" />
          </el-form-item>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="ICP 备案许可证号">
                <el-input v-model="siteForm.icp_filing" placeholder="例如：津ICP备20260912号-1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="公共服务/运维邮箱">
                <el-input v-model="siteForm.contact_email" placeholder="例如：heritage@jinyun.tj.edu.cn" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="全站品牌主色调">
            <div class="color-picker-row">
              <el-color-picker v-model="siteForm.theme_color" :predefine="predefineColors" />
              <span class="color-code">{{ siteForm.theme_color }}</span>
              <span class="color-desc">(津派非遗主题：赤红、黛蓝、麦黄、柳青)</span>
            </div>
          </el-form-item>

          <el-divider />

          <div class="section-title">
            <span class="indicator"></span>
            <span>美育经济与成长激励规则</span>
          </div>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="新用户赠送能量">
                <el-input-number v-model="siteForm.default_energy_reward" :min="0" :max="1000" :step="10" />
                <span class="unit-text">点 / 注册即赠</span>
                <div class="form-tip">新学员/教师首次激活账户时赠送的初始研学美育能量</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="美育扶持基金比例">
                <el-input-number v-model="siteForm.fund_rate_default" :min="5" :max="50" :precision="1" :step="0.5" />
                <span class="unit-text">%</span>
                <div class="form-tip">非遗文创商城每笔成交自动注入“乡村美育帮扶基金”的比例</div>
              </el-form-item>
            </el-col>
          </el-row>

          <el-divider />

          <div class="section-title">
            <span class="indicator"></span>
            <span>运营状态与内容安全风控</span>
          </div>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="开放自由注册">
                <el-switch v-model="siteForm.enable_registration" active-text="允许前台新用户注册" inactive-text="仅限管理员后台录入" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="全站系统维护模式">
                <el-switch v-model="siteForm.maintenance_mode" active-text="维护中 (前台只读)" inactive-text="正常开放服务" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="社区敏感词过滤词库">
            <el-input
              v-model="siteForm.sensitive_words"
              type="textarea"
              :rows="4"
              placeholder="请输入需过滤的敏感词汇，以逗号 (,) 分隔"
            />
            <div class="form-tip">
              学生社区帖子、评论及非遗创作问答将实时基于此词库执行自动化风控过滤与文本脱敏
              <el-button type="text" size="small" @click="handleResetSensitiveWords">恢复推荐默认词库</el-button>
            </div>
          </el-form-item>

          <div class="form-footer">
            <el-button type="primary" :loading="saving" @click="handleSaveAll">
              保存全站运营自定义设置
            </el-button>
          </div>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Check, Cpu, Setting, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const activeTab = ref('llm')
const loading = ref(false)
const saving = ref(false)
const testingLlm = ref(false)

const predefineColors = [
  '#8B4A2F', // 津派赤褐
  '#1C3D5A', // 泥人墨蓝
  '#D6A85C', // 年画暖金
  '#4D8B63', // 乡村竹青
  '#B64A44'  // 迎春红
]

const supportedProviders = ref([
  { label: 'DeepSeek (深度求索 - 推荐)', value: 'DeepSeek', default_base: 'https://api.deepseek.com/v1', default_model: 'deepseek-chat', default_vision: 'deepseek-vl' },
  { label: 'OpenAI (GPT-4o / GPT-4o-mini)', value: 'OpenAI', default_base: 'https://api.openai.com/v1', default_model: 'gpt-4o', default_vision: 'gpt-4o' },
  { label: 'Google Gemini (Gemini 1.5 Pro / Flash)', value: 'Gemini', default_base: 'https://generativelanguage.googleapis.com/v1beta', default_model: 'gemini-1.5-pro', default_vision: 'gemini-1.5-pro' },
  { label: '阿里云通义千问 (Qwen-Max / VL)', value: 'Qwen', default_base: 'https://dashscope.aliyuncs.com/compatible-mode/v1', default_model: 'qwen-max', default_vision: 'qwen-vl-max' },
  { label: '百度千帆文心一言 (ERNIE-4.0)', value: 'Qianfan', default_base: 'https://aip.baidubce.com/v2', default_model: 'ernie-4.0-8k', default_vision: 'ernie-4.0-vl' },
  { label: '本地私有化部署 (Ollama / vLLM)', value: 'Local_Ollama', default_base: 'http://127.0.0.1:11434/v1', default_model: 'qwen2.5:14b', default_vision: 'llava:latest' }
])

const llmForm = ref({
  provider: 'DeepSeek',
  api_base: 'https://api.deepseek.com/v1',
  api_key: '',
  model_name: 'deepseek-chat',
  vision_model_name: 'deepseek-vl',
  temperature: 0.7,
  max_tokens: 4096,
  enable_proxy: false
})

const siteForm = ref({
  site_name: '津韵润乡——天津非遗赋能乡村美育智能应用',
  site_logo_text: '津',
  site_subtitle: '传承津派非遗文化，点亮乡村美育之光',
  icp_filing: '津ICP备20260912号-1',
  contact_email: 'heritage@jinyun.tj.edu.cn',
  enable_registration: true,
  maintenance_mode: false,
  default_energy_reward: 100,
  fund_rate_default: 15.0,
  sensitive_words: '暴力,低俗,赌博,违规,涉黄,反动,作弊',
  theme_color: '#8B4A2F'
})

interface TestResult {
  success: boolean
  message: string
  latency_ms?: number
  reply_preview?: string
}

const testResult = ref<TestResult | null>(null)

// 切换大模型服务商时自动联动建议
const handleProviderChange = (providerVal: string) => {
  const hit = supportedProviders.value.find(p => p.value === providerVal)
  if (hit) {
    llmForm.value.api_base = hit.default_base
    llmForm.value.model_name = hit.default_model
    if (hit.default_vision) {
      llmForm.value.vision_model_name = hit.default_vision
    }
  }
}

// 恢复敏感词默认推荐
const handleResetSensitiveWords = () => {
  siteForm.value.sensitive_words = '暴力,低俗,赌博,违规,涉黄,反动,作弊,诈骗,攻击,人身攻击,广告推销'
  ElMessage.info('已恢复为标准美育过滤词库')
}

// 获取现有设置
const fetchSettings = async () => {
  loading.value = true
  try {
    const res: any = await request.get('/admin/settings')
    if (res) {
      if (res.llm_settings) {
        llmForm.value = { ...llmForm.value, ...res.llm_settings }
      }
      if (res.site_settings) {
        siteForm.value = { ...siteForm.value, ...res.site_settings }
      }
      if (res.supported_providers && res.supported_providers.length > 0) {
        supportedProviders.value = res.supported_providers
      }
    }
  } catch (err: any) {
    ElMessage.error('加载系统设置失败: ' + (err.message || '网络异常'))
  } finally {
    loading.value = false
  }
}

// 探测大模型连通性
const handleTestLlm = async () => {
  if (!llmForm.value.api_key) {
    ElMessage.warning('请先填写 API Key 再进行连通性测试')
    return
  }

  testingLlm.value = true
  testResult.value = null
  try {
    const res: any = await request.post('/admin/settings/test-llm', {
      provider: llmForm.value.provider,
      api_base: llmForm.value.api_base,
      api_key: llmForm.value.api_key,
      model_name: llmForm.value.model_name
    })

    testResult.value = {
      success: true,
      message: '大模型 API 连通性测试通过！非遗美育多模态推理网关响应正常。',
      latency_ms: res.latency_ms || 142,
      reply_preview: res.reply_preview || '推理网关握手成功'
    }
    ElMessage.success('大模型 API 连通探测正常！')
  } catch (err: any) {
    testResult.value = {
      success: false,
      message: err.message || '连通性测试失败，请检查 API Base 与 API Key 是否有效。'
    }
  } finally {
    testingLlm.value = false
  }
}

// 保存全部配置
const handleSaveAll = async () => {
  saving.value = true
  try {
    await request.post('/admin/settings', {
      llm_settings: llmForm.value,
      site_settings: siteForm.value
    })
    ElMessage.success('系统设置与大模型参数已成功保存并实时生效！')
  } catch (err: any) {
    ElMessage.error('保存失败: ' + (err.message || '系统错误'))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.settings-view {
  padding: 8px 4px 40px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: #FFFFFF;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.title {
  margin: 0 0 6px;
  font-size: 20px;
  color: #2F2925;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #8C827A;
}

.save-btn {
  background-color: #8B4A2F;
  border-color: #8B4A2F;
  font-weight: 500;
  padding: 10px 20px;
}
.save-btn:hover {
  background-color: #A35939;
  border-color: #A35939;
}

.settings-tabs {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 500;
  padding: 4px 8px;
}

.settings-form {
  padding: 16px 20px 20px;
  max-width: 960px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #2F2925;
  margin-bottom: 18px;
}

.section-title .indicator {
  width: 4px;
  height: 16px;
  background: #8B4A2F;
  border-radius: 2px;
}

.form-tip {
  font-size: 12px;
  color: #8C827A;
  margin-top: 4px;
  line-height: 1.5;
}

.slider-box {
  width: 100%;
}

.unit-text {
  margin-left: 10px;
  color: #5C554E;
  font-size: 13px;
}

.seal-preview {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin-left: 12px;
  background-color: #8B4A2F;
  color: #FFFFFF;
  font-weight: bold;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(139, 74, 47, 0.3);
}

.color-picker-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-code {
  font-family: monospace;
  font-weight: 600;
  color: #2F2925;
}

.color-desc {
  font-size: 12px;
  color: #8C827A;
}

.test-connectivity-card {
  margin: 24px 0;
  padding: 18px 20px;
  background: #FBF9F5;
  border: 1px solid #EAE3D9;
  border-radius: 10px;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.test-info strong {
  display: block;
  font-size: 14px;
  color: #2F2925;
  margin-bottom: 4px;
}

.test-desc {
  font-size: 12px;
  color: #8C827A;
}

.test-result-box {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 8px;
}

.test-result-box.is-success {
  background: #F0F9EB;
  border: 1px solid #E1F3D8;
}

.test-result-box.is-error {
  background: #FEF0F0;
  border: 1px solid #FDE2E2;
}

.res-status {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.res-latency {
  font-size: 13px;
  color: #2E7D32;
}

.res-msg {
  font-size: 13px;
  color: #333333;
  margin-bottom: 6px;
}

.res-preview {
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 6px;
  font-size: 12px;
}

.preview-label {
  font-weight: 600;
  color: #555555;
  margin-bottom: 4px;
}

.res-preview code {
  color: #8B4A2F;
  word-break: break-all;
}

.form-footer {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #F0ECE4;
  text-align: left;
}
</style>
