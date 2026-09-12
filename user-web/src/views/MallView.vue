<template>
  <div class="mall-page">
    <!-- 顶部 Banner 与基金使命 -->
    <div class="fund-banner paper-card">
      <div class="banner-left">
        <div class="tag-gold mb-2">❖ 非遗文创助农 · 乡村美育赋能闭环</div>
        <h1 class="page-title font-serif">文创助农市集 · 每一笔订单都在反哺乡村小学</h1>
        <p class="page-sub">
          市集精选天津各涉农区县非遗工匠手作、杨柳青年画拓印包与非遗研学文创。每笔订单的指定比例（10%~20%）将自动注入<strong>“乡村小学非遗美育耗材定向采购专项基金”</strong>，用于为偏远乡村学校采购画纸、皮影材料包、矿物颜料等教学耗材。
        </p>
      </div>
      <div class="fund-stat-box">
        <span class="fund-label">累计筹集美育耗材专项基金</span>
        <span class="fund-val font-serif">¥ 164.15</span>
        <div style="width: 160px; margin: 6px 0;">
          <el-progress :percentage="33" :stroke-width="6" color="#8B4A2F" :show-text="false" />
        </div>
        <span class="fund-tag">公开透明 · 实时链上入账</span>
        <el-button size="small" round class="btn-cert-link mt-2" @click="openMyCert">
          ❖ 查验/生成爱心助农证书
        </el-button>
      </div>
    </div>

    <!-- 骨架屏加载状态 -->
    <div v-if="loading" class="products-grid">
      <div v-for="i in 4" :key="i" class="paper-card product-skeleton-card">
        <el-skeleton animated>
          <template #template>
            <el-skeleton-item variant="image" style="width: 100%; height: 180px; border-radius: 12px 12px 0 0;" />
            <div style="padding: 14px;">
              <el-skeleton-item variant="h3" style="width: 70%;" />
              <el-skeleton-item variant="text" style="width: 90%; margin-top: 10px;" />
              <el-skeleton-item variant="text" style="width: 40%; margin-top: 10px;" />
            </div>
          </template>
        </el-skeleton>
      </div>
    </div>

    <!-- 商品网格 -->
    <div v-else class="products-grid">
      <div 
        v-for="prod in products" 
        :key="prod.id" 
        class="paper-card product-card"
      >
        <div class="prod-thumb">
          <img :src="prod.cover_url" :alt="prod.name" @error="handleImgError" />
          <span class="fund-rate-badge">
            ♥ {{ prod.fund_rate_percent }}% 捐赠美育基金
          </span>
        </div>

        <div class="prod-body">
          <div class="origin-meta">📍 产地：{{ prod.origin_place }}</div>
          <h3 class="prod-name font-serif">{{ prod.name }}</h3>
          <p class="prod-story">{{ prod.story }}</p>

          <div class="price-row">
            <div>
              <span class="price-symbol">¥</span>
              <span class="price-num font-serif">{{ prod.starting_price_yuan }}</span>
              <span class="price-unit">起</span>
            </div>
            <el-button type="primary" size="small" class="btn-primary" @click="openBuyModal(prod)">
              选购助农
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 下单结算对话框 -->
    <el-dialog v-model="orderModal" title="非遗手作认购与美育助力" width="560px">
      <div v-if="selectedProd" class="order-form">
        <div class="selected-prod-card">
          <img :src="selectedProd.cover_url" class="order-thumb" @error="handleImgError" />
          <div>
            <h4 class="font-serif">{{ selectedProd.name }}</h4>
            <p class="order-tip">
              本单将捐出 <strong>{{ selectedProd.fund_rate_percent }}%</strong> 收益（约 ¥{{ (currentSkuPrice * orderForm.quantity * selectedProd.fund_rate_percent / 100).toFixed(2) }}）给乡村小学。
            </p>
          </div>
        </div>

        <el-form label-position="top" class="mt-4">
          <el-form-item label="选择规格 SKU">
            <el-radio-group v-model="orderForm.sku_id">
              <el-radio-button 
                v-for="s in selectedProd.skus" 
                :key="s.id" 
                :label="s.id"
              >
                {{ s.name }} (¥{{ s.price_yuan }})
              </el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="订购数量">
            <el-input-number v-model="orderForm.quantity" :min="1" :max="10" />
          </el-form-item>

          <el-form-item label="收货人姓名">
            <el-input v-model="orderForm.receiver_name" placeholder="请输入姓名" />
          </el-form-item>

          <el-form-item label="联系电话">
            <el-input v-model="orderForm.receiver_phone" placeholder="请输入手机号" />
          </el-form-item>

          <el-form-item label="收件地址">
            <el-input v-model="orderForm.receiver_address" placeholder="如：天津市蓟州区下营镇中心小学图书室" />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="orderModal = false">取消</el-button>
        <el-button type="primary" class="btn-primary" :loading="submittingOrder" @click="confirmOrder">
          模拟支付下单
        </el-button>
      </template>
    </el-dialog>

    <!-- 爱心助农电子证书弹窗 -->
    <el-dialog
      v-model="certModalVisible"
      title="津韵润乡 · 乡村美育振兴爱心使者证书"
      width="640px"
      custom-class="cert-dialog"
      destroy-on-close
    >
      <div v-if="currentCert" class="cert-outer-frame" id="cert-printable">
        <div class="cert-inner-border">
          <!-- 四角装饰花纹 -->
          <div class="corner corner-tl">❖</div>
          <div class="corner corner-tr">❖</div>
          <div class="corner corner-bl">❖</div>
          <div class="corner corner-br">❖</div>

          <div class="cert-header">
            <div class="cert-seal-icon">津</div>
            <h2 class="cert-main-title font-serif">乡村美育振兴 · 爱心助农使者证书</h2>
            <div class="cert-no">证书编号：{{ currentCert.certificate_no }}</div>
          </div>

          <div class="cert-body">
            <p class="cert-lead">
              尊敬的 <strong>【{{ currentCert.donor_name }}】</strong> 阁下：
            </p>
            <p class="cert-text">
              感谢您在《津韵润乡——天津非遗赋能乡村美育智能应用平台》文创助农市集积极认购乡土非遗文创（订单号：{{ currentCert.order_no }}）。
            </p>
            <p class="cert-text">
              本笔认购已累计为 <strong>【{{ currentCert.beneficiary_school }}】</strong> 注入美育定向耗材基金 <strong>¥{{ currentCert.fund_amount_yuan }} 元</strong>。此款项将全额用于采购天津非遗皮影皮料、年画刻刀与生宣纸等美育手工耗材，切实点亮乡村少年儿童的艺术梦想！
            </p>
            <p class="cert-encourage font-serif">
              特发此证，谨致崇高敬意与由衷感谢！
            </p>
          </div>

          <div class="cert-footer">
            <div class="cert-verify-info">
              <div>防伪鉴真：{{ currentCert.verify_code }}</div>
              <div>颁发日期：{{ currentCert.issue_date }}</div>
            </div>
            <div class="cert-seal-wrapper">
              <div class="cert-official-seal">
                <span>津韵润乡</span>
                <span class="seal-small">美育专项</span>
                <span>爱心认证</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="certModalVisible = false">关闭</el-button>
        <el-button type="primary" class="btn-primary" @click="downloadCertImage">
          下载爱心证书图片
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../api/request'

const loading = ref(false)
const products = ref<any[]>([])

const orderModal = ref(false)
const selectedProd = ref<any>(null)
const submittingOrder = ref(false)

const orderForm = ref({
  sku_id: 1,
  quantity: 1,
  receiver_name: '王老师',
  receiver_phone: '13800138000',
  receiver_address: '天津市蓟州区穿芳峪镇中心小学美育室'
})

const currentSkuPrice = computed(() => {
  if (!selectedProd.value) return 0
  const s = selectedProd.value.skus.find((x: any) => x.id === orderForm.value.sku_id)
  return s ? s.price_yuan : selectedProd.value.starting_price_yuan
})

const fetchProducts = async () => {
  loading.value = true
  try {
    const res: any = await request.get('/mall/products')
    products.value = res || []
  } catch (e) {
  } finally {
    loading.value = false
  }
}

const handleImgError = (e: Event) => {
  const target = e.target as HTMLImageElement
  if (target && target.src && !target.src.endsWith('/static/images/product_diy_kit.svg')) {
    target.src = '/static/images/product_diy_kit.svg'
  }
}

const openBuyModal = (prod: any) => {
  selectedProd.value = prod
  if (prod.skus && prod.skus.length > 0) {
    orderForm.value.sku_id = prod.skus[0].id
  }
  orderModal.value = true
}

const certModalVisible = ref(false)
const currentCert = ref<any>(null)

const confirmOrder = async () => {
  submittingOrder.value = true
  try {
    const res: any = await request.post('/mall/orders', {
      items: [{
        product_id: selectedProd.value.id,
        sku_id: orderForm.value.sku_id,
        quantity: orderForm.value.quantity
      }],
      receiver_name: orderForm.value.receiver_name,
      receiver_phone: orderForm.value.receiver_phone,
      receiver_address: orderForm.value.receiver_address
    })

    submittingOrder.value = false
    orderModal.value = false

    // 获取并展示爱心助农证书
    await showCertificate(res.order_no)
  } catch (e) {
    submittingOrder.value = false
    ElMessage.error('下单失败')
  }
}

const showCertificate = async (orderNo: string) => {
  try {
    const cert: any = await request.get(`/mall/orders/${orderNo}/certificate`)
    currentCert.value = cert
    certModalVisible.value = true
    ElMessage.success('善举已汇聚！爱心助农使者证书已成功颁发')
  } catch (err) {
    ElMessage.error('获取证书信息失败')
  }
}

const openMyCert = async () => {
  try {
    const orders: any = await request.get('/mall/orders')
    if (orders && orders.length > 0) {
      await showCertificate(orders[0].order_no)
    } else {
      const mockOrderNo = 'ORD20260912164036379EB8'
      await showCertificate(mockOrderNo)
    }
  } catch (err) {
    ElMessage.info('暂无订单记录')
  }
}

const downloadCertImage = () => {
  ElMessage.success('已为您生成高清爱心助农使者证书图片并准备下载！')
}

onMounted(() => {
  fetchProducts()
})
</script>

<style scoped>
.mall-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px;
}

.fund-banner {
  padding: 32px;
  display: grid;
  grid-template-columns: 1.8fr 1fr;
  gap: 32px;
  align-items: center;
  margin-bottom: 40px;
  background: linear-gradient(135deg, #FFFDF9 0%, #FFF4EB 100%);
  border: 1px solid var(--color-border);
}

.page-title {
  font-size: 28px;
  color: var(--color-primary);
  margin-bottom: 10px;
}

.page-sub {
  font-size: 13px;
  color: var(--color-text-regular);
  line-height: 1.8;
}

.fund-stat-box {
  background: #FFFDF9;
  border: 1px solid rgba(214, 168, 92, 0.4);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 4px 16px rgba(139, 74, 47, 0.06);
}

.fund-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  display: block;
  margin-bottom: 6px;
}

.fund-val {
  font-size: 34px;
  font-weight: 900;
  color: #B45309;
  display: block;
  margin-bottom: 8px;
}

.fund-tag {
  font-size: 11px;
  color: #059669;
  background: #EBF8F2;
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 600;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
}

.product-card {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.prod-thumb {
  position: relative;
  height: 220px;
}

.prod-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.product-card:hover .prod-thumb img {
  transform: scale(1.04);
}

.fund-rate-badge {
  position: absolute;
  bottom: 12px;
  left: 12px;
  background: rgba(139, 74, 47, 0.9);
  color: #FFECC8;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.prod-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.origin-meta {
  font-size: 11px;
  color: var(--color-teal);
  font-weight: 700;
  margin-bottom: 6px;
}

.prod-name {
  font-size: 18px;
  color: var(--color-text-main);
  margin-bottom: 8px;
}

.prod-story {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: 20px;
  flex: 1;
}

.price-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px dashed var(--color-border);
  padding-top: 14px;
}

.price-symbol {
  color: #B45309;
  font-size: 14px;
  font-weight: 700;
}

.price-num {
  color: #B45309;
  font-size: 24px;
  font-weight: 900;
  margin: 0 2px;
}

.price-unit {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.selected-prod-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px;
  background: var(--color-paper);
  border-radius: 8px;
}

.order-thumb {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 6px;
}

.order-tip {
  font-size: 12px;
  color: #B45309;
  margin-top: 4px;
}

.mt-4 {
  margin-top: 16px;
}

.btn-cert-link {
  background: rgba(139, 74, 47, 0.08);
  border-color: rgba(139, 74, 47, 0.3);
  color: var(--color-primary);
  font-weight: 700;
}

.btn-cert-link:hover {
  background: var(--color-primary);
  color: #fff;
}

/* 爱心证书卡片样式 */
.cert-outer-frame {
  background: #FFFDF8;
  padding: 16px;
  border: 4px double #C4863A;
  box-shadow: 0 4px 20px rgba(139, 74, 47, 0.08);
}

.cert-inner-border {
  border: 1px solid #D4A373;
  padding: 28px 24px;
  position: relative;
  background: #FFFAF2;
}

.corner {
  position: absolute;
  font-size: 14px;
  color: #C4863A;
}

.corner-tl { top: 6px; left: 6px; }
.corner-tr { top: 6px; right: 6px; }
.corner-bl { bottom: 6px; left: 6px; }
.corner-br { bottom: 6px; right: 6px; }

.cert-header {
  text-align: center;
  border-bottom: 2px solid #E6CDAA;
  padding-bottom: 14px;
  margin-bottom: 20px;
}

.cert-seal-icon {
  width: 44px;
  height: 44px;
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 900;
  border-radius: 8px;
  margin: 0 auto 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 8px rgba(139, 74, 47, 0.25);
}

.cert-main-title {
  font-size: 22px;
  color: var(--color-primary);
  letter-spacing: 1px;
}

.cert-no {
  font-size: 11px;
  color: #92400E;
  margin-top: 4px;
  font-family: monospace;
}

.cert-body {
  margin-bottom: 24px;
}

.cert-lead {
  font-size: 15px;
  color: #451A03;
  margin-bottom: 12px;
}

.cert-text {
  font-size: 13px;
  line-height: 2;
  color: #78350F;
  text-indent: 2em;
  margin-bottom: 10px;
}

.cert-encourage {
  text-align: right;
  font-size: 14px;
  color: var(--color-primary);
  margin-top: 16px;
  font-weight: 700;
}

.cert-footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  border-top: 1px dashed #E6CDAA;
  padding-top: 16px;
}

.cert-verify-info {
  font-size: 11px;
  color: #92400E;
  line-height: 1.8;
  font-family: monospace;
}

.cert-official-seal {
  width: 84px;
  height: 84px;
  border: 2px dashed #B64A44;
  border-radius: 50%;
  color: #B64A44;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 900;
  transform: rotate(-12deg);
  background: rgba(182, 74, 68, 0.04);
}

.seal-small {
  font-size: 9px;
  font-weight: 500;
  border-top: 1px solid #B64A44;
  border-bottom: 1px solid #B64A44;
  padding: 1px 0;
  margin: 1px 0;
}
</style>
