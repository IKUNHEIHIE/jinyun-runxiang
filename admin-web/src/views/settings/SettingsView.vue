<template>
  <div class="settings-view">
    <div class="page-header">
      <div class="header-left">
        <h2 class="title">系统设置与模型接入</h2>
        <p class="subtitle">管理创作与教学使用的模型、站点信息及美育规则</p>
      </div>
      <div class="header-actions">
        <span class="save-status" role="status">{{ loading ? '正在读取设置…' : loadError ? '设置读取失败' : dirty ? '有未保存的修改' : '设置已同步' }}</span>
        <el-button type="primary" :loading="saving" :disabled="!settingsReady || !dirty" @click="handleSaveAll" class="save-btn">
          <el-icon><Check /></el-icon> 保存全部系统设置
        </el-button>
      </div>
    </div>
    <el-alert v-if="loadError" type="error" :closable="false" show-icon class="settings-error">
      <template #title>暂时无法读取设置</template>
      {{ loadError }}
      <el-button size="small" text @click="fetchSettings">重新加载</el-button>
    </el-alert>

    <el-tabs v-model="activeTab" class="settings-tabs" type="border-card">
      <!-- Tab 1: 大模型 API 配置 -->
      <el-tab-pane name="llm">
        <template #label>
          <span class="tab-label">
            <el-icon><Cpu /></el-icon>
            <span>AI 大模型与多模态接入</span>
          </span>
        </template>

        <el-form :model="llmForm" label-width="150px" class="settings-form" :disabled="!settingsReady || saving" v-loading="loading">
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
            <div class="form-tip">密钥只在服务端保存，回读仅显示掩码；保留掩码表示不更换，清空表示移除</div>
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

          <el-divider />
          <div class="section-title"><span class="indicator"></span><span>AI 工坊 · 生图与参考图编辑</span></div>
          <el-form-item label="启用真实生图">
            <el-switch v-model="llmForm.image_generation.enabled" />
            <div class="form-tip">用于青铜纹样、皮影与漆绣。图片理解模型名称不会自动作为生图模型使用。</div>
          </el-form-item>
          <el-form-item label="配置预设">
            <el-button @click="useSenseNova">填入 SenseNova U1.5 Lite 参数</el-button>
            <div class="form-tip">预设只填写接口参数，密钥需单独填写后保存。</div>
          </el-form-item>
          <el-form-item label="复用文本连接">
            <el-switch v-model="llmForm.image_generation.use_text_connection" />
            <div class="form-tip">开启时使用上方文本服务的地址与密钥，生图模型名仍需单独填写。</div>
          </el-form-item>
          <template v-if="!llmForm.image_generation.use_text_connection">
            <el-form-item label="生图 API Base">
              <el-input v-model="llmForm.image_generation.api_base" placeholder="https://token.sensenova.cn/v1" />
              <div class="form-tip">填写基础地址；生成请求自动追加 /images/generations。</div>
            </el-form-item>
            <el-form-item label="生图 API Key">
              <el-input v-model="llmForm.image_generation.api_key" type="password" show-password autocomplete="new-password" placeholder="填写生图服务密钥；已保存的密钥显示为掩码" />
            </el-form-item>
          </template>
          <el-form-item label="生图模型 ID">
            <el-input v-model="llmForm.image_generation.model_name" placeholder="例如 sensenova-u1.5-lite" />
          </el-form-item>
          <el-form-item label="支持参考图编辑">
            <el-switch v-model="llmForm.image_generation.supports_edit" />
            <div class="form-tip">确认模型支持图片编辑后开启；草图通过服务端发送，手机端不会接触密钥。</div>
          </el-form-item>
          <el-form-item v-if="llmForm.image_generation.supports_edit" label="编辑请求格式">
            <el-select v-model="llmForm.image_generation.edit_transport">
              <el-option label="OpenAI 标准文件上传（multipart）" value="multipart" />
              <el-option label="SenseNova 图片数组（JSON images）" value="json_images" />
            </el-select>
          </el-form-item>
          <el-form-item label="图片尺寸">
            <el-select v-model="llmForm.image_generation.size">
              <el-option v-for="size in ['1024x1024', '1536x1024', '1024x1536', '512x512', 'auto']" :key="size" :label="size" :value="size" />
            </el-select>
          </el-form-item>
          <el-form-item label="图片返回方式">
            <el-select v-model="llmForm.image_generation.response_format">
              <el-option label="服务默认" value="auto" />
              <el-option label="Base64 图片（推荐）" value="b64_json" />
              <el-option label="图片链接（服务端转存）" value="url" />
            </el-select>
          </el-form-item>
          <el-form-item label="生图超时（秒）">
            <el-input-number v-model="llmForm.image_generation.timeout_seconds" :min="30" :max="180" />
            <div class="form-tip">超时不会自动重复调用模型。重新生成可能产生新的服务调用。</div>
          </el-form-item>
          <el-form-item label="模型访问检查">
            <el-button :loading="testingImage" @click="handleTestImage">检查配置与模型访问</el-button>
            <div class="form-tip">检查当前填写的参数，不生成图片。保存后手机端才会使用新配置；部分服务不提供模型查询。</div>
            <div v-if="imageTestResult" role="status">{{ imageTestResult }}</div>
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
                  <span v-if="testResult.success && testResult.latency_ms != null" class="res-latency">
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
            <el-button type="primary" :loading="saving" :disabled="!settingsReady || !dirty" @click="handleSaveAll">
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

        <el-form :model="siteForm" label-width="150px" class="settings-form" :disabled="!settingsReady || saving" v-loading="loading">
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
            <el-button type="primary" :loading="saving" :disabled="!settingsReady || !dirty" @click="handleSaveAll">
              保存全站运营自定义设置
            </el-button>
          </div>
        </el-form>
      </el-tab-pane>

      <!-- Tab 3: 美育助农物资实体流向管理 (P3) -->
      <el-tab-pane name="supplies">
        <template #label>
          <span class="tab-label">
            <el-icon><Present /></el-icon>
            <span>美育助农物资实体流向管理</span>
          </span>
        </template>

        <div style="padding: 10px 0;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
              <h3 style="margin: 0; color: #2F2925; font-size: 16px;">🌱 乡村小学美育耗材定向调拨实体流向</h3>
              <p style="margin: 4px 0 0; color: #776D65; font-size: 13px;">基金比例按站点配置逐笔计提；物资流向以已登记的调拨批次为准，不承诺全部转化</p>
            </div>
            <el-button type="primary" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="supplyDialogVisible = true">
              + 登记新增调拨批次
            </el-button>
          </div>

          <el-table :data="suppliesList" v-loading="suppliesLoading" border stripe style="width: 100%">
            <el-table-column prop="batch_no" label="调拨批次" width="180" />
            <el-table-column prop="district" label="行政区划" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.district }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="school_name" label="受助乡村小学" min-width="160" />
            <el-table-column prop="materials_name" label="定向物资名称" min-width="200" />
            <el-table-column label="调拨数量" width="110">
              <template #default="{ row }">
                <strong style="color: #8B4A2F;">{{ row.quantity }}</strong> {{ row.unit }}
              </template>
            </el-table-column>
            <el-table-column prop="beneficiary_students" label="受益儿童" width="100">
              <template #default="{ row }">
                {{ row.beneficiary_students }} 人
              </template>
            </el-table-column>
            <el-table-column prop="delivered_date" label="签收日期" width="120" />
            <el-table-column prop="status" label="物资状态" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'DELIVERED'" type="success" size="small">已送达校区</el-tag>
                <el-tag v-else type="warning" size="small">调拨运送中</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 登记物资调拨弹窗 -->
    <el-dialog v-model="supplyDialogVisible" title="登记新增助农美育耗材调拨批次" width="500px">
      <el-form :model="newSupplyForm" label-width="110px">
        <el-form-item label="行政区划" required>
          <el-select v-model="newSupplyForm.district" placeholder="请选择天津涉农区" style="width: 100%;">
            <el-option label="蓟州区" value="蓟州区" />
            <el-option label="宝坻区" value="宝坻区" />
            <el-option label="武清区" value="武清区" />
            <el-option label="静海区" value="静海区" />
            <el-option label="宁河区" value="宁河区" />
          </el-select>
        </el-form-item>
        <el-form-item label="受助学校全称" required>
          <el-input v-model="newSupplyForm.school_name" placeholder="例如：蓟州区下营镇中心小学" />
        </el-form-item>
        <el-form-item label="调拨物资名称" required>
          <el-input v-model="newSupplyForm.materials_name" placeholder="例如：津派皮影牛皮材料包与刻刀" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="14">
            <el-form-item label="数量" required>
              <el-input-number v-model="newSupplyForm.quantity" :min="1" :max="10000" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="单位">
              <el-input v-model="newSupplyForm.unit" placeholder="套/盒/箱" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="预计受益人数">
          <el-input-number v-model="newSupplyForm.beneficiary_students" :min="1" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="supplyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addingSupply" style="background-color: #8B4A2F; border-color: #8B4A2F;" @click="submitAddSupply">
          确认登记并入库
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Check, Cpu, Setting, Connection, Present } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const activeTab = ref('llm')
const loading = ref(false)
const saving = ref(false)
const testingLlm = ref(false)
const testingImage = ref(false)
const imageTestResult = ref('')
const loadError = ref('')
const savedSettings = ref('')
const settingsReady = computed(() => !loading.value && !loadError.value && !!savedSettings.value)
const fingerprint = () => JSON.stringify({ llm_settings: llmForm.value, site_settings: siteForm.value })
const dirty = computed(() => !!savedSettings.value && fingerprint() !== savedSettings.value)

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
  enable_proxy: false,
  image_generation: {
    enabled: false, use_text_connection: true, api_base: '', api_key: '', model_name: '',
    supports_edit: false, edit_transport: 'multipart', size: '1024x1024', response_format: 'auto', timeout_seconds: 120
  }
})

function useSenseNova() {
  Object.assign(llmForm.value.image_generation, {
    use_text_connection: false, api_base: 'https://token.sensenova.cn/v1',
    model_name: 'sensenova-u1.5-lite', supports_edit: true,
    edit_transport: 'json_images', size: '1024x1024', response_format: 'b64_json'
  })
  imageTestResult.value = ''
}

async function handleTestImage() {
  if (testingImage.value || !settingsReady.value || saving.value) return
  const tested = fingerprint()
  testingImage.value = true
  imageTestResult.value = ''
  try {
    const result: any = await request.post('/admin/settings/test-image', llmForm.value)
    if (tested === fingerprint()) imageTestResult.value = result.message
  } catch (error: any) {
    if (tested === fingerprint()) imageTestResult.value = error.response?.data?.message || error.message || '模型访问检查失败'
  } finally {
    testingImage.value = false
  }
}

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
  latency_ms?: number | null
  reply_preview?: string
}

const testResult = ref<TestResult | null>(null)
watch(() => JSON.stringify(llmForm.value), () => {
  imageTestResult.value = ''
  testResult.value = null
})

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
  loadError.value = ''
  try {
    const res: any = await request.get('/admin/settings')
    if (!res?.llm_settings || !res?.site_settings) throw new Error('未能读取完整配置，请重新加载')
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
    savedSettings.value = fingerprint()
  } catch (err: any) {
    const detail = err.response?.data?.detail
    loadError.value = err.response?.data?.message || (typeof detail === 'string' ? detail : '请检查网络连接，稍后重新加载。现有配置将保留。')
  } finally {
    loading.value = false
  }
}

// 探测大模型连通性
const handleTestLlm = async () => {
  if (testingLlm.value || !settingsReady.value || saving.value) return
  if (!llmForm.value.api_key) {
    ElMessage.warning('请先填写 API Key 再进行连通性测试')
    return
  }

  testingLlm.value = true
  const tested = fingerprint()
  testResult.value = null
  try {
    const res: any = await request.post('/admin/settings/test-llm', {
      provider: llmForm.value.provider,
      api_base: llmForm.value.api_base,
      api_key: llmForm.value.api_key,
      model_name: llmForm.value.model_name
    })

    if (tested !== fingerprint()) return
    testResult.value = {
      success: true,
      message: res.is_real_call ? '服务商接口真实调用成功' : '连通性测试通过',
      latency_ms: res.latency_ms ?? null,
      reply_preview: res.reply_preview || ''
    }
    ElMessage.success('大模型 API 连通探测正常！')
  } catch (err: any) {
    if (tested !== fingerprint()) return
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
  if (saving.value || !settingsReady.value || !dirty.value) return
  const payload = JSON.parse(fingerprint())
  saving.value = true
  try {
    await request.post('/admin/settings', payload)
    if (llmForm.value.api_key) llmForm.value.api_key = '********'
    if (llmForm.value.image_generation.api_key) llmForm.value.image_generation.api_key = '********'
    savedSettings.value = fingerprint()
    ElMessage.success('设置已保存')
  } catch (err: any) {
    ElMessage.error('保存失败: ' + (err.message || '系统错误'))
  } finally {
    saving.value = false
  }
}

// -------------------------------------------------------------
// 美育助农物资流向管理逻辑 (P3)
// -------------------------------------------------------------
const suppliesList = ref<any[]>([])
const suppliesLoading = ref(false)
const supplyDialogVisible = ref(false)
const addingSupply = ref(false)
const newSupplyForm = ref({
  district: '蓟州区',
  school_name: '',
  materials_name: '',
  quantity: 100,
  unit: '套',
  beneficiary_students: 80
})

const fetchSupplies = async () => {
  suppliesLoading.value = true
  try {
    const res: any = await request.get('/admin/philanthropy/supplies')
    suppliesList.value = res || []
  } catch (e) {
    console.error(e)
  } finally {
    suppliesLoading.value = false
  }
}

const submitAddSupply = async () => {
  if (!newSupplyForm.value.school_name || !newSupplyForm.value.materials_name) {
    ElMessage.warning('请填写受助学校名称与调拨物资名称')
    return
  }
  addingSupply.value = true
  try {
    await request.post('/admin/philanthropy/supplies', newSupplyForm.value)
    ElMessage.success('助农美育物资批次已成功入库并生成调拨单')
    supplyDialogVisible.value = false
    newSupplyForm.value = {
      district: '蓟州区',
      school_name: '',
      materials_name: '',
      quantity: 100,
      unit: '套',
      beneficiary_students: 80
    }
    fetchSupplies()
  } catch (e) {
    ElMessage.error('登记失败')
  } finally {
    addingSupply.value = false
  }
}

onMounted(() => {
  fetchSettings()
  fetchSupplies()
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
  gap: 20px;
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
  flex-basis: 100%;
  min-width: 0;
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
.header-actions {
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}
.save-status { font-size: 12px; color: #8C827A; }
.settings-error { margin-bottom: 16px; }
.settings-form :deep(.el-form-item__content) { min-width: 0; }
.test-header { gap: 16px; flex-wrap: wrap; }
@media (max-width: 1100px) {
  .settings-form :deep(.el-row) > .el-col { max-width: 100%; flex: 0 0 100%; }
}
@media (max-width: 768px) {
  .page-header { align-items: flex-start; flex-direction: column; padding: 18px 16px; }
  .header-actions { justify-content: flex-start; }
  .settings-form { padding: 12px 4px; }
  .settings-form :deep(.el-form-item) { display: block; }
  .settings-form :deep(.el-form-item__label) {
    width: auto !important; height: auto; display: block;
    text-align: left; line-height: 1.6; padding: 0 0 6px;
  }
  .settings-form :deep(.el-form-item__content) { margin-left: 0 !important; }
  .tab-label { font-size: 13px; padding: 4px 0; }
}
</style>
