<template>
  <div class="ai-page">
    <div class="page-header">
      <div class="tag-gold mb-2">❖ 垂类大模型多模态生成 · AI 非遗设计中枢</div>
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
        <el-step title="4. 成果查看与下载" description="查看作品图并下载矢量图样" />
      </el-steps>
    </div>

    <!-- 线下手工实物 AI 审美测评入口 -->
    <div class="quick-eval-bar paper-card">
      <div class="quick-eval-left">
        <span class="quick-eval-icon">📷</span>
        <div>
          <strong class="eval-banner-title">乡村美育小工匠 · 线下手工作品 AI 审美门诊</strong>
          <p class="eval-banner-sub">完成非遗剪纸、皮影拼装或年画填色？拍照上传可获得 AI 图像评分与改进建议，结果非人工名师评审。</p>
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
          <span>❖ 非遗创作数字资产与生成成果</span>
          <span v-if="taskResult" class="status-chip success">生成成功</span>
        </h3>

        <div v-if="!taskResult && !generating" class="empty-state">
          <div class="empty-icon">🏮</div>
          <p>在左侧输入您的非遗灵感，AI 将为您生成专属艺术成果与可下载的矢量图样。</p>
        </div>

        <div v-else-if="generating" class="generating-state">
          <el-icon class="is-loading gen-spinner"><Loading /></el-icon>
          <p class="gen-title font-serif">匠心演算中，正在抽取天津非遗艺术特征...</p>
          <p class="gen-sub">线稿拓印 ➔ 传统套色渲染 ➔ 矢量图样整理</p>
        </div>

        <div v-else-if="taskResult" class="result-showcase">
          <!-- 成果主图卡片 -->
          <div class="result-card">
            <div class="result-img-box">
              <img 
                v-if="displayImageUrl" 
                :src="displayImageUrl" 
                :alt="currentToolName" 
                class="result-img"
                @error="handleImgError"
              />
              <div v-else class="result-placeholder font-serif">
                <span class="placeholder-icon">🎨</span>
                <span>津派非遗数字图谱已就绪</span>
              </div>
            </div>

            <!-- 曲艺特有：鼓板快板与工尺简谱试听播控器 -->
            <div v-if="taskResult.sheet_music_text || taskResult.audio_url" class="ballad-player-box">
              <div class="ballad-player-head">
                <div class="ballad-player-title">
                  <span class="music-note-icon">🥁</span>
                  <span class="font-serif">津门曲艺播控 · {{ taskResult.tune_name || '时调大鼓' }}</span>
                </div>
                <span class="ballad-rhythm-badge">{{ taskResult.rhythm_style || '骆派京韵大鼓快板' }}</span>
              </div>
              
              <div class="ballad-score-display">
                <span class="score-label">五声音阶简谱：</span>
                <code class="score-notation">{{ taskResult.sheet_music_text }}</code>
              </div>

              <div v-if="taskResult.audio_url" class="ballad-audio-controls">
                <button class="audio-play-toggle-btn" @click="toggleAudioPlay">
                  <span v-if="isPlaying">⏸ 暂停伴奏</span>
                  <span v-else>▶ 试听鼓板伴奏</span>
                </button>
                <div class="rhythm-beat-indicator" :class="{ beating: isPlaying }">
                  <span class="drum-beat-icon">🥁</span>
                  <span class="beat-text">{{ isPlaying ? '【仓】 嗒 【仓】 嗒 · 板眼流转中' : '点击试听已生成的伴奏音频' }}</span>
                </div>
              </div>
              <p v-else class="audio-unavailable">当前仅提供简谱文本，伴奏音频未生成。</p>
              <audio v-if="taskResult.audio_url" ref="balladAudioRef" :src="taskResult.audio_url" @ended="isPlaying = false" style="display: none;"></audio>
            </div>

            <div class="result-desc">
              <div class="desc-header-row">
                <span class="tag-heritage">非遗艺术语言解析</span>
                <span v-if="taskResult.llm_generated" class="tag-llm-badge">
                  ✦ 大模型实时深度推理 · {{ taskResult.llm_model || '在线' }}
                </span>
              </div>
              <p class="main-desc-text">{{ taskResult.description }}</p>

              <!-- 真实大模型解析的文脉与工艺 -->
              <div v-if="taskResult.historical_context" class="extra-desc-item">
                <span class="extra-label">❖ 文脉渊源：</span>
                <span class="extra-text">{{ taskResult.historical_context }}</span>
              </div>
              <div v-if="taskResult.craft_technique" class="extra-desc-item">
                <span class="extra-label">❖ 工艺指导：</span>
                <span class="extra-text">{{ taskResult.craft_technique }}</span>
              </div>
              <div v-if="taskResult.color_palette && taskResult.color_palette.length" class="palette-row">
                <span class="extra-label">❖ 矿物分色：</span>
                <div class="palette-chips">
                  <span v-for="(col, ci) in taskResult.color_palette" :key="ci" class="color-chip">
                    {{ col }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 矢量图样与音频下载 -->
          <div class="asset-actions">
            <div v-if="taskResult.vector_svg_url || taskResult.colored_image_url || taskResult.print_template_url" class="asset-btn-box">
              <span class="asset-name">{{ currentTool === 'BALLAD' ? '工尺简谱文本' : (currentTool === 'BRONZE' ? '金石拓片/雕模矢量' : '矢量图样（下载预览）') }}</span>
              <button class="download-btn" @click="downloadTemplate">
                下载原生矢量图样 ↓
              </button>
            </div>
            <div v-if="taskResult.audio_url" class="asset-btn-box">
              <span class="asset-name">曲牌伴奏原声</span>
              <a :href="taskResult.audio_url" target="_blank" download="津门曲艺原声伴奏.ogg" class="download-btn">
                导出伴奏音频 ↗
              </a>
            </div>
          </div>

          <!-- 底部操作按钮 -->
          <div class="showcase-footer">
            <el-button v-if="currentTool === 'SHADOW_PUPPET'" type="warning" @click="openPuppetControlModal">
              🎭 皮影三签操纵台
            </el-button>
            <el-button type="info" style="background: #394A42; border-color: #394A42; color: #FFF;" @click="openExhibitionModal">
              🖨️ 生成 A4/A3 走廊展册
            </el-button>
            <el-button type="primary" class="btn-primary" :loading="evaluating" @click="runEvaluation(null)">
              ✦ 发起 AI 图像审美诊断 (+30 能量)
            </el-button>
            <el-button type="success" @click="shareToCommunity">
              发布到美育社区广场
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 图像审美诊断评价卡片弹窗 -->
    <el-dialog
      v-model="evalModalVisible"
      title="手工作品 · AI 图像审美诊断报告"
      width="680px"
      custom-class="eval-dialog"
      destroy-on-close
    >
      <div v-if="evalResult" class="eval-card-body">
        <div v-if="evalResult.llm_generated" class="eval-llm-live-banner">
          <span class="live-dot"></span>
          <span>已调用运营后台接入大模型 <strong>【{{ evalResult.llm_model }}】</strong> 执行实时多模态审美诊断</span>
        </div>

        <div class="eval-header-banner">
          <div class="eval-badge-seal">AI<br>测评</div>
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

        <!-- AI 测评建议 -->
        <div class="eval-mentor-box">
          <div class="mentor-title">
            <span class="mentor-icon">✒️</span>
            <span>AI 测评建议与进阶指引：</span>
          </div>
          <p class="mentor-quote">{{ evalResult.mentor_comment }}</p>
          <div class="mentor-sign">
            <span>{{ evalResult.certified_by }}</span>
            <span class="eval-date">{{ evalResult.created_at }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="evalModalVisible = false">关闭报告</el-button>
      </template>
    </el-dialog>

    <!-- 津派皮影三签联动操纵台 (P2) -->
    <el-dialog
      v-model="puppetModalVisible"
      title="🎭 津派皮影传统三签操纵台 · 骨骼微交互"
      width="780px"
      custom-class="puppet-dialog"
      destroy-on-close
    >
      <div class="puppet-stage-layout">
        <!-- 操纵互动舞台 -->
        <div class="stage-screen">
          <svg viewBox="0 0 400 450" class="puppet-stage-svg">
            <defs>
              <radialGradient id="stage-spot" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#FFF8EE"/>
                <stop offset="80%" stop-color="#F3E5CF"/>
                <stop offset="100%" stop-color="#E2CCA8"/>
              </radialGradient>
            </defs>
            <rect width="400" height="450" fill="url(#stage-spot)" rx="12"/>
            <line x1="20" y1="420" x2="380" y2="420" stroke="#8B4A2F" stroke-width="4" stroke-dasharray="8,4" opacity="0.4"/>
            
            <!-- 骨骼活动总成 (通过三签角度 transform 联动) -->
            <g :transform="`translate(200, 240) rotate(${neckAngle})`">
              <!-- 躯干 -->
              <rect x="-24" y="-30" width="48" height="90" rx="8" fill="#C1272D" stroke="#332C27" stroke-width="2"/>
              <!-- 头与翎毛 -->
              <g transform="translate(0, -60)">
                <circle cx="0" cy="0" r="22" fill="#FAF0E6" stroke="#332C27" stroke-width="2"/>
                <path d="M-15,-20 Q0,-45 15,-20 Z" fill="#2F4F4F"/>
                <!-- 翎毛 -->
                <path d="M0,-45 Q30,-80 45,-10" fill="none" stroke="#FFD700" stroke-width="3"/>
              </g>
              <!-- 左臂 (手签一联动) -->
              <g :transform="`translate(-24, -15) rotate(${leftArmAngle})`">
                <rect x="-8" y="0" width="16" height="45" rx="5" fill="#FAF0E6" stroke="#332C27" stroke-width="2"/>
                <g transform="translate(0, 45) rotate(20)">
                  <rect x="-6" y="0" width="12" height="40" rx="4" fill="#C1272D" stroke="#332C27" stroke-width="2"/>
                  <!-- 操纵手签竹竿连杆 -->
                  <line x1="0" y1="35" x2="-40" y2="120" stroke="#8B5A2B" stroke-width="3"/>
                </g>
              </g>
              <!-- 右臂 (手签二联动) -->
              <g :transform="`translate(24, -15) rotate(${rightArmAngle})`">
                <rect x="-8" y="0" width="16" height="45" rx="5" fill="#FAF0E6" stroke="#332C27" stroke-width="2"/>
                <g transform="translate(0, 45) rotate(-20)">
                  <rect x="-6" y="0" width="12" height="40" rx="4" fill="#C1272D" stroke="#332C27" stroke-width="2"/>
                  <!-- 折扇或大刀道具 -->
                  <polygon points="-5,35 25,15 35,45" fill="#F9D423" stroke="#332C27" stroke-width="1.5"/>
                  <!-- 操纵手签竹竿连杆 -->
                  <line x1="0" y1="35" x2="40" y2="120" stroke="#8B5A2B" stroke-width="3"/>
                </g>
              </g>
              <!-- 下肢裙摆 -->
              <polygon points="-24,60 24,60 35,130 -35,130" fill="#2F4F4F" stroke="#332C27" stroke-width="2"/>
              <!-- 主签（颈部平衡支撑杆） -->
              <line x1="0" y1="20" x2="0" y2="170" stroke="#654321" stroke-width="4"/>
            </g>
          </svg>
        </div>

        <!-- 操纵杆控制台 -->
        <div class="stage-controls">
          <div class="control-header">
            <h4 class="font-serif" style="margin: 0 0 6px; color: #8B4A2F;">❖ 三签操纵杠杆手柄</h4>
            <p style="font-size: 12px; color: #7D756C; margin: 0;">拖动操纵签，体验皮影“签随人动，人随签活”传统把式</p>
          </div>

          <div class="rod-slider-item">
            <div class="slider-label">
              <span>🥢 主签（颈签·平衡倾仰）</span>
              <strong>{{ neckAngle }}°</strong>
            </div>
            <el-slider v-model="neckAngle" :min="-30" :max="30" @input="playGongSound" />
          </div>

          <div class="rod-slider-item">
            <div class="slider-label">
              <span>🥢 手签一（左臂武戏挥枪）</span>
              <strong>{{ leftArmAngle }}°</strong>
            </div>
            <el-slider v-model="leftArmAngle" :min="-80" :max="60" @input="playGongSound" />
          </div>

          <div class="rod-slider-item">
            <div class="slider-label">
              <span>🥢 手签二（右臂文戏抚袖）</span>
              <strong>{{ rightArmAngle }}°</strong>
            </div>
            <el-slider v-model="rightArmAngle" :min="-60" :max="80" @input="playGongSound" />
          </div>

          <div class="presets-row">
            <span style="font-size: 12px; color: #8C827A; font-weight: 600;">把式身段预设：</span>
            <div class="preset-buttons">
              <el-button size="small" round @click="setPuppetPose(0, -40, 20)">抱拳作揖</el-button>
              <el-button size="small" round @click="setPuppetPose(-15, 40, -50)">展臂亮相</el-button>
              <el-button size="small" round @click="setPuppetPose(15, -70, 60)">翻腾腾挪</el-button>
            </div>
          </div>

          <div class="drum-sound-bar">
            <el-button type="success" size="small" round @click="triggerDrumBeat">
              🥁 敲响津门皮影锣鼓点
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- A4/A3 成果走廊实体展册排版弹窗 (P2) -->
    <el-dialog
      v-model="exhibitionModalVisible"
      title="🖨️ 乡村小学非遗成果展册 · A4/A3 排版预览"
      width="820px"
      custom-class="exhibition-dialog"
      destroy-on-close
    >
      <div id="print-sheet" class="exhibition-sheet">
        <div class="sheet-border">
          <div class="sheet-header">
            <div class="header-logo-group">
              <span class="sheet-seal">津</span>
              <div>
                <h2 class="font-serif sheet-main-title">天津市乡村非遗美育成果展 · 作品展册</h2>
                <p class="sheet-sub">本页为本地排版预览，未接入实体展览认证</p>
              </div>
            </div>
            <div class="sheet-batch-stamp">
              <span>【排版预览】</span>
              <span>打印前请人工核验</span>
            </div>
          </div>

          <div class="sheet-grid">
            <!-- 左侧：线稿与激光切割打印纸样 -->
            <div class="sheet-left">
              <div class="laser-cut-card">
                <div class="laser-badge">作品图样参考 · 未验证激光切割参数</div>
                <img :src="taskResult?.line_art_url || taskResult?.colored_image_url || '/static/images/shadow_puppet_1.svg'" class="laser-preview-img" />
                <div class="laser-cut-notice">
                  <span>✂️ 沿轮廓剪裁（参考）</span>
                  <span>⭕ 关节打孔（参考）</span>
                  <span>🥢 竹签控制点（参考）</span>
                </div>
              </div>
            </div>

            <!-- 右侧：艺术赏析、名师点评与二维码 -->
            <div class="sheet-right">
              <h3 class="font-serif exhibit-title">{{ taskResult?.title || '未命名作品' }}</h3>

              <div class="sheet-detail-box">
                <template v-if="taskResult?.historical_context">
                  <h4>❖ 非遗文脉渊源：</h4>
                  <p>{{ taskResult.historical_context }}</p>
                </template>

                <template v-if="taskResult?.craft_technique">
                  <h4>❖ 工艺指导要领：</h4>
                  <p>{{ taskResult.craft_technique }}</p>
                </template>

                <template v-if="taskResult?.description">
                  <h4>❖ 作品解析：</h4>
                  <p style="color: #8B4A2F; font-weight: 500;">{{ taskResult.description }}</p>
                </template>
              </div>
            </div>
          </div>

          <div class="sheet-footer">
            <span>标准规格：A4 (210×297mm) / A3 (297×420mm)</span>
            <span>纸张建议：250g 仿古宣纸卡纸 / 哑光高保真铜版纸</span>
            <span>本地排版预览 · 未接入实体认证</span>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="exhibitionModalVisible = false">关闭预览</el-button>
        <el-button type="primary" style="background: #8B4A2F; border-color: #8B4A2F;" @click="triggerBrowserPrint">
          🖨️ 呼起浏览器标准打印 (A4/A3)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../api/request'

const tools = [
  { key: 'SHADOW_PUPPET', icon: '🎭', name: '津派皮影生成', desc: '三签关节、镂空刀法、矢量图样' },
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

// 针对曲艺类伴奏音频的播放控制
const balladAudioRef = ref<HTMLAudioElement | null>(null)
const isPlaying = ref(false)

const toggleAudioPlay = () => {
  if (!balladAudioRef.value) return
  if (isPlaying.value) {
    balladAudioRef.value.pause()
    isPlaying.value = false
  } else {
    balladAudioRef.value.play().then(() => {
      isPlaying.value = true
    }).catch(() => {
      isPlaying.value = false
      ElMessage.error('伴奏音频加载失败，请稍后重试')
    })
  }
}

// 统一的多模态艺术成果图解析（优先彩色图、渲染图、完成线稿与矢量曲谱）
const displayImageUrl = computed(() => {
  if (!taskResult.value) return ''
  return (
    taskResult.value.colored_image_url ||
    taskResult.value.rendered_image_url ||
    taskResult.value.completed_sketch_url ||
    taskResult.value.sheet_music_url ||
    taskResult.value.vector_svg_url ||
    ''
  )
})

// 图片加载容错兜底，绝对不展示系统级裂图
const handleImgError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (!img) return
  img.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='400' viewBox='0 0 600 400'><rect width='100%' height='100%' fill='%23FAF6ED'/><rect x='20' y='20' width='560' height='360' fill='none' stroke='%238B4A2F' stroke-width='2' stroke-dasharray='6,4' rx='8'/><text x='300' y='180' font-size='20' font-family='serif' font-weight='bold' fill='%238B4A2F' text-anchor='middle'>❖ 津韵润乡 · 天津非遗创客资产</text><text x='300' y='215' font-size='13' fill='%237D695B' text-anchor='middle'>高精原生矢量图谱已就绪</text></svg>"
}

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

const selectTool = async (key: string) => {
  currentTool.value = key
  if (presetPrompts.value.length > 0) {
    promptText.value = presetPrompts.value[0]
  }
  taskResult.value = null
  if (isPlaying.value && balladAudioRef.value) {
    balladAudioRef.value.pause()
    isPlaying.value = false
  }
  // 切换分类时，尝试拉取该分类下用户最近的生成历史
  await fetchLatestTask(key)
}

const fetchLatestTask = async (toolKey?: string) => {
  try {
    const res: any = await request.get('/ai/tasks/latest', {
      params: toolKey ? { tool_type: toolKey } : {}
    })
    if (res && res.result) {
      taskResult.value = res.result
      if (res.input && res.input.prompt) {
        promptText.value = res.input.prompt
      }
    }
  } catch (e) {
    // 静默忽略
  }
}

onMounted(async () => {
  await fetchLatestTask(currentTool.value)
})

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
    progressVal.value = 25
    progressText.value = '大模型正在实时深度推理与构思...'

    // 真实异步轮询直到任务成功
    let attempts = 0
    const maxAttempts = 35
    const pollInterval = setInterval(async () => {
      attempts++
      try {
        const pollRes: any = await request.get(`/ai/tasks/${taskId}`)
        if (pollRes && pollRes.status === 'SUCCESS') {
          clearInterval(pollInterval)
          progressVal.value = 100
          progressText.value = '多模态艺术资产与大模型推理已生成完成！'
          taskResult.value = pollRes.result
          generating.value = false
          ElMessage.success('非遗 AI 作品实时生成成功！美育能量 +20')
        } else if (pollRes && pollRes.status === 'FAILED') {
          clearInterval(pollInterval)
          generating.value = false
          ElMessage.error(pollRes.error_message || '生成失败，请重试')
        } else {
          if (progressVal.value < 88) {
            progressVal.value += 12
          }
          if (progressVal.value > 50) {
            progressText.value = '正在进行津派传统矿物套色与矢量纸样渲染...'
          }
        }
      } catch (err) {
        // 继续轮询
      }

      if (attempts >= maxAttempts) {
        clearInterval(pollInterval)
        generating.value = false
        ElMessage.error('生成任务耗时较长，请稍后在个人中心查看')
      }
    }, 1000)

  } catch (e) {
    generating.value = false
    ElMessage.error('生成任务失败，请重试')
  }
}

const downloadTemplate = () => {
  const url = taskResult.value?.print_template_url || 
              taskResult.value?.vector_svg_url || 
              taskResult.value?.colored_image_url || 
              displayImageUrl.value
  if (url) {
    const link = document.createElement('a')
    link.href = url
    link.download = `津韵润乡_${currentToolName.value}_矢量图样.svg`
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success(`已为您导出【${currentToolName.value}】高精度矢量图样！`)
  } else {
    ElMessage.info('正在为您生成津派非遗打印纸样...')
  }
}

const shareToCommunity = async () => {
  if (!displayImageUrl.value) {
    ElMessage.warning('请先生成或上传作品图后再发布')
    return
  }
  try {
    await request.post('/community/posts', {
      title: `我的AI非遗工坊作品：${promptText.value.slice(0, 18)}`,
      content: `在《津韵润乡》AI工坊创作完成了【${currentToolName.value}】作品，感受到了家乡非遗的美！`,
      category: currentTool.value,
      cover_url: displayImageUrl.value
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
  const targetImg = customImg || displayImageUrl.value
  if (!targetImg) {
    ElMessage.warning('请先生成或上传作品图后再诊断')
    return
  }
  if (!customImg && !/\.(png|jpe?g|webp)(\?|$)/i.test(targetImg)) {
    ElMessage.warning('当前作品是 SVG/矢量图，AI 图像测评仅支持 PNG/JPEG/WebP；请上传作品照片')
    return
  }
  evaluating.value = true
  try {
    const targetTitle = customTitle || taskResult.value?.description?.slice(0, 16) || '津派非遗手作创客作品'
    const res: any = await request.post('/ai/evaluate', {
      image_url: targetImg,
      heritage_type: currentTool.value,
      title: targetTitle
    })
    evalResult.value = res
    evalModalVisible.value = true
    ElMessage.success(res.energy_reward ? `AI 图像审美诊断完成，美育能量 +${res.energy_reward}` : 'AI 图像审美诊断完成')
  } catch (e) {
    ElMessage.error('审美诊断失败，请重试')
  } finally {
    evaluating.value = false
  }
}

// 🎭 P2: 津派皮影三签联动操纵台逻辑
const puppetModalVisible = ref(false)
const neckAngle = ref(0)
const leftArmAngle = ref(-20)
const rightArmAngle = ref(15)

let audioCtx: AudioContext | null = null
const getAudioCtx = () => {
  if (!audioCtx) {
    const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext
    if (AudioCtxClass) {
      audioCtx = new AudioCtxClass()
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume()
  }
  return audioCtx
}

// 仿真津门皮影小锣/小钹点
const playGongSound = () => {
  try {
    const ctx = getAudioCtx()
    if (!ctx) return
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(840, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(420, ctx.currentTime + 0.18)
    gain.gain.setValueAtTime(0.12, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.2)
  } catch (e) {
    // 静默降级
  }
}

// 仿真津派皮影堂鼓重音点
const triggerDrumBeat = () => {
  try {
    const ctx = getAudioCtx()
    if (!ctx) return
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'triangle'
    osc.frequency.setValueAtTime(160, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(45, ctx.currentTime + 0.25)
    gain.gain.setValueAtTime(0.35, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.3)
    ElMessage.success('🥁 咚——！津门皮影大靠亮式，堂鼓震响！')
  } catch (e) {
    ElMessage.info('咚——！')
  }
}

const setPuppetPose = (neck: number, left: number, right: number) => {
  neckAngle.value = neck
  leftArmAngle.value = left
  rightArmAngle.value = right
  playGongSound()
}

const openPuppetControlModal = () => {
  puppetModalVisible.value = true
}

// 🖨️ P2: 走廊实体展册排版逻辑
const exhibitionModalVisible = ref(false)

const openExhibitionModal = () => {
  exhibitionModalVisible.value = true
}

const triggerBrowserPrint = () => {
  window.print()
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
  background: var(--color-paper);
}

.result-img-box {
  width: 100%;
  min-height: 280px;
  max-height: 380px;
  background: #FAF6ED;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-bottom: 1px solid rgba(196, 134, 58, 0.2);
}

.result-img {
  width: 100%;
  max-height: 380px;
  object-fit: contain;
  display: block;
  transition: transform 0.3s ease;
}

.result-img:hover {
  transform: scale(1.01);
}

.result-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
  font-size: 15px;
  padding: 40px;
}

.placeholder-icon {
  font-size: 32px;
}

/* 曲艺伴奏与鼓板试听播控器 */
.ballad-player-box {
  padding: 14px 18px;
  background: linear-gradient(135deg, #FFFDF8 0%, #FBF4E8 100%);
  border-bottom: 1px dashed rgba(196, 134, 58, 0.3);
}

.ballad-player-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.ballad-player-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-primary);
}

.ballad-rhythm-badge {
  font-size: 11px;
  padding: 3px 10px;
  background: rgba(182, 62, 44, 0.1);
  color: #B63E2C;
  border: 1px solid rgba(182, 62, 44, 0.25);
  border-radius: 12px;
  font-weight: 600;
}

.ballad-score-display {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--color-text-regular);
}

.score-label {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.score-notation {
  background: #FFF;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid rgba(214, 168, 92, 0.4);
  color: #2E241E;
  font-weight: 700;
  font-family: monospace;
  font-size: 13px;
}

.ballad-audio-controls {
  display: flex;
  align-items: center;
  gap: 14px;
}

.audio-unavailable {
  margin: 0;
  font-size: 12px;
  color: #8C827A;
}

.audio-play-toggle-btn {
  background: var(--color-primary);
  color: #FFF;
  border: none;
  padding: 7px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(139, 74, 47, 0.25);
}

.audio-play-toggle-btn:hover {
  background: #A35939;
  transform: translateY(-1px);
}

.rhythm-beat-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
  padding: 5px 12px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  border: 1px solid var(--color-border);
}

.rhythm-beat-indicator.beating {
  color: #B63E2C;
  border-color: rgba(182, 62, 44, 0.35);
  animation: drumPulse 1s infinite alternate;
}

@keyframes drumPulse {
  0% { transform: scale(1); }
  100% { transform: scale(1.02); }
}

.drum-beat-icon {
  font-size: 14px;
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

/* 实时大模型标识与文脉解析样式 */
.desc-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.tag-llm-badge {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.main-desc-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-main);
  margin-bottom: 10px;
}
.extra-desc-item {
  background: #fbf8f3;
  border-left: 3px solid var(--color-primary);
  padding: 6px 10px;
  border-radius: 0 4px 4px 0;
  margin-bottom: 6px;
  font-size: 12px;
  line-height: 1.5;
}
.extra-label {
  font-weight: 700;
  color: var(--color-primary);
}
.extra-text {
  color: var(--color-text-regular);
}
.palette-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 12px;
}
.palette-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.color-chip {
  background: #efe8dc;
  color: #5d4a36;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-family: monospace;
}
.eval-llm-live-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  margin-bottom: 12px;
}
.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
}

/* 🎭 皮影操纵台样式 */
.puppet-stage-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: center;
  padding: 10px;
}

.stage-screen {
  background: #201915;
  border-radius: 12px;
  padding: 12px;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
}

.puppet-stage-svg {
  width: 100%;
  max-width: 320px;
  height: auto;
  filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.4));
}

.stage-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #FDF9F2;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #E8D8C4;
}

.rod-slider-item {
  background: #FFF;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #EEDBC8;
}

.slider-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #554438;
  margin-bottom: 6px;
}

.slider-label strong {
  color: #8B4A2F;
}

.presets-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preset-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.drum-sound-bar {
  margin-top: 8px;
  text-align: center;
}

/* 🖨️ 走廊实体展册排版样式 */
.exhibition-sheet {
  background: #FFFDF9;
  padding: 24px;
  border-radius: 8px;
  color: #2D241E;
}

.sheet-border {
  border: 3px double #8B4A2F;
  padding: 20px;
  position: relative;
  background-color: #FAF7F0;
  background-image: radial-gradient(#D6C2A5 0.75px, transparent 0.75px);
  background-size: 16px 16px;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #8B4A2F;
  padding-bottom: 14px;
  margin-bottom: 20px;
}

.header-logo-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.sheet-seal {
  width: 44px;
  height: 44px;
  background: #A63428;
  color: #FFF;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 900;
  font-family: serif;
  box-shadow: 0 2px 6px rgba(166, 52, 40, 0.4);
}

.sheet-main-title {
  font-size: 19px;
  color: #8B4A2F;
  margin: 0 0 4px;
  letter-spacing: 1px;
}

.sheet-sub {
  font-size: 12px;
  color: #786B61;
  margin: 0;
}

.sheet-batch-stamp {
  text-align: right;
  font-size: 11px;
  color: #A63428;
  font-weight: 700;
  border: 1px dashed #A63428;
  padding: 4px 8px;
  border-radius: 4px;
}

.sheet-batch-stamp span {
  display: block;
}

.sheet-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 20px;
  margin-bottom: 20px;
}

.laser-cut-card {
  background: #FFF;
  border: 2px dashed #9E897A;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.laser-badge {
  font-size: 11px;
  background: #EDE3D4;
  color: #634C3E;
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
  margin-bottom: 10px;
}

.laser-preview-img {
  width: 100%;
  max-height: 220px;
  object-fit: contain;
  margin-bottom: 12px;
  background: #FAF8F5;
  border: 1px solid #EFEAE3;
  border-radius: 6px;
}

.laser-cut-notice {
  display: flex;
  justify-content: space-around;
  font-size: 11px;
  color: #7D6F63;
  border-top: 1px dotted #DCD0C2;
  padding-top: 8px;
}

.exhibit-title {
  font-size: 18px;
  color: #362923;
  margin: 0 0 10px;
}

.author-tag-row {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.sheet-tag {
  background: #F0E8DD;
  color: #695243;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.sheet-detail-box {
  background: #FFF;
  border: 1px solid #EFE6DA;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.sheet-detail-box h4 {
  font-size: 12px;
  color: #8B4A2F;
  margin: 8px 0 3px;
}

.sheet-detail-box h4:first-child {
  margin-top: 0;
}

.sheet-detail-box p {
  font-size: 12px;
  color: #554438;
  line-height: 1.5;
  margin: 0;
}

.sheet-qr-box {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #FAF3E8;
  border: 1px solid #E4D5C0;
  border-radius: 6px;
  padding: 10px 14px;
}

.qr-code-mock {
  width: 44px;
  height: 44px;
  background: #FFF;
  border: 1px solid #D5C1A7;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-meta strong {
  font-size: 12px;
  color: #4A3A2F;
  display: block;
}

.qr-meta p {
  font-size: 10px;
  color: #7D6C5F;
  margin: 2px 0 0;
  font-family: monospace;
}

.sheet-footer {
  display: flex;
  justify-content: space-between;
  border-top: 1px solid #D5C2B0;
  padding-top: 10px;
  font-size: 10px;
  color: #8E7D70;
}

@media print {
  body * {
    visibility: hidden;
  }
  #print-sheet, #print-sheet * {
    visibility: visible;
  }
  #print-sheet {
    position: fixed;
    left: 0;
    top: 0;
    width: 100vw;
    height: 100vh;
    padding: 0;
    margin: 0;
    background: #FFF;
  }
}
</style>
